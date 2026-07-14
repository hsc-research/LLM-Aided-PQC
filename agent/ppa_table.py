#!/usr/bin/env python3
# Emit markdown PPA table across all optimized blocks (Dr. Abideen's power/area request).
import sys; sys.path.insert(0, "agent")
from ppa_reader import read_ppa

BLOCKS = [("makehint","default"),("coeff_decomposer","default"),("gen_c","default"),
          ("rejection_s","default"),("usehint","default"),("butterfly","default"),
          ("rejection_a","default"),("rejection_y","default"),("decoder","default"),
          ("encoder","2")]

rows = [read_ppa(m,p) for m,p in BLOCKS]
print("| Block | LUTs | FFs | DSP | WNS (ns) | Fmax (MHz) | Dynamic (W) | Total (W) |")
print("|---|---|---|---|---|---|---|---|")
for r in rows:
    print(f"| {r['module']} | {r['luts']} | {r['ffs']} | {r['dsp']} | {r['wns_ns']} | {r['fmax_mhz']} | {r['dynamic_w']} | {r['total_w']} |")
print()
print(f"Sums: {sum(r['luts'] for r in rows)} LUTs, {sum(r['ffs'] for r in rows)} FFs, "
      f"{round(sum(r['dynamic_w'] for r in rows),3)} W dynamic (block-level, vectorless estimates, "
      f"synth-level, 200MHz constraint; static 0.122W is per-run device floor, not additive)")
