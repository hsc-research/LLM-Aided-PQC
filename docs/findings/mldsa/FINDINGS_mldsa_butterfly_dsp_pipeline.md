# ML-DSA butterfly: First Latency-Changing Win (DSP Output Pipelining) via the Full-KAT Outer Gate

This documents the project's first successful latency-changing optimization
— the tier that per-block lockstep gates cannot verify and that the
full-KAT xsim outer gate (FINDINGS_mldsa_fullkat_gate.md) was built to
unlock. butterfly.v was closed in the latency-neutral era as
DSP-latency-bound; this session re-opened it with a +1-cycle multiply
pipeline and landed WNS -3.802 -> -3.280 (fmax 113.6 -> 120.8 MHz),
verified functionally correct through the ENTIRE keygen pipeline, 25/25
NIST KATs, all three security levels. Also documented: the root cause of
the three prior gate FAILs, a debugging-infrastructure failure that
produced false all-clear signals, and one reverted follow-up attempt.

---
## 1. The edit set (3 files, deterministic apply scripts, committed)
All edits live as re-runnable scripts (agent/mldsa/apply_*.py), each
using assert count==1 anchors with exact-byte probing for trailing
whitespace (three anchors in the pristine sources have trailing spaces
after `else` / inside case branches — probe with python repr() first,
always).
- **apply_butterfly_dsp.py** (butterfly.v): insert `mult_p` register
  between `mult_result` and `barrett_datai` (maps toward DSP48E1 PREG),
  +1 cycle on the multiply path; widen aj3 delay pipe [4:0]->[5:0];
  retap FNTT (aj3[4]->[5], valido [7]->[8]), INTT (aj3[4]->[5], valido
  [8]->[9]), MULT (aj3[3]->[4], valido [7]->[8]); ADD/SUB untouched (no
  multiplier on their path).
- **apply_bf2x2_zeta.py** (butterfly2x2.v): z2_sr/z3_sr stage-2 zeta
  delay lines were hardcoded to old stage latency; widened to [9:0],
  retapped FNTT tap 7->8, INTT 8->9. (MULT/ADD/SUB take zetas directly
  from zetai — unaffected, verified in source.)
- **apply_opmod_retap.py** (operation_module.v): addr1_sr writeback taps
  FNTT/INTT +2 ([21]->[23], [22]->[24], array widened [25:0]), MULT +1
  ([8]->[9]); FNTT/INTT pause-drain counters extended (6->8, 4->6); and
  — the fix that made everything pass — **MULT completion drain
  extension** (Section 2).

## 2. Root cause of the three prior FAILs: MULT completion drain
The corrected stream bisection (Section 3) plus a mode-boundary count
localized it precisely: in MULT mode the edited design emitted 1008
outputs where pristine emitted 1024 — 16 dropped beats — with the first
1063 outputs matching. Not a wrong-value bug; a completion bug.
operation_module's MULT/ADD/SUB completion logic drains on
`done_latch && valid_sr[6:0] == 0` with an 8-bit valid_sr. With valido_bf
now arriving one cycle later, `running` dropped before the final beats
returned, cutting the last outputs of every MULT operation; the missing
accumulator writes then corrupted everything downstream (hence total
KAT corruption from KAT#0 pk byte 33, wrong_count ~334k — the same
signature class as the deliberate whole-pipeline corruption validations,
which in retrospect was the tell that the failure was total desync, not
a localized arithmetic error).
Fix: valid_sr widened 8->9 bits, MULT/ADD/SUB shift and drain moved to
[7:0] (FNTT's [3:0]/[5:0] low-bit conditions untouched by the widening;
ADD/SUB completion is now one beat later, which is latency-slack on a
done signal, not a correctness change). After this single fix the
butterfly I/O streams matched pristine 3000/3000 and the full KAT passed
first try.
**Transferable lesson:** when adding pipeline latency to a block, audit
not just data/valid alignment but every *completion/drain* condition in
the consuming FSM — a drain window sized to the old latency silently
truncates the final transactions, and the failure signature (total
corruption) misleadingly points at data-path bugs.

## 3. Debugging-infrastructure failure: the false bisection (process negative)
Mid-investigation, a stream-level bisection harness (compare butterfly
I/O between pristine and edited runs, latency-agnostic) reported clean
100% matches on a design that demonstrably failed the KAT — because a
mv/cp sequencing bug caused the "edited" comparison copies (staged in a
parked/ directory) to silently hold pristine content. Both "sanity PASS"
and "edited PASS" that session were pristine-vs-pristine and proved
nothing. Caught by a byte-size check (parked/ files exactly matched
pristine sizes). Corrected harness (bisect_bf_streams.py, committed)
constructs the edited design by RUNNING the apply scripts into the debug
directory and asserts the presence of edit markers (grep counts) before
trusting any comparison. parked/ was deleted.
**Protocol addition (now standing):** before interpreting any
comparison involving copied/moved files, verify edit-marker presence via
grep in the actual files compared — not just gate PASS/FAIL. Two
consecutive false all-clears came from skipping this.

## 4. Result and verification chain
- Full-KAT: 25/25 PASS, sec_lvl 2/3/5, 68.3 s (batch-mode xsim).
- OOC synth (mldsa param_set): 613 LUT / 513 FF / 2 DSP / WNS -3.802
  baseline -> 614 LUT / 531 FF / 2 DSP / **WNS -3.280, fmax 120.8 MHz**
  (+0.522 ns, +7.2 MHz, +18 FFs, +1 LUT).
- Critical path moved from the DSP M+ALU output cone to the DSP A-input
  cone: `aj1 -> (adder/subtractor INTT compute) -> mult operand`, 13
  levels, 58% route. The multiply output register was absorbed as
  intended; the input side is the next frontier.

## 5. Reverted follow-up: sign-select on butterfly's subtractor
The new critical cone runs through
`subtractor = (subb > suba) ? sub_tmp - subb : suba - subb`. Applied the
validated sign_select pattern (one signed subtract, sign bit selects +Q
correction). Full-KAT 25/25 PASS, -41 LUTs (614->573), but WNS regressed
-3.280 -> -3.354 and the path deepened 13 -> 17 logic levels. Reverted.
**Prior refinement:** sign_select wins when it replaces a compare plus
two INDEPENDENT subtracts (rejection_y: compare and both subtracts were
parallel structures feeding a mux). It loses when the +Q correction must
SERIALIZE after the full-width subtract on the critical operand — the
pristine parallel dual-subtract-then-mux is faster there. The
orchestrator's sign_select entry should carry this distinction.

## 6. Next step (designed, not attempted): DSP input-register stage
Path #1 now terminates at mult_p0/A. Completing the DSP pipeline means
registering the multiply operands (toward AREG/BREG), i.e. +1 more cycle
on the multiply path (total +2 vs pristine). Mechanically this is a
second round of exactly the Section-1 retaps (aj3 pipe +1 again, valido
taps +1 for FNTT/INTT/MULT, bf2x2 zeta taps +1, opmod addr1_sr taps +1
and drains re-checked) — the apply-script pattern makes this a
contained, re-derivable edit. Expected gain: the remaining input-cone
share of the ~4 ns DSP-era path. The MULT drain lesson (Section 2)
applies again verbatim: re-audit every completion window.

## 7. State
Committed: 3-file edit set, apply scripts, corrected bisection harness,
full_kat_gate.py improvements (per-vector JSON logging, timeout
handling), synthesizer repoint of butterfly to tracked mldsa_src.
Reverted, documented here: sign-select subtractor attempt.
The latency-changing tier is open and has its first win; the
verification methodology (block bisection + full-KAT outer gate +
apply-script determinism) survived a real debugging crisis intact.
