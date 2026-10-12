#!/usr/bin/env python3
"""SLH-DSA selected-parameter SHA2 differential sign/verify gate.

PASS compares the entire dump against the frozen vendor-RTL signature for
that parameter set, not an independent FIPS 205 oracle. SHAKE is unsupported.
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
# Immutable reviewed pins, not a candidate-provided checksum sidecar. These
# files predate this gate change; no run generates or replaces a reference.
REFERENCE_COMMIT = '25a9de8fb399644889f9d6f602b302f949a6e86f'
GOLDEN_DIR = HERE / 'gate/levels'
REFERENCES = {
    '128f': ('10f35fcc0cc98680d87cf7aaef1479ba359303a84ba2553d69a8b77771bdf2a8', 2141),
    '128s': ('df0b3ed56604db3ff59f3d657403f78724d2c4c941072636c3c60382b4a016bb', 987),
    '192f': ('22bfbe1c1130b0faf039268adf00504a0ffec308f8ac7a8692593c757371dfe3', 4463),
    '192s': ('82659381c8e552f55e42cea313552b4e6505a41527831d90a5de87c2f9ec54fb', 2033),
    '256f': ('9e9d24ad3abbba973fa11cd92814cb1b345c788a8d76f4612fddc76f8e4086a9', 6237),
    '256s': ('cd388b37b2ecd17d621db43e897ebf402ceed3fb24dcccf2f181436ef0f16e4e', 3729),
}
INPUT_SHA256 = {
    '128_optrand.hex': '3b89ebeb46ef817cd5ce43bd1055221416c16ba62dd7e7eaf172a3e745aac718',
    '192_optrand.hex': '9fc287d099e0593efe7175ff08a924e30f6947fcda7e5565fe9e04337fe45397',
    '256_optrand.hex': 'f28bab6d6560942bd7eaf7552a8dd3e283b34a0d98a554795561de86a9c79738',
    'SLH_128f_PK.hex': '858887e7fb9625ab00e070f8c4d6f1fff7de29731ed0e36a9f8154c4a0074432',
    'SLH_128f_SK.hex': '249fc6a71cfaa9779be56af695a622534dd35f69f20dd6358cb6249ee09042c0',
    'SLH_128s_PK.hex': 'd6f9df912cfa76e94a89eff3fbee94b0ffd882b930614c3f3ccea51ebaed1f63',
    'SLH_128s_SK.hex': 'bb495bd7c5b39a823391ce73ad1264246d900cd7e0e758ff97c45fe4df3116c8',
    'SLH_192f_PK.hex': '417d1d2c0395e8a866142b4f336f7face872d5065ed98746efeca89597c7981a',
    'SLH_192f_SK.hex': '1be370ee5b91bcc590d076f81e3f43dfd7621a7cbabdb632a3ada2ba9eab8b01',
    'SLH_192s_PK.hex': '7d8aa665d2425d85f8d244669e6fee4517f1f63af4b4712ad0e2ca050cfcd807',
    'SLH_192s_SK.hex': 'af7d977fb9e68f8b9091ecb7d282e1c644edb56c0b673cc7a0828f6d26e0a8b5',
    'SLH_256f_PK.hex': 'bd287f5f268b3f99ea75dd6958444f65ace94df9c5c1087e00d5d1a78678c927',
    'SLH_256f_SK.hex': '0f4dacdb94dca1833bc54339eb734ae081e5c663a3a6d731c578b57a5f7dd2fb',
    'SLH_256s_PK.hex': '63df1029c12aa1dbdb58df7493ab7f9a50ad04d572bc248c28de34cc3829ca0a',
    'SLH_256s_SK.hex': '8199c1c7061c92a6759e43b6d92daff9da7a71d92a0a25cae110c814f730c675',
    'SLH_msg_33B.hex': '995fc0c6d6a9b7da4488825699ced52b2b1628785ee45d703256beeb806fa422',
}
TB_SHA256 = '687a3c45d9a54dc9e6e3782ac75ee2023ea5756a250766790c82f479f6063b0c'
SETTING_SHAPE_SHA256 = '7bfade938f04947c601e680a5a10d584807c97df3d53d69fcd55399fc7027ebf'
TIMEOUT = 3600


def check_configuration(path):
    """Read the selection; never edit or override the candidate configuration.

    Restrict the rest of setting.v to the reviewed vendor macro layout, so
    later redefinitions/conditional selections cannot redirect the testbench.
    Comments, blank lines and surrounding indentation are immaterial.
    """
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', path.read_text(), flags=re.S)
    parameters = re.findall(r'^\s*`define\s+(PARAM_(?:128|192|256)[FS])\b', text, re.M)
    if len(parameters) != 1 or re.search(r'^\s*`define\s+SHAKE\b', text, re.M):
        raise ValueError('frozen-reference gate requires exactly one SHA2 parameter set; '
                         f'candidate selects {parameters or "no known parameter set"}; SHAKE is unsupported')
    shape = re.sub(r'^\s*`define\s+PARAM_(?:128|192|256)[FS]\b',
                   '`define SELECTED_PARAMETER', text, flags=re.M)
    shape = '\n'.join(line.strip() for line in shape.splitlines() if line.strip())
    if hashlib.sha256(shape.encode()).hexdigest() != SETTING_SHAPE_SHA256:
        raise ValueError('setting.v differs from the reviewed vendor macro layout')
    return parameters[0].removeprefix('PARAM_').lower()


def load_reference(parameter):
    """Validate the whole historical vendor dump, including its padded message."""
    golden = GOLDEN_DIR / f'SIG_{parameter}.hex'
    expected = golden.read_bytes()
    digest, words = REFERENCES[parameter]
    if hashlib.sha256(expected).hexdigest() != digest:
        raise ValueError(f'frozen SHA2-{parameter} golden signature checksum mismatch')
    lines = expected.splitlines()
    if len(lines) != words or any(not re.fullmatch(rb'[0-9a-fA-F]{16}', line) for line in lines):
        raise ValueError(f'frozen SHA2-{parameter} vendor dump format/length mismatch')
    return golden, expected


def check_harness(rtl, parameter, data_root):
    """Pin the vendor testbench and the four inputs its selected mode reads."""
    if hashlib.sha256((rtl / 'sphincslet/tb.v').read_bytes()).hexdigest() != TB_SHA256:
        raise ValueError('testbench differs from the frozen vendor sign/verify harness')
    names = ('SLH_msg_33B.hex', f'SLH_{parameter}_SK.hex',
             f'SLH_{parameter}_PK.hex', f'{parameter[:3]}_optrand.hex')
    inputs = hashes(data_root / 'data_sha2' / name for name in names)
    for source, digest in inputs.items():
        if digest != INPUT_SHA256[Path(source).name]:
            raise ValueError(f'frozen SHA2-{parameter} test input checksum mismatch: {source}')
    return inputs


def check_signature(golden, produced, output, returncode, parameter=None):
    if returncode != 0:
        return {'status': 'FAIL', 'reason': f'simulator exited with status {returncode}'}
    if re.search(r'(?im)^\s*(?:ERROR|FATAL)(?:\s|:)', output):
        return {'status': 'FAIL', 'reason': 'simulator reported an error'}
    if 'The signature is not matched' in output:
        return {'status': 'FAIL', 'reason': 'testbench reported a signature mismatch'}
    if not produced.is_file():
        return {'status': 'FAIL', 'reason': 'no signature produced'}
    expected = golden if isinstance(golden, bytes) else golden.read_bytes()
    actual = produced.read_bytes()
    if not expected.strip() or not actual.strip():
        return {'status': 'FAIL', 'reason': 'empty golden or produced signature'}
    if expected != actual:
        return {'status': 'FAIL', 'reason': 'signature differs from golden'}
    for marker in ('sig gen done', 'sig verification done', 'The signature is matched!?'):
        if not re.search(r'^\s*' + marker + r'\s*$', output, re.M):
            return {'status': 'FAIL', 'reason': 'testbench did not report completed sign and verify with match'}
    label = f'SHA2-{parameter}' if parameter else 'vendor'
    return {'status': 'PASS', 'reason': f'signature matches frozen {label} reference, verify OK'}


def run_equiv(rtl_dir=DEFAULT_RTL, timeout=TIMEOUT):
    base = {}
    stage = 'setup'
    try:
        rtl = Path(rtl_dir).resolve()
        if not rtl.is_dir():
            raise ValueError(f'RTL directory missing: {rtl}')
        parameter = check_configuration(rtl / 'sphincslet/setting.v')
        base.update(parameter_set=f'SHA2-{parameter}', evidence_kind='vendor_rtl_differential',
                    independent_fips_205_validation=False, reference_commit=REFERENCE_COMMIT)
        golden, expected_bytes = load_reference(parameter)
        base.update(golden=str(golden), golden_sha256=REFERENCES[parameter][0],
                    signature_words=REFERENCES[parameter][1],
                    produced_filename=f'SIG_file0_{parameter}_w.hex')
        data_root = Path(os.environ.get('SLH_DATA_ROOT', str(rtl / 'imports'))).resolve()
        input_hashes = check_harness(rtl, parameter, data_root)
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
        staged_hashes = {str(staged / Path(source).relative_to(rtl)): digest
                         for source, digest in original_hashes.items()}
        if hashes(staged.rglob('*.v')) != staged_hashes:
            raise RuntimeError('candidate source set or bytes changed while staging')
        # Validate the staged selection and testbench again to bind checks to
        # exactly the files the tools will compile, not a pre-copy observation.
        if check_configuration(staged / 'sphincslet/setting.v') != parameter:
            raise RuntimeError('candidate parameter changed while staging')
        check_harness(staged, parameter, data_root)
        (work / 'sources.json').write_text(json.dumps(original_hashes, indent=2))
        (work / 'reference.json').write_text(json.dumps(base, indent=2))
        (work / 'inputs.json').write_text(json.dumps(input_hashes, indent=2))
        # Preserve the testbench's four-level-relative vendor data layout.
        sim = work / 'a/b/c/d'
        sim.mkdir(parents=True)
        data = work / 'TECS_v8.srcs/sources_1/imports/data_sha2'
        data.mkdir(parents=True)
        for source, digest in input_hashes.items():
            copy = data / Path(source).name
            shutil.copy2(source, copy)
            if hashlib.sha256(copy.read_bytes()).hexdigest() != digest:
                raise RuntimeError(f'test input changed while staging: {source}')
        produced = data / base['produced_filename']
        # The private output starts absent. No output from any external tree is
        # copied, removed or treated as current evidence.
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
        if hashes(rtl.rglob('*.v')) != original_hashes:
            raise RuntimeError('selected candidate sources changed during verification')
        if hashes(staged.rglob('*.v')) != staged_hashes:
            raise RuntimeError('staged candidate sources changed during verification')
        if hashes(input_hashes) != input_hashes:
            raise RuntimeError('selected test inputs changed during verification')
        for source, digest in input_hashes.items():
            if hashlib.sha256((data / Path(source).name).read_bytes()).hexdigest() != digest:
                raise RuntimeError('staged test inputs changed during verification')
        if load_reference(parameter)[1] != expected_bytes:
            raise RuntimeError('frozen reference changed during verification')
        return {**check_signature(expected_bytes, produced, result.stdout, result.returncode, parameter), **base}
    except subprocess.TimeoutExpired:
        return {'status': 'FAIL', 'stage': stage, 'reason': f'{stage} timed out', **base}
    except (OSError, ValueError, RuntimeError, IndexError) as exc:
        return {'status': 'ERROR', 'stage': stage, 'reason': str(exc), **base}


if __name__ == '__main__':
    result = run_equiv(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RTL)
    print(json.dumps(result, indent=2))
    print(f"SLH-DSA GATE: {result['status']} - {result['reason']}")
    raise SystemExit({'PASS': 0, 'FAIL': 1}.get(result['status'], 2))
