"""Explicit Genus/DC fixed-period logic synthesis, not RTL/PPA admission.

Vendor scripts require qualification with licensed site tools and libraries.
Unknown report values stay null. No Fmax inference and no automatic fallback.
"""
from __future__ import annotations
import argparse
import itertools
import gzip
import hashlib
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
ADMISSION_POLICY = 'strict-rtl-flops-v1'
ADMISSION_CHECKS = ('missing_modules', 'empty_modules', 'port_width_mismatches',
                    'port_connection_errors', 'multiple_drivers', 'latches',
                    'implicit_nets', 'undriven_nets', 'combinational_loops',
                    'unreviewed_diagnostics')
ADMISSION_POSITIVE_CONTROLS = ('known_good', 'known_good_flop_memory', 'compilation_unit', 'language_standard')
ADMISSION_CONTROLS = (*ADMISSION_POSITIVE_CONTROLS, 'missing_modules', 'empty_modules',
                      'port_width_mismatches', 'port_connection_errors',
                      'multiple_drivers', 'latches', 'implicit_nets', 'undriven_nets',
                      'combinational_loops', 'unreviewed_diagnostics', 'memory_macro')
MEMORY_FIELDS = ('memory_inventory_complete', 'memory_macro_cells', 'memory_blackboxes',
                 'unmapped_memory_bits', 'mapped_memory_bits', 'flip_flop_memory_bits')


def read_json_object(path):
    """Do not silently accept duplicate keys in admission/qualification evidence."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate JSON key: {key}')
            result[key] = value
        return result
    result = json.loads(Path(path).read_text(), object_pairs_hook=unique)
    if not isinstance(result, dict):
        raise ValueError(f'Expected JSON object: {path}')
    return result


def load_admission(cfg, spec, root, tool):
    """Optional strict contract; no bundled adapter is claimed vendor-qualified.

    A site supplies a reviewed Tcl adapter, qualification controls and diagnostic
    policy for one exact tool release. Dry-run may describe a missing adapter;
    execution cannot. Legacy measurement is explicitly not structural admission.
    """
    policy = cfg.get('admission')
    if policy is None:
        if spec.get('admission_adapter') is not None:
            raise ValueError('admission_adapter requires an explicit admission policy')
        return None, []
    if not isinstance(policy, dict) or set(policy) - {'policy', 'waivers'}:
        raise ValueError('Unsupported admission configuration fields')
    if policy.get('policy') != ADMISSION_POLICY or cfg['memory_model'] != 'flops':
        raise ValueError('Strict admission requires strict-rtl-flops-v1 and memory_model=flops')
    waivers = policy.get('waivers', [])
    if not isinstance(waivers, list):
        raise ValueError('admission.waivers must be a list of exact reviewed diagnostics')
    seen = set()
    for waiver in waivers:
        if (not isinstance(waiver, dict) or
                set(waiver) != {'diagnostic_id', 'line_sha256', 'reason', 'approved_by'} or
                any(not isinstance(waiver.get(k), str) or not waiver[k].strip() for k in waiver) or
                not re.fullmatch(r'[0-9a-f]{64}', waiver['line_sha256'])):
            raise ValueError('Each waiver needs diagnostic_id, exact line_sha256, reason and approved_by')
        identity = (waiver['diagnostic_id'], waiver['line_sha256'])
        if identity in seen:
            raise ValueError('Duplicate diagnostic waiver')
        seen.add(identity)
    adapter = spec.get('admission_adapter')
    result = {'policy': ADMISSION_POLICY, 'waivers': waivers, 'adapter': None}
    if adapter is None:
        return result, []
    if not isinstance(adapter, dict) or set(adapter) != {'tcl', 'qualification', 'inputs'}:
        raise ValueError('admission_adapter requires tcl, qualification and inputs')
    if not isinstance(adapter['inputs'], list):
        raise ValueError('admission_adapter.inputs must declare all adapter dependencies')
    paths = {key: resolve(adapter[key], root) for key in ('tcl', 'qualification')}
    dependencies = [resolve(path, root) for path in adapter['inputs']]
    qualification = read_json_object(paths['qualification'])
    version = spec.get('version', 'unspecified')
    if (qualification.get('schema_version') != 1 or qualification.get('policy') != ADMISSION_POLICY or
            qualification.get('tool') != tool or qualification.get('tool_version') != version or
            not isinstance(version, str) or not version.strip() or '\n' in version or '\r' in version or
            version in ('unspecified', 'record-installed-version')):
        raise ValueError('Unsupported or unqualified admission tool/version/policy')
    for key in ('reviewed_by', 'reviewed_at', 'diagnostic_policy_review'):
        if not isinstance(qualification.get(key), str) or not qualification[key].strip():
            raise ValueError(f'Site qualification requires {key}')
    for field in ('compilation_unit', 'language_standard'):
        declaration = cfg.get(field, 'unspecified')
        if declaration == 'unspecified' or qualification.get(field) != declaration:
            raise ValueError(f'Strict admission requires qualified matching {field} semantics')
    adapter_hashes = hashes([paths['tcl'], *dependencies])
    declared_hashes = qualification.get('adapter_hashes')
    if not isinstance(declared_hashes, dict):
        raise ValueError('Site qualification requires adapter_hashes')
    declared_hashes = {resolve(path, Path(paths['qualification']).parent): value
                       for path, value in declared_hashes.items()}
    if adapter_hashes != declared_hashes:
        raise ValueError('Admission adapter/dependencies differ from qualified hashes')
    controls = qualification.get('controls')
    if not isinstance(controls, dict) or set(controls) != set(ADMISSION_CONTROLS):
        raise ValueError('Site qualification lacks required positive/negative admission controls')
    evidence_inputs = []
    for control, record in controls.items():
        expected = 'PASS' if control in ADMISSION_POSITIVE_CONTROLS else 'REJECT'
        if not isinstance(record, dict) or record.get('observed') != expected:
            raise ValueError(f'Admission control {control} must demonstrate {expected}')
        filename = resolve(record.get('evidence', ''), Path(paths['qualification']).parent)
        if hashes([filename])[filename] != record.get('sha256'):
            raise ValueError(f'Admission control evidence hash differs: {control}')
        evidence_inputs.append(filename)
    diagnostics = qualification.get('diagnostics')
    if not isinstance(diagnostics, list):
        raise ValueError('Reviewed site diagnostics policy is required')
    ids = set()
    for diagnostic in diagnostics:
        if (not isinstance(diagnostic, dict) or
                set(diagnostic) != {'id', 'pattern', 'category', 'disposition', 'reason'} or
                any(not isinstance(diagnostic.get(k), str) or not diagnostic[k].strip() for k in diagnostic) or
                diagnostic['id'] in ids or diagnostic['disposition'] not in ('fatal', 'review', 'benign') or
                diagnostic['category'] not in (*ADMISSION_CHECKS, 'memory_macro', 'other') or
                (diagnostic['category'] != 'other' and diagnostic['disposition'] != 'fatal')):
            raise ValueError('Invalid reviewed diagnostic policy entry')
        re.compile(diagnostic['pattern'])
        ids.add(diagnostic['id'])
    review_ids = {d['id'] for d in diagnostics if d['disposition'] == 'review'}
    if any(w['diagnostic_id'] not in review_ids for w in waivers):
        raise ValueError('Waivers may name only review diagnostics; structural/fatal checks cannot be waived')
    result['adapter'] = {**paths, 'inputs': dependencies, 'qualification': qualification,
                         'qualification_path': paths['qualification']}
    return result, [paths['tcl'], paths['qualification'], *dependencies, *evidence_inputs]


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
    cfg = read_json_object(path)
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
                'unresolved.rpt', 'constraint_audit.rpt', 'units.rpt', 'check_timing.rpt', 'hold.rpt',
                'gates.rpt', 'admission_pre_synth.rpt', 'admission_post_synth.rpt',
                'admission_pre_synth_native.rpt', 'admission_post_synth_native.rpt'}
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
    compilation_unit = cfg.get('compilation_unit', 'unspecified')
    if not isinstance(compilation_unit, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', compilation_unit):
        raise ValueError('compilation_unit must be an explicit site-qualified semantics identifier')
    language_standard = cfg.get('language_standard', 'unspecified')
    if not isinstance(language_standard, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', language_standard):
        raise ValueError('language_standard must be an explicit site-qualified dialect identifier')
    admission, admission_inputs = load_admission(cfg, spec, root, selected)
    inputs += admission_inputs
    return {'tool': selected, 'root': str(root), 'top': cfg['top'], 'period_ns': period,
            'time_unit': unit, 'scope': cfg.get('scope', 'unspecified'),
            'memory_model': cfg['memory_model'], 'files': sources, 'include_dirs': includes,
            'compilation_unit': compilation_unit,
            'language_standard': language_standard,
            'defines': defines, 'parameters': parameters, 'libraries': libraries,
            'link_libraries': extras, 'sdc': sdc, 'setup': setup, 'data_files': data,
            'effort': effort, 'compile': compile_mode, 'executable': executable,
            'output_root': resolve(cfg.get('output_root', 'runs/asic'), root),
            'timeout_seconds': timeout, 'input_hashes': hashes(inputs),
            'area_unit': spec.get('area_unit', 'library_unit'),
            'tool_version_declared': spec.get('version', 'unspecified'),
            'power_activity': spec.get('power_activity', 'unspecified'),
            'library_corner_declared': spec.get('corner', 'unspecified'),
            'site_environment': {name: os.environ.get(name) for name in SITE_ENVIRONMENT},
            'admission': admission}


def admission_setup_tcl(plan):
    admission = plan.get('admission')
    if not admission or not admission.get('adapter'):
        return []
    return ['set PQC_ADMISSION_POLICY ' + word(ADMISSION_POLICY),
            'set PQC_ADMISSION_COMPILATION_UNIT ' + word(plan['compilation_unit']),
            'set PQC_ADMISSION_LANGUAGE_STANDARD ' + word(plan['language_standard']),
            'set PQC_ADMISSION_QUALIFICATION ' + word(admission['adapter']['qualification_path']),
            'set PQC_ADMISSION_WAIVERS_JSON ' + word(json.dumps(admission['waivers'])),
            'source ' + word(admission['adapter']['tcl']),
            'if {[llength [info commands pqc_admission_snapshot]] != 1} '
            '{error "Missing site admission snapshot procedure"}']


def admission_tcl(plan, phase):
    """Our own interchange protocol, NOT a claimed DC/Genus report dialect.

    The qualified site proc pqc_admission_snapshot(phase, native_report_path)
    must query the installed tool and return a dictionary with tool_version,
    checks (all ADMISSION_CHECKS counts), and memory (all MEMORY_FIELDS counts).
    It must retain the underlying full-hierarchy vendor evidence in native_report.
    The adapter is responsible for memory-bit ownership/complete classification
    and for applying reviewed exact diagnostic waivers supplied in the Tcl globals.
    Generic Tcl checks counts before mapping, rather than discovering faults only
    after an expensive run. Python independently validates both output snapshots.
    """
    admission = plan.get('admission')
    if not admission or not admission.get('adapter'):
        return []
    lines = []
    native = f'admission_{phase}_native.rpt'
    lines += [f'set admission [pqc_admission_snapshot {phase} {native}]',
              'if {[dict get $admission tool_version] ne ' + word(plan['tool_version_declared']) +
              '} {error "Admission runtime tool version differs from qualified version"}',
              f'if {{![file isfile {native}] || [file size {native}] == 0}} {{error "Missing native admission evidence"}}',
              f'set admission_file [open admission_{phase}.rpt w]',
              'puts $admission_file "PQC_ADMISSION_SCHEMA 1"',
              f'puts $admission_file "PHASE {phase}"',
              'puts $admission_file ' + word('TOOL ' + plan['tool']),
              'puts $admission_file ' + word('VERSION ' + plan['tool_version_declared']),
              'puts $admission_file ' + word('TOP ' + plan['top'])]
    for section, fields in (('checks', ADMISSION_CHECKS), ('memory', MEMORY_FIELDS)):
        for field in fields:
            lines += [f'set value [dict get $admission {section} {field}]',
                      'if {![string is integer -strict $value] || $value < 0} {error "Malformed admission count"}',
                      f'puts $admission_file "{field} $value"']
            if section == 'checks' or field in ('memory_macro_cells', 'memory_blackboxes'):
                lines.append(f'if {{$value != 0}} {{error "Admission rejected: {field}"}}')
            elif field == 'memory_inventory_complete':
                lines.append('if {$value != 1} {error "Memory inventory is not complete"}')
    if phase == 'post_synth':
        lines += ['if {[dict get $admission memory unmapped_memory_bits] != 0 || '
                  '[dict get $admission memory mapped_memory_bits] != '
                  '[dict get $admission memory flip_flop_memory_bits]} '
                  '{error "RTL memory flip-flop implementation is not proved"}']
    lines.append('close $admission_file')
    return lines


def render_tcl(plan):
    tool = plan['tool']
    lines = ['# Fixed-period LOGICAL synthesis, not place-and-route.',
             '# Qualify against the installed EDA release and library before publishing PPA.',
             'if {[catch {', f"set PQC_PERIOD_NS {plan['period_ns']}",
             f"set PERIOD_PS {plan['period_ns'] * 1000:.12g}",
             f"set PQC_PERIOD {plan['period_ns'] / TIME_NS[plan['time_unit']]:.12g}"]
    if plan.get('admission') and not plan['admission'].get('adapter'):
        lines.append('error "Strict ASIC admission requires a reviewed, version-qualified site adapter"')
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
    # Load the site policy before any HDL, so it can configure diagnostic
    # collection and the qualified language/compilation-unit behavior.
    lines += admission_setup_tcl(plan)
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
    lines += admission_tcl(plan, 'pre_synth')
    lines += ['source ' + word(plan['sdc'])]
    if tool == 'genus':
        lines += ['if {[llength [get_db clocks]] != 1} {error "Expected exactly one clock after SDC"}',
                  'set actual_period [lindex [get_db clocks .period] 0]']
        lines += clock_audit_tcl()
        for phase in ('generic', 'map', 'opt'):
            lines += [f"set_db syn_{phase}_effort {plan['effort'][phase]}"]
        lines += ['syn_generic', 'syn_map', 'syn_opt']
        lines += admission_tcl(plan, 'post_synth')
        lines += ['report timing -nworst 20 > timing.rpt',
                  'report area > area.rpt', 'report gates > gates.rpt', 'report power > power.rpt',
                  'write_hdl > netlist.v', 'write_sdc > constraints.sdc', 'write_db design.db']
    else:
        lines += ['if {[sizeof_collection [all_clocks]] != 1} {error "Expected exactly one clock after SDC"}',
                  'set actual_period [get_attribute [all_clocks] period]']
        lines += clock_audit_tcl()
        lines += ['compile_ultra -no_autoungroup' if plan['compile'] == 'compile_ultra' else 'compile']
        lines += admission_tcl(plan, 'post_synth')
        lines += ['redirect timing.rpt {report_timing -delay_type max -max_paths 20 -nosplit}',
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


def validate_tool_log(text, admission=None):
    if re.search(r'^\s*(?:Error|Fatal)\s*(?::|\[)', text, re.M | re.I):
        raise RuntimeError('Tool log contains an error despite zero exit status')
    if re.search(r'\[(?:CDFG-428|TUI-273)\]|\bblackbox was created\b|Unable to resolve reference', text, re.I):
        raise RuntimeError('Tool log reports an unresolved or blackboxed design')
    # Narrow positive diagnostics only. Informational zero-count summaries and
    # ordinary benign warnings must not become a generic "any warning fails" gate.
    for line in text.splitlines():
        if re.match(r'^\s*Warning\s*(?::|\[)', line, re.I) and re.search(
                r'\b(?:port width mismatch|width mismatch on port|multiple drivers|'
                r'multiply[- ]driven|inferred latch|latch inferred)\b', line, re.I):
            raise RuntimeError('Tool log contains a fatal RTL structural diagnostic: ' + line.strip())
    if not admission or not admission.get('adapter'):
        return {'policy': 'legacy-known-errors-only', 'waived': []}
    waivers = {(w['diagnostic_id'], w['line_sha256']): w for w in admission['waivers']}
    waived = []
    for diagnostic in admission['adapter']['qualification']['diagnostics']:
        for line in text.splitlines():
            if not re.search(diagnostic['pattern'], line):
                continue
            digest = hashlib.sha256(line.encode()).hexdigest()
            if diagnostic['disposition'] == 'fatal':
                raise RuntimeError('Fatal site diagnostic: ' + diagnostic['id'] + ': ' + line)
            if diagnostic['disposition'] == 'review':
                waiver = waivers.get((diagnostic['id'], digest))
                if waiver is None:
                    raise RuntimeError('Unwaived site diagnostic: ' + diagnostic['id'] + ': ' + line)
                waived.append(waiver)
    return {'policy': ADMISSION_POLICY, 'waived': waived}


def validate_admission_report(text, plan, phase):
    """Validate our strict site-adapter interchange, not a vendor report dialect.

    A reviewed, hash-pinned per-release site adapter extracts and preserves the
    native evidence. Missing/unknown/duplicate fields are fatal. memory_model
    alone cannot satisfy complete inventory and mapped FF-bit accounting.
    """
    fields = {}
    for line in text.splitlines():
        key, separator, value = line.partition(' ')
        if not separator or not value or key in fields:
            raise ValueError('Malformed or duplicate strict admission evidence field')
        fields[key] = value
    headers = {'PQC_ADMISSION_SCHEMA': '1', 'PHASE': phase, 'TOOL': plan['tool'],
               'VERSION': plan['tool_version_declared'], 'TOP': plan['top']}
    if set(fields) != set(headers) | set(ADMISSION_CHECKS) | set(MEMORY_FIELDS):
        raise ValueError('Missing or unknown strict admission evidence fields')
    if any(fields[key] != value for key, value in headers.items()):
        raise ValueError('Strict admission evidence tool/version/top/phase mismatch')
    counts = {}
    for key in (*ADMISSION_CHECKS, *MEMORY_FIELDS):
        if not re.fullmatch(r'0|[1-9]\d*', fields[key]):
            raise ValueError('Invalid strict admission count: ' + key)
        counts[key] = int(fields[key])
    for key in ADMISSION_CHECKS:
        if counts[key] != 0:
            raise ValueError('Strict RTL admission rejected: ' + key)
    if (counts['memory_inventory_complete'] != 1 or counts['memory_macro_cells'] != 0 or
            counts['memory_blackboxes'] != 0):
        raise ValueError('Complete macro-free RTL memory inventory is not proved')
    if phase == 'post_synth' and (counts['unmapped_memory_bits'] != 0 or
            counts['mapped_memory_bits'] != counts['flip_flop_memory_bits']):
        raise ValueError('RTL memory flip-flop implementation is not proved')
    return {'phase': phase, 'checks': {key: counts[key] for key in ADMISSION_CHECKS},
            'memory': {key: counts[key] for key in MEMORY_FIELDS}}


def run(plan, dry_run=False):
    script = render_tcl(plan)
    admission = plan.get('admission')
    if dry_run:
        return {'status': 'DRY_RUN', 'tool': plan['tool'], 'stage': 'post_synth',
                'top': plan['top'], 'period_ns': plan['period_ns'], 'tcl': script,
                'admission_policy': admission['policy'] if admission else None,
                'admission_qualification': ('site_adapter_configured_not_executed' if admission and
                     admission['adapter'] else 'site_qualification_required' if admission else 'not_requested'),
                'admission_passed': False, 'structural_checks_verified': False,
                'memory_implementation_verified': False, 'memory_implementation': None}
    if admission and not admission.get('adapter'):
        raise ValueError('Strict ASIC admission needs a reviewed, version-qualified site adapter; no tool launched')
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
              'admission_policy': admission['policy'] if admission else None,
              'admission_passed': False, 'structural_checks_verified': False,
              'memory_implementation_verified': False, 'memory_implementation': None,
              'memory_semantics_verified': False,
              'qualification_evidence_origin': 'site_supplied_not_independently_reproduced' if admission else None,
              'generated_tcl_sha256': hashes([directory / 'run.tcl'])[str(directory / 'run.tcl')]}
    started = time.monotonic()
    try:
        completed = run_process(command, cwd=directory, timeout=plan['timeout_seconds'], log_path=directory / 'tool.log')
        result['returncode'] = completed.returncode
        if completed.returncode or not re.search(r'^PQC_SYNTHESIS_DONE\s*$', completed.stdout, re.M):
            raise RuntimeError('Tool failed or completion marker is absent; see tool.log')
        result['diagnostic_audit'] = validate_tool_log(completed.stdout, admission)
        required = ['timing.rpt', 'area.rpt', 'power.rpt', 'netlist.v', 'constraints.sdc',
                    'design.db' if plan['tool'] == 'genus' else 'design.ddc', 'constraint_audit.rpt']
        if plan['tool'] == 'genus':
            required.append('unresolved.rpt')
        else:
            required += ['units.rpt', 'check_timing.rpt', 'hold.rpt']
        if admission:
            required += [f'admission_{phase}{suffix}.rpt' for phase in ('pre_synth', 'post_synth')
                         for suffix in ('', '_native')]
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
        if admission:
            result['admission_evidence'] = {
                phase: validate_admission_report((directory / f'admission_{phase}.rpt').read_text(), plan, phase)
                for phase in ('pre_synth', 'post_synth')}
        if hashes(before) != before:
            raise RuntimeError('Declared input files changed during synthesis')
        result['metrics'] = parse_metrics(plan['tool'], *((directory / name).read_text() for name in
                                          ('timing.rpt', 'area.rpt', 'power.rpt')), plan['time_unit'], plan['top'], plan['area_unit'])
        result['metrics_complete'] = all(result['metrics'].get(k) is not None for k in
                                        ('worst_setup_slack_ns', 'cell_count', 'cell_area_reported', 'power_w'))
        result['report_hashes'] = hashes(directory / name for name in required if name.endswith('.rpt'))
        if admission:
            result.update(admission_passed=True, structural_checks_verified=True,
                          memory_implementation_verified=True, memory_implementation='flops',
                          tool_qualification='site_qualification_record_validated')
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
