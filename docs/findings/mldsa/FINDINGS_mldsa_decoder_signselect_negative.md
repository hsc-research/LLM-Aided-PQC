# FINDINGS: decoder T0/Z sign-select — negative result, strategy now closed

**Verdict: REVERTED.** WNS -4.299 -> -4.639 (regressed 0.340ns), LUT 2226 -> 2441.
Correctness clean: full-KAT 25/25 PASS; the rewrite was bit-exact.

## What was tried
The last taxonomy-internal idea on the board: sign_select on decoder's T0 (13b)
and Z (18b/20b) compare-correct transforms — replace
(x > C) ? C + Q - x : C - x with a single signed subtract sd = C - x and select
sd[24] ? sd + Q : sd. Width/bounds audited pre-edit (all fit signed [24:0];
truncation behavior matches pristine).

## Result and interpretation
Same failure mode as butterfly's 24b case: the rewrite serializes
subtract -> sign -> conditional-add where the pristine form lets synthesis
evaluate both arms in parallel and select on the (fast) wide compare. The
"narrower operands might behave differently" hypothesis is now tested and
falsified at 13b, 18b, 20b. sign_select on compare-correct shapes is EXCLUDED
regardless of operand width; the pattern only pays where the pristine idiom is
itself serial (the >>31 sign-extract form, as in coeff_decomposer sub_val).

## Rule for orchestrator priors
sign_select applies ONLY when the pristine code computes the correction via a
sign-extract/mask idiom (>>31 & Q style). If the pristine form is already a
ternary on an explicit compare, both arms already synthesize in parallel:
proposing sign_select there serializes and regresses (n=2: butterfly 24b,
decoder 13-20b).

## Board status
decoder's transform cone: constant_lut excluded (domain width), sign_select
excluded (this result). Block residual is now confirmed
architectural/placement class. The latency-preserving taxonomy is closed on
the entire ML-DSA board under current strategies.
