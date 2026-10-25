"""Fail-closed result parsers shared by the ML-DSA block harnesses."""
import os
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[2]


def pristine_source(name=None):
    root = Path(os.environ.get('MLDSA_ROOT', str(REPO / 'third_party/mldsa_osh/upstream')))
    source = root.resolve() / 'ref_combined/src'
    return str(source / name if name else source)


def failure_reason(returncode, stdout, stderr=''):
    if returncode != 0:
        return f'simulator exited with status {returncode}: {stderr[-300:]}'
    bad = re.search(r'\b(?:FAIL|MISMATCH|FATAL|ERROR)\b', stdout + '\n' + stderr, re.I)
    return 'simulator reported ' + bad.group(0) if bad else None


def lockstep_result(result):
    out, err = result.stdout or '', result.stderr or ''
    reason = failure_reason(result.returncode, out, err)
    matches = re.findall(r'^\s*EQUIV RESULT: PASS checked (\d+)(?: outputs 0 errors)?\s*$', out, re.M)
    checked = int(matches[0]) if len(matches) == 1 else 0
    if reason or checked <= 0:
        return {'status': 'FAIL', 'reason': reason or 'missing unique PASS marker with positive checked coverage',
                'checked': checked}
    return {'status': 'PASS', 'reason': 'lockstep match', 'checked': checked}


def block_result(returncode, out, err='', expected=200):
    reason = failure_reason(returncode, out, err)
    summary = re.findall(r'checked\s+(\d+)\s+outputs,\s*(\d+)\s+errors', out)
    marker = re.findall(r'^\s*BLOCK-KAT RESULT: PASS\s+\((\d+)/(\d+)\)\s*$', out, re.M)
    checked = int(summary[0][0]) if len(summary) == 1 else 0
    if (reason or expected <= 0 or summary != [(str(expected), '0')]
            or marker != [(str(expected), str(expected))]):
        return False, reason or 'missing or incomplete block-KAT coverage', checked
    return True, 'all expected outputs match', checked


def encoder_result(result):
    out, err = result.stdout or '', result.stderr or ''
    reason = failure_reason(result.returncode, out, err)
    configs = re.findall(r'^CFG sl=(\d+) em=(\d+) done: (\d+) words\s*$', out, re.M)
    switches = re.findall(r'^SWITCHSEQ sl=(\d+) done: (\d+) words\s*$', out, re.M)
    expected = {(str(level), str(mode)) for level in (2, 3, 5) for mode in range(6)}
    words = sum(int(row[-1]) for row in configs + switches)
    covered = (len(configs) == 18 and {(level, mode) for level, mode, _ in configs} == expected
               and len(switches) == 2 and {level for level, _ in switches} == {'3', '5'}
               and all(int(row[-1]) > 0 for row in configs + switches))
    marker = re.findall(r'^\s*GATE RESULT: PASS\s*$', out, re.M)
    if reason or not covered or len(marker) != 1:
        return {'status': 'FAIL', 'reason': reason or 'missing, duplicate or empty encoder configuration coverage',
                'words': words}
    return {'status': 'PASS', 'reason': '18 configurations and two mode-switch sequences stream-match', 'words': words}
