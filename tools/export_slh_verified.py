#!/usr/bin/env python3
"""Export exact qualified SLH sources and metadata without running any EDA tool."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

import check_slh_portable as portable

ROOT = portable.ROOT
VARIANTS = {
    'corrected-baseline': ROOT / 'agent/slh_dsa/pristine',
    'corrected-candidate': ROOT / 'agent/slh_dsa/slh_src',
}
RECORDS = {
    ('corrected-baseline', '128f'): 'slh-portable-corrected-128f-2026-10-12.json',
    ('corrected-candidate', '128f'): 'slh-portable-corrected-candidate-128f-2026-10-12.json',
    ('corrected-baseline', '192f'): 'slh-portable-corrected-baseline-192f-2026-10-12.json',
    ('corrected-candidate', '192f'): 'slh-portable-corrected-192f-2026-10-12.json',
}
CORE_DIFFERENCES = {'sphincslet/sha/sha256_core.v', 'sphincslet/sha/sha512_core.v'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def source_order(rtl):
    main = sorted(p for p in rtl.rglob('*.v') if p.name not in ('clog2.v', 'setting.v', 'fifo.v')
                  and 'sha' not in p.relative_to(rtl).parts)
    return [rtl / 'imports/global_include/clog2.v', rtl / 'sphincslet/setting.v', *main,
            rtl / 'imports/fifo.v', *sorted((rtl / 'sphincslet/sha').rglob('*.v'))]


def prepare_sources(source, destination, parameter):
    """Use exactly the staging transformations exercised by the functional runner."""
    before = portable.rtl_hashes(source)
    for name in before:
        output = destination / name
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, output)
    if portable.rtl_hashes(destination) != before:
        raise ValueError('source changed while staging export')
    change = portable.select_parameter(destination, parameter)
    changes = ([change] if change else []) + portable.portability_variant(destination)
    changes.append(portable.auth_sensitivity_variant(destination))
    return before, changes


def validate_qualification(report, *, parameter, original_hashes, staged_hashes, inputs):
    """Reject stale, wrong-mode, partial, or non-discriminating qualification."""
    requirements = (
        report.get('status') == 'PASS', report.get('auth_sensitivity_fix') is True,
        report.get('parameter_set') == 'SHA2-' + parameter,
        report.get('evidence_kind') == 'portable_vendor_rtl_differential',
        report.get('independent_fips_205_validation') is False,
        report.get('source_sha256') == original_hashes,
        report.get('staged_source_sha256') == staged_hashes,
        report.get('input_sha256') == inputs,
        report.get('golden_sha256') == portable.gate.REFERENCES[parameter][0],
        report.get('tracked_inputs_unchanged') is True,
        report.get('staged_inputs_unchanged') is True,
        type(report.get('compile_returncode')) is int and report['compile_returncode'] == 0,
    )
    if not all(requirements):
        raise ValueError('qualification does not match the selected source, mode, fixtures and corrected variant')
    cases = report.get('cases', [])
    if len(cases) != 2 or {c.get('case') for c in cases} != {'baseline', 'signature-memory-bitflip'}:
        raise ValueError('qualification is missing the positive or negative control')
    for case in cases:
        expected_flag = '0' if case['case'] == 'baseline' else '1'
        if not (case.get('status') == 'PASS'
                and type(case.get('simulator_returncode')) is int and case['simulator_returncode'] == 0
                and case.get('rtl_verification_flag') == [expected_flag]
                and case.get('full_vendor_dump_matches') is True
                and type(case.get('output_words')) is int
                and case['output_words'] == portable.gate.REFERENCES[parameter][1]
                and case.get('output_sha256') == portable.gate.REFERENCES[parameter][0]):
            raise ValueError('qualification contains incomplete output or failed controls')
        if expected_flag == '1' and not all(case.get(k) is True for k in (
                'negative_control_qualified', 'negative_control_contract_satisfied', 'observed_rejection')):
            raise ValueError('negative-control qualification requires consistent rejection and a passing positive baseline')


def export_sources(variant, parameter, out):
    if variant not in VARIANTS or (variant, parameter) not in RECORDS:
        raise ValueError('export supports corrected baseline/candidate SHA2-128f and SHA2-192f only')
    source = VARIANTS[variant]
    out = Path(out).resolve()
    if any(out == root or out.is_relative_to(root) or root.is_relative_to(out) for root in VARIANTS.values()):
        raise ValueError('export destination overlaps a protected source tree')
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError('export destination must be absent or empty')
    original_parameter = portable.gate.check_configuration(source / 'sphincslet/setting.v')
    inputs_abs = portable.gate.check_harness(source, parameter, source / 'imports')
    inputs = {Path(p).name: digest for p, digest in inputs_abs.items()}
    golden, golden_bytes = portable.gate.load_reference(parameter)
    record_path = ROOT / 'docs/verification' / RECORDS[(variant, parameter)]
    report_bytes = record_path.read_bytes()
    report = json.loads(report_bytes)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.slh-export-', dir=out.parent) as temporary:
        work = Path(temporary) / 'bundle'
        rtl = work / 'rtl'
        original_hashes, changes = prepare_sources(source, rtl, parameter)
        staged_hashes = portable.rtl_hashes(rtl)
        validate_qualification(report, parameter=parameter, original_hashes=original_hashes,
                               staged_hashes=staged_hashes, inputs=inputs)
        (work / 'changes.patch').write_text(''.join(c['diff'] for c in changes))
        evidence = work / 'evidence'
        evidence.mkdir()
        (evidence / 'qualification.json').write_bytes(report_bytes)
        (evidence / 'golden.hex').write_bytes(golden_bytes)
        if record_path.with_suffix('.txt').is_file():
            shutil.copyfile(record_path.with_suffix('.txt'), evidence / 'qualification.log.txt')
        data_root = work / 'simulation/TECS_v8.srcs/sources_1/imports/data_sha2'
        data_root.mkdir(parents=True)
        (work / 'simulation/a/b/c/d').mkdir(parents=True)
        data_files = []
        for source_file, expected in sorted(inputs_abs.items()):
            target = data_root / Path(source_file).name
            shutil.copyfile(source_file, target)
            if sha(target) != expected:
                raise ValueError('fixture changed while exporting')
            data_files.append({'path': str(target.relative_to(work)), 'sha256': expected,
                               'role': 'public deterministic test input; never production keys'})
        for name in ('LICENSE', 'NOTICE'):
            shutil.copyfile(ROOT / name, work / name)
        include_dirs = ['rtl/sphincslet', 'rtl/imports/global_include', 'rtl/sphincslet/fsm']
        ordered = source_order(rtl)
        simulation_sources = [{'path': str(p.relative_to(work)), 'language': 'Verilog-2005', 'sha256': sha(p)} for p in ordered]
        design_sources = [p for p in simulation_sources if not p['path'].endswith('/tb.v')]
        for name, sources in (('sources.f', design_sources), ('simulation_sources.f', simulation_sources)):
            (work / name).write_text(''.join(p['path'] + '\n' for p in sources))
        (work / 'include_dirs.f').write_text(''.join('+incdir+' + p + '\n' for p in include_dirs))
        # Source-only Tcl variables; sourcing this file invokes no synthesis command.
        tcl = '# Run from the bundle root. This file only sets variables; it runs no EDA commands.\n'
        tcl += 'set slh_top {top}\nset slh_include_dirs {' + ' '.join(include_dirs) + '}\n'
        tcl += 'set slh_sources {\n' + ''.join('  {' + p['path'] + '}\n' for p in design_sources) + '}\n'
        (work / 'sources.tcl').write_text(tcl)
        # Compare normalized same-parameter sources, never compare the two different default modes.
        other_variant = 'corrected-candidate' if variant == 'corrected-baseline' else 'corrected-baseline'
        other_rtl = Path(temporary) / 'other-rtl'
        other_original, _ = prepare_sources(VARIANTS[other_variant], other_rtl, parameter)
        other_hashes = portable.rtl_hashes(other_rtl)
        differences = sorted(name for name in set(staged_hashes) | set(other_hashes)
                             if staged_hashes.get(name) != other_hashes.get(name))
        if set(differences) != CORE_DIFFERENCES:
            raise ValueError('same-parameter source relationship changed beyond the reviewed SHA cores')
        partner_path = ROOT / 'docs/verification' / RECORDS[(other_variant, parameter)]
        partner_qualified = False
        partner_report_bytes = None
        if partner_path.is_file():
            partner_report_bytes = partner_path.read_bytes()
            partner = json.loads(partner_report_bytes)
            validate_qualification(partner, parameter=parameter, original_hashes=other_original,
                                   staged_hashes=other_hashes, inputs=inputs)
            partner_qualified = True
            (evidence / 'partner_qualification.json').write_bytes(partner_report_bytes)
        manifest = {
            'schema_version': 1, 'scheme': 'SLH-DSA/SPHINCSLET historical SHA2 vendor differential',
            'variant': variant, 'parameter_set': 'SHA2-' + parameter,
            'top': 'top', 'simulation_top': 'tb', 'parameter_overrides': {}, 'defines': [],
            'configuration_source': 'rtl/sphincslet/setting.v', 'selected_parameter_macro': 'PARAM_' + parameter.upper(),
            'source_selected_defaults': {'parameter_set': parameter, 'IO_WIDTH': 64}, 'include_dirs': include_dirs,
            'sources': design_sources, 'simulation_sources': simulation_sources,
            'original_source_root': str(source.relative_to(ROOT)),
            'original_parameter_set': 'SHA2-' + original_parameter,
            'original_source_sha256': original_hashes, 'qualified_staged_source_sha256': staged_hashes,
            'transformations': [{k: v for k, v in change.items() if k != 'diff'} for change in changes],
            'qualification_report': {'path': 'evidence/qualification.json', 'repository_path': str(record_path.relative_to(ROOT)), 'sha256': sha(record_path)},
            'golden': {'path': 'evidence/golden.hex', 'sha256': sha(golden), 'words': portable.gate.REFERENCES[parameter][1], 'includes_padded_message': True},
            'tested_cases': report['cases'], 'data_files': data_files, 'memory_init_files': [],
            'simulation_working_directory': 'simulation/a/b/c/d',
            'runtime_controls': {'clock': 'clk', 'reset': 'rstn (active low)', 'i_sig_mode': {'0': 'sign', '1': 'verify'}, 'i_FSM_start': 'start request', 'o_FSM_done': 'completion', 'o_c_flag': {'0': 'accepted', '1': 'rejected'}, 'i_msg_in_size': 'message byte count'},
            'memories': [
                {'source': 'rtl/imports/mem_dual.v', 'module': 'mem_dual', 'kind': 'generic inferred synchronous dual-port RAM', 'depth_semantics': 'vendor array [0:DEPTH] contains DEPTH+1 elements; preserved unchanged', 'initialization': 'optional FILE/readmemh or INIT loop; production instances use empty FILE defaults'},
                {'source': 'rtl/imports/mem_single.v', 'module': 'mem_single', 'kind': 'generic inferred synchronous single-port RAM', 'depth_semantics': 'DEPTH elements', 'initialization': 'optional FILE/readmemb or INIT loop'},
                {'source': 'rtl/imports/fifo.v', 'module': 'fifo', 'kind': 'generic RTL FIFO; no technology macro substitution'},
                {'source': 'rtl/sphincslet/tb.v', 'instance': 'SIG_MEM', 'kind': 'testbench-only signature store; excluded from synthesis source list', 'interface': 'top exposes sig_mem_out0 / sig_mem_addr0_w; implementation must supply external signature storage consistently in both arms'},
            ],
            'source_relationship': {'comparison_group': 'corrected-SHA2-' + parameter, 'partner_variant': other_variant, 'partner_qualified': partner_qualified, 'partner_qualification_report': str(partner_path.relative_to(ROOT)), 'partner_qualification_sha256': hashlib.sha256(partner_report_bytes).hexdigest() if partner_report_bytes is not None else None, 'partner_qualification_export_path': 'evidence/partner_qualification.json' if partner_qualified else None, 'only_same_parameter_differences': differences, 'optimization': 'candidate SHA-256/SHA-512 carry-save adder trees; same corrected control logic and configuration'},
            'limits': ['No EDA tool is invoked by this exporter; no new FPGA/ASIC/PPA claim.', 'This bundle is a corrected portable variant, not unchanged vendor RTL.', 'Compare baseline and candidate only at the same parameter set, wrapper, clocks, constraints and memory mapping.', 'Never override parameter_set alone: setting.v also controls widths and SHA core selection.', 'The testbench is excluded from design sources; its #5 clock is not an implementation timing constraint.', 'Generic memory inference and initialization need target-specific review; no ASIC SRAM macros or FPGA constraints are supplied.', 'Historical vendor differential fixture only; not independent FIPS 205/ACVP validation or full-message coverage.', 'Source-specific notices are preserved. Repository LICENSE/NOTICE do not replace component licenses.'],
        }
        (work / 'README.txt').write_text('SLH corrected source handoff\n\n'
            + 'Variant: ' + variant + '; parameter: SHA2-' + parameter + '\n'
            + 'Design top: top; simulation top: tb. Paths are relative to this bundle.\n'
            + 'Same-parameter partner qualified: ' + str(partner_qualified) + '. Never substitute the other parameter set.\n'
            + 'sources.f excludes the testbench; simulation_sources.f includes it. Preserve source ordering and include_dirs.f.\n'
            + 'sources.tcl only defines variables and does not launch synthesis.\n'
            + 'manifest.json binds exact exported RTL, test fixtures and qualification. Verify SHA256SUMS before implementation.\n'
            + 'Do not compare different parameter sets. Do not include the testbench in PPA.\n'
            + 'Supply identical external signature storage, clock/reset handling, constraints and memory mappings in both arms.\n'
            + 'No target-specific timing constraints, memory macros, FPGA/ASIC runs or PPA numbers are supplied.\n')
        manifest['bundle_files_sha256'] = {str(p.relative_to(work)): sha(p) for p in sorted(work.rglob('*')) if p.is_file()}
        write_json(work / 'manifest.json', manifest)
        checksums = {str(p.relative_to(work)): sha(p) for p in sorted(work.rglob('*')) if p.is_file()}
        (work / 'SHA256SUMS').write_text(''.join(h + '  ' + name + '\n' for name, h in checksums.items()))
        if portable.rtl_hashes(source) != original_hashes or portable.rtl_hashes(VARIANTS[other_variant]) != other_original:
            raise ValueError('tracked source changed during export')
        if portable.hashes(inputs_abs) != inputs_abs or record_path.read_bytes() != report_bytes:
            raise ValueError('qualification input changed during export')
        if portable.gate.load_reference(parameter)[1] != golden_bytes:
            raise ValueError('frozen golden changed during export')
        if partner_report_bytes is not None and partner_path.read_bytes() != partner_report_bytes:
            raise ValueError('partner qualification changed during export')
        if out.exists():
            out.rmdir()  # Only an empty destination accepted above can be removed.
        work.rename(out)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=tuple(VARIANTS), required=True)
    parser.add_argument('--parameter-set', choices=('128f', '192f'), required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = export_sources(args.variant, args.parameter_set, args.out)
    except (OSError, ValueError, RuntimeError) as exc:
        print('SLH export ERROR: ' + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({'status': 'EXPORTED', 'variant': args.variant, 'parameter_set': manifest['parameter_set'],
                      'source_count': len(manifest['sources']), 'partner_qualified': manifest['source_relationship']['partner_qualified'],
                      'manifest': str(args.out / 'manifest.json')}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
