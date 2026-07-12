# FINDINGS: coeff_decomposer width narrowing (56b -> 28b)

**Verdict: ACCEPTED.** WNS -1.247 -> -1.196 (+0.051, at threshold), LUT 338 -> 268
(-21%), FF 170 -> 142. Block gate 400/400 (sec_lvl 2+3) + full-KAT 25/25 PASS.
Commit 901a676. Latency-preserving; no gate changes required.

## Design
All six pipeline regs (a1_0..a0_2) were declared signed [55:0] while carrying
at most 26 signed bits: a1_0 holds a 6-bit map1 output, a0_0 a 24-bit
coefficient, and the decompose intermediate a0_1 is bounded by
|a0_0| + a1_max*(2^19-2^9) < 2^25 (sec_lvl 3 worst case; sec_lvl 2 smaller).
Narrowed to signed [27:0] with 2 spare bits. The prior critical path
(a1_0 -> a0_1, 13 levels, 61% logic) was a 56-bit subtract carry chain doing
~26-bit work; narrowing halves the chain.

## Bound derivation (recorded for audit)
sec_lvl 3: a1_0 <= 43 (map1 range), (2^19-2^9) = 523776, product <= 22.5M
(25 bits); a0_1 in (-23M, +17M) -> 26 signed bits. sec_lvl 2 multiplier
(2^17+2^16-2^12-2^11) = 190464, product <= 8.2M. a0_2 post-correction in
(-Q/2, Q/2). 28 bits covers all with margin.

## Policy interaction
Orchestrator policy forbids width-narrowing on PLACEMENT-SENSITIVE paths
(two prior regressions). This path was logic-bound (61% logic, 13 levels),
where narrowing attacks the carry chain directly. Refined rule: narrowing is
a valid strategy when (a) the path is logic-heavy, (b) the declared width
provably exceeds the value bound, and (c) the bound derivation is written
down before the edit.

## Residual
New worst path is di_buffer -> a1_0 (-1.196, 7 levels, 76% route): the
decomp_map1 LUT cascade, routing-bound. Different problem class (placement,
not logic); no obvious RTL lever. Block considered near its floor for
latency-preserving RTL transformations.
