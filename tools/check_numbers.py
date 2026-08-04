#!/usr/bin/env python3
"""Check that every frequency quoted in docs/ is a number we can defend.

The failure this prevents: a number is superseded in one document and keeps
being quoted in four others. That happened three times on the HQC figures
before anyone noticed, because nothing connected the retraction to the places
the number appeared.

How it works. Frequencies in MHz are extracted from every tracked markdown
file. Each is classified:

  CANONICAL   listed in ALLOWED below, with a note on what it is
  SUPERSEDED  listed in RETIRED below; an occurrence is an ERROR unless the
              file is a handoff, an archived finding, or the line itself
              marks it as superseded
  UNKNOWN     not in either list; a WARNING, since it is either a new result
              that has not been recorded or a number nobody can trace

Usage:
    python3 tools/check_numbers.py            # report
    python3 tools/check_numbers.py --strict   # exit 1 on any error

Run before committing anything that touches a results document. When a number
changes, edit ALLOWED and RETIRED here first, then run this to find every
place that needs updating.
"""
import os, re, sys, subprocess

ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip() or "."

# ---------------------------------------------------------------------------
# Canonical results. Source of truth is docs/findings/INDEX.md; this mirrors it.
# Update BOTH together.
# ---------------------------------------------------------------------------
ALLOWED = {
    # ML-DSA chip-level, post-route closure, Artix-7 -1
    "70.2":  "ML-DSA combined_top baseline, 14.25 ns",
    "82.7":  "ML-DSA combined_top optimized (banked encoder), 12.09 ns",
    "69.0":  "ML-DSA block-composition regression, the documented null",
    "73.4":  "ML-DSA optimized pre-banked, intermediate build",
    "78.6":  "ML-DSA banked encoder at 12.73 ns, superseded by 82.7 at closure",

    # HQC chip-level, post-route closure, joint KEM, OOC, measured 2026-08-03
    "109.6": "HQC hqc_joint_pristine baseline, 9.12 ns, commit 6351cac",
    "116.0": "HQC hqc_joint_opt optimized, 8.62 ns, commit 6351cac",

    # Block-level, quoted in the taxonomy and rule discussions
    "141":   "HQC fixed_weight before, block OOC",
    "205":   "HQC fixed_weight after, block OOC",
    "117.5": "ML-DSA makehint before, block OOC",
    "177.3": "ML-DSA makehint after, block OOC",
    "111.0": "ML-DSA rejection_s before, block OOC",
    "133.6": "ML-DSA rejection_s after, block OOC",
    "113.6": "ML-DSA butterfly before, block OOC",
    "120.8": "ML-DSA butterfly after, block OOC",
    "101.5": "ML-DSA flow-directive search best, tier 3",
    "116":   "GMU published ML-DSA figure, comparison point",
}

# ---------------------------------------------------------------------------
# Retired. Quoting these outside an archived document is an error.
# ---------------------------------------------------------------------------
RETIRED = {
    "117.1": "pre-a1a7ad2 HQC pair, regen period not recorded, not comparable",
    "119.3": "pre-a1a7ad2 HQC pair, regen period not recorded, not comparable",
    "117.6": "pre-a1a7ad2 HQC spread, binary-search granularity",
    "114.8": "NOT a baseline: the optimized arm while its composition was "
             "silently reverted by a1a7ad2. The baseline is 109.6.",
    "72.6":  "ML-DSA projected from a violated run, 1/(T-WNS), invalid",
    "65.3":  "ML-DSA projected from a violated run, 1/(T-WNS), invalid",
    "780.49": "GPDK045 ASIC, retracted with the library change to ASAP7",
    "695.65": "GPDK045 ASIC, retracted with the library change to ASAP7",
    "1406.59": "GPDK045 ASIC, retracted with the library change to ASAP7",
    "1340.31": "GPDK045 ASIC, retracted with the library change to ASAP7",
    "488.55": "encoder search that hit its bracket floor, not a measurement",
    "730.59": "GPDK045 encoder, retracted with the library change to ASAP7",
}

# Files where a retired number is expected and correct: dated records that
# should not be rewritten, and the ledger that documents the supersession.
ARCHIVE_HINTS = ("handoffs/", "findings/", "PAPER_UPDATE_CHECKLIST")

# A line that marks its own number as retired is fine anywhere.
MARKERS = ("supersede", "SUPERSEDE", "retract", "RETRACT", "~~",
           "do not quote", "DO NOT QUOTE", "invalid", "INVALID",
           "NOT a baseline", "stale", "STALE")

FREQ = re.compile(r"(\d+\.?\d*)\s*MHz")


def tracked_markdown():
    r = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT,
                       capture_output=True, text=True)
    return [f for f in r.stdout.split("\n") if f.strip()]


def main():
    strict = "--strict" in sys.argv
    errors, warnings, ok = [], [], 0

    for rel in tracked_markdown():
        path = os.path.join(ROOT, rel)
        try:
            lines = open(path, errors="replace").read().split("\n")
        except OSError:
            continue
        archived = any(h in rel for h in ARCHIVE_HINTS)
        for n, line in enumerate(lines, 1):
            for val in FREQ.findall(line):
                if val in ALLOWED:
                    ok += 1
                elif val in RETIRED:
                    if archived or any(m in line for m in MARKERS):
                        ok += 1
                    else:
                        errors.append((rel, n, val, RETIRED[val]))
                else:
                    warnings.append((rel, n, val))

    print(f"checked {len(tracked_markdown())} files, {ok} citations verified\n")

    if errors:
        print(f"ERRORS ({len(errors)}): retired numbers quoted as current\n")
        for rel, n, val, why in errors:
            print(f"  {rel}:{n}  {val} MHz")
            print(f"      {why}\n")

    if warnings:
        print(f"WARNINGS ({len(warnings)}): numbers in neither list\n")
        seen = {}
        for rel, n, val in warnings:
            seen.setdefault(val, []).append(f"{rel}:{n}")
        for val, where in sorted(seen.items()):
            print(f"  {val} MHz")
            for w in where[:4]:
                print(f"      {w}")
            if len(where) > 4:
                print(f"      ... and {len(where)-4} more")
        print("\n  Either add to ALLOWED with a note on what it is, or add to")
        print("  RETIRED with the reason it should not be quoted.\n")

    if not errors and not warnings:
        print("clean")

    if strict and errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
