"""Explicit Genus/DC fixed-period logic synthesis, not RTL/PPA admission.

Vendor scripts require qualification with licensed site tools and libraries.
Unknown report values stay null. No Fmax inference and no automatic fallback.
"""
from __future__ import annotations
import argparse
import itertools
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
                'area.rpt', 'power.rpt', 'netlist.v', 'constraints.sdc', 'design.db', 'design.ddc'}
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
            'tool_version_declared': spec.get('version', 'unspecified')}


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
        lines += ['if {[llength [get_db clocks]] == 0} {error "No clocks after SDC"}']
        for phase in ('generic', 'map', 'opt'):
            lines += [f"set_db syn_{phase}_effort {plan['effort'][phase]}"]
        lines += ['syn_generic', 'syn_map', 'syn_opt', 'report timing -nworst 20 > timing.rpt',
                  'report area > area.rpt', 'report gates > gates.rpt', 'report power > power.rpt',
                  'write_hdl > netlist.v', 'write_sdc > constraints.sdc', 'write_db design.db']
    else:
        lines += ['if {[sizeof_collection [all_clocks]] == 0} {error "No clocks after SDC"}',
                  'compile_ultra -no_autoungroup' if plan['compile'] == 'compile_ultra' else 'compile',
                  'redirect timing.rpt {report_timing -delay_type max -max_paths 20 -nosplit}',
                  'redirect area.rpt {report_area -nosplit}', 'redirect power.rpt {report_power -nosplit}',
                  'write -format verilog -hierarchy -output netlist.v', 'write_sdc constraints.sdc',
                  'write -format ddc -hierarchy -output design.ddc']
    lines += ['puts "PQC_SYNTHESIS_DONE"', '} message]} {',
              'puts stderr "PQC_SYNTHESIS_ERROR: $message"', 'exit 1', '}', 'exit 0']
    return '\n'.join(lines) + '\n'


def parse_metrics(tool, timing, area, power, time_unit, top, area_unit):
    slacks = []
    if tool == 'genus':
        records = re.findall(r'Path\s+\d+:\s*(MET|VIOLATED)\s*\((' + NUMBER + r')\s*(ps|ns|us)\)', timing)
    else:
        records = [(status.upper(), value, time_unit) for status, value in
                   re.findall(r'slack\s*\((MET|VIOLATED)\)\s*(' + NUMBER + r')', timing, re.I)]
    for status, value, unit in records:
        value = float(value)
        if (status == 'VIOLATED' and value >= 0) or (status == 'MET' and value < 0):
            raise ValueError('Contradictory timing status')
        slacks.append(value * TIME_NS[unit])
    if not slacks or any(not math.isfinite(v) for v in slacks):
        raise ValueError('No finite supported setup-slack result in timing.rpt')
    cell_count, cell_area = None, None
    if tool == 'genus':
        match = re.search(r'^\s*' + re.escape(top) + r'\s+\S+\s+(\d+)\s+(' + NUMBER + r')', area, re.M)
        if match:
            cell_count, cell_area = int(match[1]), float(match[2])
    else:
        match = re.search(r'Total cell area:\s*(' + NUMBER + r')', area, re.I)
        if match:
            cell_area = float(match[1])
        match = re.search(r'Number of cells:\s*(\d+)', area, re.I)
        if match:
            cell_count = int(match[1])
    powers = []
    for label in ('Total Dynamic Power', 'Cell Leakage Power'):
        match = re.search(label + r'\s*=\s*(' + NUMBER + r')\s*(pW|nW|uW|mW|W)\b', power)
        if match:
            powers.append(float(match[1]) * {'pW': 1e-12, 'nW': 1e-9, 'uW': 1e-6, 'mW': 1e-3, 'W': 1}[match[2]])
    return {'worst_setup_slack_ns': min(slacks), 'timing_met_reported': min(slacks) >= 0,
            'cell_count': cell_count, 'cell_area_reported': cell_area, 'area_unit': area_unit,
            'power_w': sum(powers) if len(powers) == 2 else None, 'fmax_mhz': None,
            'tns_ns': None, 'reported_path_count': len(slacks)}


def run(plan, dry_run=False):
    script = render_tcl(plan)
    if dry_run:
        return {'status': 'DRY_RUN', 'tool': plan['tool'], 'stage': 'post_synth',
                'top': plan['top'], 'period_ns': plan['period_ns'], 'tcl': script}
    executable = shutil.which(os.path.expandvars(os.path.expanduser(plan['executable'])))
    if not executable:
        raise ValueError(f"Selected executable not found: {plan['executable']}; no fallback performed")
    before = plan['input_hashes']
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
              'tool_qualification': 'site_validation_required', 'status': 'ERROR'}
    started = time.monotonic()
    try:
        completed = run_process(command, cwd=directory, timeout=plan['timeout_seconds'], log_path=directory / 'tool.log')
        result['returncode'] = completed.returncode
        if completed.returncode or not re.search(r'^PQC_SYNTHESIS_DONE\s*$', completed.stdout, re.M):
            raise RuntimeError('Tool failed or completion marker is absent; see tool.log')
        if re.search(r'^\s*(?:Error|ERROR|Fatal|FATAL)\s*(?::|\[)', completed.stdout, re.M):
            raise RuntimeError('Tool log contains an error despite zero exit status')
        required = ['timing.rpt', 'area.rpt', 'power.rpt', 'netlist.v', 'constraints.sdc',
                    'design.db' if plan['tool'] == 'genus' else 'design.ddc']
        for name in required:
            file = directory / name
            if not file.is_file() or file.is_symlink() or file.stat().st_size == 0:
                raise RuntimeError(f'Missing or empty artifact: {name}')
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
        (directory / 'result.json').write_text(json.dumps(result, indent=2))
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
