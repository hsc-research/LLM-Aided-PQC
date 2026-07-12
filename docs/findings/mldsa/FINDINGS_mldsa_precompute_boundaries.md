# ML-DSA Session: ENCODE_LVL / ge-Flag Precompute Wins and the Boundary Conditions of the Precompute Pattern

Two committed wins (decoder -4.756 -> -4.482, rejection_y -4.230 ->
-3.511), four documented negatives, and — the transferable output — a
sharpened statement of exactly when the precompute pattern (gen_c's
sample_addr generalization of flag_precompute) works and when it fails.
All results full-KAT 25/25 verified where kept; every negative reverted.

---
## 1. Win: decoder ENCODE_LVL precompute (committed)
Critical path was encode_mode -> ENCODE_LVL casex decode -> 192-bit
`SIPO_IN >> 4*ENCODE_LVL` barrel shift, 15 levels, -4.756. Since
`encode_mode <= encode_modei` every cycle, ENCODE_LVL is a pure function
of a value available one cycle early: a parallel registered casex on
`{sec_lvl, encode_modei}` produces `ENCODE_LVL_r`, provably equal to
ENCODE_LVL every cycle, and the shifter consumes the registered copy
(`SIPO_IN >> {ENCODE_LVL_r, 2'b00}`). The combinational ENCODE_LVL and
the per-mode coefficient transforms are untouched (other consumers).
Block gate PASS, full-KAT 25/25, **WNS -4.756 -> -4.482** (+0.274),
LUTs ~flat. Note the contrast with the earlier dead-edit finding on
rejection_y's literal-assigned shifter: here the shift amount reaches
the shifter through a 6-bit decoded variable with mode fanout, and the
15-level report proved Vivado had NOT collapsed it — the
literal-vs-computed classifier cue correctly predicted this one would
pay while that one was dead.

## 2. Win: rejection_y ge-flag precompute (committed)
Residual path (post all prior rejection_y wins) was sipo_in_len ->
threshold compares (>= 1/2/3 x RDI_SAMPLE_W, RSW sec_lvl-dependent) ->
SHIFT_IN_AMT select + lane-valid masks -> 80-bit SIPO_IN merge, -4.230.
The exact expression registered into sipo_in_len
(`sipo_in_len_next - SHIFT_IN_AMT`) is fully computed each cycle, so the
three comparisons were registered from it one cycle early (ge1/2/3_r,
value-identical by construction; reset branch clears them to match
len=0). Block gate PASS, full-KAT 25/25, **WNS -4.230 -> -3.511**
(+0.719, fmax +12%), +18 LUT / +29 FF. Largest single-edit timing win
since gen_c's sample_addr.

## 3. Negative: decoder one-hot mode select (reverted)
Attempted increment 2 on decoder: register an 8-bit one-hot branch
select from {sec_lvl, encode_modei} and rewrite the transform casex to
dispatch on it. Gate PASS, full-KAT 25/25 PASS — and WNS regressed
-4.482 -> -4.849. Vivado's native handling of the pattern-form casex
(parallel-case extraction) beats a hand-rolled one-hot dispatch.
**Prior:** do not restructure casex dispatch forms that synthesis
already optimizes; precompute the *data* consumed by branches, not the
branch-selection encoding.

## 4. Negative: rejection_s ge-flag port (reverted)
The identical ge-flag edit ported to rejection_s (same SIPO family, same
len-compare structure): gate PASS, full-KAT 25/25, WNS -2.486 -> -2.476
— noise. rejection_s's critical cone is the output-side
SIPO_IN -> sipo_out_in transform -> SIPO_OUT merge; the len compares are
present but not binding there. **Prior:** the precompute lever pays only
when the precomputed comparison is ON the binding path — verify with the
path report before porting a win across the family; structural
similarity of the RTL does not imply the same binding constraint.

## 5. Negative: usehint ctr_hit precompute (reverted)
usehint's critical path is a ctr self-loop (9 levels) through
`(ctr+1)*8 > hint_addrlen+num_hints` in ctr_next's select. Registered
`ctr_hit_r` from ctr_next (the gen_c move). Gate PASS, full-KAT 25/25 —
WNS regressed -2.542 -> -3.212. Root cause: ctr_next IS the critical
loop's endpoint; computing f(ctr_next) into a register serializes the
multiply-compare AFTER the loop's existing depth instead of in parallel
with an independent copy. **This is the sharpest boundary condition of
the pattern: precompute-from-X_next helps only when X_next is a parallel
copy of state (gen_c's dout_buffer, rejection_y's len expression), never
when X_next is itself the critical loop variable.** The orchestrator's
flag_precompute/addr_precompute entry should test whether the precompute
source lies on the reported critical loop before proposing.

## 6. Negative with reusable methodology: rejection_s output skid buffer
First attempted latency-changing edit on the rejection family: a
registered output stage (samples_r/valid_r with ready_int = ~valid_r |
ready_o), +1 output latency, internal credit loop (valid_int/ready_int/
sipo_out_len) completely untouched. Full-KAT 25/25 PASS — the skid
methodology works and never destabilized the handshake (the risk that
made this family look redesign-class). But WNS -2.486 -> -2.493: zero
gain, because the binding cone is the INTERNAL SIPO_IN -> SIPO_OUT
merge, which sits entirely before the new register. Reverted.
**Two takeaways:** (a) the skid-buffer recipe is now a proven-safe way
to add interface latency to a handshaked block without touching its
credit accounting — reusable wherever an interface (not internal) cone
binds; (b) the rejection family's honest closure label is
internal-merge-bound: gaining here requires splitting the SIPO_OUT merge
itself, which drags the same-cycle credit loop (valid/ready/len are
mutually dependent combinationally) — redesign-class, confirmed by
evidence rather than assessment alone.

## 7. Board after this session (WNS, Artix-7 OOC, 200 MHz target)
makehint -0.633 | coeff_decomposer -1.196 | rejection_s -2.486 (closed:
internal-merge-bound) | usehint -2.542 (closed: ctr-loop, precompute
inapplicable) | butterfly -2.793 (closed) | rejection_a -2.857 (closed:
family) | gen_c -3.307 (residual: FSM cstate -> C_POLY 256-way CE fanout,
81.9% route — one untried lever noted: fanout control on cstate or a
registered write-strobe; next session candidate) | rejection_y -3.511
(improved this session) | decoder -4.482 (improved this session;
residual is the per-mode coefficient transform cone).
