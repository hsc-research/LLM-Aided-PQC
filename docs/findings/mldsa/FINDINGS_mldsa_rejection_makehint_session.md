# Findings: ML-DSA rejection_a/s/y + makehint optimization session

Target: Artix-7 xc7a200tfbg676-1, 200 MHz OOC. All results lockstep-gate-verified
(sec_lvl epochs {2,3,5}, corruption-validated gates) and committed.

## Results summary

| Block | WNS before | WNS after | Fmax | LUT delta | Strategy |
|---|---|---|---|---|---|
| makehint | -3.511 | -0.633 | 117.5 -> 177.5 MHz (+51%) | — | flag-precompute + registered prefix sums |
| rejection_s | -4.013 | -2.486 | 111 -> 133.6 MHz | -138 | 16-entry constant LUT |
| rejection_y | -4.470 | -4.230 | — | -251 (1588 -> 1313) | sign-select + explicit 14-way shifter |
| rejection_a | -2.933 | -2.857 | — | — | max_fanout=16 on SIPO regs |

## makehint (biggest win of project)
Two commits. (1) Registered `hint_needed` from pre-register `poly_ie` inputs
(flag-precompute: compute the decision in the same clocked block that registers
the data, so the CE decode on `hint_addr` sees a 1-level flag instead of a
7-level compare cone). (2) Registered prefix sums (hn_off1-3, hn_total).

## rejection_s
Case-map + add + mux sample chain has a 4-bit input domain -> replaced with a
16-entry constant LUT. -138 LUTs, +1.527 ns.

## rejection_y
(1) Sign-select sample computation: -251 LUTs, WNS-neutral — critical path
disjoint, verified by path extraction BEFORE keeping (LUT win accepted under
WNS-neutrality rule). (2) Explicit 14-way input shifter exploiting the
eff-shift ∈ {0,2,...,26} invariant. Invariant is probe-observed + gate-verified
(43500 cycles), NOT formally proven — noted in commit.

## rejection_a
max_fanout=16 on SIPO_IN/sipo_out_len: -2.933 -> -2.857. Negative result on
its output shifter: sipo_out_len (8-bit) wraps under stall, all shift amounts
0-255 reachable — load-bearing overflow states, mux-reduction impossible.

## Methodology notes (gate-construction pitfalls caught this session)
1. Boundary-value stimulus gaps (makehint): <= -> < corruption passed until
   exact-boundary constants were added to stimulus. Corruption-validate every gate.
2. Functionally masked corruption (rejection_y): chosen corruption was a dead
   distinction; replaced with +1 on a live arithmetic branch. A PASS from an
   unvalidated gate is worthless.
3. Shifter probes: registered sampling at consumption, never $display in
   always@(*) (combinational glitch pollution).

## Validated policy additions
- Compare-on-registered-inputs feeding CE decode -> flag-precompute (n=3 now,
  incl. HQC fixed_weight_ct; best-performing pattern).
- <=4-bit-domain arithmetic -> constant-LUT collapse (n=1).
- Compare-then-conditional-subtract -> sign-select (n=2).
- Variable shifter mux-reduction requires PROVEN-closed reachable set
  (worked: rejection_y input; impossible: rejection_a output).
- max_fanout=16 on source registers only; never combinational always@(*) regs
  (regressed both attempts); 8 overshoots.

## Follow-up
Orchestrator v1 (commit aa56252) autonomously re-derived the makehint
flag-precompute from pristine: -3.511 -> -0.640 (+2.871 ns), within 7 ps of
the hand result — first end-to-end autonomous validation of the policy.
