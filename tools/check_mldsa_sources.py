#!/usr/bin/env python3
"""Offline check of pinned ML-DSA source bytes and bundled vector shape."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agent.mldsa_sources import BUNDLED_ROOT, verify_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=BUNDLED_ROOT,
                        help='snapshot to check against the same reviewed upstream pin')
    args = parser.parse_args()
    try:
        result = verify_snapshot(args.root)
    except (OSError, ValueError, KeyError) as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
