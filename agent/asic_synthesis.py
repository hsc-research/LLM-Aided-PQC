"""Explicit Genus/DC fixed-period logic synthesis, not RTL/PPA admission.

Vendor scripts require qualification with licensed site tools and libraries.
Unknown report values stay null. No Fmax inference and no automatic fallback.
"""
from __future__ import annotations
import argparse
import itertools
import gzip
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import time
import uuid

try:
    from .run_safety import hashes, run_process
except ImportError:
    from run_safety import hashes, run_process

TIME_NS = {'ps': 0.001, 'ns': 1.0, 'us': 1000.0}
SITE_ENVIRONMENT = ('PQC_ASIC_INPUT_TRANSITION_NS', 'PQC_ASIC_CLOCK_UNCERTAINTY_NS', 'PQC_ASIC_OUTPUT_LOAD')
NUMBER = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'


def word(value):
    text = str(value)
    for old, new in (('\\', '\\\\'), ('"', '\\"'), ('$', '\\$'),
                     ('[', '\\['), (']', '\\]'), ('\n', '\\n'), ('\r', '\\r')):
        text = text.replace(old, new)
    return '"' + text + '"'


def tlist(values):
    return '[list ' + ' '.join(word(v) for v in values) + ']'


def resolve(value, root):
    text = os.path.expandvars(os.path.expanduser(str(value)))
    if '$' in text or 'REPLACE_ME' in text:
        raise ValueError(f'Unresolved configuration path: {value}')
    path = Path(text)
    return str((root / path).resolve()) if not path.is_absolute() else str(path.resolve())


def positive(value, label):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f'{label} must be finite and positive')
    return value


def validate_liberty_time_units(libraries, declared):
    """Verify declared Genus native units against every loaded Liberty header.

    This verifies library metadata, not arbitrary unit-changing site Tcl.
    Unknown/compiled formats are intentionally unsupported in this Genus flow.
    """
    for filename in libraries:
        path = Path(filename)
        if path.name.endswith('.lib.gz'):
            with gzip.open(path, 'rt') as stream:
                text = stream.read()
        elif path.suffix == '.lib':
            text = path.read_text()
        else:
            raise ValueError('Genus requires inspectable .lib or .lib.gz files for unit verification')
        text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
        declarations = re.findall(r'\btime_unit\s*:\s*"([^"\n]+)"\s*;', text)
        if not declarations:
            raise ValueError(f'No Liberty time_unit metadata in {path.name}')
        for value in declarations:
            match = re.fullmatch(r'\s*(' + NUMBER + r')\s*(ps|ns|us)\s*', value)
            if not match or not math.isclose(float(match[1]) * TIME_NS[match[2]], TIME_NS[declared], rel_tol=1e-12):
                raise ValueError(f'Liberty time_unit differs from declared {declared}: {path.name}')


def load_config(path, tool=None):
    path = Path(path).resolve()
    cfg = json.loads(path.read_text())
    if cfg.get('schema_version') != 1:
        raise ValueError('schema_version must be 1')
    selected = tool or cfg.get('synthesis_tool', 'genus')
    if selected not in ('genus', 'dc'):
        raise ValueError('Choose genus or dc')
    spec = cfg.get('tools', {}).get(selected)
    if not isinstance(spec, dict):
        raise ValueError(f'No configuration for {selected}')
    root = Path(resolve(cfg.get('root', '..'), path.parent))
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_$]*', cfg.get('top', '')):
        raise ValueError('top must be an HDL identifier')
    period = positive(cfg.get('period_ns'), 'period_ns')
    unit = spec.get('time_unit')
    if unit not in TIME_NS:
        raise ValueError('Declare native library time_unit: ps, ns, or us')
    if cfg.get('memory_model') not in ('flops', 'macros'):
        raise ValueError('Declare memory_model: flops or macros; no unmodeled-blackbox mode')
    files = cfg.get('files', [])
    if not isinstance(files, list) or not files:
        raise ValueError('An ordered files manifest is required')
    sources = []
    for item in files:
        if item.get('language') not in ('verilog', 'systemverilog', 'vhdl'):
            raise ValueError('Unsupported source language')
        sources.append({'path': resolve(item['path'], root), 'language': item['language']})
    if len({x['path'] for x in sources}) != len(sources):
        raise ValueError('Duplicate source file in manifest')
    libraries = [resolve(p, root) for p in spec.get('target_libraries', [])]
    if not libraries:
        raise ValueError('target_libraries is required')
    if selected == 'dc' and any(not p.endswith('.db') for p in libraries):
        raise ValueError('DC requires compiled .db libraries; no implicit .lib conversion')
    includes = [resolve(p, root) for p in cfg.get('include_dirs', [])]
    sdc = resolve(cfg['sdc'], root)
    inputs = [str(path), sdc, *libraries, *(x['path'] for x in sources)]
    data = [resolve(p, root) for p in cfg.get('data_files', [])]
    if len({Path(p).name for p in data}) != len(data):
        raise ValueError('Data files must have unique basenames for run-directory staging')
    reserved = {'run.tcl', 'manifest.json', 'tool.log', 'result.json', 'timing.rpt',
                'area.rpt', 'power.rpt', 'netlist.v', 'constraints.sdc', 'design.db', 'design.ddc',
                'unresolved.rpt', 'constraint_audit.rpt', 'units.rpt', 'check_timing.rpt', 'hold.rpt'}
    if any(Path(p).name in reserved for p in data):
        raise ValueError('Data file collides with reserved run artifact')
    inputs += data
    for directory in includes:
        if not Path(directory).is_dir():
            raise ValueError(f'Missing include directory: {directory}')
        inputs += [str(p) for p in Path(directory).rglob('*') if p.is_file()
                   and p.suffix in ('.v', '.vh', '.sv', '.svh', '.vhd', '.vhdl')]
    setup = resolve(spec['setup_tcl'], root) if spec.get('setup_tcl') else None
    if setup:
        inputs.append(setup)
    extras = [resolve(p, root) for p in spec.get('link_libraries', [])]
    inputs += extras
    if selected == 'genus':
        validate_liberty_time_units(libraries + extras, unit)
    defines = cfg.get('defines', [])
    if not isinstance(defines, list) or any(not isinstance(d, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(?:=[^\r\n]*)?', d) for d in defines):
        raise ValueError('defines must contain NAME or NAME=value strings')
    params = cfg.get('parameters', {})
    if not isinstance(params, dict) or any(not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', k) for k in params):
        raise ValueError('Invalid parameter names')
    parameters = []
    for key, value in params.items():
        if isinstance(value, bool):
            value = int(value)
        if isinstance(value, str):
            if not re.fullmatch(r'[A-Za-z0-9_.-]+', value):
                raise ValueError('String parameters must be simple identifiers')
            value = '"' + value + '"'
        elif not isinstance(value, int):
            raise ValueError('Parameters must be integers or simple strings')
        parameters.append(f'{key}={value}')
    effort = spec.get('effort', {'generic': 'high', 'map': 'high', 'opt': 'high'})
    if not isinstance(effort, dict) or any(effort.get(k) not in ('low', 'medium', 'high') for k in ('generic', 'map', 'opt')):
        raise ValueError('Genus effort requires generic/map/opt = low, medium, or high')
    compile_mode = spec.get('compile', 'compile_ultra')
    if compile_mode not in ('compile', 'compile_ultra'):
        raise ValueError('DC compile must be compile or compile_ultra')
    timeout = positive(cfg.get('timeout_seconds', 288000), 'timeout_seconds')
    executable = spec.get('executable', 'genus' if selected == 'genus' else 'dc_shell')
    if not isinstance(executable, str) or not executable or '\x00' in executable:
        raise ValueError('executable must be one executable path/name')
    return {'tool': selected, 'root': str(root), 'top': cfg['top'], 'period_ns': period,
            'time_unit': unit, 'scope': cfg.get('scope', 'unspecified'),
            'memory_model': cfg['memory_model'], 'files': sources, 'include_dirs': includes,
            'defines': defines, 'parameters': parameters, 'libraries': libraries,
            'link_libraries': extras, 'sdc': sdc, 'setup': setup, 'data_files': data,
            'effort': effort, 'compile': compile_mode, 'executable': executable,
            'output_root': resolve(cfg.get('output_root', 'runs/asic'), root),
            'timeout_seconds': timeout, 'input_hashes': hashes(inputs),
            'area_unit': spec.get('area_unit', 'library_unit'),
            'tool_version_declared': spec.get('version', 'unspecified'),
            'power_activity': spec.get('power_activity', 'unspecified'),
            'library_corner_declared': spec.get('corner', 'unspecified'),
            'site_environment': {name: os.environ.get(name) for name in SITE_ENVIRONMENT}}


def render_tcl(plan):
    tool = plan['tool']
    lines = ['# Fixed-period LOGICAL synthesis, not place-and-route.',
             '# Qualify against the installed EDA release and library before publishing PPA.',
             'if {[catch {', f"set PQC_PERIOD_NS {plan['period_ns']}",
             f"set PERIOD_PS {plan['period_ns'] * 1000:.12g}",
             f"set PQC_PERIOD {plan['period_ns'] / TIME_NS[plan['time_unit']]:.12g}"]
    if tool == 'genus':
        lines += [f"set_db library {tlist(plan['libraries'] + plan['link_libraries'])}",
                  f"set_db init_hdl_search_path {tlist(plan['include_dirs'])}",
                  'set_db hdl_error_on_blackbox true']
    else:
        lines += [f"set_app_var target_library {tlist(plan['libraries'])}",
                  f"set_app_var link_library [concat [list *] {tlist(plan['libraries'] + plan['link_libraries'])}]",
                  f"set_app_var search_path [concat $search_path {tlist(plan['include_dirs'])}]",
                  'file mkdir work', 'define_design_lib WORK -path ./work']
    if plan['setup']:
        lines.append('source ' + word(plan['setup']))
    for language, items in itertools.groupby(plan['files'], key=lambda item: item['language']):
        files = tlist(item['path'] for item in items)
        define = ' -define ' + tlist(plan['defines']) if plan['defines'] and language != 'vhdl' else ''
        if tool == 'genus':
            flag = ' -sv' if language == 'systemverilog' else ' -language vhdl' if language == 'vhdl' else ''
            lines.append(f'read_hdl{flag}{define} {files}')
        else:
            language = 'sverilog' if language == 'systemverilog' else language
            lines.append(f'if {{![analyze -format {language}{define} {files}]}} {{error "HDL analysis failed"}}')
    parameter = ''
    if plan['parameters']:
        value = tlist(plan['parameters']) if tool == 'genus' else word(','.join(plan['parameters']))
        parameter = ' -parameters ' + value
    lines.append('elaborate ' + word(plan['top']) + parameter)
    if tool == 'dc':
        lines += ['current_design ' + word(plan['top']), 'if {![link]} {error "Link failed"}',
                  'if {![check_design]} {error "Design checks failed"}']
    else:
        lines += ['check_design -unresolved > unresolved.rpt']
    lines += ['source ' + word(plan['sdc'])]
    if tool == 'genus':
        lines += ['if {[llength [get_db clocks]] != 1} {error "Expected exactly one clock after SDC"}',
                  'set actual_period [lindex [get_db clocks .period] 0]']
        lines += clock_audit_tcl()
        for phase in ('generic', 'map', 'opt'):
            lines += [f"set_db syn_{phase}_effort {plan['effort'][phase]}"]
        lines += ['syn_generic', 'syn_map', 'syn_opt', 'report timing -nworst 20 > timing.rpt',
                  'report area > area.rpt', 'report gates > gates.rpt', 'report power > power.rpt',
                  'write_hdl > netlist.v', 'write_sdc > constraints.sdc', 'write_db design.db']
    else:
        lines += ['if {[sizeof_collection [all_clocks]] != 1} {error "Expected exactly one clock after SDC"}',
                  'set actual_period [get_attribute [all_clocks] period]']
        lines += clock_audit_tcl()
        lines += ['compile_ultra -no_autoungroup' if plan['compile'] == 'compile_ultra' else 'compile',
                  'redirect timing.rpt {report_timing -delay_type max -max_paths 20 -nosplit}',
                  'redirect area.rpt {report_area -nosplit}', 'redirect power.rpt {report_power -nosplit}',
                  'redirect units.rpt {report_units}', 'redirect check_timing.rpt {check_timing}',
                  'redirect hold.rpt {report_timing -delay_type min -max_paths 20 -nosplit}',
                  'write -format verilog -hierarchy -output netlist.v', 'write_sdc constraints.sdc',
                  'write -format ddc -hierarchy -output design.ddc']
    lines += ['puts "PQC_SYNTHESIS_DONE"', '} message]} {',
              'puts stderr "PQC_SYNTHESIS_ERROR: $message"', 'exit 1', '}', 'exit 0']
    return '\n'.join(lines) + '\n'


def clock_audit_tcl():
    return [
        'if {![string is double -strict $actual_period] || abs($actual_period - $PQC_PERIOD) > 1e-6 * $PQC_PERIOD} {error "SDC clock period differs from configured period"}',
        'set audit [open constraint_audit.rpt w]',
        'puts $audit "PQC_PERIOD_NATIVE $actual_period"',
        'close $audit',
    ]


def _finite(value, label, *, nonnegative=False):
    number = float(value)
    if not math.isfinite(number) or (nonnegative and number < 0):
        raise ValueError(f'{label} must be finite' + (' and nonnegative' if nonnegative else ''))
    return number


def _one_labeled_number(text, label, pattern):
    """A missing field is unknown; a present but malformed field is an error."""
    lines = re.findall(r'^\s*' + re.escape(label) + r'[^\n]*$', text, re.M | re.I)
    if not lines:
        return None
    if len(lines) != 1:
        raise ValueError(f'Ambiguous {label}')
    match = re.fullmatch(pattern, lines[0].strip(), re.I)
    if not match:
        raise ValueError(f'Malformed {label}')
    return match


def parse_metrics(tool, timing, area, power, time_unit, top, area_unit):
    """Parse supported report dialects without silently dropping bad rows.

    Reports summarize sampled paths, not a timing-signoff coverage proof.
    Missing area/power remains null. A recognized but invalid row fails closed.
    """
    if tool not in ('genus', 'dc') or time_unit not in TIME_NS:
        raise ValueError('Unsupported tool or time unit')
    if re.search(r'\bunconstrained\b|No\s+(?:constrained\s+)?(?:timing\s+)?paths', timing, re.I):
        raise ValueError('Unconstrained or absent timing paths')
    if tool == 'genus':
        lines = re.findall(r'^\s*Path\s+\S+:[^\n]*$', timing, re.M)
        records = []
        for number, line in enumerate(lines, 1):
            match = re.fullmatch(r'\s*Path\s+(\d+):\s*(MET|VIOLATED)\s*\((' + NUMBER +
                                 r')\s*(ps|ns|us)\)\s+Setup Check(?:\s+[^\n]*)?', line)
            if not match or int(match[1]) != number:
                raise ValueError('Malformed, unsupported, or out-of-order Genus timing path')
            records.append((match[2], match[3], match[4]))
    else:
        lines = re.findall(r'^\s*slack\b[^\n]*$', timing, re.M | re.I)
        types = re.findall(r'^\s*Path Type:\s*(\S+)\s*$', timing, re.M | re.I)
        if len(types) != len(lines) or not types or any(t.lower() != 'max' for t in types):
            raise ValueError('Expected one DC max/setup Path Type for each slack row')
        records = []
        for line in lines:
            match = re.fullmatch(r'\s*slack\s*\((MET|VIOLATED)\)\s*(' + NUMBER + r')\s*', line, re.I)
            if not match:
                raise ValueError('Malformed DC slack row')
            records.append((match[1].upper(), match[2], time_unit))
    if not records:
        raise ValueError('No supported setup-slack result in timing.rpt')
    slacks = []
    for status, value, unit in records:
        value = _finite(value, 'Setup slack')
        # A VIOLATED -0 result can be rounded by the tool. Preserve its status.
        if (status == 'VIOLATED' and value > 0) or (status == 'MET' and value < 0):
            raise ValueError('Contradictory timing status')
        slacks.append(_finite(value * TIME_NS[unit], 'Normalized setup slack'))
    cell_count, cell_area = None, None
    if tool == 'genus':
        lines = re.findall(r'^\s*' + re.escape(top) + r'(?=\s)[^\n]*$', area, re.M)
        if lines:
            if len(lines) != 1:
                raise ValueError('Ambiguous top-level Genus area row')
            match = re.fullmatch(r'\s*' + re.escape(top) + r'\s+\S+\s+(\d+)\s+(' + NUMBER +
                                 r')(?:\s+' + NUMBER + r')*\s*', lines[0])
            if not match:
                raise ValueError('Malformed Genus area row')
            cell_count, cell_area = int(match[1]), _finite(match[2], 'Cell area', nonnegative=True)
    else:
        match = _one_labeled_number(area, 'Total cell area:', r'Total cell area:\s*(' + NUMBER + r')')
        if match:
            cell_area = _finite(match[1], 'Cell area', nonnegative=True)
        match = _one_labeled_number(area, 'Number of cells:', r'Number of cells:\s*(\d+)')
        if match:
            cell_count = int(match[1])
    if cell_count == 0 or cell_area == 0:
        raise ValueError('Zero mapped cell area/count is not a supported design measurement')
    powers = []
    factors = {'pw': 1e-12, 'nw': 1e-9, 'uw': 1e-6, 'mw': 1e-3, 'w': 1}
    if tool == 'dc':
        for label in ('Total Dynamic Power', 'Cell Leakage Power'):
            match = _one_labeled_number(power, label, re.escape(label) + r'\s*=\s*(' + NUMBER +
                                        r')\s*(pW|nW|uW|mW|W)(?:\s+\([^\n]*\))?')
            if match:
                powers.append(_finite(float(match[1]) * factors[match[2].lower()], label, nonnegative=True))
        total_power = _finite(sum(powers), 'Total power', nonnegative=True) if len(powers) == 2 else None
    else:
        units = re.findall(r'^\s*Power Unit:\s*(\S+)\s*$', power, re.M)
        rows = re.findall(r'^\s*Subtotal\b[^\n]*$', power, re.M)
        total_power = None
        if rows:
            if len(rows) != 1 or len(units) != 1 or units[0].lower() not in factors:
                raise ValueError('Unsupported or ambiguous Genus power unit/subtotal')
            match = re.fullmatch(r'\s*Subtotal\s+' + r'\s+'.join('(' + NUMBER + ')' for _ in range(4)) +
                                 r'\s+' + NUMBER + r'%\s*', rows[0])
            if not match:
                raise ValueError('Malformed Genus power subtotal')
            values = [_finite(v, 'Genus power', nonnegative=True) for v in match.groups()]
            if not math.isclose(sum(values[:3]), values[3], rel_tol=5e-4, abs_tol=1e-12):
                raise ValueError('Genus power subtotal contradicts components')
            total_power = _finite(values[3] * factors[units[0].lower()], 'Total power', nonnegative=True)
    return {'worst_setup_slack_ns': min(slacks),
            'timing_met_reported': all(status == 'MET' for status, _, _ in records),
            'cell_count': cell_count, 'cell_area_reported': cell_area, 'area_unit': area_unit,
            'power_w': total_power, 'fmax_mhz': None,
            'tns_ns': None, 'reported_path_count': len(slacks)}


def validate_unresolved_report(text, top):
    # Genus 25.12 dialect, independently backed by tracked HQC reports.
    # Unknown dialects must be reviewed rather than treated as zero references.
    allowed = (r"^\s*(?:Check Design Report \(c\)|-+|Unresolved References & Empty Modules|"
               r"No (?:unresolved references|empty modules) in design '" + re.escape(top) +
               r"'|Done Checking the design\.)?\s*$")
    for line in text.splitlines():
        if not re.fullmatch(allowed, line):
            raise ValueError('Unsupported or contradictory Genus unresolved-reference findings')
    for label in ('unresolved references', 'empty modules'):
        pattern = r"^\s*No " + label + r" in design '" + re.escape(top) + r"'\s*$"
        if len(re.findall(pattern, text, re.M)) != 1:
            raise ValueError(f'No explicit zero-{label} evidence for {top}')


def validate_dc_units(text, expected):
    units = re.findall(r'^\s*Time\s+Units\s*:\s*(' + NUMBER + r')\s*(ps|ns|us)\s*$', text, re.M | re.I)
    if len(units) != 1 or not math.isclose(_finite(units[0][0], 'Report time unit') * TIME_NS[units[0][1].lower()],
                                         TIME_NS[expected], rel_tol=1e-12):
        raise ValueError('DC report_units time unit is unsupported or differs from configuration')


def validate_tool_log(text):
    if re.search(r'^\s*(?:Error|Fatal)\s*(?::|\[)', text, re.M | re.I):
        raise RuntimeError('Tool log contains an error despite zero exit status')
    if re.search(r'\[(?:CDFG-428|TUI-273)\]|\bblackbox was created\b|Unable to resolve reference', text, re.I):
        raise RuntimeError('Tool log reports an unresolved or blackboxed design')


def run(plan, dry_run=False):
    script = render_tcl(plan)
    if dry_run:
        return {'status': 'DRY_RUN', 'tool': plan['tool'], 'stage': 'post_synth',
                'top': plan['top'], 'period_ns': plan['period_ns'], 'tcl': script}
    executable = shutil.which(os.path.expandvars(os.path.expanduser(plan['executable'])))
    if not executable:
        raise ValueError(f"Selected executable not found: {plan['executable']}; no fallback performed")
    before = plan['input_hashes']
    if {name: os.environ.get(name) for name in SITE_ENVIRONMENT} != plan.get('site_environment', {}):
        raise ValueError('Site constraint environment changed after configuration loading')
    if hashes(before) != before:
        raise ValueError('Inputs changed after configuration loading')
    directory = Path(plan['output_root']) / (plan['tool'] + '-' + uuid.uuid4().hex)
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.mkdir(exist_ok=False)
    (directory / 'run.tcl').write_text(script)
    (directory / 'manifest.json').write_text(json.dumps(plan, indent=2))
    for data in plan['data_files']:
        shutil.copy2(data, directory / Path(data).name)
    flag = ['-no_gui', '-files'] if plan['tool'] == 'genus' else ['-f']
    command = [executable, *flag, str(directory / 'run.tcl')]
    result = {'tool': plan['tool'], 'stage': 'post_synth', 'scope': plan['scope'], 'top': plan['top'],
              'period_ns': plan['period_ns'], 'memory_model': plan['memory_model'],
              'command': command, 'run_dir': str(directory), 'automatic_acceptance': False,
              'tool_qualification': 'site_validation_required', 'status': 'ERROR',
              'power_activity': plan.get('power_activity', 'unspecified'),
              'workload_power_validated': False, 'timing_signoff': False,
              'tool_version_declared': plan['tool_version_declared'],
              'library_corner_declared': plan.get('library_corner_declared', 'unspecified'),
              'time_units_verified': False,
              'library_time_units_verified': plan['tool'] == 'genus',
              'period_semantics': 'requested period; check unit evidence before publication',
              'actual_period_ns': None,
              'generated_tcl_sha256': hashes([directory / 'run.tcl'])[str(directory / 'run.tcl')]}
    started = time.monotonic()
    try:
        completed = run_process(command, cwd=directory, timeout=plan['timeout_seconds'], log_path=directory / 'tool.log')
        result['returncode'] = completed.returncode
        if completed.returncode or not re.search(r'^PQC_SYNTHESIS_DONE\s*$', completed.stdout, re.M):
            raise RuntimeError('Tool failed or completion marker is absent; see tool.log')
        validate_tool_log(completed.stdout)
        required = ['timing.rpt', 'area.rpt', 'power.rpt', 'netlist.v', 'constraints.sdc',
                    'design.db' if plan['tool'] == 'genus' else 'design.ddc', 'constraint_audit.rpt']
        if plan['tool'] == 'genus':
            required.append('unresolved.rpt')
        else:
            required += ['units.rpt', 'check_timing.rpt', 'hold.rpt']
        for name in required:
            file = directory / name
            if not file.is_file() or file.is_symlink() or file.stat().st_size == 0:
                raise RuntimeError(f'Missing or empty artifact: {name}')
        audit = (directory / 'constraint_audit.rpt').read_text().strip()
        match = re.fullmatch(r'PQC_PERIOD_NATIVE (' + NUMBER + ')', audit)
        if not match or not math.isclose(_finite(match[1], 'Audited period') * TIME_NS[plan['time_unit']],
                                        plan['period_ns'], rel_tol=1e-6):
            raise ValueError('Missing or contradictory clock-period audit')
        if plan['tool'] == 'dc':
            validate_dc_units((directory / 'units.rpt').read_text(), plan['time_unit'])
            result['time_units_verified'] = True
            result['actual_period_ns'] = float(match[1]) * TIME_NS[plan['time_unit']]
        if plan['tool'] == 'genus':
            validate_unresolved_report((directory / 'unresolved.rpt').read_text(), plan['top'])
        if hashes(before) != before:
            raise RuntimeError('Declared input files changed during synthesis')
        result['metrics'] = parse_metrics(plan['tool'], *((directory / name).read_text() for name in
                                          ('timing.rpt', 'area.rpt', 'power.rpt')), plan['time_unit'], plan['top'], plan['area_unit'])
        result['metrics_complete'] = all(result['metrics'].get(k) is not None for k in
                                        ('worst_setup_slack_ns', 'cell_count', 'cell_area_reported', 'power_w'))
        result['report_hashes'] = hashes(directory / name for name in required if name.endswith('.rpt'))
        result['status'] = 'MEASURED'
    except BaseException as error:
        result['error'] = str(error)
        raise
    finally:
        result['runtime_seconds'] = time.monotonic() - started
        (directory / 'result.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--tool', choices=('genus', 'dc'))
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    try:
        print(json.dumps(run(load_config(args.config, args.tool), args.dry_run), indent=2))
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print('ASIC RUN FAILED:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
