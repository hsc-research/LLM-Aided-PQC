# ML-DSA coeff_decomposer / decomp_map1: sub_val Win and a Placement-Coupling Case Study

This follows on from `FINDINGS_mldsa_pipelining_coeff_decomposer.md`, whose
Section 7 next-step was the `sub_val` sign-extraction idiom on the
`a0_1 -> a0_2` path (path #2, -1.218 ns, 24 logic levels). That fix landed
cleanly. Five further restructuring attempts on the adjacent `a1_0_reg ->
a0_1_reg` path (path #1, the binding constraint throughout) and on
`decomp_map1` all failed, each for a related reason. The negative results
are documented in full since the pattern (arithmetic restructuring loses
to Vivado's existing placement on these specific paths) is a real,
reusable constraint for future work on this block.

---
## 1. Committed win: sub_val direct signed comparison
Commit `a6af6f7`. Per the prior findings doc's Section 5/7 lead, the
sign-extraction idiom
```verilog
assign sub_val = ((((Q-1)/2 - a0_1) >> 31) & Q);
```
was replaced with a direct signed comparison:
```verilog
assign above_mid = (a0_1 > 24'sd4190208);   // (Q-1)/2
a0_2 <= above_mid ? (a0_1 - 24'sd8380417) : a0_1;
```
- **Correctness:** PASS, both sec_lvls, 200/200.
- **Area:** -24 LUTs (362 -> 338).
- **Timing:** WNS unchanged (-1.247 ns). Path #1 (`a1_0_reg -> a0_1_reg`)
  was and remains the binding constraint; path #2 was successfully
  shortened but was never critical after the fix, so WNS was neutral by
  construction. Still a real, clean area win with zero risk.
All baselines below are measured against this commit's RTL
(338 LUTs / 170 FFs / WNS -1.247 ns / Fmax 160.1 MHz), i.e. current `main`.

## 2. Path #1 in detail
`path_extractor.py coeff_decomposer default 20` on baseline:
```
#1  -1.247 ns  61.8% logic  38.2% route  13 lvls  a1_0_reg[0] -> a0_1_reg[54]
#2  -1.196 ns  24.2% logic  75.8% route   7 lvls  di_buffer_reg[2] -> a1_0_reg[2]
```
Path #1 is logic-bound (13 levels, mostly logic); path #2 (decomp_map1's
output feeding a1_0) is route-bound (75.8% route, one high-fanout `din`
net feeding 45+17 parallel comparators). These are two back-to-back
pipeline stages, roughly matched in slack, with opposite bottleneck types.
This distinction drove every attempt below and, in hindsight, is also
why none of them worked in isolation.
Source cone (all in `coeff_decomposer.v`):
```verilog
reg signed [55:0] a1_0, a1_1, a1_2, a0_0, a0_1, a0_2;
...
a1_0 <= map1_out;                      // decomp_map1 output, 6 bits
a0_0 <= di_buffer;
if (sec_lvl == 2)
    a0_1 <= a0_0 - ((a1_0<<17)+(a1_0<<16)-(a1_0<<12)-(a1_0<<11));
else
    a0_1 <= a0_0 - ((a1_0<<19)-(a1_0<<9));
```
`a1_0` is a 6-bit index but declared 56-bit signed; `a0_1`'s true range is
bounded by ~±Q (24-bit). The 56-bit width was legacy/generous, not
required.

## 3. Attempt 1: decomp_map1 arithmetic-divide rewrite (route-bound path)
File: `decomp_map1.v`. Replaced 45+17 parallel `>=` comparators (all fed
by the single high-fanout `din` net responsible for path #2's 75.8% route
delay) with a closed-form arithmetic divide:
```verilog
raw = (din + gamma2) / (2*gamma2);   // + FIPS204 top-index wraparound -> 0
```
- **Correctness:** PASS, both sec_lvls, 200/200.
- **Area:** -26 LUTs (338 -> 312).
- **Timing: severe regression.** WNS -1.247 -> **-8.744 ns**, Fmax 160.1 ->
  72.8 MHz, timing not met.
- **Reverted.**
**Why:** collapsing a wide fanout tree into a divider changes the netlist
wholesale; the divider's own logic depth (and however Vivado maps `/` for
non-power-of-2 `2*gamma2`) evidently dominates far worse than the fanout
problem it was meant to fix. Route-bound diagnosis does not imply an
arithmetic rewrite is the right lever; it may just relocate the cost.

## 4. Attempt 2: path #1 width narrowing (first try, in isolation)
Narrowed only the subtract expression in path #1 to 28 bits, with
decomp_map1 still in its Attempt-1 (rewritten) state at the time.
- **Correctness:** PASS.
- **Timing:** WNS -1.247 -> -1.513 ns.
- **Reverted.**
**Why:** disturbed decomp_map1's placement (a route-bound path is
sensitive to physical position, not logic shape), confirming the two
paths are placement-coupled: an edit to one can move where the other's
registers land, even without a logic change to the second path itself.
This motivated re-testing path #1 narrowing only after decomp_map1 was
fully reverted to baseline (Section 5).

## 5. Attempt 3: a0_1 DSP inference
With decomp_map1 back at baseline, replaced the shift-add for `a0_1` with
an explicit narrow signed multiply intended to infer one DSP48E1 per
sec_lvl branch:
```verilog
a0_1 <= a0_0 - ($signed({1'b0, a1_0[5:0]}) * 21'sd190464);   // sec_lvl 2
a0_1 <= a0_0 - ($signed({1'b0, a1_0[5:0]}) * 21'sd523776);   // sec_lvl 3
```
- **Correctness:** PASS, both sec_lvls, 200/200.
- **Area:** -45 LUTs (338 -> 293), +2 DSP (0 -> 2).
- **Timing:** WNS -1.247 -> -2.475 ns, Fmax 160.1 -> 133.8 MHz.
- **Reverted.**
**Why:** an unpipelined DSP48E1 multiply-subtract (no MREG/PREG) has
~4 ns of intrinsic M+ALU delay at this width; it only beats fabric logic
when registered internally, which changes latency and was out of scope
without revisiting the cycle-exact gate contract.

## 6. Attempt 4: register width narrowing (56 -> 25 bit)
Range analysis: `a0_0` in `[0, Q)` (23-bit), max `a1_0 * 2*gamma2` term
~8.2M, so `a0_1` provably fits signed 25-bit with margin; `a0_2` fits
signed 24-bit. Narrowed `a1_0, a1_1, a1_2, a0_0, a0_1, a0_2` from
`[55:0]` to `[24:0]`. Verified no consumer (doa/dob/above_mid/`+Q`
wraparound) depends on the high bits.
- **Correctness:** PASS, both sec_lvls, 200/200.
- **Area:** -93 LUTs (338 -> 245), largest area win of the session.
- **Timing:** WNS -1.247 -> -1.549 ns, Fmax 160.1 -> 152.7 MHz.
- **Reverted.**
**Why:** same placement-coupling effect as Attempt 2, this time triggered
by the register narrowing itself rather than by decomp_map1's state.
Shrinking the flops changed how Vivado placed/packed the surrounding
logic, and the tool's prior solution for -1.247 ns was evidently closer
to a local optimum than the narrower, "more correct" netlist.

## 7. Attempt 5: product retiming (built on Attempt 4)
Hypothesis: since `valid_o` is tracked via a shift register (`valid_sr`),
latency-preserving retiming is legal (per Section 3 of the prior findings
doc). Moved the shift-add computation one stage earlier, computing it
directly off `map1_out` (6-bit) into a new register `prod`, in parallel
with `a1_0`'s own register, then reduced path #1 to a single subtract:
```verilog
prod <= (sec_lvl==2) ? shifts_of(map1_out) : other_shifts_of(map1_out);
a0_1 <= a0_0 - prod;
```
- **Correctness:** PASS, both sec_lvls, 200/200.
- **Area:** 266 LUTs, 149 FFs (between baseline and Attempt 4).
- **Timing: worst regression of the session.** WNS -1.247 -> **-4.883 ns**,
  Fmax 160.1 -> 101.2 MHz.
- **Reverted.**
**Why:** this moved the shift-add tree from after `a1_0`'s register to
before `prod`'s register, stacking it directly onto decomp_map1's own
combinational cone, i.e. onto path #2 (di_buffer -> a1_0, -1.196 ns,
already route-bound and near-critical). The retime was only valid if
`map1_out -> a1_0` had slack to absorb the extra logic; it did not.
Direct confirmation that path #1 and path #2 are not just placement-
coupled but genuinely adjacent stages of one tight two-stage pipeline:
work cannot be freely shifted between them.

## 8. Conclusion: coeff_decomposer, current state
Baseline (committed, `a6af6f7`) stands: **338 LUTs, 170 FFs, WNS -1.247 ns,
Fmax 160.1 MHz**, 0 DSP, 0 BRAM. Five independent restructuring strategies
were tried against path #1 and/or decomp_map1's path #2:
1. Arithmetic-divide rewrite of decomp_map1 (route-bound path) -> -8.744 ns
2. Path #1 width narrowing, decomp_map1 not yet reverted -> -1.513 ns
3. DSP inference (unpipelined) -> -2.475 ns
4. Path #1 register narrowing alone (decomp_map1 at baseline) -> -1.549 ns
5. Product retiming onto path #2's cone -> -4.883 ns
Every attempt that touched either path's logic shape regressed WNS,
despite three of them (1, 3, 4) producing legitimate area wins in
isolation. The consistent explanation: Vivado's existing placement for
this specific -1.247 ns solution is a strong local optimum that
LUT-count-driven or shape-driven rewrites keep destroying, and paths #1/#2
are tightly coupled adjacent pipeline stages, not independent targets.
**Recommendation for whoever picks this up next:** do not attempt further
logic restructuring on path #1 or decomp_map1 without also constraining
placement explicitly (e.g. `LOC`/`RLOC` directives or Vivado
`sweep_opt`/directive changes on this specific region), which is a
different intervention category from everything tried this session. Bank
this as a well-characterized negative-result case study: coeff_decomposer
at 200 MHz target is optimized-as-is under the RTL-restructuring taxonomy
used throughout this project; -1.247 ns WNS is not currently closable by
pure Verilog editing under 200 gate-passing, honestly-tried candidates.

## 9. Toward an autonomous agent
The loop followed this session (backup -> str-replace with assert count==1
-> `mldsa_block_gate.py` -> `synthesizer.py` -> compare WNS/LUTs -> commit
or revert-and-document) is already fully mechanical; every script needed
exists. What is missing is a decision policy, and this session supplies
concrete priors for it: (a) `path_extractor.py`'s logic%/route% split
should classify a path before choosing a strategy family; (b) arithmetic
rewrites on route-bound paths and unpipelined DSP mapping on tight
sub-2ns budgets both reliably fail here; (c) two adjacent pipeline stages
with comparable slack should be treated as a joint optimization target,
not attempted independently, after Attempt 5's result. These negative
results are the natural seed for a search-space-pruning policy in a
future autonomous version of this pipeline.
