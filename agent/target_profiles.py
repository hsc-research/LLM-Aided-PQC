"""Read-only binding of prepared source profiles to whole-design target runs.

A prepared profile is provenance under the reviewed exporter/configuration trust
boundary, not cryptographic proof that arbitrary rewritten RTL was tested, and
not target-tool or full-operation qualification.
Only fresh verification and implementation evidence can admit a candidate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from .run_safety import hashes


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def _path(value, profile_root, design_root, directory=False):
    _require(isinstance(value, str) and value and not Path(value).is_absolute(),
             'Target profile paths must be relative to the profile directory')
    original = profile_root / value
    path = original.resolve()
    _require(path.is_relative_to(profile_root) and path.is_relative_to(design_root),
             'Target profile path escapes its source bundle')
    _require(not any(p.is_symlink() for p in (original, *original.parents)),
             'Symlinked target profile input')
    _require(path.is_dir() if directory else path.is_file(), f'Missing target profile input: {path}')
    return str(path)


def load_profile(filename, root, cfg, sources, immutable):
    """Validate initial baseline bytes and normalize the selected target contract."""
    path = Path(filename)
    value = json.loads(path.read_text())
    _require(isinstance(value, dict) and value.get('schema_version') == 1 and
             value.get('profile_kind') == 'qualified_source_target_preparation',
             'Unsupported target profile schema')
    claimed = value.get('profile_fingerprint')
    _require(claimed == fingerprint({k: v for k, v in value.items() if k != 'profile_fingerprint'}),
             'Target profile fingerprint mismatch')
    _require(value.get('design') in ('mldsa', 'slh', 'slh_dsa', 'slh-dsa', 'mlkem'),
             'Unsupported or unqualified target design (HQC is not executable)')
    target, elaboration = value.get('target', {}), value.get('elaboration', {})
    _require(target.get('kind') == cfg['target'], 'Cross-target source profile is forbidden')
    expected_memory = 'flops' if cfg['target'] == 'asic' else 'fpga_inferred_ram'
    _require(target.get('memory_implementation') == expected_memory and target.get('memory_macros') == []
             and target.get('memory_compiler_allowed') is False,
             'Target profile memory implementation differs from the selected policy')
    _require(elaboration.get('top') == cfg['top'], 'Target profile top mismatch')
    selected, baseline = [], {}
    rows = elaboration.get('sources')
    _require(isinstance(rows, list) and rows, 'Missing target profile ordered sources')
    for row in rows:
        _require(isinstance(row, dict) and row.get('language') in ('verilog', 'systemverilog', 'vhdl'),
                 'Missing target profile source language')
        source = _path(row.get('path'), path.parent, root)
        _require(source not in baseline, 'Duplicate target profile source')
        selected.append({'path': source, 'language': row['language']})
        baseline[source] = row.get('sha256')
    _require(list(baseline) == sources, 'Sources do not exactly match selected target profile read order')
    _require(hashes(sources) == baseline, 'Initial sources differ from selected target profile baseline')
    dependencies = {}
    normalized_files = {}
    for kind in ('include_files', 'data_files'):
        rows = elaboration.get(kind)
        _require(isinstance(rows, list), f'Target profile must declare {kind}')
        normalized_files[kind] = []
        for row in rows:
            _require(isinstance(row, dict), f'Malformed target profile {kind}')
            dependency = _path(row.get('path'), path.parent, root)
            _require(dependency not in dependencies, 'Duplicate target profile dependency')
            dependencies[dependency] = row.get('sha256')
            normalized_files[kind].append(dependency)
    export_manifest = value.get('provenance', {}).get('export_manifest')
    _require(isinstance(export_manifest, dict), 'Missing source export manifest provenance')
    manifest_path = _path(export_manifest.get('path'), path.parent, root)
    dependencies[manifest_path] = export_manifest.get('sha256')
    report = value.get('qualification', {}).get('report')
    _require(isinstance(report, dict), 'Missing source qualification report')
    report_path = _path(report.get('path'), path.parent, root)
    dependencies[report_path] = report.get('sha256')
    _require(hashes(dependencies) == dependencies, 'Target profile dependency bytes differ')
    _require(set(dependencies) <= set(immutable) | set(sources),
             'Freeze every target profile include, data and qualification input')
    _require(str(path) in immutable, 'Target profile must be an immutable input')
    includes = elaboration.get('include_dirs')
    _require(isinstance(includes, list) and len(includes) == len(set(includes)),
             'Declare unique target profile include directories')
    includes = [_path(p, path.parent, root, directory=True) for p in includes]
    defines = elaboration.get('defines')
    _require(isinstance(defines, list) and all(isinstance(d, str) and
             re.fullmatch(r'[A-Za-z_]\w*(?:=[^\r\n]*)?', d) for d in defines) and
             len({d.split('=')[0] for d in defines}) == len(defines),
             'Declare unique target profile defines')
    parameters = elaboration.get('parameters')
    _require(isinstance(parameters, dict) and all(isinstance(k, str) and re.fullmatch(r'[A-Za-z_]\w*', k)
             and type(v) in (str, int, bool) for k, v in parameters.items()), 'Invalid target profile parameters')
    compilation_unit = elaboration.get('compilation_unit')
    _require(isinstance(compilation_unit, str) and compilation_unit, 'Declare target compilation unit semantics')
    language_standard = elaboration.get('language_standard')
    _require(language_standard in ('verilog2005', 'systemverilog2017'),
             'Declare the supported target HDL language standard')
    global_files = elaboration.get('global_include_files')
    _require(isinstance(global_files, list), 'Declare global include files')
    global_files = [_path(p, path.parent, root) for p in global_files]
    _require(set(global_files) <= set(sources) | set(dependencies), 'Unbound global include files')
    working_directory = _path(elaboration.get('working_directory'), path.parent, root, directory=True)
    required = value.get('qualification', {}).get('required_operations')
    _require(isinstance(required, list) and required and all(isinstance(x, str) and x for x in required)
             and len(required) == len(set(required)), 'Missing target full-operation admission requirements')
    minimum_operations = (['mlkem_keygen', 'mlkem_encaps', 'mlkem_decaps',
                           'mldsa_keygen', 'mldsa_sign', 'mldsa_verify']
                          if value['design'] == 'mlkem' else ['keygen', 'sign', 'verify'])
    _require(set(minimum_operations) <= set(required),
             'Target profile omits mandatory full-design operation coverage')
    _require(value.get('qualification', {}).get('source_qualified') is True,
             'Unqualified source profile cannot start optimization')
    result = {'profile_path': str(path), 'profile_fingerprint': claimed,
              'design': value['design'], 'variant': value.get('variant'),
              'parameter_set': value.get('parameter_set'), 'target': target,
              'elaboration': {'top': cfg['top'], 'sources': selected, 'include_dirs': includes,
                              'defines': defines, 'parameters': parameters,
                              'compilation_unit': compilation_unit, 'language_standard': language_standard,
                              'global_include_files': global_files,
                              'working_directory': working_directory, **normalized_files},
              'baseline_source_hashes': baseline, 'required_operations': required,
              'boundary': value.get('boundary')}
    measurement = cfg['measurement']
    if cfg['target'] == 'fpga':
        _require(measurement.get('memory_model') == 'fpga_inferred_ram',
                 'FPGA target profile requires memory_model fpga_inferred_ram')
        part = measurement.get('part')
        _require(isinstance(part, str) and part and 'REPLACE' not in part and part != 'unspecified',
                 'Freeze the exact FPGA part')
    else:
        _require(measurement.get('memory_model') == 'flops', 'ASIC target profile requires flop memories')
        plan = measurement.get('asic_effective_config')
        validate_asic_plan(plan, result)
        _require(plan.get('tool') == cfg['backend'], 'ASIC effective backend differs from target configuration')
        _require(plan.get('period_ns') == measurement['period_ns'], 'ASIC effective period differs from target configuration')
        constraints = [str((root / name).resolve()) for name in measurement['constraints']]
        _require(constraints == [plan.get('sdc')], 'ASIC effective constraints differ from target configuration')
        for dependency in [*plan['libraries'], *plan.get('link_libraries', []), *([plan['setup']] if plan.get('setup') else [])]:
            _require(dependency in immutable, 'ASIC library/setup must be a frozen immutable input')
    declared = set(sources) | set(dependencies)
    for files in include_inventory(result).values():
        _require(set(files) <= declared, 'Undeclared HDL input in target include directory')
    return result


def include_inventory(profile):
    if profile is None:
        return {}
    result = {}
    for name in profile['elaboration']['include_dirs']:
        directory = Path(name)
        _require(directory.is_dir() and not directory.is_symlink(), 'Target include directory changed')
        files = []
        for path in directory.rglob('*'):
            _require(not path.is_symlink(), 'Symlink appeared in target include directory')
            if path.is_file() and path.suffix.lower() in ('.v', '.sv', '.vh', '.svh', '.vhd', '.vhdl'):
                files.append(str(path.resolve()))
        result[name] = sorted(files)
    return result


def validate_asic_plan(plan, profile):
    """An outer target label may not contradict the effective EDA read plan."""
    _require(isinstance(plan, dict), 'Strict target profile needs the effective ASIC plan')
    elaboration = profile['elaboration']
    for field in ('files', 'include_dirs', 'defines', 'data_files'):
        expected = elaboration['sources' if field == 'files' else field]
        _require(plan.get(field) == expected, f'ASIC {field} differ from selected target profile')
    parameters = []
    for name, value in elaboration['parameters'].items():
        if isinstance(value, bool):
            value = int(value)
        if isinstance(value, str):
            value = '"' + value + '"'
        parameters.append(f'{name}={value}')
    _require(plan.get('parameters') == parameters, 'ASIC parameters differ from selected target profile')
    _require(plan.get('language_standard') == elaboration['language_standard'],
             'ASIC language standard differs from selected target profile')
    _require(plan.get('compilation_unit') == elaboration['compilation_unit'],
             'ASIC compilation-unit semantics differ from selected target profile')
    _require(plan.get('top') == elaboration['top'] and plan.get('memory_model') == 'flops',
             'ASIC top/memory differs from target profile')
    _require(isinstance(plan.get('libraries'), list) and plan['libraries'], 'Freeze actual ASIC target libraries')
    _require(plan.get('admission', {}).get('policy') == 'strict-rtl-flops-v1',
             'Target-profile optimization requires strict-rtl-flops-v1 ASIC admission')


def unchanged_directives(before, after):
    """Conservatively freeze complete directives, including continued macro bodies.

    Matching inside comments/strings can reject harmless edits, but never allows
    a compile-time switch to be edited through line placement or continuation.
    """
    directive = re.compile(r'`(?:define|undef|include|ifdef|ifndef|elsif|else|endif|'
                           r'timescale|default_nettype|resetall|celldefine|endcelldefine|'
                           r'unconnected_drive|nounconnected_drive|line|pragma|'
                           r'begin_keywords|end_keywords)\b')
    def collect(text):
        lines = text.splitlines(keepends=True)
        found = []
        for index, line in enumerate(lines):
            match = directive.search(line)
            if match is None:
                continue
            value = line[match.start():]
            while lines[index].rstrip('\r\n').endswith('\\') and index + 1 < len(lines):
                index += 1
                value += lines[index]
            found.append(value)
        return found
    return collect(before) == collect(after)
