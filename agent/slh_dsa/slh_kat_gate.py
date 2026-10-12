#!/usr/bin/env python3
"""SLH-DSA SHA2-128f differential sign/verify gate.

PASS compares against the frozen vendor-RTL signature, not an independent
FIPS 205 oracle. Other parameter sets require their own reviewed gate.
The current candidate is snapshotted; simulation data and logs live under
PQC_RUN_DIR (default repository/.pqc_runs). No vendor shell script or shared
external simulation directory is used. VIVADO_BIN optionally augments PATH.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
from run_safety import hashes, run_process

DEFAULT_RTL = HERE / 'slh_src'
GOLDEN = HERE / 'gate/SIG_file0_128f_w.hex'
TIMEOUT = 3600


def check_configuration(path):
    text = path.read_text()
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
    parameters = re.findall(r'^\s*`define\s+(PARAM_(?:128|192|256)[FS])\b', text, re.M)
    if parameters != ['PARAM_128F'] or re.search(r'^\s*`define\s+SHAKE\b', text, re.M):
        raise ValueError('this frozen-reference gate supports SHA2 PARAM_128F only; '
                         f'candidate selects {parameters or "no known parameter set"}')


def check_signature(golden, produced, output, returncode):
    if returncode != 0:
        return {'status': 'FAIL', 'reason': f'simulator exited with status {returncode}'}
    if re.search(r'(?im)^\s*(?:ERROR|FATAL)(?:\s|:)', output):
        return {'status': 'FAIL', 'reason': 'simulator reported an error'}
    if 'The signature is not matched' in output:
        return {'status': 'FAIL', 'reason': 'testbench reported a signature mismatch'}
    if not produced.is_file():
        return {'status': 'FAIL', 'reason': 'no signature produced'}
    expected, actual = golden.read_bytes(), produced.read_bytes()
    if not expected.strip() or not actual.strip():
        return {'status': 'FAIL', 'reason': 'empty golden or produced signature'}
    if expected != actual:
        return {'status': 'FAIL', 'reason': 'signature differs from golden'}
    if 'The signature is matched' not in output:
        return {'status': 'FAIL', 'reason': 'testbench verify did not report match'}
    return {'status': 'PASS', 'reason': 'signature matches frozen SHA2-128f reference, verify OK'}


def run_equiv(rtl_dir=DEFAULT_RTL, timeout=TIMEOUT):
    base = {}
    stage = 'setup'
    try:
        rtl = Path(rtl_dir).resolve()
        golden = Path(GOLDEN)
        if not rtl.is_dir():
            raise ValueError(f'RTL directory missing: {rtl}')
        check_configuration(rtl / 'sphincslet/setting.v')
        if not golden.is_file() or not golden.read_bytes().strip():
            raise ValueError(f'golden missing or empty: {golden}')
        checksum = golden.with_suffix('.sha256').read_text().split()[0]
        if hashlib.sha256(golden.read_bytes()).hexdigest() != checksum:
            raise ValueError('frozen golden signature checksum mismatch')
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout < float('inf'):
            raise ValueError('timeout must be positive and finite')
        parent = Path(os.environ.get('PQC_RUN_DIR', str(REPO / '.pqc_runs'))).resolve()
        parent.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix='slh-kat-', dir=parent))
        base['run_dir'] = str(work)
        original_hashes = hashes(rtl.rglob('*.v'))
        if not original_hashes:
            raise ValueError('no RTL sources')
        staged = work / 'rtl'
        shutil.copytree(rtl, staged)
        for source, expected in original_hashes.items():
            copy = staged / Path(source).relative_to(rtl)
            if hashes([copy])[str(copy)] != expected:
                raise RuntimeError(f'source changed while staging: {source}')
        (work / 'sources.json').write_text(json.dumps(original_hashes, indent=2))
        # Preserve the testbench's four-level-relative vendor data layout.
        sim = work / 'a/b/c/d'
        sim.mkdir(parents=True)
        data = work / 'TECS_v8.srcs/sources_1/imports/data_sha2'
        data_root = Path(os.environ.get('SLH_DATA_ROOT', str(DEFAULT_RTL / 'imports'))).resolve()
        shutil.copytree(data_root / 'data_sha2', data)
        produced = data / 'SIG_file0_128f_w.hex'
        # Clear only the private copy, never the user's shared simulation data.
        if produced.exists():
            produced.unlink()
        main = [p for p in staged.rglob('*.v')
                if p.name not in ('clog2.v', 'setting.v', 'fifo.v')
                and 'sha' not in p.relative_to(staged).parts]
        last = [staged / 'imports/fifo.v', *sorted((staged / 'sphincslet/sha').rglob('*.v'))]
        command = ['xvlog', '--relax', str(staged / 'imports/global_include/clog2.v'),
                   str(staged / 'sphincslet/setting.v'), *map(str, sorted(main)), *map(str, last),
                   '-i', str(staged / 'sphincslet'), '-i', str(staged / 'imports/global_include'),
                   '-i', str(staged / 'sphincslet/fsm')]
        env = dict(os.environ)
        if env.get('VIVADO_BIN'):
            env['PATH'] = env['VIVADO_BIN'] + os.pathsep + env.get('PATH', '')
        for stage, argv in (('xvlog', command),
                            ('xelab', ['xelab', '--relax', 'tb', '-s', 'tb_sim', '-debug', 'off']),
                            ('xsim', ['xsim', 'tb_sim', '-R'])):
            result = run_process(argv, cwd=sim, env=env, timeout=timeout,
                                 log_path=work / (stage + '.log'))
            if result.returncode or re.search(r'(?im)^\s*(?:ERROR|FATAL)(?:\s|:)', result.stdout):
                return {'status': 'FAIL', 'stage': stage,
                        'reason': f'{stage} failed (exit {result.returncode}): {result.stdout[-800:]}', **base}
        if hashes(original_hashes) != original_hashes:
            raise RuntimeError('selected candidate sources changed during verification')
        return {**check_signature(golden, produced, result.stdout, result.returncode), **base}
    except subprocess.TimeoutExpired:
        return {'status': 'FAIL', 'stage': stage, 'reason': f'{stage} timed out', **base}
    except (OSError, ValueError, RuntimeError, IndexError) as exc:
        return {'status': 'ERROR', 'stage': stage, 'reason': str(exc), **base}


if __name__ == '__main__':
    result = run_equiv(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RTL)
    print(json.dumps(result, indent=2))
    print(f"SLH-DSA GATE: {result['status']} - {result['reason']}")
    raise SystemExit({'PASS': 0, 'FAIL': 1}.get(result['status'], 2))
