#!/usr/bin/env python3
"""Genus Fmax binary search, per-arm. Accepts only MET.
Usage: genus_fmax_arm.py TOP SRCDIR OUTDIR [LO] [HI]"""
import os, re, subprocess, sys, json, time

TOP    = sys.argv[1]
SRCDIR = sys.argv[2]
OUTDIR = os.path.expanduser(sys.argv[3])
LO     = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
HI     = float(sys.argv[5]) if len(sys.argv) > 5 else 5.0
TOL    = 0.05
SCRIPTS= os.path.expanduser("~/pqc/hqc/asic/scripts")
os.makedirs(OUTDIR, exist_ok=True)

def run(period):
    env = dict(os.environ, GENUS_PERIOD=f"{period:.3f}", GENUS_TOP=TOP,
               GENUS_SRCDIR=SRCDIR, GENUS_OUTDIR=OUTDIR)
    t0 = time.time()
    subprocess.run(["genus","-no_gui","-f","genus_fmax_arm.tcl"],
                   cwd=SCRIPTS, env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=7200)
    rpt = f"{OUTDIR}/{TOP}_p{period:.3f}_timing.rpt"
    if not os.path.exists(rpt):
        print(f"  period={period:.3f}ns  NO REPORT", flush=True); return None
    txt = open(rpt).read()
    m = re.search(r"Path 1:\s+(MET|VIOLATED)\s+\(([-0-9]+)\s*ps\)", txt)
    if not m:
        print(f"  period={period:.3f}ns  UNPARSED", flush=True); return None
    print(f"  period={period:.3f}ns  {m.group(1)}  slack={m.group(2)}ps  "
          f"({time.time()-t0:.0f}s)", flush=True)
    return m.group(1) == "MET"

print(f"Genus Fmax: {TOP}  src={SRCDIR}  bracket [{LO}, {HI}] ns", flush=True)
if not run(HI):
    print(f"FAIL: upper bound {HI}ns does not meet."); sys.exit(1)
best, lo, hi = HI, LO, HI
while hi - lo > TOL:
    mid = (lo + hi) / 2
    if run(mid): hi, best = mid, mid
    else:        lo = mid
print(f"\nRESULT {TOP}: min period {best:.3f} ns  ->  Fmax {1000/best:.2f} MHz")
json.dump({"top":TOP,"src":SRCDIR,"period_ns":best,"fmax_mhz":1000/best,
           "effort":"high","corner":"GPDK045_SVT_slow_0p9V_125C"},
          open(f"{OUTDIR}/{TOP}_fmax.json","w"), indent=2)
