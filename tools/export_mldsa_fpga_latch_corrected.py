#!/usr/bin/env python3
"""Export an explicit FPGA derivative with complete gen_c selector defaults.

Original guarded-baseline/corrected-candidate sources and profiles are unchanged.
Only unsupported sec_lvl selector behavior changes; supported levels are 2/3/5.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.export_mldsa_verified import export as export_reference, validate_report

VARIANTS = {
    'fpga-latch-corrected-baseline': 'guarded-baseline',
    'fpga-latch-corrected-candidate': 'corrected-candidate',
}
REPORT_ROOT = 'docs/verification/mldsa-fpga-latch-correction-2026-10-13'
OLD = '''        default: begin
            W1_LEN = 0;
            TAU    = 0;
            ctilde_out_len = 0;'''
NEW = OLD + '''
            C_SIPO_START = 0;
            ch = 0;'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def correct_selector(text):
    if text.count(OLD) != 1 or 'C_SIPO_START = 0;' in text:
        raise ValueError('gen_c selector anchor changed or correction already applied')
    return text.replace(OLD, NEW)


def stage(out, variant):
    """Create bytes for verification, without claiming the new bytes are tested."""
    reference = VARIANTS[variant]
    out = Path(out).resolve()
    export_reference(out, reference, 'verilog')
    manifest = json.loads((out / 'manifest.json').read_text())
    prior = sha(out / 'manifest.json')
    path = out / 'rtl/gen_c.v'
    before = sha(path)
    path.write_text(correct_selector(path.read_text()))
    for row in manifest['sources']:
        if row['path'] == 'rtl/gen_c.v':
            row['sha256'] = sha(path)
    manifest.update(variant=variant, source_variant=reference,
        reference_manifest_sha256=prior,
        reference_qualification_report=manifest.pop('qualification_report'),
        reference_qualification_report_sha256=manifest.pop('qualification_report_sha256'),
        tested_cases=0,
        source_relationship='FPGA derivative: only two zero defaults added to unsupported gen_c sec_lvl branch.',
        correction={'file':'rtl/gen_c.v','before_sha256':before,'after_sha256':sha(path),
                    'supported_levels':[2,3,5],
                    'unsupported_levels':'Zero selector outputs for unsupported binary and X/Z selectors; unsupported cryptographic operations remain unsupported.'})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (out/'README.txt').write_text('Explicit FPGA latch-corrected ML-DSA derivative.\n'
        'Only gen_c unsupported sec_lvl defaults changed. Original FPGA RAM initialization remains.\n'
        'Vivado target synthesis, timing and implementation must be rerun on these exact bytes.\n')
    return manifest


def validate_evidence(report, root, variant, hashes, data_hash):
    from agent.mldsa.portable_kat_gate import evaluate_log
    if (report.get('status') != 'PASS' or report.get('variant') != variant
            or report.get('source_hashes') != hashes
            or report.get('data_sha256') != data_hash
            or report.get('full_210_case_coverage') is not True
            or report.get('supported_selector_differential') != 'PASS'):
        raise ValueError('missing or mismatched complete derivative qualification report')
    inventory = report.get('evidence_files_sha256', {})
    mandatory = {'raw-kat-result.json'} | {
        'selector/' + name for name in ('result.json','reference.v','corrected.v','tb.v',
            'compile.log','simulate.log','reference-yosys.log','corrected-yosys.log',
            'reference.json','corrected.json')}
    for case in ('keygen','sign','verify','verify_mutations','verify_canonical'):
        op = 'verify' if case.startswith('verify') else case
        mandatory.update({case+'/compile.log', case+'/simulate-seed-0.log',
                          case+'/ref_combined/src_tb/tb_'+op+'_top.v'})
    if not mandatory.issubset(inventory):
        raise ValueError('incomplete mandatory derivative evidence inventory')
    if any(Path(p).is_absolute() or '..' in Path(p).parts for p in inventory):
        raise ValueError('evidence paths must remain inside the report directory')
    if any(sha(Path(root)/p) != h for p,h in inventory.items()):
        raise ValueError('derivative evidence inventory is missing or changed')
    coverage = {}
    for case,count in {'keygen':25,'sign':15,'verify':15,'verify_mutations':4,'verify_canonical':11}.items():
        log = case + '/simulate-seed-0.log'
        if log not in inventory:
            raise ValueError('missing KAT log')
        operation = 'verify' if case.startswith('verify') else case
        row = evaluate_log((Path(root)/log).read_text(), operation, count, 0)
        recorded = report['coverage'][case+':seed-0']
        for field in ('status','expected','completed','vectors','simulator_returncode'):
            if row[field] != recorded[field]:
                raise ValueError('KAT result disagrees with retained log')
        for field in ('known_valid','known_invalid'):
            if field in recorded: row[field] = recorded[field]
        coverage[case] = row
    reference_variant = VARIANTS[variant]
    reference_name = {'guarded-baseline':'pinned-baseline+canonical-hints',
                      'corrected-candidate':'candidate+encoder-fallthrough+canonical-hints'}[reference_variant]
    validate_report({'status':'PASS','variant':reference_name,'coverage':coverage}, reference_variant)
    selector = json.loads((Path(root)/'selector/result.json').read_text())
    if (selector.get('status') != 'PASS' or selector.get('corrected_generic_latch_bits') != 0
            or selector.get('source_hashes',{}).get('corrected') != hashes.get('rtl/gen_c.v')
            or selector.get('supported_basis_cases') != 1542):
        raise ValueError('selector evidence does not match corrected source')


def export(out, variant):
    manifest = stage(out, variant)
    report_path = ROOT / REPORT_ROOT / variant / 'result.json'
    report = json.loads(report_path.read_text())
    hashes = {row['path']:row['sha256'] for row in manifest['sources']}
    validate_evidence(report, report_path.parent, variant, hashes, sha(Path(out)/'zetas.txt'))
    manifest.update(qualification_report=str(report_path.relative_to(ROOT)),
        qualification_report_sha256=sha(report_path), tested_cases=210)
    (Path(out)/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',required=True)
    p.add_argument('--variant',choices=tuple(VARIANTS),required=True)
    a=p.parse_args()
    print(json.dumps(export(a.out,a.variant),indent=2))
