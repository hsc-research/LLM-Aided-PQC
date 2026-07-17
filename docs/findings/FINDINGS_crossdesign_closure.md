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
