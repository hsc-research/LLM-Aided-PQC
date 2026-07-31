#!/usr/bin/env python3
"""Genus Fmax binary search. Accepts only MET, mirrors fmax_search.py semantics."""
import os, re, subprocess, sys, json, time

TOP    = sys.argv[1] if len(sys.argv) > 1 else "poly_mult"
LO     = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0   # ns, aggressive
HI     = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0   # ns, known-MET
TOL    = 0.05
OUTDIR = os.path.expanduser("~/pqc/hqc/asic/out")
SCRIPTS= os.path.expanduser("~/pqc/hqc/asic/scripts")

def run(period):
    env = dict(os.environ, GENUS_PERIOD=f"{period:.3f}",
               GENUS_TOP=TOP, GENUS_OUTDIR=OUTDIR)
    t0 = time.time()
    subprocess.run(["genus","-no_gui","-f","genus_fmax.tcl"],
                   cwd=SCRIPTS, env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=7200)
    rpt = f"{OUTDIR}/{TOP}_p{period:.3f}_timing.rpt"
    if not os.path.exists(rpt):
        return None, None
    txt = open(rpt).read()
    m = re.search(r"Path 1:\s+(MET|VIOLATED)\s+\(([-0-9]+)\s*ps\)", txt)
    if not m:
        return None, None
    met = (m.group(1) == "MET")
    print(f"  period={period:.3f}ns  {m.group(1)}  slack={m.group(2)}ps  "
          f"({time.time()-t0:.0f}s)", flush=True)
    return met, int(m.group(2))

print(f"Genus Fmax search: {TOP}  bracket [{LO}, {HI}] ns")
ok, _ = run(HI)
if not ok:
    print(f"FAIL: upper bound {HI}ns does not meet. Raise HI."); sys.exit(1)
best = HI
lo, hi = LO, HI
while hi - lo > TOL:
    mid = (lo + hi) / 2
    met, _ = run(mid)
    if met:
        hi, best = mid, mid
    else:
        lo = mid
print(f"\nRESULT {TOP}: min period {best:.3f} ns  ->  Fmax {1000/best:.2f} MHz")
json.dump({"top":TOP,"period_ns":best,"fmax_mhz":1000/best,
           "corner":"GPDK045_SVT_slow_0p9V_125C","memories":"blackboxed"},
          open(f"{OUTDIR}/{TOP}_fmax.json","w"), indent=2)
