#!/usr/bin/env python3
"""ML-DSA KeyGen KAT gate: N vectors for each of II, III and V must pass.

MLDSA_ROOT selects the external pristine tree (default: sibling
ML-DSA-OSH-main). VIVADO_BIN optionally augments PATH. Run artifacts go into
unique PQC_RUN_DIR children (default: repository/.pqc_runs), never archived logs.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
from run_safety import hashes, run_process

ROOT = Path(os.environ.get('MLDSA_ROOT', str(REPO.parent / 'ML-DSA-OSH-main'))).resolve()
VIVADO_BIN = os.environ.get('VIVADO_BIN', '')
TIMEOUT = 86400
LEVELS = ('II', 'III', 'V')


def parse_per_vector(out):
    """Keep security level in identity; reject duplicate completion records."""
    vecs, by_key, current = [], {}, None
    for line in out.splitlines():
        match = re.search(r'KAT\s*#\s*(\d+)', line)
        if match:
            level = re.search(r'ML-DSA-(II|III|V)\.KeyGen', line)
            key = (level.group(1) if level else None, int(match.group(1)))
            if key not in by_key:
                by_key[key] = {'level': key[0], 'kat': key[1], 'completed': False,
                               'cycles': None, 'wrong': 0, 'completions': 0}
                vecs.append(by_key[key])
            current = by_key[key]
            if 'completed in' in line:
                cycles = re.search(r'completed in\s*(\d+)\s+clock cycles', line)
                current['completions'] += 1
                current['cycles'] = int(cycles.group(1)) if cycles else None
                current['completed'] = current['cycles'] is not None and current['cycles'] > 0
        if 'WRONG' in line and current is not None:
            current['wrong'] += 1
    for vector in vecs:
        vector['pass'] = (vector['level'] in LEVELS and vector['completed']
                          and vector['wrong'] == 0 and vector['completions'] == 1)
    return vecs


def evaluate_simulation(out, returncode, expected_vectors, timed_out=False):
    """A success marker alone is insufficient: prove the exact coverage set."""
    vectors = parse_per_vector(out)
    expected = {(level, index) for level in LEVELS for index in range(expected_vectors)}
    actual = {(v['level'], v['kat']) for v in vectors}
    failures = [line for line in out.splitlines() if 'WRONG' in line or
                re.match(r'\s*(?:ERROR|FATAL)(?:\s|:)', line, re.I)]
    reason = None
    if timed_out:
        reason = 'simulator timed out'
    elif returncode != 0:
        reason = f'simulator exited with status {returncode}'
    elif failures:
        reason = failures[0]
    elif 'testbench done' not in out:
        reason = "missing 'testbench done'"
    elif actual != expected or not all(v['pass'] for v in vectors):
        reason = 'missing, duplicate, malformed, or incomplete vector results'
    return {'status': 'FAIL' if reason else 'PASS', 'stage': 'sim',
            'reason': reason or 'all expected KeyGen vectors completed without errors',
            'kats_expected': len(expected),
            'kats_completed': sum(v['completed'] for v in vectors),
            'vector_pass': sum(v['pass'] for v in vectors),
            'vector_fail': sum(not v['pass'] for v in vectors),
            'wrong_count': sum('WRONG' in line for line in out.splitlines())}, vectors


def run_full_kat(override_dir=None, vectors=None, timeout=TIMEOUT, root=None):
    if vectors is not None and (isinstance(vectors, bool) or not isinstance(vectors, int) or not 1 <= vectors <= 25):
        return {'status': 'FAIL', 'stage': 'setup', 'reason': 'vectors must be an integer from 1 to 25 per level'}
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout < float('inf'):
        return {'status': 'FAIL', 'stage': 'setup', 'reason': 'timeout must be positive and finite'}
    parent = Path(os.environ.get('PQC_RUN_DIR', str(REPO / '.pqc_runs'))).resolve()
    parent.mkdir(parents=True, exist_ok=True)
    work = tempfile.mkdtemp(prefix='mldsa-fullkat-', dir=parent)
    log_file = str(Path(work) / 'fullkat_run.log')
    vector_file = str(Path(work) / 'fullkat_vectors.json')
    base = {'run_dir': work, 'log_file': log_file, 'per_vector_file': vector_file}
    stage = 'setup'
    started = time.monotonic()
    try:
        source_root = Path(root or ROOT).resolve()
        source = source_root / 'ref_combined/src'
        tb = source_root / 'ref_combined/src_tb/tb_keygen_top.v'
        if not source.is_dir() or not tb.is_file():
            raise ValueError(f'MLDSA_ROOT lacks ref_combined/src and src_tb/tb_keygen_top.v: {source_root}')
        chosen = {p.name: p for p in source.iterdir() if p.is_file()}
        if not any(p.suffix == '.v' for p in chosen.values()):
            raise ValueError('pristine source set contains no Verilog files')
        if override_dir is not None:
            override = Path(override_dir).resolve()
            if not override.is_dir():
                raise ValueError(f'override directory missing: {override}')
            replacements = [p for p in override.iterdir() if p.suffix in ('.v', '.vhd', '.vh') and p.is_file()]
            if not replacements:
                raise ValueError('override directory contains no supported source files')
            for path in replacements:
                if path.name not in chosen:
                    raise ValueError(f'override has no pristine counterpart: {path.name}')
                chosen[path.name] = path
        original_hashes = hashes(chosen.values())
        staged = Path(work) / 'ref_combined/src'
        staged.mkdir(parents=True)
        for name, path in chosen.items():
            shutil.copy2(path, staged / name)
            if hashes([staged / name])[str(staged / name)] != original_hashes[str(path)]:
                raise RuntimeError(f'source changed while staging: {path}')
        (Path(work) / 'sources.json').write_text(json.dumps(original_hashes, indent=2))
        vfiles = {p.name: str(p) for p in staged.glob('*.v')}
        vhfiles = {p.name: str(p) for p in staged.glob('*.vhd')}
        rundir = Path(work) / 'ref_combined/src_tb'
        shutil.copytree(tb.parent, rundir)
        shutil.copytree(source_root / 'common', Path(work) / 'common')
        shutil.copytree(source_root / 'KAT', Path(work) / 'KAT')
        tb_dst = rundir / tb.name
        text = tb_dst.read_text()
        # Check the supported pristine capacity even for full runs. Do not
        # trust a modified NUM_TV value to lower the required coverage.
        anchor = re.compile(r'\blocalparam\s+NUM_TV\s*=\s*(\d+)\s*;')
        declarations = anchor.findall(text)
        if declarations != ['25']:
            raise ValueError(f'expected one NUM_TV = 25 declaration, found {declarations}')
        expected_vectors = vectors if vectors is not None else 25
        tb_dst.write_text(anchor.sub(f'localparam NUM_TV = {expected_vectors};', text))
        for folder in (Path(work) / 'common', Path(work) / 'KAT'):
            for path in folder.iterdir():
                if path.is_file() and not (rundir / path.name).exists():
                    shutil.copy2(path, rundir / path.name)
        # shim: hoist ALL forward-referenced reg/wire declarations in combined_top.v
        # (xvlog rejects use-before-declaration; other tools allowed it)
        ct = vfiles.get("combined_top.v")
        if ct:
            import re as _re
            src_ct = Path(ct).read_text()
            decl_re = _re.compile(r"^[ \t]*(reg|wire)(\s+(signed)?\s*(\[[^\]]+\])?)?\s+([A-Za-z_][A-Za-z0-9_]*(\s*\[[^\]]+\])?(\s*,\s*[A-Za-z_][A-Za-z0-9_]*(\s*\[[^\]]+\])?)*)\s*;\s*$", _re.M)
            hoisted = []
            def first_use(name, before):
                m = _re.search(r"\b" + _re.escape(name) + r"\b", before)
                return m is not None
            # iterate declarations bottom-up; hoist any whose name is used earlier
            for m in list(decl_re.finditer(src_ct)):
                names = [_re.split(r"\s*\[", n.strip())[0] for n in m.group(5).split(",")]
                body_before = src_ct[:m.start()]
                if any(first_use(n, body_before) for n in names):
                    hoisted.append(m.group(0).strip())
            if hoisted:
                for d in hoisted:
                    src_ct = src_ct.replace(d + "\n", "", 1) if d + "\n" in src_ct else src_ct.replace(d, "", 1)
                hdr_end = src_ct.find(");", src_ct.find("module combined_top")) + 2
                src_ct = src_ct[:hdr_end] + "\n    // xvlog shim: hoisted forward-referenced decls\n    " + "\n    ".join(hoisted) + "\n" + src_ct[hdr_end:]
                shim = os.path.join(work, "combined_top.v")
                Path(shim).write_text(src_ct)
                vfiles["combined_top.v"] = shim

        env = dict(os.environ)
        if VIVADO_BIN:
            env['PATH'] = VIVADO_BIN + os.pathsep + env.get('PATH', '')
        counter = 0

        def execute(argv, sim=False):
            nonlocal counter
            counter += 1
            path = log_file if sim else str(Path(work) / f'{counter:03d}-{Path(argv[0]).name}.log')
            return run_process(argv, cwd=rundir, env=env, timeout=timeout, log_path=path)

        stage = 'xvhdl'
        pending = [v for name, v in sorted(vhfiles.items()) if name.endswith('_pkg.vhd')]
        pending += [v for name, v in sorted(vhfiles.items()) if not name.endswith('_pkg.vhd')]
        for _ in range(len(pending) + 1):
            failed = []
            for path in pending:
                result = execute(['xvhdl', path])
                if result.returncode or re.search(r'(?im)^\s*ERROR\b', result.stdout):
                    failed.append(path)
            if not failed:
                break
            if len(failed) == len(pending):
                raise RuntimeError('VHDL compile made no progress: ' + ', '.join(Path(p).name for p in failed))
            pending = failed
        for stage, argv in (
                ('xvlog', ['xvlog', *sorted(vfiles.values()), tb.name]),
                ('xelab', ['xelab', 'tb_keygen_top', '-s', 'kat_sim', '--timescale', '1ns/1ps'])):
            result = execute(argv)
            if result.returncode or re.search(r'(?im)^\s*(?:ERROR|FATAL)\b', result.stdout):
                raise RuntimeError(f'{stage} failed: {result.stdout[-800:]}')
        stage = 'sim'
        timed_out = False
        try:
            result = execute(['xsim', 'kat_sim', '-R'], sim=True)
            output, returncode = result.stdout, result.returncode
        except subprocess.TimeoutExpired:
            output = Path(log_file).read_text(errors='replace') if Path(log_file).exists() else ''
            returncode, timed_out = -9, True
        outcome, parsed = evaluate_simulation(output, returncode, expected_vectors, timed_out)
        Path(vector_file).write_text(json.dumps(parsed, indent=2))
        if hashes(original_hashes) != original_hashes:
            raise RuntimeError('selected candidate sources changed during verification')
        return {**outcome, **base, 'runtime_s': round(time.monotonic() - started, 1),
                'override': str(override_dir) if override_dir else 'pristine',
                'vectors_per_level': expected_vectors}
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        return {'status': 'FAIL', 'stage': stage, 'reason': str(exc), **base,
                'runtime_s': round(time.monotonic() - started, 1)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('override_dir', nargs='?')
    parser.add_argument('--vectors', type=int)
    parser.add_argument('--timeout', type=float, default=TIMEOUT)
    parser.add_argument('--root', help='external pristine ML-DSA source root')
    args = parser.parse_args()
    outcome = run_full_kat(args.override_dir, vectors=args.vectors, timeout=args.timeout, root=args.root)
    print(json.dumps(outcome, indent=2))
    raise SystemExit(0 if outcome['status'] == 'PASS' else 1)
