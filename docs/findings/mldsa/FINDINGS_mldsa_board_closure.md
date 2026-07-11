# ML-DSA Board Closure: butterfly, gen_a_ext, expandmask_ext Characterization

This closes out the remaining scout board. No new optimizations landed;
the value here is three characterizations that bound what latency-neutral
RTL editing can achieve on the remaining blocks, plus one dead-edit data
point refining the shifter-rewrite policy. All numbers Vivado OOC,
xc7a200tfbg676-1, 5 ns clock.

---
## 1. butterfly (and butterfly2x2): DSP-latency-bound, closed without gate
Baseline: 613 LUTs / 513 FFs / 2 DSP / WNS -3.802 / Fmax 113.6 MHz.
Top-10 paths are all one path: `zeta_delay_reg -> barrett_datai_reg`,
71.3% logic, 3 levels — the 24x24 `mult_result = multb * ajlen2_INTT`
through an unpipelined DSP48E1 (~4 ns intrinsic M+ALU delay), with a
mode mux (`modei == INVERSE_NTT_MODE ? zeta_delay2 : zeta_delay`) on the
DSP input. The fix is registering the DSP internally (MREG/PREG), which
changes latency and is out of lockstep-gate scope. The only
latency-neutral lever (retiming the input mux one stage earlier) has a
predicted ceiling of ~0.3 ns against a ~1.3+ ns gap: not worth the hours
of gate construction (5 modes x mod-q boundary batteries). Decision: no
gate built, block closed as DSP-latency-bound. `butterfly2x2` is a pure
4x instantiation wrapper (verified by grep: four `butterfly BFx_x`
instances, no own logic) and closes with it. Same closure class as
gen_c's serial RMW: the bottleneck is architectural, not expressible as
a latency-neutral RTL edit.

## 2. gen_a_ext: critical path is (closed) rejection_a, bit-for-bit
Registered in synthesizer with pristine rejection_a + sampler_a_ext deps
(pristine per the composition-study inversion that reverted rejection_a's
fanout attributes). Baseline: 1855 LUTs / WNS -2.933. Top-10 paths are
rejection_a's SIPO_IN -> SIPO_OUT shifter in *both* sampler instances at
exactly -2.933 — identical to standalone pristine rejection_a to the
picosecond. Two conclusions: (a) gen_a_ext's own orchestration logic is
timing-irrelevant; (b) no composition penalty at this level, consistent
with the earlier sampler-level study. Nothing to optimize here without
solving rejection_a's output shifter, which is characterized-closed
(8-bit sipo_out_len wraps under stall; all 256 shift amounts reachable;
documented previously).

## 3. expandmask_ext: optimized rejection_y transfers exactly; mux
rewrite of its residual is a DEAD edit
Registered with the *tracked optimized* rejection_y. Baseline: 1934 LUTs
/ WNS -4.230 — exactly rejection_y's standalone post-optimization WNS,
critical path `sipo_in_len -> SIPO_IN` inside the sampler. Wins transfer
with zero composition penalty (second confirmation of the
structural-rewrites-compose rule).
The residual path's `SIPO_IN_SHIFT = SIPO_IN >> SHIFT_IN_AMT` looked like
the last mux-reducible shifter on the board: SHIFT_IN_AMT is assigned
only the literal constants {0, RSW, 2RSW, 3RSW}, RSW in {18,20} — a
*structurally* closed 7-value set (stronger than rejection_y's earlier
probe-observed invariant). The 8-way explicit-select rewrite gate-PASSED
(43500 cyc) and synthesized to **bit-identical results** on both
rejection_y (1313/-4.230) and expandmask_ext (1934/-4.230): LUTs, FFs,
and WNS all exact. Vivado had already inferred the constant-select
structure from the original if-chain. Reverted per protocol.
**Policy refinement:** the explicit-mux shifter rewrite pays off only
when the shift amount reaches the shifter as an opaque *computed* value
(rejection_y's `sipo_in_len - SHIFT_IN_AMT` subtraction: won +0.312 ns);
when the amount is already a directly-assigned constant set visible to
synthesis, the rewrite is dead. Classifier cue for the orchestrator:
trace whether the shift-amount signal is assigned arithmetic or literals.

## 4. Board state after this session
Every scouted ML-DSA block is now optimized, characterized-closed, or
bounded:
- Wins standing: makehint (-3.511 -> -0.633), rejection_s (-4.013 ->
  -2.486), rejection_y (1588/-4.470 -> 1313/-4.230), gen_c max_fanout
  (+0.204), decoder max_fanout (+0.050), sub_val (-24 LUTs).
- Closed, characterized: coeff_decomposer/decomp_map1 (placement-coupled,
  5 negatives), rejection_a output shifter (overflow-states
  load-bearing), butterfly/butterfly2x2 (DSP-latency), gen_c residual
  (serial RMW), decoder residual (ENCODE_LVL barrel cone), usehint
  (0 net; hint_offset priority-encoder lead remains, guided-only).
- Composites: gen_a_ext, expandmask_ext, sampler_s/y/a — all inherit
  block-level ceilings exactly; no composite-level logic is critical.
Latency-neutral RTL editing on this board is exhausted. Remaining
directions are out-of-scope interventions (DSP pipelining with
latency-tolerant verification, placement constraints, the usehint
priority-encoder guided rewrite) — all candidates for the paper's
future-work section rather than this campaign.
