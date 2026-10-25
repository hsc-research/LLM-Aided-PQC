"""Full finite-vector gate for the exact exported FPGA Verilog source closure.

No RTL regeneration, guard insertion or encoder replacement is performed here.
This is a 2-state finite RTL check, not formal equivalence or mapped-memory proof.
"""
from __future__ import annotations
import argparse
import json
import os
import re
from pathlib import Path
import shutil

from agent.mldsa.portable_kat_gate import prepare_testbench, evaluate_log, stage_verify_mutations, stage_canonical_cases
from agent.mldsa_sources import BUNDLED_ROOT, verify_snapshot
from agent.run_safety import hashes, run_process
from agent.whole_design import require, save
from agent.whole_design_adapters import read_request, verify_inputs, require_immutable

CASES = {'keygen': 25, 'sign': 15, 'verify': 15, 'verify_mutations': 4, 'verify_canonical': 11}


def coverage_contract():
    return {'required_checks': list(CASES),
            'operations': [f'{case}_{level}_{i}' for case, count in CASES.items()
                           for level in ('II', 'III', 'V') for i in range(count)],
            'covered_operations': ['keygen', 'sign', 'verify'],
            'required_negative_controls': ['verify_mutations', 'verify_canonical']}


def dependencies():
    return sorted([str(p.resolve()) for folder in ('KAT', 'common', 'ref_combined/src_tb')
                   for p in (BUNDLED_ROOT / folder).iterdir() if p.is_file()] +
                  [str(Path(__file__).resolve()), str(Path(__file__).with_name('portable_kat_gate.py').resolve())] +
                  [str(Path(__file__).resolve().parents[1] / name) for name in
                   ('mldsa_sources.py', 'run_safety.py', 'whole_design.py', 'whole_design_adapters.py',
                    'target_profiles.py', 'edit_ops.py', 'llm_client.py')])


def validate_simulator_version(version):
    # Reproduced EPEL 5.022-3 compiles with unrolling but produces wrong KAT
    # bytes. Reject the known failing release, not an untested version range.
    require(re.search(r"\bVerilator\s+5\.022\b", version) is None,
            'Verilator 5.022 is incompatible with this exported ML-DSA gate: '
            'KeyGen byte comparisons fail despite successful compilation. '
            'Use a separately qualified newer simulator and rerun the full '
            '210-case baseline in a fresh output directory before paid proposals.')


def verify(request_path, response_path, jobs=2, timeout=1800):
    request, response = read_request(request_path, response_path, 'verify')
    cfg = request['configuration']; profile = cfg.get('target_profile', {})
    require(cfg['target'] == 'fpga' and profile.get('design') == 'mldsa' and cfg['top'] == 'combined_top',
            'Only the exported ML-DSA FPGA combined_top is supported')
    elab = profile['elaboration']
    require(elab['parameters'] == {} and elab['defines'] == [] and elab['global_include_files'] == [],
            'Nondefault source controls need separate verifier qualification')
    require(all(row['language'] == 'verilog' for row in elab['sources']), 'Verilog export required')
    require([row['path'] for row in elab['sources']] == cfg['source_read_order'] and set(cfg['source_read_order']) == set(request['source_hashes']),
            'Exact source read order is required')
    contract = coverage_contract()
    require(cfg['required_checks'] == contract['required_checks'] and cfg['operations'] == contract['operations'],
            'Full 210-case coverage/latency contract required; run --describe')
    require(set(contract['required_negative_controls']) <= set(cfg['required_negative_controls']),
            'Negative controls must be mandatory')
    require(type(jobs) is int and 1 <= jobs <= 32 and 0 < timeout <= 86400, 'Invalid bounded run limits')
    verify_snapshot()
    for path in dependencies(): require_immutable(path, request)
    require(shutil.which('verilator') is not None, 'Verilator required; no implicit installation')
    directory = Path(response_path).resolve().parent
    work = directory / 'kat-work'
    require(not work.exists(), 'Use a fresh verification directory')
    work.mkdir()
    version = run_process(['verilator', '--version'], timeout=30, log_path=work/'version.log')
    require(version.returncode == 0, 'Cannot establish Verilator version')
    validate_simulator_version(version.stdout.strip())
    report = {'status': 'RUNNING', 'scope': 'finite_210_case_rtl_only', 'simulator': version.stdout.strip(),
              'two_state_simulation': True, 'mapped_memory_verified': False,
              'source_hashes': request['source_hashes'], 'coverage': {}, 'commands': []}
    source_files = cfg['source_read_order']
    require(len(elab['data_files']) == 1 and Path(elab['data_files'][0]).name == 'zetas.txt', 'Expected one bound zetas ROM input')
    result_file = directory / 'functional.json'
    save(result_file, report)
    try:
        for case, count in CASES.items():
            operation = 'verify' if case.startswith('verify') else case
            base = work / case
            tbdir = base / 'ref_combined/src_tb'; tbdir.mkdir(parents=True)
            shutil.copytree(BUNDLED_ROOT/'common', base/'common')
            if case == 'verify_mutations': stage_verify_mutations(BUNDLED_ROOT/'KAT', tbdir)
            elif case == 'verify_canonical': stage_canonical_cases(BUNDLED_ROOT/'KAT', tbdir)
            else:
                for source in (BUNDLED_ROOT/'KAT').iterdir():
                    if source.is_file(): shutil.copy2(source, tbdir/source.name)
            shutil.copy2(elab['data_files'][0], tbdir/'zetas.txt')
            tb = tbdir / f'tb_{operation}_top.v'
            tb.write_text(prepare_testbench((BUNDLED_ROOT/'ref_combined/src_tb'/tb.name).read_text(), operation, count, 20000000))
            before = hashes([*tbdir.iterdir(), *(base/'common').iterdir()])
            obj = base/'obj'; top = tb.stem
            command = ['verilator', '--binary', '--timing', '--top-module', top, '--Mdir', str(obj),
                       '-j', str(jobs), '-Wno-fatal', '--unroll-count', '512', *['-I'+p for p in elab['include_dirs']], *source_files, str(tb)]
            report['commands'].append({'case': case, 'compile': command, 'cwd': str(tbdir)})
            env = os.environ.copy(); env['MAKEFLAGS'] = 'CFG_CXXFLAGS_PCH_I=-include'
            compiled = run_process(command, cwd=tbdir, timeout=timeout, env=env, log_path=base/'compile.log')
            require(compiled.returncode == 0, f'{case} compilation failed; inspect compile.log')
            executable = obj/('V'+top); executable_hash = hashes([executable])
            run = run_process([str(executable)], cwd=tbdir, timeout=timeout, log_path=base/'simulation.log')
            require(hashes(before) == before and hashes(executable_hash) == executable_hash, 'Simulation inputs changed')
            row = evaluate_log(run.stdout, operation, count, run.returncode)
            if operation == 'verify':
                values = [(tbdir/f'SigVer_result_{level}.txt').read_text().split()[:count] for level in ('44','65','87')]
                row.update(known_valid=sum(v.count('0') for v in values), known_invalid=sum(v.count('1') for v in values))
                require((row['known_valid'], row['known_invalid']) == {'verify': (9,36), 'verify_mutations': (0,12), 'verify_canonical': (18,15)}[case], 'Verify polarity fixture changed')
            row['simulation_input_hashes'] = before
            row['executable_sha256'] = executable_hash
            report['coverage'][case] = row; save(result_file, report)
            require(row['status'] == 'PASS', f'{case} failed: {row.get("reason")}')
            verify_inputs(request)
        report['status'] = 'PASS'
    except Exception:
        report['status'] = 'FAIL'; save(result_file, report)
        raise
    save(result_file, report)
    response.update(status='PASS', scope='full_design', coverage_scope='full_selected_design',
                    covered_operations=contract['covered_operations'], checks={c:'PASS' for c in CASES},
                    latency_cycles={f'{case}_{v["level"]}_{v["kat"]}':v['cycles'] for case, row in report['coverage'].items() for v in row['vectors']},
                    source_hashes=request['source_hashes'], source_read_order=cfg['source_read_order'],
                    configuration=cfg, target_profile_fingerprint=profile['profile_fingerprint'],
                    reports={'functional': {'path':'functional.json', 'sha256':hashes([result_file])[str(result_file)]}})
    verify_inputs(request); save(response_path, response)
    return response


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--describe',action='store_true');p.add_argument('--request');p.add_argument('--response');p.add_argument('--jobs',type=int,default=2);p.add_argument('--timeout',type=float,default=1800)
    a=p.parse_args()
    if a.describe: print(json.dumps({**coverage_contract(),'immutable_inputs':dependencies(),'qualification':'ADAPTER_NOT_SITE_QUALIFIED'},indent=2));return
    if not a.request or not a.response:p.error('--request and --response required')
    verify(a.request,a.response,a.jobs,a.timeout)

if __name__=='__main__':main()
