# ASIC PPA Analysis

All measurements in this project are from FPGA out-of-context synthesis on an
Artix-7. This document analyzes how each class of optimization is expected to
translate to a standard-cell ASIC flow, because the project's longer-term
interest is an ASIC implementation with custom SRAM generation. The central
point is that the three optimization classes translate very differently, and one
of them reverses character entirely.

A note on method: the numbers below are FPGA-measured. The ASIC direction of
each effect is argued from the structure of the transformation, not measured;
confirming the magnitudes requires a standard-cell library, an SRAM compiler,
and a synthesis/place-and-route run. Where a claim is structural and where it
needs ASIC measurement is called out explicitly.

## Summary

| Optimization class | FPGA effect (measured) | ASIC translation | Sign on ASIC |
|--------------------|------------------------|------------------|--------------|
| Precompute flag | -comb logic, +1 FF + update logic | Comparator cells move off the path; register added | Favorable, same direction |
| Strength reduction (divider) | Removes a non-power-of-two divider from the path | Removes a large combinational arithmetic block | Strongly favorable, larger than on FPGA |
| Memory retarget (BRAM to distributed) | -1 BRAM primitive, +LUTRAM | No BRAM/LUT distinction; becomes SRAM-macro vs. register-file/std-cell-RAM | Reframed entirely; depends on SRAM compiler |

## Class 1 — Precompute flags (the majority of the wins)

**What the transformation does to the netlist.** It removes a combinational
comparator from the critical path and adds one flip-flop plus the small amount
of logic that recomputes the comparison at each counter-update site.

**FPGA measurement.** On the FPGA this shows up as a handful of added
flip-flops and a low-single-digit-percent rise in LUT count, with the comparator
LUTs leaving the timing path. No DSP, no block-RAM change. Cycle count
unchanged.

**ASIC translation (structural).** This trade carries over cleanly and keeps its
sign:

- *Timing.* The comparator becomes standard-cell logic (a chain of gates) on the
  ASIC just as it is LUTs on the FPGA. Moving it off the critical path and behind
  a register has the same first-order benefit: the path now launches from a
  flip-flop's clock-to-Q instead of propagating through a comparator. The detailed
  magnitude differs, because ASIC interconnect delay is a smaller fraction of a
  short logic path than FPGA interconnect is, but the direction is the same.
- *Area.* One flip-flop per flag plus its update gates. On the ASIC this is a
  small, predictable cell-area addition. The comparator is not removed from the
  design (it is still computed at the update sites), it is moved out of the
  timing-critical fan-in cone, so total combinational area is roughly preserved
  rather than reduced.
- *Power.* The added flip-flop has clock and a small switching cost, but it only
  toggles when the counter is written (the update sites), which is no more often
  than the comparator changed before. Net dynamic power change is expected to be
  small. There is a second-order benefit on ASIC: shortening the worst path can
  permit a lower-Vt-to-higher-Vt cell swap or relaxed drive strength on that
  path during optimization, which the ASIC tool can convert into leakage/area
  savings that have no FPGA analog. This requires ASIC measurement to quantify.

**Bottom line.** Favorable on ASIC, same direction as FPGA, with a possible
extra power/area benefit from cell re-selection on the relaxed path.

## Class 2 — Strength reduction: removing the divider (Win 12)

This is the most ASIC-relevant optimization in the set, and the one whose ASIC
benefit is expected to *exceed* its FPGA benefit.

**What the transformation does.** It replaces a combinational divide of a counter
by a constant (3 or 5) with a maintained quotient/remainder pair updated
incrementally. The combinational divider is removed from the netlist entirely;
in its place are a small register, a comparator against the constant, and an
increment.

**Why ASIC benefits more than FPGA.** A non-power-of-two integer divider is one
of the most expensive combinational structures in a standard-cell flow: it
synthesizes to a wide, deep array of subtract/compare logic with a long carry
structure, consuming significant area and contributing a long timing arc. On the
FPGA, the divider was costing critical-path delay (it appeared as a bit-by-bit
ripple in the delay table). On an ASIC:

- *Area.* Removing a constant divider removes a comparatively large block of
  combinational cells and replaces it with a small counter and comparator. This
  is a net area reduction on ASIC, whereas on the FPGA it was area-neutral
  (LUTs are fungible). This is the one optimization in the set that is expected
  to *reduce* ASIC area.
- *Timing.* The long divider arc is gone, replaced by a register read. Same
  direction as FPGA, likely larger in absolute terms because the divider's
  standard-cell depth is substantial.
- *Power.* A constant divider is a wide combinational structure that glitches on
  every input change; replacing it with a registered incremental value cuts the
  glitch activity in that cone. Expected dynamic-power reduction, to be
  confirmed by ASIC measurement.

**Bottom line.** Strongly favorable on ASIC across all three of PPA, and the
clearest example of an optimization whose value is understated by the FPGA
numbers.

## Class 3 — Memory retargeting: the class that must be reframed

This class does not translate directly, because the FPGA distinction it exploits
does not exist on an ASIC.

**The FPGA transformation.** On the FPGA, moving a small or feedback-bound memory
from a block-RAM primitive (a hardened SRAM block with fixed ports and access
timing) to distributed RAM (LUTs configured as small RAMs) removes block-RAM
access timing from the path and frees a block-RAM. The measured effect was a
reduction in block-RAM count and a small rise in LUT count.

**Why it does not map directly.** An ASIC has no block-RAM-versus-LUT
distinction. Memory on an ASIC is one of:

1. a compiled SRAM macro (from an SRAM compiler, analogous in spirit to a
   block-RAM: hardened, area-efficient per bit at larger sizes, with its own
   access-time characteristic), or
2. a register file or standard-cell latch/flip-flop array (analogous in spirit
   to distributed RAM: built from the standard-cell library, fast for small
   sizes, area-expensive per bit at larger sizes).

So the FPGA decision "block-RAM vs. distributed" becomes the ASIC decision
"compiled SRAM macro vs. standard-cell register file," and the crossover point
is set by the SRAM compiler's characteristics, not by FPGA primitive counts.

**How to reframe each memory retarget for ASIC.**

- The small memories we moved to distributed RAM (for example a 4-word message
  memory) are below the size where a compiled SRAM macro is efficient. On an
  ASIC these are natural register files / standard-cell arrays regardless of the
  FPGA decision; the FPGA win simply anticipated the ASIC-correct choice for a
  small memory. Favorable, but for SRAM-compiler reasons rather than the FPGA
  reason.
- The feedback-bound FFT FIFO was retargeted on the FPGA to break a
  same-primitive read-modify-write loop. On an ASIC the same loop would be
  evaluated against the SRAM macro's read and write access times; whether a
  register-file implementation wins depends on the macro timing. This is exactly
  the kind of memory that should be generated both ways and compared.

**What to measure on ASIC.** For each retargeted memory, generate it both as a
compiled SRAM macro and as a standard-cell register file at the actual width and
depth used at each security level, and compare access time, area, and energy per
access. The crossover depth tells us which memories should be macros and which
should be register files in the ASIC implementation. This is the specific
follow-up the principal investigator identified for the BRAM-to-distributed
results, and the project's control over SRAM generation makes it directly
answerable.

**Bottom line.** Reframed, not carried over. The FPGA wins point at the right
memories to examine, but the ASIC decision must be made against the SRAM
compiler, and a wide memory whose access is on the path's *input* side (the
regression case in the taxonomy) is a warning that the register-file form is not
universally better.

## What does not change

- **Cycle counts.** Every optimization is cycle-schedule neutral, so latency in
  cycles is identical on FPGA and ASIC. Wall-clock latency then scales purely
  with the achievable clock period.
- **Constant-time behavior.** No optimization introduces a secret-dependent
  branch or memory access that was not already present in the baseline; the
  flags compute the same predicates the original comparators did. The
  constant-time properties relevant to side-channel resistance are preserved
  identically on an ASIC.
- **DSP/multiplier usage.** Zero hard multipliers are used on the FPGA. On an
  ASIC the corresponding question is standard-cell multiplier inference; the
  Barrett-reduction negative result (re-enabling DSP did not help on FPGA)
  suggests the hand-written shift-and-add forms are already efficient, but this
  should be re-evaluated against the standard-cell library.
