"""Evidence-derived Vivado post-synthesis qualification, not routed sign-off.

The fixed Tcl producer queries real design objects. This parser never turns a
user/model-provided ``verified`` flag into admission. Local hashes bind bytes,
not an adversarial EDA installation. Mapped-memory behavioral qualification is
intentionally distinct from observing BRAM/LUTRAM primitives.
"""
from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path
import re

from agent.run_safety import hashes
from agent.whole_design import digest, require, save
from agent.ppa_reader import parse_util

SCHEMA = 'vivado-object-audit-v1'
CHECKS = ('no_clock', 'constant_clock', 'pulse_width_clock',
          'unconstrained_internal_endpoints', 'no_input_delay', 'no_output_delay',
          'multiple_clock', 'generated_clocks', 'loops', 'partial_input_delay',
          'partial_output_delay', 'latch_loops')
DRC_CHECKS = {'MDRV-1', 'LUTLP-1', 'INBB-3'}
RAW_REPORTS = ('objects.tsv', 'check_timing.rpt', 'clocks.rpt', 'exceptions.rpt',
               'effective.xdc', 'structural_drc.rpt', 'timing.rpt', 'paths.rpt',
               'utilization.rpt', 'utilization_hierarchical.rpt', 'drc.rpt',
               'implementation.v', 'synthesized.dcp', 'tool-version.txt',
               'synthesis.log', 'launch.tcl', 'input-manifest.json')
REPORT_KEYS = {'timing': 'paths.rpt', 'timing_summary': 'timing.rpt',
               'structural': 'qualification.json', 'memory': 'qualification.json',
               'qualification': 'qualification.json',
               'implementation_netlist': 'implementation.v', 'checkpoint': 'synthesized.dcp'}
NUMBER = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'


def dependencies():
    """Freeze these along with the existing adapter dependencies before execution."""
    base = Path(__file__).resolve().parent
    return [str(base / name) for name in
            ('vivado_qualification.py', 'vivado_qualification.tcl', 'fpga_feedback.py')]


def _number(value, label):
    require(isinstance(value, str) and re.fullmatch(NUMBER, value) is not None,
            'Missing/non-numeric ' + label)
    number = float(value)
    require(math.isfinite(number), 'Nonfinite ' + label)
    return number


def _count(value, label):
    require(isinstance(value, str) and re.fullmatch(r'\d+', value) is not None,
            'Invalid count: ' + label)
    return int(value)


def _text(path, maximum=32 * 1024 * 1024):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= maximum,
            'Missing, empty, symlinked or oversized report: ' + path.name)
    return path.read_text(encoding='utf-8')


def parse_check_timing(text):
    """Require every check. Conflicting duplicate summary/detail counts fail."""
    values = {}
    for name, count in re.findall(r'^\s*\d+\.\s+checking\s+(\w+)\s+\((\d+)\)\s*$', text, re.M):
        value = int(count)
        require(name not in values or values[name] == value, 'Contradictory timing check: ' + name)
        values[name] = value
    require(set(CHECKS) <= set(values), 'Missing required check_timing categories')
    return values


def parse_timing_summary(text):
    lines = text.splitlines()
    headers = [i for i, line in enumerate(lines) if re.match(r'^\s*WNS\(ns\)\s+TNS\(ns\)', line)]
    require(len(headers) == 1, 'Expected one global setup/hold timing summary')
    index = headers[0]
    require('WHS(ns)' in lines[index] and 'THS(ns)' in lines[index], 'Missing global hold summary')
    for line in lines[index + 1:]:
        if not line.strip() or set(line.strip()) <= {'-', ' '}:
            continue
        row = line.split()
        require(len(row) >= 8, 'Incomplete setup/hold summary')
        result = dict(zip(('worst_setup_slack_ns', 'total_setup_slack_ns',
                           'setup_failing_endpoints', 'setup_endpoints',
                           'worst_hold_slack_ns', 'total_hold_slack_ns',
                           'hold_failing_endpoints', 'hold_endpoints'),
                          [_number(v, 'timing summary') if i % 4 < 2 else _count(v, 'endpoints')
                           for i, v in enumerate(row[:8])]))
        require(result['setup_endpoints'] > 0 and result['hold_endpoints'] > 0,
                'No constrained setup/hold endpoints')
        for kind in ('setup', 'hold'):
            require(result[f'{kind}_failing_endpoints'] <= result[f'{kind}_endpoints'], 'Invalid endpoint count')
            require(result[f'total_{kind}_slack_ns'] <= 0, 'Positive total negative slack')
            worst, failing = result[f'worst_{kind}_slack_ns'], result[f'{kind}_failing_endpoints']
            require(not ((worst < 0 and failing == 0) or (worst > 0 and failing > 0)),
                    'Slack contradicts failing endpoint count')
        return result
    raise ValueError('Missing setup/hold summary values')


def parse_objects(text):
    kinds = {'meta': 2, 'cell': 7, 'latch': 1, 'blackbox': 1, 'clock': 4,
             'port': 3, 'port_timing': 5, 'drc_check': 2, 'drc_violation': 2,
             'path': 5, 'path_cell': 2, 'memory_property': 3}
    rows = {name: [] for name in kinds}
    for line in text.splitlines():
        fields = line.split('\t')
        require(all(re.fullmatch(r'(?:[0-9a-f]{2})*', x) is not None for x in fields), 'Invalid object field encoding')
        decoded = [bytes.fromhex(x).decode('utf-8') for x in fields]
        require(decoded[0] in kinds and len(decoded) == kinds[decoded[0]] + 1, 'Malformed object report row')
        rows[decoded[0]].append(decoded[1:])
    meta = {}
    for key, value in rows['meta']:
        require(key not in meta, 'Duplicate object metadata: ' + key)
        meta[key] = value
    require(meta.get('schema') == SCHEMA and meta.get('complete') == '1', 'Incomplete object collection')
    rows['meta'] = meta
    for kind in ('cell', 'clock', 'port', 'path'):
        names = [r[0] for r in rows[kind]]
        require(len(set(names)) == len(names), 'Duplicate ' + kind + ' objects')
    require(_count(meta.get('primitive_count'), 'primitives') == len(rows['cell']) > 0, 'Primitive inventory mismatch')
    for kind in ('latch', 'blackbox'):
        key = 'latch_inventory_count' if kind == 'latch' else 'blackbox_count'
        require(_count(meta.get(key), kind) == len({r[0] for r in rows[kind]}) == len(rows[kind]), kind + ' inventory mismatch')
    require({r[0] for r in rows['drc_check']} == DRC_CHECKS and len(rows['drc_check']) == 3,
            'Missing structural DRC coverage')
    return rows


def _locations(rows, sources):
    result = {}
    line_counts = {path: len(Path(path).read_text(encoding='utf-8').splitlines()) for path in sources}
    for name, ref, primitive, ref_type, subgroup, filename, line in rows['cell']:
        location = {'cell': name, 'ref_name': ref, 'primitive_type': primitive,
                    'source_file': None, 'source_line': None, 'confidence': 'unknown',
                    'basis': 'No exact FILE_NAME/LINE_NUMBER in the frozen source manifest'}
        # Never infer ownership from hierarchical instance names, REF_NAME, or a
        # matching basename. Relative/ambiguous vendor source paths stay unknown.
        if filename and Path(filename).is_absolute() and line.isdigit():
            canonical = str(Path(filename).resolve())
            if canonical in sources and 1 <= int(line) <= line_counts[canonical]:
                location.update(source_file=canonical, source_line=int(line),
                                source_sha256=sources[canonical], confidence='direct_source_property',
                                basis='Vivado cell FILE_NAME and LINE_NUMBER; exact frozen source')
        result[name] = location
    return result


def _paths(rows, report, locations, path_count):
    spans = {}
    active = None
    for line_no, line in enumerate(report.splitlines(), 1):
        begin = re.fullmatch(r'PQC_PATH_BEGIN (\S+)', line)
        end = re.fullmatch(r'PQC_PATH_END (\S+)', line)
        if begin:
            require(active is None and begin[1] not in spans, 'Nested or duplicate path report marker')
            active = (begin[1], line_no)
        if end:
            require(active is not None and end[1] == active[0], 'Mismatched path report marker')
            spans[end[1]] = (active[1], line_no)
            active = None
    require(active is None, 'Unclosed path report marker')
    path_rows = {row[0]: row for row in rows['path']}
    require(set(spans) == set(path_rows), 'Path report/object coverage mismatch')
    cells = {name: [] for name in path_rows}
    for path, cell in rows['path_cell']:
        require(path in cells and cell in locations, 'Path references an unknown cell')
        if cell not in cells[path]:
            cells[path].append(cell)
    paths = []
    for name, kind, start, end, slack in rows['path']:
        require(kind in ('setup', 'hold') and name.startswith(kind + '-') and start and end,
                'Malformed timing path')
        slack = _number(slack, 'path slack')
        begin, finish = spans[name]
        body = '\n'.join(report.splitlines()[begin:finish - 1])
        detail = re.search(r'Slack\s+\((MET|VIOLATED)\)\s*:\s*(' + NUMBER + r')ns', body)
        require(detail is not None and (detail[1] == 'MET') == (slack >= 0)
                and abs(float(detail[2]) - slack) <= 0.0011, 'Path object/report slack differs')
        require(re.search(r'Path Type:\s*' + ('Setup' if kind == 'setup' else 'Hold') + r'\b', body), 'Wrong path delay type')
        require(re.search(r'^\s*Source:\s*' + re.escape(start) + r'\s*$', body, re.M)
                and re.search(r'^\s*Destination:\s*' + re.escape(end) + r'\s*$', body, re.M),
                'Path object/report endpoints differ')
        owners = [locations[cell] for cell in cells[name]]
        files = list(dict.fromkeys(p['source_file'] for p in owners if p['source_file']))
        paths.append({'id': name, 'kind': kind, 'startpoint': start, 'endpoint': end,
                      'slack_ns': slack, 'instances': cells[name], 'report': 'timing',
                      'line_start': begin, 'line_end': finish, 'source_locations': owners,
                      'responsible_files': files,
                      'ownership_confidence': 'direct_source_property' if files else 'unknown'})
    for kind in ('setup', 'hold'):
        chosen = [p for p in paths if p['kind'] == kind]
        require(chosen, 'Missing ' + kind + ' paths')
        require(len(chosen) <= path_count, 'Unexpected extra timing paths')
        require(len({(p['startpoint'], p['endpoint']) for p in chosen}) == len(chosen), 'Repeated timing endpoints')
    return paths


def _io_exceptions(configuration, ports, directory):
    """Recognize only exact all-path per-port false paths with cited user XDC.

    Wildcards, multicycle, internal exceptions and arbitrary Tcl need a separately
    qualified parser. They never become permission to ignore timing defects.
    """
    policy = configuration['measurement'].get('qualification', {})
    require(isinstance(policy, dict), 'Invalid qualification policy')
    entries = policy.get('io_exceptions', [])
    require(isinstance(entries, list) and len(entries) <= len(ports), 'Invalid I/O exception ledger')
    approved = {}
    constraints = set(configuration['measurement']['constraints'])
    for item in entries:
        require(isinstance(item, dict) and set(item) == {'port', 'direction', 'reason', 'xdc', 'line'},
                'I/O exception requires exact port/direction/reason/XDC/line')
        port, direction = item['port'], item['direction']
        require(port in ports and ports[port][1] == direction and direction in ('IN', 'OUT')
                and port not in approved and ports[port][2] == '0', 'Invalid/duplicate exception port')
        require(isinstance(item['reason'], str) and 8 <= len(item['reason'].strip()) <= 2000,
                'Missing user justification for I/O exception')
        path = str(Path(item['xdc']).resolve())
        require(path in constraints and path in configuration['immutable_hashes'], 'Exception XDC is not frozen')
        lines = Path(path).read_text().splitlines()
        line = item['line']
        require(type(line) is int and 1 <= line <= len(lines), 'Invalid exception source line')
        # Exact literal port only; bracket bus indices are permitted inside braces.
        require(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_./\[\]-]*', port), 'Unsupported exception port syntax')
        selector = r'(?:' + re.escape(port) + r'|\{' + re.escape(port) + r'\})'
        command = r'set_false_path\s+-' + ('from' if direction == 'IN' else 'to') + r'\s+\[get_ports\s+' + selector + r'\]'
        require(re.fullmatch(command, lines[line - 1].strip()) is not None,
                'Exception must cite one exact all-path set_false_path command')
        approved[port] = {**item, 'xdc_sha256': configuration['immutable_hashes'][path],
                          'command': lines[line - 1].strip()}
    # Audit the effective constraints as well. Unknown commands that can hide
    # timing are blocked even if the global summary happens to look clean.
    effective = _text(Path(directory) / 'effective.xdc')
    hidden = []
    for line in effective.splitlines():
        if re.match(r'^\s*(set_false_path|set_multicycle_path|set_clock_groups|set_max_delay|set_min_delay|set_disable_timing|set_case_analysis)\b', line):
            if not any(re.fullmatch(r'\s*' + r'set_false_path\s+-' + ('from' if x['direction'] == 'IN' else 'to') +
                                    r'\s+\[get_ports\s+(?:' + re.escape(port) + r'|\{' + re.escape(port) + r'\})\]\s*', line)
                       for port, x in approved.items()):
                hidden.append(line)
    return approved, hidden


def evaluate(directory, request):
    """Derive observed gates from fixed reports; never consume PASS booleans."""
    directory = Path(directory).resolve()
    cfg, sources = request['configuration'], request['source_hashes']
    spec = cfg['measurement']
    objects = parse_objects(_text(directory / 'objects.tsv', 128 * 1024 * 1024))
    meta = objects['meta']
    tool_build = meta.get('tool_build')
    require(isinstance(tool_build, str) and 0 < len(tool_build.encode('utf-8')) <= 16384
            and bool(tool_build.strip()), 'Missing, empty or oversized Vivado tool build identity')
    for key, value in (('tool_version', spec['tool_version']), ('part', spec['part']),
                       ('top', cfg['top']), ('stage', spec['stage']), ('mode', 'out_of_context'),
                       ('effort', spec.get('effort', 'default')), ('seed', spec.get('seed', 'not_applicable'))):
        require(meta.get(key) == value, 'Observed Vivado ' + key + ' differs from frozen configuration')
    require(_text(directory / 'tool-version.txt').strip() == meta['tool_version'], 'Tool version reports disagree')
    counts = parse_check_timing(_text(directory / 'check_timing.rpt'))
    timing_text = _text(directory / 'timing.rpt')
    summary = parse_timing_summary(timing_text)
    timer_coverage = (re.search(r'Enable Multi Corner Analysis\s*:\s*Yes\b', timing_text) is not None
                      and re.search(r'Ignore I/O Paths\s*:\s*No\b', timing_text) is not None
                      and all(re.search(r'^\s*' + corner + r'\s+Yes\s+Yes\s*$', timing_text, re.M)
                              for corner in ('Slow', 'Fast')))
    resources = parse_util(directory / 'utilization.rpt')
    require(all(type(value) in (int, float) and math.isfinite(value) and value >= 0 for value in resources.values()),
            'Missing resource metrics')
    locations = _locations(objects, sources)
    path_count = spec.get('critical_path_count', 5)
    require(type(path_count) is int and 1 <= path_count <= 100, 'Invalid path count')
    paths = _paths(objects, _text(directory / 'paths.rpt'), locations, path_count)
    for kind in ('setup', 'hold'):
        require(abs(min(p['slack_ns'] for p in paths if p['kind'] == kind) - summary[f'worst_{kind}_slack_ns']) <= 0.0011,
                kind + ' path disagrees with global summary')
    primitive_latches = {r[0] for r in objects['cell'] if r[3] == 'LATCH' or r[4] == 'LATCH'
                         or '.LATCH.' in r[2] or re.match(r'^LD', r[1])}
    reported_latches = {r[0] for r in objects['latch']}
    require(primitive_latches == reported_latches, 'Latch inventories disagree')
    synthesis_warnings = [line.strip() for line in _text(directory / 'synthesis.log').splitlines()
                          if re.match(r'^\s*(?:CRITICAL WARNING|WARNING|ERROR):', line)]
    structural_counts = {'latches': len(primitive_latches), 'blackboxes': len(objects['blackbox']),
                         'multiple_driver_violations': sum(r[0].startswith('MDRV-1') for r in objects['drc_violation']),
                         'combinational_loop_violations': sum(r[0].startswith('LUTLP-1') for r in objects['drc_violation']),
                         'structural_drc_violations': len(objects['drc_violation']),
                         'disabled_structural_checks': sum(row[1].lower() not in ('1', 'true') for row in objects['drc_check']),
                         'unreviewed_synthesis_warnings': len(synthesis_warnings)}
    structural_ok = not any(structural_counts.values()) and counts['loops'] == 0 and counts['latch_loops'] == 0
    clocks = [{'name': row[0], 'period_ns': _number(row[1], 'clock period'),
               'generated': row[2], 'source_pins': row[3]} for row in objects['clock']]
    clock_ports = (cfg.get('target_profile', {}).get('boundary') or {}).get('clock_ports', [])
    clock_ok = len(clocks) == 1 and abs(clocks[0]['period_ns'] - spec['period_ns']) <= 1e-9 and clocks[0]['generated'] in ('0', 'false', 'FALSE')
    clock_ok = clock_ok and len(clock_ports) == 1 and clocks[0]['source_pins'] == clock_ports[0]
    ports = {row[0]: row for row in objects['port']}
    require(ports, 'Missing port inventory')
    approved, hidden = _io_exceptions(cfg, ports, directory)
    port_timing = {}
    for port, delay, number, slack, ignored in objects['port_timing']:
        require(port in ports and delay in ('max', 'min') and (port, delay) not in port_timing, 'Invalid port timing row')
        finite_slack = re.fullmatch(NUMBER, slack) is not None and math.isfinite(float(slack))
        port_timing[port, delay] = {'paths': _count(number, 'port paths'), 'finite_slack': finite_slack,
                                   'ignored_paths': _count(ignored, 'ignored port paths')}
    uncovered, exceptions_observed = [], []
    for port, direction, clock_count in objects['port']:
        clock_count = _count(clock_count, 'port clocks')
        if clock_count:
            if direction != 'IN' or clock_count != 1 or not clocks or clocks[0]['source_pins'] != port:
                uncovered.append(port)
            continue
        evidence = [port_timing.get((port, delay)) for delay in ('max', 'min')]
        if direction not in ('IN', 'OUT') or any(x is None for x in evidence):
            uncovered.append(port)
        elif port in approved:
            if all(x['ignored_paths'] == 1 for x in evidence):
                exceptions_observed.append(approved[port])
            else:
                uncovered.append(port)
        elif not all(x['paths'] == 1 and x['finite_slack'] and x['ignored_paths'] == 0 for x in evidence):
            uncovered.append(port)
    # Never subtract waivers from positive counts: check_timing distinguishes
    # constrained user-ignored paths; unexplained missing-delay counts still fail.
    constraints_ok = clock_ok and timer_coverage and not uncovered and not hidden and all(value == 0 for value in counts.values())
    memories = [row for row in objects['cell'] if re.match(r'^(RAM|ROM|SRL)', row[1])]
    memory_names = {row[0] for row in memories}
    memory_properties = {}
    for cell, property_name, value in objects['memory_property']:
        require(cell in memory_names, 'Memory properties reference a non-memory cell')
        require(property_name not in memory_properties.setdefault(cell, {}), 'Duplicate memory property')
        memory_properties[cell][property_name] = value
    ram_count = sum(row[1].startswith('RAM') for row in memories)
    memory_ok = ram_count > 0 and not objects['blackbox']
    setup_paths = [p for p in paths if p['kind'] == 'setup']
    ownership_ok = len(setup_paths) >= path_count and all(p['responsible_files'] and p['instances'] for p in setup_paths)
    minimum_setup = cfg.get('admission', {}).get('minimum_slack_ns', 0)
    require(type(minimum_setup) in (int, float) and math.isfinite(minimum_setup), 'Invalid admission setup floor')
    setup_ok = (summary['worst_setup_slack_ns'] >= max(0, minimum_setup) and summary['setup_failing_endpoints'] == 0
                and min(p['slack_ns'] for p in setup_paths) >= max(0, minimum_setup))
    hold_ok = (summary['worst_hold_slack_ns'] >= 0 and summary['hold_failing_endpoints'] == 0
               and min(p['slack_ns'] for p in paths if p['kind'] == 'hold') >= 0)
    gates = {'setup_timing': 'PASS' if setup_ok else 'BLOCKED',
             'hold_timing': 'PASS' if hold_ok else 'BLOCKED',
             'structural': 'PASS' if structural_ok else 'BLOCKED',
             'constraint_coverage': 'PASS' if constraints_ok else 'BLOCKED',
             'path_ownership': 'PASS' if ownership_ok else 'BLOCKED',
             'mapped_memory_inventory': 'PASS' if memory_ok else 'BLOCKED',
             'mapped_memory_semantics': 'UNVERIFIED'}
    reasons = {'setup_timing': f"setup slack={summary['worst_setup_slack_ns']} ns; failing endpoints={summary['setup_failing_endpoints']}; required floor={max(0, minimum_setup)} ns",
               'hold_timing': f"hold slack={summary['worst_hold_slack_ns']} ns; failing endpoints={summary['hold_failing_endpoints']}",
               'structural': ', '.join(f'{key}={value}' for key, value in structural_counts.items() if value)
                             or f"loops={counts['loops']}, latch_loops={counts['latch_loops']}",
               'constraint_coverage': ', '.join(f'{key}={value}' for key, value in counts.items() if value)
                                      + f'; uncovered ports={len(uncovered)}, unsupported exceptions={len(hidden)}, clock valid={bool(clock_ok)}, all corners={bool(timer_coverage)}',
               'path_ownership': f'{sum(bool(p["responsible_files"]) for p in setup_paths)}/{path_count} required paths have direct source locations',
               'mapped_memory_inventory': f'RAM primitive count={ram_count}; blackboxes={len(objects["blackbox"])}',
               'mapped_memory_semantics': 'exact-netlist startup/reset, read/write latency and collision checks are missing'}
    blockers = [name + ': ' + reasons[name] for name, verdict in gates.items() if verdict != 'PASS']
    return {'schema': SCHEMA, 'stage': 'post_synth', 'scope': 'post_synthesis_estimate_only',
            'observed_tool': meta, 'gates': gates, 'blockers': blockers,
            'structural': {'counts': structural_counts, 'latch_cells': sorted(primitive_latches),
                           'drc_checks': sorted(DRC_CHECKS), 'drc_violations': objects['drc_violation'],
                           'synthesis_warnings': synthesis_warnings},
            'constraints': {'check_timing': counts, 'clocks': clocks, 'complete': constraints_ok,
                            'full_min_max_corner_coverage': bool(timer_coverage),
                            'ports': objects['port'], 'uncovered_ports': uncovered,
                            'qualified_io_exceptions': exceptions_observed, 'unsupported_effective_exceptions': hidden},
            'metrics': {**resources, 'lut': resources['luts'], **summary}, 'critical_paths': setup_paths,
            'source_ownership': [{'instance': row['cell'], 'source_path': row['source_file'],
                                  'line_start': row['source_line'], 'line_end': row['source_line'],
                                  'confidence': row['confidence'], 'basis': row['basis'],
                                  'source_sha256': row.get('source_sha256')}
                                 for row in locations.values() if row['cell'] in {cell for path in paths for cell in path['instances']}],
            'hold_paths': [p for p in paths if p['kind'] == 'hold'],
            'memory': {'implementation': 'fpga_inferred_ram', 'primitive_counts': dict(Counter(row[1] for row in memories)),
                       'configuration': {cell: {'parameters': {key: value for key, value in properties.items()
                                                            if not key.startswith(('INIT', 'SRVAL'))},
                                                 'initialization_property_count': sum(key.startswith(('INIT', 'SRVAL')) for key in properties),
                                                 'all_properties_sha256': digest(properties)}
                                         for cell, properties in memory_properties.items()},
                       'properties_report': 'objects.tsv', 'semantics_verified': False,
                       'missing_checks': ['exact-netlist startup/reset', 'read/write latency', 'read-during-write/collision behavior'],
                       'note': 'An inventory is not behavioral evidence. The 210-case RTL gate does not simulate this netlist.'}}


def input_manifest(request, request_sha256):
    return {'schema': SCHEMA, 'request_sha256': request_sha256,
            'configuration_sha256': digest(request['configuration']),
            'source_hashes': request['source_hashes'],
            'immutable_hashes': request['configuration']['immutable_hashes'],
            'source_read_order': request['configuration']['source_read_order'],
            'producer_hashes': hashes(dependencies())}


def build_qualification(directory, request, request_sha256):
    directory = Path(directory).resolve()
    manifest = input_manifest(request, request_sha256)
    require(json.loads(_text(directory / 'input-manifest.json')) == manifest, 'Input manifest mismatch')
    report_hashes = {}
    for name in RAW_REPORTS:
        path = directory / name
        require(path.is_file() and not path.is_symlink() and path.stat().st_size > 0, 'Missing evidence: ' + name)
        report_hashes[name] = hashes([path])[str(path)]
    observations = evaluate(directory, request)
    require(all(hashes([directory / name])[str(directory / name)] == value for name, value in report_hashes.items()),
            'Evidence changed while being parsed')
    result = {'schema_version': 1, **manifest, 'report_hashes': report_hashes,
              'observations': observations,
              'integrity_note': 'Hashes bind this local trusted invocation; they are not vendor signatures.'}
    save(directory / 'qualification.json', result)
    return result


def validate_feedback(response, request, directory):
    """Rehash all artifacts and recompute every observable gate for exploration."""
    directory = Path(directory).resolve()
    run = directory / 'vivado'
    require(run.is_dir() and not run.is_symlink(), 'Missing/symlinked invocation directory')
    for dependency in dependencies():
        require(request['configuration']['immutable_hashes'].get(dependency) == hashes([dependency])[dependency],
                'Qualification producer is not frozen')
    require(response.get('executed') is True and response.get('tool_returncode') == 0,
            'No completed Vivado invocation')
    request_file = directory / 'request.json'
    require(request_file.is_file(), 'Missing invocation request')
    request_sha = hashes([request_file])[str(request_file)]
    require(json.loads(_text(request_file)) == request and response.get('request_sha256') == request_sha,
            'Feedback request mismatch')
    require(response.get('configuration') == request['configuration'] and response.get('source_hashes') == request['source_hashes']
            and response.get('source_read_order') == request['configuration']['source_read_order'], 'Feedback source/configuration mismatch')
    expected_manifest = input_manifest(request, request_sha)
    qualification = json.loads(_text(run / 'qualification.json', 128 * 1024 * 1024))
    require(qualification.get('schema_version') == 1 and all(qualification.get(k) == v for k, v in expected_manifest.items()),
            'Qualification manifest mismatch')
    require(json.loads(_text(run / 'input-manifest.json')) == expected_manifest, 'Invocation manifest mismatch')
    require(set(qualification.get('report_hashes', {})) == set(RAW_REPORTS), 'Incomplete bound report set')
    for name, expected in qualification['report_hashes'].items():
        path = run / name
        require(path.is_file() and not path.is_symlink() and hashes([path])[str(path)] == expected, 'Changed qualification evidence: ' + name)
    expected_reports = {**{name: name for name in RAW_REPORTS}, **REPORT_KEYS}
    for key, name in expected_reports.items():
        record = response.get('reports', {}).get(key, {})
        path = run / name
        require(record.get('sha256') == hashes([path])[str(path)] and (directory / record.get('path', '')).resolve() == path,
                'Response evidence binding mismatch: ' + key)
    require(hashes(request['source_hashes']) == request['source_hashes']
            and hashes(request['configuration']['immutable_hashes']) == request['configuration']['immutable_hashes'], 'Frozen inputs changed')
    observations = evaluate(run, request)
    require(observations == qualification.get('observations'), 'Claimed qualification contradicts raw reports')
    for key in ('metrics', 'critical_paths', 'source_ownership'):
        require(response.get(key) == observations[key], 'Claimed ' + key + ' contradicts raw reports')
    require(response.get('qualification') == observations, 'Response qualification differs')
    require(all(hashes([run / name])[str(run / name)] == value for name, value in qualification['report_hashes'].items()),
            'Evidence changed while being validated')
    return observations


def validate_admission(response, request, directory):
    """Strict boundary. No boolean, waiver or RTL KAT can replace netlist checks."""
    observations = validate_feedback(response, request, directory)
    require(all(value == 'PASS' for value in observations['gates'].values()),
            'Vivado admission blocked: ' + ', '.join(observations['blockers']))
    return observations
