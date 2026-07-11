# Findings: decoder + usehint autonomous campaigns (orchestrator v1)

Both targets scout-selected. Gates corruption-validated first pass (lesson
from gen_c's boundary-blind first gate now baked into TB construction:
mode-appropriate boundary constants injected from the start).

## decoder (bit-unpack engine, T0/T1/S1/S2/W1/Z) — net +0.050 ns
Gate: 18 epochs (3 sec_lvl x 6 encode modes), per-epoch output-beat
coverage guard. Validation: > -> >= on Z-mode GAMMA1_2 compare FAILED in
the correct epoch (~2^-18 event, proving the boundary injection lands at
lane alignments); +1 live-branch on T0 subtract FAILED.

Run 1: gate-LEGAL flag-precompute of ENCODE_LVL regressed -0.621 —
auto-reverted by synth compare. New outcome class vs gen_c: an edit can
be functionally correct and still harmful; the loop needs both the gate
AND the measurement, neither alone suffices.
Run 2/3: max_fanout=16 on encode_mode, +0.04999 — reverted by float
compare, then ACCEPTED after round(,3) fix. At-threshold result, +3 LUTs.
Run 4: no_action; 15-level ENCODE_LVL -> SIPO_IN barrel-shift cone is the
residual, same family as rejection_a's load-bearing shifter.

## usehint (verify-side hint application) — net 0, two correct rejections
Gate: 3 sec_lvl epochs, GAMMA2/wrap boundary injection on poly lanes.
Validation: > -> >= GAMMA2 FAIL; wrap 15 -> 14 FAIL.

Run 1: flag-precompute of the EXPAND_HINT state transition mispaired
(uninitialized first cycle; hint_cnt shifts under it) — gate REJECTED.
Second autonomous catch of the same-cycle-consumption trap class.
Run 2/3: max_fanout=16 on ctr: +0.043/+117 LUTs, under threshold, twice
(byte-identical repeat exposed the missing duplicate guard, now fixed;
also touched combinational ctr_next — rule enforcement on v2 backlog).
Run 4: no_action. Residual cone: hint_offset 8-deep sequential compare
ladder feeding ctr_next — logged as guided-restructuring lead
(priority-encoder rewrite, outside the validated menu).

## Orchestrator hardening driven by these campaigns
round(,3) gain compare; duplicate-edit refusal; marginal-positive
classified as exhausted (only exact 0.000 = dead edit); accepted-strategy
cone closure; accepted-edit history in prompt.
