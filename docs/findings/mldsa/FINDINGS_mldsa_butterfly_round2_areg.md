# FINDINGS: butterfly round-2 — INTT AREG stage (sub_r)

**Verdict: ACCEPTED.** WNS -3.280 → -2.793 ns (+0.487), fmax 120.8 → 128.3 MHz.
Cumulative vs pristine: -3.802 → -2.793 ns, 113.6 → 128.3 MHz (+12.9%).
Area: 614 → 609 LUT, 531 → 604 FF (+73, the added pipe stages), 2 DSP unchanged.
Full-KAT 25/25 PASS. Commit 61d7b8e.

## Design
Round-1 left the critical path as aj1 → subtractor → DSP A-input cone (13 levels,
-3.280). Round-2 registers the subtractor result (`sub_r`) one cycle before it
loads `ajlen2_INTT` (the DSP operand register), INTT-only: total latency INTT +2,
FNTT/MULT +1 (round-1's stage only). Retaps: aj3 pipe [5:0]→[6:0] with INTT aj5
source [5]→[6]; valid_sr 10→11 bits, INTT valido [9]→[10]; multb reads new
zeta_delay3 for INTT; butterfly2x2 z2_sr/z3_sr [9:0]→[10:0], INTT tap +1;
operation_module addrb1 addr1_sr[24]→[26], array widened [26:0], INTT pause
drain 6→8. Deterministic script: agent/mldsa/apply_butterfly_areg.py
(round-2 deltas only, applies onto committed round-1 state).

## Failure history and root cause (2 failed attempts before success)
- Attempt 1: X-propagation FAIL — z_sr loop bounds not updated with the widen.
  Rule reaffirmed: widening an array requires updating ALL loop bounds
  (initial, reset, shift).
- Attempt 2: aj2 was double-delayed (add_r AND aj3 retap). Fixed to load adder
  directly. Still FAILed with a new signature.
- Root cause (found by write-stream bisection): addrb1 retap was +1 but must be
  +2 — butterfly2x2 chains TWO butterfly stages for NTT modes, so +1 internal
  stage shifts system-visible write timing by +1 PER CHAINED STAGE. The
  INTT writeback data was byte-identical to pristine but landed one address
  slot early from write #0. Same +2 applied to the INTT pause drain (6→8).
  **General rule: total system shift = per-stage shift × chained instances,
  derived per mode.**

## Method note
Latency-agnostic stream bisection (bisect_bf_streams.py / bisect_wr_streams2.py)
localized the bug in one run after by-eye derivation failed three times: BFI
divergence at the first INTT round-2 read + WR1 compare showing
data-match/address-shift pinpointed the addr tap. Scripts construct
edited builds by RUNNING apply scripts fresh (never copying) after a prior
silent-overwrite incident. This bisection loop is now being automated in
orchestrator_latency.py (divergence-guided repair).

## Dead code note
`add_r` registered but unconsumed (attempt-2 leftover) — remove in a later
cleanup pass; left in place to keep anchors stable.
