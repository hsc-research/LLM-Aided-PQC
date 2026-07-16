# FINDINGS: flow-space directive search (roadmap Vector 1)

Method: synthesize once, write checkpoint, sweep place_design x phys_opt_design
x route_design directives reusing the checkpoint (agent/flow_sweep.py). One
synth + N fast impls instead of N full runs. combined_top optimized, -1 grade,
5.0 ns constraint.

| place / phys_opt / route | WNS | fmax |
|---|---|---|
| Default / Default / Default (baseline) | -8.766 | 72.6 MHz |
| **Explore / Explore / Explore** | **-8.497** | **74.1 MHz** |
| ExtraNetDelay_high / AggressiveExplore / Explore | -8.505 | 74.0 MHz |
| ExtraPostPlacementOpt / AggressiveExplore / AggressiveExplore | -8.983 | 71.5 MHz |

Result: best directive set (all-Explore) gives +1.5 MHz (+2.1%) over default,
ZERO RTL change. Two findings:
1. More aggressive directives did NOT help and several regressed; the tools'
   default heuristics are already near-optimal, and Explore's broader search
   beats Aggressive's narrower/greedier one at this design size.
2. This is a single constraint point (5.0 ns). Directive headroom is expected
   to be larger at looser constraints (8.62 ns / -3, the GMU-comparable corner)
   where the router has slack to exploit — a follow-up sweep should confirm.

Observation from logs: phys_opt autonomously replicated FSM-state nets
(cstate0_reg _rep) — the same fanout-replication lever our RTL max_fanout rule
applies, but at implementation stage. Corroborates the FSM-fanout finding and
shows the flow tier and RTL tier attack the same physical problem from two
ends.

## Significance
Establishes a THIRD optimization tier: the agent optimizing the implementation
FLOW, not just the RTL. Novel vs. the LLM-for-EDA literature, which optimizes
or generates RTL only. The sweep infrastructure is reusable and the log feeds
the dashboard.

## Second sweep: GMU-comparable corner (-3 grade, 8.62 ns)
| place / phys_opt / route | WNS | fmax |
|---|---|---|
| Default (single-point baseline) | -1.779 | 96.2 MHz |
| AltSpreadLogic_high / Explore / AggressiveExplore | -1.362 | 100.2 MHz |
| **ExtraPostPlacementOpt / AggressiveExplore / AggressiveExplore** | **-1.235** | **101.5 MHz** |

Directive search recovered +5.3% here (96.2 -> 101.5) vs +2.1% at the 5.0 ns
stretch corner — confirming the prediction that directive headroom scales with
constraint slack.

CONSTRAINT-DEPENDENT OPTIMUM (finding): at the tight 5.0 ns corner, aggressive
directives REGRESSED and all-Explore won; at the loose 8.62 ns corner,
aggressive directives WON. There is no universally-best directive set; the
optimal flow depends on the constraint. This is exactly the search space a
frequency-target-iterating flow (GMU's Minerva) explores.

GMU gap status: 96.2 -> 101.5 MHz closes the directive component. Residual to
their 116 MHz (~12.5%) is now attributable to constraint-target search
(Minerva iterates the target period itself, not just directives) — the one
lever we have not yet applied. Cost note: the winning aggressive combo ran
2.3 hours; the +5% carries a real wall-time cost worth stating.

## Constraint-target sweep (-1 grade, default directives) — NULL result
| Target period | WNS | Achievable fmax |
|---|---|---|
| 8.0 ns | -6.201 | 70.4 MHz |
| 8.62 ns | -5.874 | 69.0 MHz |
| 9.0 ns | -5.410 | 69.4 MHz |
| 9.5 ns | -5.291 | 67.6 MHz |
| 10.0 ns | -4.334 | 69.8 MHz |

Achievable fmax is flat at ~68-70 MHz regardless of target period on this
fabric with default directives. Constraint-target search alone does NOT help
here — the -1 Artix-7 fabric floor dominates. Conclusion: the Minerva-style
gain on our part comes from DIRECTIVES (captured: +5.3% at -3), not from
constraint-target iteration. This is a checked null result, not an omission.

## GMU gap — final decomposition
1. Speed grade -1 -> -3: the dominant factor (68.5 -> 94.1 MHz).
2. Directives: +5.3% (96.2 -> 101.5 MHz at -3).
3. Constraint target: negligible on our fabric (this sweep).
4. Residual to GMU's 116 MHz: DEVICE FAMILY. GMU's ML-DSA-OSH reports on
   ZCU102 (UltraScale+), a substantially faster fabric than our Artix-7.
   VERIFY exact device in their paper; if confirmed, the residual is largely
   device-family, and the honest framing is "comparable frequency on a slower,
   lower-cost part," not a methodology deficit.

## Policy hygiene validation (post-Keccak rules live)
Re-ran the ML-DSA orchestrator on decoder and rejection_s with the
Keccak-derived RAM-macro exclusion in POLICY. Both returned correct no_action:
rejection_s citing the wide-SIPO load-profile rule, decoder additionally
reasoning through constant_lut (correctly identified the 8-value ENCODE_LVL
domain within the cap, correctly rejected on route-domination) before
terminating. The refinement loop is closed: a rule learned on HQC's Keccak now
governs ML-DSA proposals. Cost ~$0.05.

## Flow-parity fairness study (pristine sweep, 5.0 ns, -1)
Pristine best across the same 7 combos: 72.2 MHz (ExtraNetDelay_high/
AggressiveExplore/Explore) vs optimized best 74.1 MHz (all-Explore).

Two honest claims, different questions:
- Default flow both variants: 65.3 -> 72.6 MHz (+11.2%) — RTL contribution
  under identical default implementation.
- Best-searched flow both variants: 72.2 -> 74.1 MHz (+2.6%) — RTL
  contribution surviving flow parity.

INTERACTION FINDING: directive search recovers +10.6% on pristine but only
+2.1% on optimized — the RTL edits and the flow search partially consume the
SAME slack (both attack routing pressure on the binding cone). RTL wins and
flow wins do not compose additively; report both corners, never their sum.
Reviewers should see the flow-matched number (+2.6%) alongside the
default-flow number (+11.2%).

## Flow-parity fairness study (pristine sweep, 5.0 ns, -1)
Pristine best across the same 7 combos: 72.2 MHz (ExtraNetDelay_high/
AggressiveExplore/Explore) vs optimized best 74.1 MHz (all-Explore).

Two honest claims, different questions:
- Default flow both variants: 65.3 -> 72.6 MHz (+11.2%) — RTL contribution
  under identical default implementation.
- Best-searched flow both variants: 72.2 -> 74.1 MHz (+2.6%) — RTL
  contribution surviving flow parity.

INTERACTION FINDING: directive search recovers +10.6% on pristine but only
+2.1% on optimized — the RTL edits and the flow search partially consume the
SAME slack (both attack routing pressure on the binding cone). RTL wins and
flow wins do not compose additively; report both corners, never their sum.
Reviewers should see the flow-matched number (+2.6%) alongside the
default-flow number (+11.2%).

## Tier-3 validation: agent-driven flow search (first run)
4 autonomous calls, $0.016: proposed ExtraTimingOpt (97.1, new family probe),
then EXPLOITED the AltSpreadLogic family -> AltSpreadLogic_medium = 101.7 MHz,
a NEW BEST (beats hand-sweep 101.5). Then SSI_SpreadLogic_low (101.5, tie),
then BalanceSLLs (invalid on Artix-7 — SSI/multi-die directive, instant fail;
vocabulary pruned). Reasoning per call was sound and history-grounded:
explore-then-exploit without being told to. Tier-3 loop validated end-to-end:
the agent optimizes the implementation flow autonomously, same untrusted-
proposal structure as the RTL tiers.

## Tier-3 breakthrough: 153.0 MHz on -3 (agent-discovered, validated)
Agent run at a 5.0 ns target on the -3 checkpoint (checkpoint-grade mixup,
made rigorous below) discovered ExtraTimingOpt/Explore/Explore = WNS -1.535 ->
153.0 MHz. VALIDATED by deterministic re-run: bit-exact -1.535 reproduction.
This beats GMU's Minerva-searched 116 MHz by 32% on the comparable speed
grade. Mechanism: the TIGHT target (5.0 ns vs 8.62) pushes placement much
harder, and ExtraTimingOpt placement had never been paired with a tight
target in the hand sweeps. The agent found the combination in call 1 and
correctly exploited the family for 3 more calls (151.4, 149.7, 148.0 — the
original stands as best). Constraint-target search is NOT null on -3 with
timing-directed placement: the earlier null was -1/default-directives only.
Checkpoints are now keyed by speed grade (post_synth_grade{N}.dcp) to prevent
grade mixups; pristine-at-same-recipe run pending for the fair delta.

## Fair delta at the breakthrough recipe (-3, 5.0 ns, ExtraTimingOpt/Explore/Explore)
| Variant | WNS | fmax |
|---|---|---|
| Pristine | -5.107 | 98.9 MHz |
| Optimized | -1.535 | 153.0 MHz |

RTL contribution under flow parity at this corner: +54.7%. The flow-RTL
interaction INVERTS between corners: at -1/5.0 flow search compressed the RTL
delta to +2.6%; at -3/5.0 with timing-directed placement the RTL edits UNLOCK
flow headroom pristine cannot reach (its deeper cones bind before
ExtraTimingOpt's placement pressure pays). Corner-dependent interaction is
now a central finding: report deltas per corner, never a single number.
vs GMU 116 MHz (Minerva-searched, -3): pristine 98.9 (-15%), optimized 153.0
(+32%).
