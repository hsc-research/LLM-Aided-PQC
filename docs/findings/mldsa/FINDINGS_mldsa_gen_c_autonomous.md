# Findings: gen_c (SampleInBall) — first fully autonomous optimization campaign

Target selected by scout (no human choice): worst untouched-block WNS,
-5.233 ns @ 200 MHz OOC, 2141 LUTs. Source: GMU/Beckwith ML-DSA, gen_c.v.
All runs: orchestrator v1, human only pressed enter and reviewed diffs.

## Gate construction (protocol pitfall #1 replayed and caught)
Lockstep TB: scripted Keccak driver, sec_lvl {2,3,5} x modes {sign,verify},
6/6 completion coverage guard. FIRST-PASS GATE WAS BOUNDARY-BLIND:
<= -> < corruption of the Fisher-Yates accept compare PASSED, because the
equality case (sample_addr == sample_no, ~1/256 per sample under uniform
bytes) never occurred in short runs. Live-branch corruption (sign-encoding
swap) failed correctly, proving the blindness was narrow. Fix: whitebox
boundary injection — 25% of cycles set all dout bytes to REF's current
sample_no, guaranteeing equality accepts. Post-fix: self-check PASS, both
corruptions FAIL. Third instance of the rule: a PASS from an
unvalidated gate is worthless.

## Run 1: unsound flag-precompute REJECTED autonomously
Model proposed registering the accept compare (sample_addr <= sample_no)
one cycle early. The edit assumed sample_no+1 unconditionally (wrong on
reject) and the flag was uninitialized on the first S_SAMPLEC cycle. This
is the same-cycle-consumption trap class that was KAT-fatal in HQC
fixed_weight_ct — the decision's consumers (sample_no, C_POLY) update as
functions of the decision in the same cycle, so naive precompute mispairs
decision k-1 with candidate k. The boundary-validated gate FAILED it;
auto-reverted. Had the gate remained boundary-blind, this edit could have
passed and synthesized as a fake win.

## Run 2: max_fanout=16 on dout_buffer — ACCEPTED
WNS -5.233 -> -5.029 (+0.204 ns), LUTs 2141 -> 2147 (+6, replication).
Gate PASS. Committed.

## Run 3: dead synonym attribute — auto-reverted
Model re-proposed fanout limiting via Synplify pragma (syn_maxfan) on the
already-attributed register; Vivado ignores it; exactly +0.000; reverted.
Led to orchestrator improvement: accepted-edit history now included in
the prompt, and an accepted strategy is closed for its cone.

## Run 4: no_action — campaign closed
Model correctly concluded the residual cone is exhausted for
latency-neutral single edits.

## Cone analysis
S_SAMPLEC implements an in-place Fisher-Yates swap: 256-way read mux
(C_POLY[sample_addr]) + compare + 256-way write decode, serially dependent
cycle to cycle. The -5.0 ns residual is architectural (RMW on a 256-entry
2-bit register file at 5 ns); closing it requires latency or memory-mapping
changes outside the latency-neutral contract. Documented ceiling, not failure.

## Autonomy claim (for IEEE consolidation)
- Target: machine-selected (scout WNS ranking)
- Strategy + edit: model-selected from validated policy menu
- Correctness: machine-enforced (corruption-validated lockstep gate)
- Accept/revert: machine-decided (MIN_GAIN threshold)
- Human role: gate corruption-validation review, diff review, commits
