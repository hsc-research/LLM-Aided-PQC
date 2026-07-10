# ML-DSA coeff_decomposer: Block-Level Verification and a Pipelining Experiment
This documents a working session that (1) built and validated a fast,
isolated correctness gate for the ML-DSA `coeff_decomposer` block, then
(2) used that gate to test whether pipelining could recover the timing
the agent's existing (cycle-neutral) transformation taxonomy could not.
The verification result is solid and reusable. The pipelining attempt
produced a negative result that redirected the search toward a more
promising lead, documented below for whoever picks this up next.

---
## 1. Why a block-level gate, and not the shipped NIST KAT
ML-DSA-OSH ships a self-checking KAT testbench (`tb_keygen_top.v`) that reads
official NIST vectors and compares byte-for-byte against `combined_top`, the
full design. It is real and runnable, but two things make it unsuitable as
the agent's per-edit inner-loop gate:
- `combined_top` instantiates `keccak_top`, which is **VHDL**
  (`keccak_top.vhd` and ~10 other `.vhd` files). `iverilog` cannot compile
  mixed Verilog/VHDL designs, so this KAT can only run via Vivado's `xsim`.
- Even with `xsim`, it verifies the *entire* keygen pipeline per check, far
  too slow for an agent proposing many candidate edits.
`coeff_decomposer` has no dependency on Keccak (it is pure decomposition
arithmetic), so it can be verified in isolation, fast, in plain Verilog,
no VHDL involved. The full NIST KAT remains the intended outer confirmation
for any future change, deferred for now.

## 2. The block-level gate: built, then proven correct in three steps
Files: `agent/mldsa_block_gate.py`, `agent/mldsa_check/`
(`gen_vectors.py`, `tb_coeff_decomposer.v`).
**Reference model.** `gen_vectors.py` implements FIPS 204 `Decompose` in
Python (gamma2 = (Q-1)/88 for sec_lvl 2, (Q-1)/32 for sec_lvl 3 and 5),
emitting `di.hex` / `a1.hex` / `a0.hex` / `nvec.txt`. Early versions used a
single `vectors.txt` parsed with `$fscanf`, which produced a mysterious
even/odd 50% failure rate that took several rounds to track down. **Root
cause: `$fscanf` parsing was unreliable in iverilog for this format.** Fix:
write three separate single-column hex files and load each with
`$readmemh`, which is rock-solid. Anyone building a new block gate should
use the `$readmemh` pattern from the start.
**Testbench.** `tb_coeff_decomposer.v` drives one input per cycle
(non-blocking assignment) and samples `doa`/`dob` every cycle `valid_o` is
high, matching the Nth output to the Nth input in order. The security
level is read from a `` `define TB_SEC_LVL `` (default 3), overridable via
`-DTB_SEC_LVL=N` at compile time.
**Validation, three tests, all required before the gate was trusted:**
1. **Pristine RTL -> PASS**, sec_lvl 2 and 3, 200/200 vectors each.
2. **Deliberately broken RTL -> FAIL.** First attempt corrupted the
   sec_lvl==2 branch while testing only at sec_lvl=3, a false PASS, because
   the corrupted line was dead code for that test. This revealed a real
   coverage hole: a single-level gate cannot see edits to the untested
   branch. Fix: the gate now runs **both** sec_lvl 2 and 3 and requires
   both to pass. After the fix, the same line-85 corruption correctly
   produces FAIL at sec_lvl 2.
2b. A second corruption, in the sec_lvl 3 (else) branch
   (`<<9` changed to `<<8`), correctly produces FAIL at sec_lvl 3 even
   before the multi-level fix, confirming the gate mechanism itself works;
   the multi-level fix specifically closed the cross-branch coverage gap.
The gate's contract matches the existing HQC `kat_gate.py` convention:
`run_block_kat(candidate_rtl=None)` returns
`{"status": "PASS"|"FAIL", "reason": ..., "levels": {...}}`.

## 3. The latency-tolerance finding (the most reusable result this session)
Before attempting any real pipelining, we tested whether the *existing*
gate could verify a block whose latency had changed, since pipelining adds
pipeline-register cycles and naive verification schemes assume a fixed
cycle count.
**Experiment:** `make_lat1.py` transforms pristine `coeff_decomposer.v` by
extending `valid_sr` from 5 to 6 bits, moving the `valid_o` tap from `[4]`
to `[5]`, and adding one extra register stage on both `doa` and `dob`
(`doa_p`/`dob_p`). This delays every output by exactly one cycle while
changing no values.
- Run through the unmodified gate: **PASS**, 200/200, both levels.
- Same +1-latency variant with a corrupted constant
  (sec_lvl 3, `<<9` -> `<<8`): **FAIL**, correctly caught at sec_lvl 3.
**Why this works:** the gate samples "every cycle `valid_o` is high" and
matches outputs to inputs in arrival order, not against a fixed cycle
count. Any block whose `valid` signal is pipelined in step with its data
(true of any correctly written pipeline) will verify correctly under this
scheme regardless of added latency. **This means block-level
latency-changing edits (i.e., pipelining) can be verified for correctness
with no changes to the existing gate.** This is the main piece of
infrastructure this session produced and should transfer to any future
pipelining attempt on any block.
What this does NOT prove: full-design integration. A block that takes one
more cycle than before may misalign with whatever consumes its output
inside `combined_top`. That check still requires the deferred full
NIST KAT (via `xsim`, since Keccak is VHDL).

## 4. The pipelining attempt on coeff_decomposer: negative result
`coeff_decomposer`'s baseline critical path (`a1_0_reg -> a0_1_reg`) sits at
**WNS -1.247 ns, Fmax 160.1 MHz**, the stage that computes
`a0_1 <= a0_0 - (a1_0 * 2*gamma2)` via a shift-add tree
(`(a1_0<<19)-(a1_0<<9)` for sec_lvl 3,
`(a1_0<<17)+(a1_0<<16)-(a1_0<<12)-(a1_0<<11)` for sec_lvl 2).
`make_pipe.py` split this into two cycles: compute the constant-multiply
into a new register `mult_s` on cycle 1, subtract from a delayed `a0_0_d`
on cycle 2. `a1`'s path was extended one stage (`a1_3`) to stay aligned;
`valid_sr` extended 5->6 to match.
- **Correctness: PASS**, both levels, 200/200. The retiming itself was done
  correctly per the gate.
- **Timing: regressed.** WNS went from **-1.247 ns to -1.688 ns**
  (Fmax 160.1 -> 149.5 MHz), and area increased (362 -> 423 LUTs,
  170 -> 242 FFs). The pipeline cut added registering overhead without
  removing real combinational depth.
**Why, probably:** Vivado's synthesis already balances/retimes
combinational logic within a register-to-register stage. The two-subtract
chain (`a0_0 - ((a1_0<<19)-(a1_0<<9))`) may already have been collapsed by
the tool into something close to optimal for a single cycle; inserting a
register at the seam chosen did not correspond to where the real logic
depth lived, it just added latching overhead. Lesson: **do not assume an
RTL-visible "two operations in series" shape means a register between them
will reduce critical-path depth.** Check the post-synthesis path detail
first.

## 5. Where the post-mortem path-extraction pointed instead
Re-running `path_extractor.py coeff_decomposer default 5` on the pristine
RTL surfaced a second, deeper path that the first attempt never touched:

```
#1  -1.247 ns   61.8% logic   13 levels   a1_0_reg  -> a0_1_reg   (targeted, see above)
#2  -1.218 ns   79.4% logic   24 levels   a0_1_reg  -> a0_2_reg   (deeper, untouched)
#3  -1.196 ns   24.2% logic    7 levels   di_buffer_reg -> a1_0_reg
```

Path #2 is **deeper** than path #1 (24 logic levels vs. 13) and is a
different operation entirely: `a0_2 <= a0_1 - sub_val`, where
```verilog
assign sub_val = ((((Q-1)/2 - a0_1) >> 31) & Q);
```
This is a sign-extraction idiom (`>>31` on a wide signed value pulls out
the sign bit, sign-extended) implementing "if `a0_1 > (Q-1)/2`, apply a
Q-correction, else don't." Twenty-four logic levels for what is
conceptually a single comparison-driven conditional is a lot, and the
shape (a comparison feeding a correction) is much closer to the agent's
existing **flag-precompute** transformation (the same pattern behind the
validated HQC `fixed_weight_ct` win) than the arithmetic-pipelining problem
path #1 turned out to be. Importantly, **fixing this would not require a
latency change** at all, so it could be verified with the original
single-cycle gate, no pipelining infrastructure needed.
Also note: even a perfect fix to path #1 alone would have left path #2 as
the next bottleneck at nearly identical slack (-1.218 ns vs -1.247 ns),
which is itself a likely contributor to why the pipelining attempt's net
gain was small to negative; the block has two comparably deep stages, not
one dominant one.

## 6. butterfly: scouted, deprioritized as a pipelining target
`butterfly.v`'s Barrett reducer (`Barrett_8380417.v`) is Chisel-generated
(`DecoupledStage`, `DecoupledStage_1` modules, `io_in_ready`/`io_in_valid`
handshaking) and already internally pipelined and opaque. `butterfly`
itself already runs a 10-bit `valid_sr` with mode-dependent taps
(`valid_sr[8]`, `[7]`, `[3]` across forward-NTT, inverse-NTT, mult, add,
sub modes). Inserting a new pipeline seam into an already multi-staged,
partially black-boxed, multi-mode structure carries materially more risk
than `coeff_decomposer` for uncertain payoff. Recommendation: do not
attempt butterfly next; the `sub_val` lead in coeff_decomposer (Section 5)
is better positioned, cycle-neutral, and uses gate infrastructure that
already exists.

## 7. Concrete next step
Investigate `sub_val` / the `a0_1 -> a0_2` path as a flag-precompute
candidate:
1. Determine why a conceptually simple compare-and-correct synthesizes to
   24 logic levels (`a0_1` is declared `signed [55:0]` though only ~24
   meaningful bits are in play; check whether the wide signed comparison
   is inflating depth).
2. Propose a logically-equivalent, shallower restructuring (e.g. a direct
   comparison `(a0_1 > (Q-1)/2) ? Q : 0` rather than
   subtract-then-shift-extract).
3. Verify with the existing `mldsa_block_gate.py` as-is; no latency change,
   no gate modification needed.
4. Synthesize and compare WNS against both the -1.247 ns baseline and the
   -1.688 ns failed pipeline attempt.
If this also does not yield a timing win, the fallback is to bank the
ML-DSA boundary characterization (six blocks checked: butterfly,
coeff_decomposer, rejection_a, makehint, decomposer_unit, norm_check, each
either already arithmetic-minimal or placement/routing-bound) as the
session's contribution, with the latency-tolerant gate (Section 3) banked
separately as reusable verification infrastructure for future pipelining
work on any block.

## 8. Loose ends
- `agent/synthesizer.py`'s `MODULE_SOURCES` additions for `butterfly`,
  `rejection_a`, `decomposer_unit`, `coeff_decomposer`, `makehint` are
  committed as part of this session's changes.
- Worth raising with Dr. Abideen: whether to keep investing in taxonomy
  growth (pipelining and/or flag-precompute-on-arithmetic-blocks) toward
  an autonomous ML-DSA win, or to frame the boundary characterization
  itself as the ICCAD contribution with this work as active future work.
  Not urgent, but his ASIC/Genus plans intersect this decision.
