#!/usr/bin/env python3
"""Require exact per-(security level, KAT) cycle equivalence.

A constant nonzero offset is latency-changing and therefore FAIL here.
Consume only the artifact paths returned by each successful fresh full-KAT
run. Archived cycle records are never used or overwritten.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def run(srcdir, tag=None):
    result = subprocess.run([sys.executable, str(HERE / 'full_kat_gate.py'), str(srcdir)],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f'{tag or "KAT"} failed: {result.stdout[-1000:]} {result.stderr[-300:]}')
    outcome = json.loads(result.stdout)
    if outcome.get('status') != 'PASS':
        raise RuntimeError(f'{tag or "KAT"} did not pass')
    path = Path(outcome['per_vector_file']).resolve()
    run_dir = Path(outcome['run_dir']).resolve()
    if not path.is_relative_to(run_dir) or not path.is_file():
        raise RuntimeError('KAT vector artifact is missing or outside its run directory')
    records = json.loads(path.read_text())
    if len(records) != 75 or outcome.get('kats_expected') != 75 or outcome.get('kats_completed') != 75:
        raise RuntimeError('full timing-equivalence gate requires 75 completed KeyGen vectors')
    return records, str(path)


def compare_vectors(baseline, optimized):
    def indexed(records):
        if not isinstance(records, list) or not records:
            raise ValueError('vector records must be nonempty')
        result = {}
        for record in records:
            key = (record.get('level'), record.get('kat'))
            cycles = record.get('cycles')
            if (key[0] not in ('II', 'III', 'V') or isinstance(key[1], bool)
                    or not isinstance(key[1], int) or key[1] < 0 or key in result
                    or record.get('completed') is not True or record.get('pass') is not True
                    or record.get('wrong') != 0 or record.get('completions') != 1 or isinstance(cycles, bool)
                    or not isinstance(cycles, int) or cycles <= 0):
                raise ValueError('invalid, duplicate or failed vector record')
            result[key] = cycles
        counts = {level: {index for lv, index in result if lv == level} for level in ('II', 'III', 'V')}
        size = len(counts['II'])
        if not 1 <= size <= 25 or any(indices != set(range(size)) for indices in counts.values()):
            raise ValueError('incomplete security-level/vector coverage')
        return result

    base, opt = indexed(baseline), indexed(optimized)
    if base.keys() != opt.keys():
        raise ValueError('vector identities differ')
    deltas = [opt[key] - value for key, value in base.items()]
    distinct = sorted(set(deltas))
    different = [{'level': key[0], 'kat': key[1], 'baseline': value, 'optimized': opt[key]}
                 for key, value in base.items() if opt[key] != value]
    return {'status': 'PASS' if distinct == [0] else 'FAIL',
            'reason': 'cycle-identical' if distinct == [0] else 'per-vector latency changed',
            'vectors': len(base), 'distinct_deltas': distinct, 'mismatched': len(different),
            'first_10': different[:10], 'baseline_total': sum(base.values()),
            'optimized_total': sum(opt.values())}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline')
    parser.add_argument('optimized')
    args = parser.parse_args(argv)
    try:
        baseline, base_path = run(args.baseline, 'baseline')
        optimized, opt_path = run(args.optimized, 'optimized')
        outcome = {**compare_vectors(baseline, optimized),
                   'baseline_vectors': base_path, 'optimized_vectors': opt_path}
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        outcome = {'status': 'FAIL', 'reason': str(exc)}
    print(json.dumps(outcome, indent=2))
    return 0 if outcome['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
