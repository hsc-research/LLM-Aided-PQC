"""Read-only, bounded summaries of current source-bound proposal records.

Never follows recorded paths, runs tools, loads API credentials, or treats a
proposal preview as functional verification. Historical logs are separate.
"""
from pathlib import Path
import hashlib
import json
import math
import re
from .asic_dashboard import collect as collect_asic

LIMIT = 4 * 1024 * 1024


def read_record(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > LIMIT:
        raise ValueError('Missing, symlinked, or oversized record')
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('Record must be an object')
    return value, hashlib.sha256(raw).hexdigest()


def number(value):
    return value if type(value) in (int, float) and math.isfinite(value) else None


def label(value):
    # Never expose credential-like content from errors or untrusted records.
    value = str(value or '')[:240]
    return re.sub(r'(?i)(sk-[a-z0-9_-]+|(?:api[_ -]?key|authorization)\s*[:=]\s*\S+)', '[redacted]', value)


def resource_instances(text):
    """Rank reported hierarchical rows; overlapping rows must never be summed."""
    headings = None
    result = []
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        cells = [part.strip() for part in line.split('|')[1:-1]]
        if 'Instance' in cells and 'Total LUTs' in cells:
            headings = cells
            continue
        if not headings or len(cells) != len(headings):
            continue
        row = dict(zip(headings, cells))
        name = row.get('Instance', '')
        if not name or name.startswith('(') or row.get('Module') == '(top)':
            continue
        if not row.get('Total LUTs', '').replace(',', '').isdigit():
            continue
        item = {'instance': label(name), 'module': label(row.get('Module'))}
        for source, target in [('Total LUTs', 'luts'), ('FFs', 'ffs'), ('RAMB36', 'ramb36'), ('RAMB18', 'ramb18'), ('DSP Blocks', 'dsp')]:
            value = row.get(source, '').replace(',', '')
            item[target] = int(value) if value.isdigit() else None
        result.append(item)
    return sorted(result, key=lambda row: row['luts'], reverse=True)[:12]


def timing_paths(text):
    """Read reported Vivado paths, retaining setup/hold type and ns units."""
    paths = []
    for block in re.split(r'(?=^Slack \(\w+\)\s*:)', text, flags=re.M):
        slack = re.match(r'Slack \(\w+\)\s*:\s*([-+]?\d+(?:\.\d+)?)ns', block)
        if not slack:
            continue
        def field(name):
            found = re.search(r'^\s*' + re.escape(name) + r':\s*([^\n]+)', block, re.M)
            return label(found.group(1).strip()) if found else None
        def numeric(pattern):
            found = re.search(pattern, block)
            return number(float(found.group(1))) if found else None
        paths.append({'startpoint': field('Source'), 'endpoint': field('Destination'),
                      'path_group': field('Path Group'), 'path_type': field('Path Type'),
                      'slack_ns': number(float(slack.group(1))),
                      'data_path_delay_ns': numeric(r'Data Path Delay:\s*([0-9.]+)ns'),
                      'logic_delay_ns': numeric(r'\(logic\s+([0-9.]+)ns'),
                      'net_delay_ns': numeric(r'route\s+([0-9.]+)ns'),
                      'logic_levels': numeric(r'Logic Levels:\s*(\d+)')})
        if len(paths) == 16:
            break
    return paths


def report_summary(reports):
    """Parse observations only; positive slack does not qualify timing."""
    timing = str(reports.get('timing.rpt', ''))
    utilization = str(reports.get('utilization.rpt', ''))
    check = str(reports.get('check_timing.rpt', ''))
    result = {'worst_setup_slack_ns': None, 'worst_hold_slack_ns': None, 'latency_cycles': None, 'luts': None, 'ffs': None,
              'ramb36': None, 'ramb18': None, 'bram_tiles': None, 'dsp': None, 'power_w': None}
    match = re.search(r'^\s*WNS\(ns\).*\n[^\n]*\n\s*([-+]?\d+(?:\.\d+)?)', timing, re.M)
    if match:
        result['worst_setup_slack_ns'] = float(match.group(1))
        # Global timing-summary column 5 is WHS, not a setup clock-table value.
        row = timing[match.start():].splitlines()[2].split()
        if len(row) >= 8 and 'WHS(ns)' in timing[match.start():].splitlines()[0]:
            try:
                result['worst_hold_slack_ns'] = number(float(row[4]))
            except ValueError:
                pass
    rows = [line.split('|')[1:-1] for line in utilization.splitlines() if line.startswith('|')]
    for i, row in enumerate(rows):
        headings = [x.strip() for x in row]
        if 'Total LUTs' not in headings:
            continue
        for values in rows[i + 1:]:
            values = [x.strip() for x in values]
            if len(values) != len(headings):
                continue
            mapped = dict(zip(headings, values))
            if not mapped.get('Total LUTs', '').isdigit():
                continue
            for source, dest in [('Total LUTs', 'luts'), ('FFs', 'ffs'), ('RAMB36', 'ramb36'), ('RAMB18', 'ramb18'), ('DSP Blocks', 'dsp')]:
                if mapped.get(source, '').isdigit():
                    result[dest] = int(mapped[source])
            break
        break
    # Flat report_utilization tables use resource rows rather than instances.
    # Keep RAMB counts and 36-Kbit tile-equivalent usage distinct.
    flat_labels = {'Slice LUTs': 'luts', 'CLB LUTs': 'luts',
                   'Slice Registers': 'ffs', 'CLB Registers': 'ffs',
                   'Block RAM Tile': 'bram_tiles', 'RAMB36/FIFO*': 'ramb36',
                   'RAMB36/FIFO': 'ramb36', 'RAMB18': 'ramb18',
                   'DSPs': 'dsp', 'DSP48E1': 'dsp', 'DSP48E2': 'dsp'}
    for row in rows:
        cells = [cell.strip() for cell in row]
        if len(cells) < 2:
            continue
        key = flat_labels.get(cells[0].rstrip('*').strip())
        if key is None or result[key] is not None:
            continue
        token = cells[1].replace(',', '')
        if not re.fullmatch(r'\d+(?:\.\d+)?', token):
            continue
        value = float(token)
        if math.isfinite(value) and (key == 'bram_tiles' or value.is_integer()):
            result[key] = int(value) if value.is_integer() else value
    warnings = {}
    for field in ('no_clock', 'unconstrained_internal_endpoints', 'no_input_delay', 'no_output_delay', 'latch_loops'):
        found = re.search(r'checking\s+' + field + r'\s*\((\d+)\)', check)
        warnings[field] = int(found.group(1)) if found else None
    return {'metrics': result, 'warnings': warnings, 'critical_paths': timing_paths(timing),
            'resource_instances': resource_instances(str(reports.get('utilization_hierarchical.rpt', utilization))),
            'qualification': 'PRELIMINARY_IMPORTED_REPORTS',
            'latch_inventory': 'UNKNOWN: latch_loops is not an inferred-latch count',
            'timing_signoff': False}


def proposal(directory):
    context, context_hash = read_record(directory / 'proposal-context.json')
    if context.get('schema_version') != 1:
        raise ValueError('Unsupported proposal schema')
    prompt, prompt_hash = read_record(directory / 'prompt.json')
    if prompt_hash != context.get('prompt_sha256'):
        raise ValueError('Prompt hash mismatch')
    user = prompt.get('user', {})
    if not isinstance(user, dict) or user.get('profile_fingerprint') != context.get('profile_fingerprint'):
        raise ValueError('Profile fingerprint mismatch')
    summary = {'id': directory.name, 'kind': 'proposal', 'status': label(context.get('status')),
               'profile_fingerprint': label(context.get('profile_fingerprint')),
               'target': label(context.get('target', user.get('target'))), 'tool': 'vivado',
               'part': label(context.get('part', user.get('part'))),
               'period_ns': number(context.get('period_ns', user.get('period_ns'))),
               'tool_version': label(context.get('tool_version_declared', user.get('tool_version_declared'))),
               'measurement_stage': 'post_synth', 'functional_verification': 'NOT_RUN',
               'candidate_measurement': 'NOT_RUN', 'automatic_acceptance': 'BLOCKED',
               'target_tool_qualified': False, 'api_calls_attempted': 0,
               'reported_cost_usd': None, 'estimated_max_cost_usd': None,
               'comparison': {'status': 'BLOCKED', 'reason': 'No verified candidate measurement under matching settings'},
               'observations': report_summary(user.get('reports', {})),
               'notes': ['Imported report hashes do not prove execution/source association.',
                         'Proposal review does not apply RTL or verify correctness.']}
    summary['report_provenance'] = [
        {'name': name, 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
         'scope': 'Frozen imported text; execution association is not independently proven'}
        for name, text in user.get('reports', {}).items()
        if name in {'timing.rpt', 'utilization.rpt', 'utilization_hierarchical.rpt', 'check_timing.rpt', 'drc.rpt'} and isinstance(text, str)]
    for filename in ('proposal-run.json', 'review.json'):
        path = directory / filename
        if not path.exists():
            continue
        record, _ = read_record(path)
        if record.get('context_sha256') != context_hash:
            summary['notes'].append(filename + ': stale or unbound record excluded')
            continue
        allowed = ({'PREFLIGHT_RUNNING', 'RUNNING', 'PROPOSAL_REVIEW_READY', 'STOP', 'FAILED', 'FAILED_OUTCOME_UNKNOWN', 'BLOCKED_BUDGET'}
                   if filename == 'proposal-run.json' else {'STOP', 'EDIT_PREVIEW_VALID_NOT_APPLIED'})
        if record.get('status') not in allowed:
            summary['notes'].append(filename + ': unsupported status excluded')
            continue
        summary['status'] = label(record.get('status'))
        if filename == 'proposal-run.json':
            for key in ('api_calls_attempted', 'token_count_requests_attempted', 'reported_cost_usd', 'estimated_max_cost_usd', 'input_tokens', 'output_tokens'):
                value = record.get(key)
                if key.endswith('_usd') and isinstance(value, str):
                    try:
                        value = float(value)
                    except ValueError:
                        value = None
                summary[key] = number(value) if number(value) is not None and value >= 0 else None
            summary['model'] = label(record.get('model'))
            # Only bounded enums/numbers, never SDK exception text or credentials.
            if record.get('failure_stage') in {'credential_setup', 'token_count', 'budget_check', 'generation', 'response_review'}:
                summary['failure_stage'] = record['failure_stage']
            if record.get('error_category') in {'interrupted', 'workspace_required', 'authentication', 'permission', 'not_found', 'rate_limit', 'provider_unavailable', 'local_credentials', 'connection_or_timeout', 'local_configuration_or_validation', 'invalid_request', 'unknown'}:
                summary['error_category'] = record['error_category']
            status = record.get('provider_http_status')
            if type(status) is int and 100 <= status <= 599:
                summary['provider_http_status'] = status
            summary['cost_note'] = 'Generation attempts exclude token-count requests. Costs use declared pricing; unknown usage/cost stays unknown. Estimates are not billing caps.'
        else:
            summary['review_status'] = label(record.get('status'))
    return summary


def collect(root):
    root = Path(root)
    records, errors = [], []
    base = root / '.pqc_runs' / 'fpga-proposals'
    if base.is_symlink() or (root / '.pqc_runs').is_symlink():
        return {'runs': [], 'errors': ['Run directory symlink refused'], 'read_only': True}
    if base.is_dir():
        for directory in sorted(base.iterdir(), key=lambda x: x.name, reverse=True)[:200]:
            if directory.is_symlink() or not directory.is_dir():
                continue
            try:
                records.append(proposal(directory))
            except (ValueError, OSError, TypeError, KeyError, AttributeError) as error:
                errors.append({'id': directory.name, 'status': 'INCOMPLETE_OR_INVALID', 'reason': label(error)})
    asic = collect_asic(root)
    records.extend(asic['runs'])
    errors.extend(asic['errors'])
    return {'runs': records, 'errors': errors, 'read_only': True,
            'notice': 'Current FPGA proposals and recorded ASIC measurements. No verified optimization gain is implied. Historical records remain separate.'}
