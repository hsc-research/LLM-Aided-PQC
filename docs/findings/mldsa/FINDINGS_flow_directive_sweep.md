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
