"""Bounded, read-only ASIC observations. Never runs EDA or requalifies evidence.

Only known local run layouts are read. Recorded source hashes are displayed as
provenance, never followed as filenames. Hash binding is not proof of execution.
"""
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re

LIMIT = 4 * 1024 * 1024
HASH = re.compile(r'[0-9a-f]{64}')


def number(value):
    return value if type(value) in (int, float) and math.isfinite(value) else None


def label(value):
    value = str(value or '')[:240]
    return re.sub(r'(?i)(sk-[a-z0-9_-]+|(?:api[_ -]?key|authorization)\s*[:=]\s*\S+)', '[redacted]', value)


def safe_path(path, boundary):
    """Reject traversal and every symlink component before reading a file."""
    path, boundary = Path(path), Path(boundary).absolute()
    if not path.is_absolute():
        path = boundary / path
    if '..' in path.parts or not path.is_relative_to(boundary):
        raise ValueError('Evidence path escapes its permitted directory')
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError('Symlink evidence refused')
    return path


def read_bytes(path, boundary):
    path = safe_path(path, boundary)
    if not path.is_file() or path.stat().st_size > LIMIT:
        raise ValueError('Missing or oversized evidence')
    with path.open('rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise ValueError('Oversized evidence')
    return raw


def record(path, boundary):
    raw = read_bytes(path, boundary)
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError('Record must be an object')
    return value, hashlib.sha256(raw).hexdigest()


def source_manifest(value):
    if not isinstance(value, dict) or not value or len(value) > 10000:
        raise ValueError('Missing or excessive source manifest')
    if not all(isinstance(k, str) and isinstance(v, str) and HASH.fullmatch(v) for k, v in value.items()):
        raise ValueError('Malformed source hashes')
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def reports_bound(reports, directory):
    if not isinstance(reports, dict) or not {'timing', 'area'} <= reports.keys() or len(reports) > 32:
        raise ValueError('Missing or excessive report manifest')
    texts = {}
    for name, entry in reports.items():
        if not isinstance(entry, dict):
            raise ValueError('Malformed report entry')
        filename = entry.get('path')
        if not isinstance(filename, str):
            raise ValueError('Missing report path')
        path = safe_path(filename, directory)
        # Do not use the dashboard to read arbitrary source/config/credential files.
        if path.suffix != '.rpt':
            if name == 'implementation_netlist' and path.name == 'netlist.v':
                continue
            raise ValueError('Unsupported report file type')
        raw = read_bytes(path, directory)
        if hashlib.sha256(raw).hexdigest() != entry.get('sha256'):
            raise ValueError('Report hash mismatch')
        texts[name] = raw.decode('utf-8')
    return texts


def path_observations(paths, texts):
    output = []
    if not isinstance(paths, list) or len(paths) > 100:
        return output
    for row in paths:
        if not isinstance(row, dict) or row.get('report') != 'timing':
            continue
        first, last = row.get('line_start'), row.get('line_end')
        if type(first) is not int or type(last) is not int or not 1 <= first <= last <= len(texts['timing'].splitlines()):
            continue
        if not row.get('startpoint') or not row.get('endpoint') or number(row.get('slack_ns')) is None:
            continue
        output.append({**{k: label(row.get(k)) for k in ('id', 'startpoint', 'endpoint', 'path_type')},
                       **{k: number(row.get(k)) for k in ('slack_ns', 'data_path_delay_ns', 'logic_delay_ns', 'net_delay_ns', 'logic_levels')},
                       'report': 'timing', 'line_start': first, 'line_end': last,
                       'provenance': 'HASH_BOUND_ADAPTER_OBSERVATION'})
    return output


def dc_paths(text, time_unit):
    """Only explicit DC setup endpoints/slack; arrival time is not path delay."""
    from .asic_synthesis import NUMBER, TIME_NS
    factor = TIME_NS.get(time_unit)
    if factor is None:
        return []
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if re.match(r'\s*Startpoint:', line)]
    output = []
    for index, first in enumerate(starts[:100]):
        last = starts[index + 1] if index + 1 < len(starts) else len(lines)
        block = '\n'.join(lines[first:last])
        start = re.findall(r'^\s*Startpoint:\s*(\S+)', block, re.M)
        end = re.findall(r'^\s*Endpoint:\s*(\S+)', block, re.M)
        kind = re.findall(r'^\s*Path Type:\s*(\S+)', block, re.M)
        slack = re.findall(r'^\s*slack\s*\((?:MET|VIOLATED)\)\s*(' + NUMBER + r')\s*$', block, re.M)
        if len(start) == len(end) == len(slack) == 1 and kind == ['max']:
            output.append({'id': str(index), 'startpoint': start[0], 'endpoint': end[0],
                           'path_type': 'setup', 'slack_ns': float(slack[0]) * factor,
                           'report': 'timing', 'line_start': first + 1, 'line_end': last})
    return output


def metrics_view(value):
    if not isinstance(value, dict):
        raise ValueError('Malformed metrics')
    result = {key: number(value.get(key)) for key in ('worst_setup_slack_ns', 'worst_hold_slack_ns',
              'cell_area_reported', 'cell_count', 'power_w', 'dynamic_power_w', 'leakage_power_w')}
    result.update(area=result['cell_area_reported'], total_power_w=result['power_w'],
                  area_unit=label(value.get('area_unit')) or None, latency_cycles=None)
    return result


def card(identifier, config, value, texts, sources, role):
    spec = config.get('measurement', {})
    if not isinstance(spec, dict):
        raise ValueError('Malformed measurement configuration')
    metrics = metrics_view(value.get('metrics', {}))
    metrics['area_unit'] = label(value.get('area_unit') or metrics['area_unit']) or None
    profile = config.get('target_profile') or {}
    libraries = spec.get('libraries', (spec.get('asic_effective_config') or {}).get('libraries', []))
    if not isinstance(libraries, list):
        libraries = []
    return {'id': identifier, 'kind': 'asic_measurement', 'target': 'asic', 'measurement_role': role if role in ('baseline', 'candidate') else 'unspecified',
            'tool': label(config.get('backend')), 'tool_version': label(spec.get('tool_version')),
            'top': label(config.get('top')), 'technology': label(spec.get('technology')),
            'corner': label(spec.get('corner')),
            'libraries': [label(Path(x).name) for x in libraries[:32] if isinstance(x, str)],
            'period_ns': number(spec.get('period_ns')),
            'measurement_stage': label(spec.get('stage')), 'status': label(value.get('status')),
            'profile_fingerprint': label(profile.get('profile_fingerprint')),
            'source_manifest_sha256': source_manifest(sources),
            'configuration_sha256': hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
            'source_binding': 'RECORDED_SOURCE_HASHES_REQUEST_BOUND',
            'functional_verification': 'NOT_ESTABLISHED_BY_DASHBOARD',
            'candidate_measurement': label(value.get('status')), 'automatic_acceptance': 'BLOCKED',
            'target_tool_qualified': False,
            'recorded_qualification': {key: (value.get(key) if type(value.get(key)) is bool else label(value.get(key)) or None) for key in ('tool_qualification', 'admission_passed',
               'structural_checks_verified', 'memory_implementation_verified', 'memory_semantics_verified')},
            'comparison': {'status': 'BLOCKED', 'reason': 'No independently qualified matching baseline/candidate comparison'},
            'observations': {'metrics': metrics, 'critical_paths': path_observations(value.get('critical_paths', []), texts),
                'qualification': 'HASH_BOUND_RECORDED_OBSERVATIONS', 'warnings': {}, 'timing_signoff': False},
            'notes': ['Report/request hashes verify local record consistency, not EDA execution or source correctness.',
                      'Missing values are Not measured. No Fmax is derived from slack.',
                      'Power is a tool estimate; workload activity is not validated.']}


def whole_run(directory, root):
    manifest, _ = record(directory / 'manifest.json', root)
    config = manifest.get('configuration', {})
    if config.get('target') != 'asic':
        return [], []
    rows, errors = [], []
    for phase in children(directory, root):
        if not re.fullmatch(r'\d+-measure', phase.name):
            continue
        try:
            request, sha = record(phase / 'request.json', root)
            response, _ = record(phase / 'response.json', root)
            if (request.get('schema_version') != 1 or response.get('schema_version') != 1
                    or request.get('phase') != 'measure' or request.get('run_id') != directory.name
                    or response.get('request_sha256') != sha or request.get('configuration') != config
                    or response.get('configuration') != config or response.get('scope') != 'full_design'
                    or response.get('status') != 'MEASURED' or config.get('backend') not in ('genus', 'dc')):
                raise ValueError('Measurement request/configuration/status mismatch')
            sources = request.get('source_hashes')
            source_manifest(sources)
            if response.get('source_hashes', sources) != sources:
                raise ValueError('Response source manifest mismatch')
            texts = reports_bound(response.get('reports'), phase)
            role = 'baseline' if sources == manifest.get('baseline_sources') else 'candidate'
            rows.append(card(directory.name + '/' + phase.name, config, response, texts, sources, role))
        except (ValueError, OSError, TypeError, KeyError, AttributeError) as error:
            errors.append(error_row(directory.name + '/' + phase.name, error))
    return rows, errors


def standalone(directory, root):
    from .asic_synthesis import parse_metrics, NUMBER
    manifest, _ = record(directory / 'manifest.json', root)
    value, _ = record(directory / 'result.json', root)
    for key in ('tool', 'top', 'scope', 'period_ns', 'memory_model'):
        if value.get(key) != manifest.get(key):
            raise ValueError('ASIC result/manifest mismatch')
    if value.get('tool') not in ('genus', 'dc') or value.get('status') != 'MEASURED' or value.get('stage') != 'post_synth':
        raise ValueError('ASIC measurement incomplete or unsupported')
    hashes = value.get('report_hashes', {})
    if not isinstance(hashes, dict):
        raise ValueError('Malformed report hashes')
    reports = {}
    for filename, sha in hashes.items():
        path = safe_path(filename, directory)
        if path.stem in reports:
            raise ValueError('Duplicate report name')
        reports[path.stem] = {'path': str(path), 'sha256': sha}
    texts = reports_bound(reports, directory)
    parsed = parse_metrics(value['tool'], texts['timing'], texts['area'], texts.get('power', ''),
                           manifest.get('time_unit'), manifest['top'], manifest.get('area_unit'))
    if any(value.get('metrics', {}).get(k) != v for k, v in parsed.items()):
        raise ValueError('Recorded ASIC metrics disagree with reports')
    # DC labels explicitly identify components. Genus unlabeled subtotals do not.
    if value['tool'] == 'dc':
        for heading, key in [('Total Dynamic Power', 'dynamic_power_w'), ('Cell Leakage Power', 'leakage_power_w')]:
            matches = re.findall(re.escape(heading) + r'\s*=\s*(' + NUMBER + r')\s*(pW|nW|uW|mW|W)\b', texts.get('power', ''))
            if len(matches) == 1:
                amount, unit = matches[0]
                parsed[key] = number(float(amount) * {'pW': 1e-12, 'nW': 1e-9, 'uW': 1e-6, 'mW': 1e-3, 'W': 1}[unit])
    config = {'backend': value['tool'], 'top': manifest['top'], 'measurement': {
        'period_ns': manifest.get('period_ns'), 'stage': 'post_synth',
        'tool_version': manifest.get('tool_version_declared'), 'technology': manifest.get('technology'),
        'corner': manifest.get('library_corner_declared'), 'libraries': manifest.get('libraries', [])}}
    paths = dc_paths(texts['timing'], manifest.get('time_unit')) if value['tool'] == 'dc' else []
    row = card(directory.name, config, {**value, 'metrics': parsed, 'critical_paths': paths}, texts, manifest.get('input_hashes'), 'standalone')
    for path in row['observations']['critical_paths']:
        path['provenance'] = 'HASH_BOUND_DC_REPORT'
    row['source_binding'] = 'RECORDED_INPUT_HASHES_REPORT_BOUND'
    row['notes'].append('Standalone synthesis does not establish baseline/candidate identity or functional qualification.')
    return row


def children(directory, root):
    directory = safe_path(directory, root)
    if not directory.is_dir():
        return []
    result = []
    for path in itertools.islice(directory.iterdir(), 201):
        if len(result) >= 200:
            break
        if not path.is_symlink() and path.is_dir():
            result.append(path)
    return sorted(result, key=lambda p: p.name)


def error_row(identifier, error):
    # Do not echo arbitrary file contents or recorded paths in exceptions.
    return {'id': identifier, 'status': 'INCOMPLETE_OR_INVALID', 'reason': label(type(error).__name__) + ': ASIC evidence unavailable or inconsistent'}


def collect(root):
    root = Path(os.path.abspath(root))
    runs, errors = [], []
    for relative, mode in [('.pqc_runs/whole_design', 'whole'), ('runs/asic', 'standalone')]:
        try:
            for directory in children(root / relative, root):
                try:
                    if mode == 'whole':
                        rows, failures = whole_run(directory, root)
                        runs.extend(rows)
                        errors.extend(failures)
                    elif re.fullmatch(r'(?:genus|dc)-[A-Za-z0-9_-]+', directory.name):
                        runs.append(standalone(directory, root))
                except (ValueError, OSError, TypeError, KeyError, AttributeError) as error:
                    errors.append(error_row(directory.name, error))
        except (ValueError, OSError) as error:
            errors.append(error_row(relative, error))
    return {'runs': runs, 'errors': errors, 'read_only': True}
