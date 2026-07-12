# Transfer v1: First Autonomous Cross-Design Win (HQC decap, +0.726 ns, $0.037) and the POLICY v2 Butterfly Validation

Covers the queued validation runs from the prior handoff plus their
follow-ups: the first fully autonomous cross-design transfer win, two
honest marginal reverts confirming block floors, the POLICY v2
rendezvous-rubric result on butterfly, two orchestrator tooling fixes,
and two prior refinements. All commits pushed.

---
## 1. THE TRANSFER WIN: decap v_minus_uy flag_precompute (autonomous)
After the resolver fix (Section 4), the transfer orchestrator — running
the ML-DSA-derived POLICY verbatim against HQC, a design none of the
priors were derived from — targeted decap's top path
(uv_addr_1_reg -> POLY_MULT dshift, route-heavy) and proposed a
textbook flag_precompute: register the two OOB comparisons
(`uv_addr_X > (X+X%2)/2 - 1`) in parallel with the address registers
they read (same source, same edge, value-identical), swap the two
combinational consumers to the registered flags. Applied clean, HQC KAT
PASS, **WNS -2.233 -> -1.507 (+0.726 ns)**, one API call, **$0.037**.
Committed (12d930d). This is the project's first autonomous
cross-design win and the paper's transfer headline: priors mined from
one design family produced a verified timing win on another,
untouched-by-humans design, at negligible cost.

## 2. Honest floors: decap rerun and encap rerun
- decap rerun on its improved residual (FSM state -> POLY_MULT dshift):
  correct profile match, clean apply, KAT PASS, WNS -1.507 -> -1.545 —
  auto-reverted at -0.038. decap is at its transfer-taxonomy floor.
- encap rerun (post two rounds of prior hardening): same honest
  -0.007 marginal revert as transfer v0 — encap's -0.247 floor is
  reproducible, not run-noise.
- fixed_weight: **timing already MET (+0.100)** — the correct outcome
  is no proposal at all; see Section 4 for the early-exit added.
HQC board final under transfer taxonomy: keygen -0.091, encap -0.247,
fixed_weight +0.100 (MET), decap -1.507.

## 3. POLICY v2 butterfly validation: rubric closed the design gap
Two runs (--retries 1 each, ~$0.15/run). Every proposal across both
runs was **output-side** (mult_p2 after mult_p, Barrett-input delay) —
the insertion-point error class that consumed 12 Sonnet calls
pre-rubric is gone; the rendezvous rubric works at Sonnet cost. The
chained-stage rule (+2 NTT / +1 MULT) was also correctly restated in
the DESIGN text unprompted. Residual failure modes observed, both
non-design: (a) mechanical anchor collisions (butterfly2x2 edit3
count=2) burning retries; (b) one applied attempt whose stream bisect
caught a real divergence at mode 3 (ADD_MODE) — the model's "ADD/SUB
unaffected" claim was wrong in exactly the drain/valido-tap class that
humans also missed in round-1, and the automated bisect localized and
auto-reverted it. Verdict for the paper: rubric closes insertion-point
selection; remaining gap is cross-file consequence tracing
(drains/taps/valid windows), and the gate+bisect safety net converts
those misses into cheap, localized negatives instead of silent wrongs.

## 4. Tooling fixes (committed)
- **FSM rename resolver**: Vivado renames FSM state regs
  (FSM_sequential_/FSM_onehot_/FSM_gray_ prefixes); the target-file
  resolver never matched the RTL declaration and fell through to the
  first source file (add_fft.v, then clog2.v — a macro header),
  producing spurious no_actions. Fixed by adding stripped-prefix
  candidates. Both prior "no_action" results on decap/fixed_weight from
  the unfixed resolver are invalid datapoints; the post-fix runs above
  supersede them.
- **Timing-met early exit**: fixed_weight was extracted and sent to the
  API despite +0.100 slack. Orchestrator now logs no_action and returns
  before any API call when WNS >= 0.

## 5. Prior refinements from this session's negatives
- dest=R (reset pins) across a register bank is NOT the CE profile:
  the original fixed_weight false-positive fanned to rd_addr_ctx/R.
- dest=D across a wide shift register (POLY_MULT dshift) is NOT the CE
  profile either, even from a narrow FSM source: decap's -0.038 revert.
  The load-profile rule's paying case is specifically homogeneous
  **clock-enable** banks; both R and D lookalikes now have measured
  counterexamples. Encode in classifier: require dest pin == CE.
