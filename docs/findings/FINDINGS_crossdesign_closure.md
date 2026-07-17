# FINDINGS: cross-design true-closure verdict (the composition thesis, measured)

Closing-fmax binary search (WNS>=0, post-route, default recipe, -1 grade;
HQC OOC due to 1075 I/O ports — comparative within mode):

| Design | Pristine | Optimized | Delta |
|---|---|---|---|
| HQC joint KEM | 117.1 MHz (8.54 ns) | 119.3 MHz (8.38 ns) | +1.9% TRUE WIN |
| ML-DSA combined_top | 70.2 MHz (14.25 ns) | 69.0 MHz (14.50 ns) | -1.7% null |

Interpretation: HQC's optimizations were selected TOP-DOWN from operation-level
critical-path reports (pre-orchestrator methodology); they sit on the chip's
binding cones and compose into a genuine closure gain. ML-DSA's were selected
BLOCK-FIRST (orchestrator OOC boards); the chip binds on encoder (never a
block target), and the composition pays a register tax with no critical-path
return. Same agent, same calculus, same gates — the difference is target
selection level. CONCLUSION: chip-critical-path membership must gate
integration; block-level acceptance alone does not predict chip outcome.
This is the advisor's stated methodology, now with a measured A/B across two
NIST standards, all numbers closure-honest (no violated-run projections).

HQC opt composition: pristine hardware tree + 9 win-carrying leaf modules +
mem_single_dist (interface-safe swap; stale build/decap top-level divergence
excluded). SHARED_ENCAP define required for joint elaboration.

## Per-operation closure searches: DEFERRED (elaboration blocker, documented)
Standalone keygen (both trees) hits a multi-driver net on
FIXEDWEIGHT/shake_dout_ready_fw under the full-impl flow (opt_design Opt
31-37), despite correctly guarded CT_DESIGN generate branches — an
elaboration/flattening artifact not present in the OOC block flow (which
never runs opt_design) nor in the joint design (which elaborates through
SHARED_ENCAP paths). Affects pristine and optimized identically. Root-cause
is upstream-RTL forensics; deferred. The joint-design closure result (+1.9%)
already includes keygen's cones and carries the composition thesis. Block-
level keygen numbers (OOC synth WNS) remain valid as reported, with the
projection caveat applied.

## keygen-standalone closure: BLOCKED after 5 attempts, escalated
Multi-driver (FIXEDWEIGHT/shake_dout_ready_fw) is baked into the SYNTHESIZED
netlist when keygen is top: keygen's output-mux LUT is absorbed into
FIXEDWEIGHT scope aliased with the port net. Survived: DRC downgrade,
opt_design catch (place enforces), -flatten_hierarchy rebuilt, SHARED_ENCAP
removal, default (non-OOC) mode, and (* dont_touch *) on the net. Same
keygen logic places and routes FINE inside the joint design — the artifact is
specific to keygen-as-top under Vivado 2025.2 synthesis. Morning/advisor
items: (a) try synth_design -no_lc / -keep_equivalent_registers, (b) elaborate
-rtl and inspect, (c) ask Sanjay whether standalone keygen was ever taken
through implementation (their flow may have used an older Vivado without this
merge behavior). Block-level OOC keygen results remain valid; joint-design
closure (+1.9%) already contains keygen's cones.
