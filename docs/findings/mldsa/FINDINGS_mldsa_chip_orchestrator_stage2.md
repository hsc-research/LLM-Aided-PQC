# Findings: ML-DSA Chip Orchestrator Stage-2 Validation

## Summary
Stage-2 autonomous closure→dispatch loop (`agent/chip_orchestrator.py --dispatch`)
validated end-to-end on a clean run following bracket narrowing (12.0–13.5ns).
The loop correctly measures, extracts, and gates — it does not autonomously
edit RTL. No architectural change was applied by this run.

## Run result
- Regenerated `combined_top` checkpoint from current `MODULE_SOURCES` (banked
  encoder + all committed block wins).
- Closure search (binary search, WNS≥0): closed at 12.09ns → 82.7 MHz,
  WNS margin +0.095ns.
- Worst path at closure: `FSM_sequential_cstate2_reg[0]_rep__0_replica/C →
  start_op_reg[0]/D`.
- `map_to_file`: no block-orchestrator entry owns this cone
  (instance=None, file=None).
- Loop exited via the graceful no-target branch: "no dispatch target:
  worst-path instance is outside the block-orchestrator scope." No edit
  proposed or applied.

## What this validates
The regen → closure-search → path-extraction → map-to-file →
dispatch-or-graceful-exit pipeline runs unattended and correctly recognizes
when a critical-path cone falls outside block-orchestrator scope, halting
safely rather than acting incorrectly or crashing (contrast with the prior
session's corrupted first run, which crashed on this same code path before
the no-target guard was added).

## What this does NOT show
This run did not autonomously fix or improve the design. The 82.7 MHz figure
re-measures last session's human/Claude-designed banked-encoder architecture
(ACC+FIFO restructure of `encoder.v`, KAT-verified 25/25) at a tighter search
bracket than the earlier standalone `fmax_search.py` run (78.6 MHz). Same
netlist both times — the difference is measurement precision (narrower
bracket → probes converge closer to the true WNS=0 boundary), not a design
change. The 78.6 MHz figure carries residual risk from a corrupted probe in
the prior session (Vivado processes killed mid-flight during a Minerva memory
conflict); 82.7 MHz should be reproduced once via standalone `fmax_search.py`
at the same bracket before replacing 78.6 in any paper table.

## Verified post-route PPA vs. pristine (banked encoder, human-designed,
## KAT-gated 25/25 pass, both corruption directions fail)
Each side measured at its own closing period:
- Pristine: 14.25ns → 70.2 MHz, 52987 LUT / 29081 FF / 1.286W
- Banked:   12.73ns → 78.6 MHz, 53309 LUT / 30034 FF / 1.480W
  (+12.0% fmax, +0.6% LUT, +3.3% FF, +2.7% power)

If 82.7 MHz (12.09ns) is reproduced and confirmed, closure-point PPA at that
period should be re-pulled before it replaces the 78.6 MHz table entry.

## Next
- Current worst-path cone (FSM replica → start_op) is the next architectural
  target, not Keccak as previously assumed — reassess before further work.
- Reproduce 82.7 MHz via standalone `fmax_search.py`, same bracket.
- Update advisor package with corrected framing (measurement precision, not
  autonomous fix).
