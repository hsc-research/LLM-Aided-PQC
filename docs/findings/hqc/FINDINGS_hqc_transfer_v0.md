# FINDINGS: cross-design transfer v0 — ML-DSA priors on HQC (first contact)

## Setup
transfer_orchestrator.py applies the ML-DSA orchestrator POLICY verbatim
(single source of truth, no re-tuning) to HQC blocks, gated by the HQC
full-KAT. Two harness bugs fixed on first runs: target-file selection now
locates the file DECLARING the critical path's source register (was matching
filenames, then the pin name).

## Result: encap/hqc128 (worst path -0.247, sel_uv 1-bit select, 74.6% route)
The model correctly recognized the load-profile HIGH-CONFIDENCE shape
(narrow flag reg -> homogeneous BRAM enable bank) learned on ML-DSA gen_c,
proposed max_fanout, edit applied cleanly, **HQC KAT PASS**, synthesized:
WNS -0.247 -> -0.254 (-0.007). Correctly auto-reverted as marginal
(netlist-noise level). Cost: $0.09, 2 calls total across runs.

## Interpretation
The transferred calculus produced a structurally correct, correctness-verified,
honestly-adjudicated decision on first contact with a foreign codebase:
right rule, right target, clean gate, truthful revert. The specific instance
didn't pay (encap is already near target at -0.247; sel_uv's loads are BRAM
macros, which replicate differently than fabric CE banks — a candidate
refinement to the load-profile rule: macro-pin banks may not respond).
Remaining HQC transfer targets: decap cones (known placement-bound, expect
no_action — itself a transfer test of the closure priors) and keygen residuals.
