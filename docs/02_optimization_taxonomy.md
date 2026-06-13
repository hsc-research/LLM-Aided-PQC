# Optimization Taxonomy

This document records the classification of optimization patterns used in the
project, the synthesis fingerprints that predict whether a given pattern will
help or hurt a particular critical-path cluster, and the negative results that
bound the patterns. The goal is a reusable theory: given a critical-path
cluster, decide which transformation (if any) applies before editing RTL.

## The transformations

### Face 2b — Precompute-by-increment (the flag)

**Pattern.** A combinational comparison on a counter, for example
`count < LIMIT`, sits in a critical path. The counter is updated only at a small
number of statically enumerable sites (resets to a constant, increments,
decrements). Introduce a registered flag that is recomputed from each site's
right-hand side at the moment the counter is written, and replace the
combinational comparison with a read of the flag.

**Why it works.** The comparison is evaluated one cycle early, when the counter
value is already being computed for the write, and its result is stored in a
flip-flop. The critical path then reads a register output instead of evaluating
a comparator made of LUTs.

**Correctness.** The flag equals the comparison on the counter's value by
induction over the counter's assignment sites: the base case is the reset value,
and each update site recomputes the flag from the same expression that produces
the new counter value. Non-monotonic counters (those with a decrement) are fine,
because the flag is recomputed from the actual new value at every site rather
than assumed to move in one direction.

**Applies regardless of assignment style.** The pattern works for both
nonblocking counters (`count <= count + 1;`) and blocking counters inside a
single clocked block. For a blocking counter, the flag update is placed
*after* the counter write and reads the post-update value directly.

### Strength reduction — incremental function of a counter

**Pattern.** The generalization of Face 2b from comparisons to any value that is
a pure incremental function of a counter. The canonical case in this project was
a combinational divide-by-constant, `addr = counter / COPIES`, where `COPIES` is
3 or 5. A non-power-of-two divider synthesizes to a subtract/compare ripple that
showed up directly in the delay table as a bit-by-bit carry chain.

**Transformation.** Maintain the quotient and a small remainder counter that are
updated in lockstep with the source counter (the remainder wraps at `COPIES` and
carries into the quotient). The combinational divider is removed from the netlist
entirely.

**Correctness.** Quotient equals `counter / COPIES` and remainder equals
`counter % COPIES` by induction over the counter's sites. Output-width
truncation at the consumer is identical to the original divide.

### Face 3 — Memory retargeting (block-RAM to distributed)

**Pattern.** A memory that is small, or that sits inside a tight feedback loop,
occupies a block-RAM primitive but is bottlenecked by block-RAM access timing.
Retarget it to distributed (LUT) RAM by changing the RAM-style attribute on a
dedicated module variant.

**Where it helps and where it hurts.** This is the pattern with the sharpest
sign-dependence on path direction, described under fingerprints below.

## Fingerprints — predicting help vs. regression

The delay table from a per-path timing report is the ground truth. Read it
before theorizing.

### Flag / strength-reduction wins

- **Predictive of a win:** the comparison or divider appears as a multi-level
  LUT chain at the head of a logic-bearing cone. The flag collapses several
  logic levels into one register read.
- **Predictive of a marginal result or regression:** the comparison is already
  a single shallow decode (for example 4 logic levels at roughly 25 percent
  logic delay, the rest routing). Here the flag removes very little logic, and
  the added fan-out of the flag's update assignments across the counter's
  always-blocks can cost more routing than the decode saved. A logic-light,
  routing-dominated cone is not a flag candidate even when a comparison is
  present.

### Memory-retargeting wins

The distinguishing fingerprint is **which end of the path touches the memory**:

- **Helps when the failing path STARTS at the memory** (the memory output drives
  the cone; the relevant delay is clock-to-out). Moving to distributed RAM
  shortens that launch. Confirmed wins: a small message memory, the FFT
  butterfly feedback FIFO, and a Reed-Solomon inverse table.
- **Hurts when the failing path ENDS at the memory** (the memory's address or
  data input is the endpoint; the relevant delay is setup). Converting a
  synchronous block-RAM read into an asynchronous distributed-RAM read moves the
  entire address-decode and wide readout combinationally in front of the
  capture register, which is longer than the block-RAM address setup it
  replaced. This is especially bad for wide words.

## Negative and calibration results

These are as important as the wins; they bound the patterns and are preserved so
the agent (and future work) does not blindly reapply a transformation.

- **CODEWORD to distributed (regression).** Retargeting a 128-bit-wide code-word
  memory to distributed RAM regressed its cluster, because the failing paths
  *terminate* at the memory's address pins. This is the canonical "path ends at
  the memory" counter-case above.

- **Marginal flag on a logic-light cone (regression).** A precompute flag on a
  shallow address counter whose cone was only about 25 percent logic regressed
  the cluster: the added flag-update fan-out exceeded the small decode removed.
  This is the canonical "not a flag candidate" counter-case above. It was found
  autonomously by the agent and reverted autonomously on the measured result.

- **Barrett reduction DSP mapping (negative).** Re-enabling DSP48 mapping for the
  Barrett constant multiplications did not improve the critical path. See
  [findings/FINDINGS_barrett_dsp.md](findings/FINDINGS_barrett_dsp.md).

- **`poly_mult` RAMWIDTH narrowing (negative).** Narrowing the multiply datapath
  reduces area but roughly doubles the cycle count per halving, a losing trade.
  See [findings/FINDINGS_poly_mult_ramwidth.md](findings/FINDINGS_poly_mult_ramwidth.md).

- **FSM retiming on the decap cross-module bundle (negative).** Registering a
  single signal of the v_minus_uy to poly_mult transaction breaks correctness,
  because the data, address, shift amount, valid, and accumulator-writeback
  signals are locked together. A valid fix must retime the whole bundle. See
  [findings/FINDINGS_decap_encap_crossmodule.md](findings/FINDINGS_decap_encap_crossmodule.md).

### The calibration lesson: neutral at one level is not neutral at all levels

Registering one particular decode measured as timing-neutral at HQC-128 and was
initially set aside as exhausted. The identical edit at HQC-192 was worth more
than 0.4 ns, because the constants that size the decode scale with the security
level. A per-level verdict requires per-level evidence; a result measured at one
parameter set must not be generalized to the others without re-synthesis. This
is now an explicit rule in both the manual methodology and the agent prompt.
