# FINDINGS: Keccak (shared PQC primitive) — transfer probe, correct refusal after full exploration

Target: HQC Keccak/SHAKE core (keccak_top, Verilog), registered as keccak_hqc.
Baseline -1.898 ns / 145.0 MHz, 4970 LUT. This is the symmetric permutation
shared by ALL PQC schemes (SHA-3/SHAKE), so a result here speaks to every
NIST candidate, not just HQC/ML-DSA.

## Autonomous run (transfer orchestrator, ML-DSA policy verbatim + HQC KAT)
Critical path: data_path/state_ram raddr_low/high_reg -> 25 distributed-RAM
lane SP ports (7 levels, 76% route). A narrow address register broadcasting
across the 25-lane state array.

With auto-exclusion of prior failures, the agent explored the full applicable
menu across three runs (~$0.07 total):
- max_fanout_16: KAT PASS, WNS -1.898 -> -2.130 (-0.232, REGRESSED, reverted).
  Consistent with the load-profile negative direction: replication regresses
  on distributed-RAM macro address ports (macro pins, not fabric CE banks).
- memory_retarget: KAT PASS, +0.000 (no-op; tool ignored/undid the restructure),
  reverted.
- no_action: correctly refused, citing both viable strategies exhausted.

Arithmetic strategies (sign_select, constant_lut, width_narrowing) are
inapplicable by construction: Keccak is XOR/rotate only.

## Conclusion
The Keccak state-RAM critical path is placement/memory-bound, not
RTL-addressable by the current strategy menu. This is a CORRECT REFUSAL after
genuine exploration, not a null result: right target, right candidate levers,
KAT-gated attempts, honest termination. Transfer holds on the shared primitive.

## Policy refinement (candidate rule from this negative)
max_fanout is excluded on distributed-RAM / block-RAM MACRO address or select
ports (SP/I pins of *_reg RAM primitives): replication cannot shorten macro-pin
broadcast and regresses. This extends the existing load-profile rule (which
covered heterogeneous fabric loads) to memory-macro loads specifically.
