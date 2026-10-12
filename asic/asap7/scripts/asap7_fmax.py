#!/usr/bin/env python3
"""Retired historical ASIC binary-search entry point.

The measured synthesis response was non-monotonic, so binary search cannot
establish Fmax. The former drivers also permitted stale reports after failures.
Historical source and measurements remain in Git history and logs/asic/.
"""
import sys


def main():
    print("This legacy Fmax search is disabled: synthesis is not monotonic. "
          "Use scripts/run_asic_tool.py with an explicit reviewed configuration "
          "for independent fixed-period points. See asic/README.md.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
