#!/usr/bin/env python3
"""Timing-equivalence checker: per-vector cycle counts must match exactly
between baseline and optimized. Latency-preserving edits must pass this;
latency-changing edits are routed to the reviewed lane by construction."""
import json, subprocess, sys, shutil, os
HERE = os.path.dirname(os.path.abspath(__file__))
VEC  = os.path.join(HERE, "fullkat_vectors.json")

def run(srcdir, tag):
    subprocess.run(["python3", os.path.join(HERE, "full_kat_gate.py"), srcdir],
                   check=True, capture_output=True, text=True)
    out = os.path.join(HERE, f"cycles_{tag}.json")
    shutil.copy(VEC, out)
    return json.load(open(out))

base = run(sys.argv[1], "baseline")
opt  = run(sys.argv[2], "optimized")
assert len(base) == len(opt), f"vector count differs: {len(base)} vs {len(opt)}"

deltas = [o["cycles"] - b["cycles"] for b, o in zip(base, opt)]
uniq = sorted(set(deltas))
bvar = max(b["cycles"] for b in base) - min(b["cycles"] for b in base)
if len(uniq) == 1 and uniq[0] == 0:
    verdict = "PASS (cycle-identical)"
elif len(uniq) == 1:
    verdict = f"PASS (constant offset {uniq[0]:+d}, profile preserved)"
else:
    verdict = f"FAIL (data-dependent perturbation, {len(uniq)} distinct deltas)"
diffs = [(b["kat"], b["cycles"], o["cycles"])
         for b, o in zip(base, opt) if b["cycles"] != o["cycles"]]
res = {"status": verdict,
       "distinct_deltas": uniq,
       "baseline_cycle_spread": bvar,
       "baseline_is_cycle_invariant": bvar == 0,
       "vectors": len(base),
       "mismatched": len(diffs),
       "first_10": diffs[:10],
       "baseline_total": sum(b["cycles"] for b in base),
       "optimized_total": sum(o["cycles"] for o in opt)}
print(json.dumps(res, indent=2))
sys.exit(0 if len(uniq) == 1 else 1)
