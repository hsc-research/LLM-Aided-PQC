#!/usr/bin/env python3
"""HQC joint-design shared-secret consistency check in a private workspace.

Default hqc128; --all checks 128/192/256. This is not an independent NIST
response-vector oracle. Never restore Git HEAD or stage over live candidate RTL.
"""
import argparse
import importlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
from run_safety import hashes, run_process, stage_sources
try:
    from .kat_gate import compare_secrets, copy_inputs, new_run_dir
except ImportError:
    from kat_gate import compare_secrets, copy_inputs, new_run_dir

SIMDIR = Path('test_joint_design/test_joint_design.sim/sim_1/behav/xsim')
KEYGEN_SIM = Path('test_keygen/test_keygen.sim/sim_1/behav/xsim')
ENCAP_SIM = Path('test_encap/test_encap.sim/sim_1/behav/xsim')
TIMEOUT_S = 3600
CYCLES = {}


def stage(work):
    import synthesizer
    synthesis = importlib.reload(synthesizer)
    sources = synthesis.ordered_sources('hqc_joint_opt')
    origin_hashes = hashes(sources)
    target = work / 'build/joint_design'
    manifest = stage_sources(sources, target)
    # Supporting operation trees are copied, not rebuilt over live edits.
    for op in ('keygen', 'encap'):
        source = REPO / 'build' / op
        if not (source / 'tb' / (op + '.tcl')).is_file():
            raise RuntimeError(f'Missing standalone build tree: {source}')
        shutil.copytree(source, work / 'build' / op)
    (target / 'tb').mkdir(parents=True, exist_ok=True)
    for source in (REPO / 'hardware/joint_design/tb').iterdir():
        if source.is_file():
            shutil.copy2(source, target / 'tb')
    for directory in ('hardware/common/fixed_weight', 'hardware/common/memory',
                      'hardware/common/shake256/rtl', 'hardware/common/adders',
                      'hardware/common/barrett_reduction'):
        for source in (REPO / directory).iterdir():
            if source.is_file() and source.suffix != '.v' and not (target / source.name).exists():
                shutil.copy2(source, target / source.name)
    shutil.copy2(REPO / 'hardware/encap/memory_files/seed_align.py', target)
    for name in ('pk_seed.in', 'sk_seed.in'):
        result = run_process([sys.executable, str(target / 'seed_align.py'),
                              'seed_align', '0', '40', name, 'yes'], cwd=work)
        if result.returncode or re.search(r'(?im)^\s*(?:ERROR|FATAL)(?:\s|:)', result.stdout):
            raise RuntimeError('Seed staging failed: ' + result.stdout[-500:])
        shutil.move(str(work / name), str(target / 'tb' / name))
    record = {'sources': origin_hashes, 'staged_basenames': manifest,
              'scope': 'joint decapsulation; standalone keygen/encap provide stimuli'}
    (work / 'joint_kat_sources.json').write_text(json.dumps(record, indent=2))
    return manifest, origin_hashes


def verify_sources(manifest, origin_hashes, work):
    if hashes(origin_hashes) != origin_hashes:
        raise RuntimeError('Live candidate changed during verification')
    for name, expected in manifest.items():
        path = (work / 'build/joint_design' / name).resolve()
        if hashes([path])[str(path)] != expected:
            raise RuntimeError(f'Staged candidate changed: {name}')


def joint_tcl(top, level, extra_files, manifest):
    source_list = ' '.join('{./build/joint_design/' + name + '}' for name in manifest)
    inputs = ' '.join('{' + str(p) + '}' for p in extra_files)
    return f'''create_project test_joint_design ./test_joint_design -part xc7a200tfbg676-1
set_property target_language Verilog [current_project]
add_files -norecurse [list {source_list}]
set_property include_dirs {{./build/joint_design}} [get_filesets sources_1]
set_property include_dirs {{./build/joint_design}} [get_filesets sim_1]
set_property verilog_define {{SHARED=1 SHARED_ENCAP=1}} [get_filesets sources_1]
set_property verilog_define {{SHARED=1 SHARED_ENCAP=1}} [get_filesets sim_1]
add_files -fileset sim_1 -norecurse [glob ./build/joint_design/tb/*.v]
add_files -fileset sim_1 -norecurse [list {inputs}]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1
set_property top {top} [get_filesets sim_1]
set_property generic parameter_set=\\"{level}\\" [get_filesets sim_1]
set_property -name {{xsim.simulate.runtime}} -value {{100000us}} -objects [get_filesets sim_1]
launch_simulation
'''


def run_sim(top, level, inputs, work, manifest):
    script = work / (level + '.tcl')
    script.write_text(joint_tcl(top, level, inputs, manifest))
    shutil.rmtree(work / 'test_joint_design', ignore_errors=True)
    result = run_process([os.environ.get('VIVADO', 'vivado'), '-mode', 'batch', '-nojournal', '-nolog',
                          '-notrace', '-source', str(script)], cwd=work, timeout=TIMEOUT_S,
                          log_path=work / (level + '.log'))
    if result.returncode or re.search(r'(?im)^\s*(?:ERROR|FATAL)(?:\s|:)', result.stdout):
        raise RuntimeError('Joint simulation failed: ' + result.stdout[-800:])
    total = re.findall(r'Total Clock Cycles:\s*(\d+)', result.stdout)
    decode = re.findall(r'Decode Clock Cycles:\s*(\d+)', result.stdout)
    if total:
        CYCLES[f'{top}@{level}'] = {'total': int(total[-1]), 'decode': int(decode[-1]) if decode else None}


def run_standalone(script, work):
    result = run_process([os.environ.get('VIVADO', 'vivado'), '-mode', 'batch', '-nojournal', '-nolog',
                          '-notrace', '-source', script], cwd=work, timeout=TIMEOUT_S,
                          log_path=work / (Path(script).stem + '.log'))
    if result.returncode or re.search(r'(?im)^\s*(?:ERROR|FATAL)(?:\s|:)', result.stdout):
        raise RuntimeError('Standalone simulation failed: ' + result.stdout[-800:])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true')
    args = parser.parse_args(argv)
    levels = ['hqc128', 'hqc192', 'hqc256'] if args.all else ['hqc128']
    CYCLES.clear()
    started = time.monotonic()
    work = new_run_dir('hqc-joint-', REPO)
    print(f'Run artifacts: {work}')
    try:
        manifest, original = stage(work)
        run_standalone('./build/keygen/tb/keygen.tcl', work)
        copy_inputs(work / KEYGEN_SIM, work / 'build/encap/tb', ('s', 'h', 'x', 'y'))
        for level in levels:
            suffix = level[3:]
            for kind in ('s', 'h', 'x', 'y'):
                name = f'{kind}_{suffix}.in'
                shutil.copy2(work / KEYGEN_SIM / name, work / 'build/encap/tb')
                shutil.copy2(work / KEYGEN_SIM / name, work / name)
        run_standalone('./build/encap/tb/encap.tcl', work)
        copy_inputs(work / ENCAP_SIM, work, ('u', 'v', 'd', 's'))
        for level in levels:
            suffix = level[3:]
            for name in ([f'{kind}_{suffix}.in' for kind in ('u', 'v', 'd', 's')]
                         + [f'ss_output_{suffix}.out']):
                shutil.copy2(work / ENCAP_SIM / name, work / name)
        for level in levels:
            verify_sources(manifest, original, work)
            suffix = level[3:]
            inputs = list((work / 'build/joint_design').glob('*.mem'))
            inputs += [work / 'build/joint_design/tb' / name for name in ('pk_seed.in', 'sk_seed.in')]
            inputs += [work / f'{kind}_{suffix}.in' for kind in ('s', 'h', 'x', 'y', 'u', 'v', 'd')]
            run_sim('hqc_joint_design_decap_tb', level, inputs, work, manifest)
            produced = work / SIMDIR / f'test_ss_output_{suffix}.out'
            expected = work / f'ss_output_{suffix}.out'
            if compare_secrets(expected, produced) != 'MATCH':
                raise RuntimeError(f'{level}: missing or mismatched shared secret')
            shutil.copy2(produced, work / f'test_ss_output_{suffix}.out')
            print(f'[{level}] SS MATCH')
        verify_sources(manifest, original, work)
        (work / 'joint_kat_cycles.json').write_text(json.dumps(CYCLES, indent=2))
        print(f'JOINT KAT GATE: PASS ({time.monotonic()-started:.0f}s)')
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print('JOINT KAT GATE: FAIL -', error)
        return 1


if __name__ == '__main__':
    sys.exit(main())
