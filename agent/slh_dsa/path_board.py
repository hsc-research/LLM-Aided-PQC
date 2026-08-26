#!/usr/bin/env python3
"""Extract the top-N post-route timing paths for SLH-DSA and group them by
module cone.

fmax_search.py writes report_timing_summary, which carries only Path 1. The
ML-DSA block loop worked from a top-10 board (path_extractor.run_extraction),
so this restores the same decision surface at chip level.

Runs place_opt/route at the CLOSING period so the board reflects the design
as actually closed. Every path at the closing period is MET by definition;
paths 2..N have MORE slack than path 1 and do NOT gate closure. They matter
only for knowing which cone binds NEXT if path 1 is fixed (see the HQC
ledger, where the binding path moved between arms).

Usage: python3 agent/slh_dsa/path_board.py [period_ns] [n_paths]
"""
import os, re, sys, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
CKPT = "/mnt/c/PQC/slh_test/slh_128f_sha2_synth.dcp"
OUT  = "/tmp/slh_board.rpt"

PERIOD = float(sys.argv[1]) if len(sys.argv) > 1 else 11.98
N      = int(sys.argv[2])   if len(sys.argv) > 2 else 10

TCL = f"""open_checkpoint {CKPT}
create_clock -period {PERIOD:.3f} -name clk [get_ports clk]
catch {{opt_design}}
place_design -directive ExtraTimingOpt
phys_opt_design -directive Explore
route_design -directive Explore
report_timing -max_paths {N} -sort_by slack -file {OUT}
puts "BOARD DONE"
"""

PATH_RE = re.compile(
    r"Slack \((MET|VIOLATED)\)\s*:\s*(-?[\d.]+)ns.*?"
    r"Source:\s*(\S+).*?Destination:\s*(\S+).*?"
    r"Data Path Delay:\s+([\d.]+)ns\s+\(logic ([\d.]+)ns \(([\d.]+)%\)\s+"
    r"route ([\d.]+)ns \(([\d.]+)%\)\).*?"
    r"Logic Levels:\s+(\d+)\s+\(([^)]*)\)",
    re.S)


def parse(txt):
    out = []
    for m in PATH_RE.finditer(txt):
        out.append({
            "verdict": m.group(1),
            "slack": float(m.group(2)),
            "source": m.group(3),
            "dest": m.group(4),
            "delay_ns": float(m.group(5)),
            "logic_pct": float(m.group(7)),
            "route_pct": float(m.group(9)),
            "levels": int(m.group(10)),
            "cells": m.group(11).strip(),
        })
    return out


def cone(p):
    """Module cone = deepest shared hierarchy prefix of source and dest."""
    a = p["source"].split("/")[:-1]
    b = p["dest"].split("/")[:-1]
    shared = []
    for x, y in zip(a, b):
        if x != y:
            break
        shared.append(x)
    return "/".join(shared) or (a[0] if a else "?")


def main():
    tf = "/tmp/slh_board.tcl"
    open(tf, "w").write(TCL)
    print(f"routing at {PERIOD} ns, extracting top {N} paths ...")
    r = subprocess.run(["vivado", "-mode", "batch", "-source", tf,
                        "-nojournal", "-log", "/tmp/slh_board.log"],
                       capture_output=True, text=True, timeout=7200)
    if "BOARD DONE" not in r.stdout:
        print(r.stdout[-2000:]); raise SystemExit("board extraction failed")

    paths = parse(open(OUT).read())
    if not paths:
        raise SystemExit(f"no paths parsed from {OUT}")

    groups = {}
    for i, p in enumerate(paths):
        p["rank"] = i
        groups.setdefault(cone(p), []).append(p)

    print(f"\n{len(paths)} paths, {len(groups)} distinct cones\n")
    for c, ps in sorted(groups.items(), key=lambda kv: kv[1][0]["slack"]):
        w = ps[0]
        print(f"[{len(ps)} path(s)] slack {w['slack']:+.3f}  {c}")
        print(f"    {w['levels']}lv  logic {w['logic_pct']}%  route {w['route_pct']}%  {w['cells']}")
        print(f"    worst: {w['source']} -> {w['dest']}")

    board = os.path.join(HERE, "path_board.json")
    json.dump({"period_ns": PERIOD, "n": N, "paths": paths,
               "cones": {c: [p["rank"] for p in ps] for c, ps in groups.items()}},
              open(board, "w"), indent=1)
    print(f"\nwrote {board}")


if __name__ == "__main__":
    main()
