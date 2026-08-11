#!/usr/bin/env python3
"""ASAP7 Genus Fmax binary search. Periods in PICOSECONDS.
Usage: asap7_fmax.py TOP SRCDIR SDC OUTDIR LO_PS HI_PS"""
import os, re, subprocess, sys, json, time

TOP, SRCDIR, SDC = sys.argv[1], sys.argv[2], sys.argv[3]
OUTDIR = os.path.expanduser(sys.argv[4])
LO, HI = float(sys.argv[5]), float(sys.argv[6])
TOL = 5.0                       # ps
RUN = os.path.expanduser("~/pqc/hqc/asic/asap7/run")
os.makedirs(OUTDIR, exist_ok=True)

def run(p):
    env = dict(os.environ, GENUS_TOP=TOP, GENUS_SRCDIR=SRCDIR, GENUS_SDC=SDC,
               GENUS_PERIOD_PS=f"{p:.0f}", GENUS_OUTDIR=OUTDIR)
    t0 = time.time()
    subprocess.run(["genus","-no_gui","-f","../scripts/genus_asap7.tcl"],
                   cwd=RUN, env=env, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    rpt = f"{OUTDIR}/{TOP}_p{p:.0f}_timing.rpt"
    if not os.path.exists(rpt):
        print(f"  period={p:.0f}ps  NO REPORT", flush=True); return None
    m = re.search(r"Path 1:\s+(MET|VIOLATED)\s+\(([-0-9]+)\s*ps\)", open(rpt).read())
    if not m:
        print(f"  period={p:.0f}ps  UNPARSED", flush=True); return None
    print(f"  period={p:.0f}ps  {m.group(1)}  slack={m.group(2)}ps  "
          f"({time.time()-t0:.0f}s)", flush=True)
    return m.group(1) == "MET"

print(f"ASAP7 Fmax: {TOP}  src={SRCDIR}  bracket [{LO:.0f}, {HI:.0f}] ps", flush=True)
if not run(HI):
    print(f"FAIL: upper bound {HI:.0f}ps does not meet. Raise HI."); sys.exit(1)
# The bracket must be proven, not assumed. A search whose LO never violates
# reports the bracket floor, not the design limit.
if run(LO):
    print(f"FAIL: lower bound {LO:.0f}ps MEETS. Result would be the bracket "
          f"floor, not a measurement. Lower LO and re-run."); sys.exit(2)

best, lo, hi = HI, LO, HI
while hi - lo > TOL:
    mid = (lo + hi) / 2
    r = run(mid)
    if r is None: print("aborting: unparsable point"); sys.exit(3)
    if r: hi, best = mid, mid
    else: lo = mid
print(f"\nRESULT {TOP}: min period {best:.0f} ps -> Fmax {1e6/best:.1f} MHz")
json.dump({"top":TOP,"src":SRCDIR,"period_ps":best,"fmax_mhz":1e6/best,
           "effort":"high","library":"ASAP7 7nm LVT+SLVT TT",
           "sdc":SDC,"stage":"pre_layout"},
          open(f"{OUTDIR}/{TOP}_fmax.json","w"), indent=2)
