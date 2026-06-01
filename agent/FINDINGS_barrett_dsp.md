# Findings: Barrett Reduction DSP Mapping (Negative Result)

**Module:** `hqc_barrett_red` (instantiated inside `fixed_weight`)
**Date:** May 30, 2026
**Author:** Lloyd Alcorn
**Target:** Xilinx Artix-7 xc7a200tfbg676-1, 200 MHz (5.000 ns), OOC synthesis

## Hypothesis

The baseline design uses zero DSP blocks across all modules. `hqc_barrett_red`
carries an explicit `(* use_dsp48 = "no" *)` attribute and implements its two
constant multiplications (`475 * a` and `t * N`) as hand-written shift-and-add
chains. Hypothesis: re-enabling DSP and writing the multiplications as `*`
operators would let Vivado map them onto DSP48 blocks and shorten the critical
path, which the baseline confirms runs through Barrett reduction
(fixed_weight and keygen share WNS = -2.064 ns).

## Method

A copy of `hqc_barrett_red.v` was modified to:
1. Comment out the `(* use_dsp48 = "no" *)` attribute.
2. Replace shift-add `a475` with `assign a475 = 475 * a_i;`.
3. Replace shift-add `tN` with `assign tN = t * N;`.
4. Fix `c_o` port direction from `input` to `output` (latent bug; the module
   only synthesizes to non-empty logic in isolation once `c_o` is an output).

The DSP version was then synthesized in context inside `fixed_weight` (HQC-128)
and compared against the baseline `fixed_weight`.

## Result

| Version | LUTs | FFs | BRAM | DSP | WNS (ns) | Fmax (MHz) |
|---------|------|-----|------|-----|----------|------------|
| Baseline (shift-add, DSP off) | 235 | 119 | 2 | 0 | -2.064 | 141.6 |
| DSP-mapped Barrett            | 320 | 153 | 2 | 2 | -3.340 | 119.9 |

Vivado did map both multiplications onto 2 DSP48 blocks. However, every metric
got worse: LUTs +36%, FFs +29%, WNS -1.28 ns, Fmax -22 MHz.

## Interpretation

DSP48 blocks occupy fixed columns in the FPGA fabric. Routing signals from the
fixed_weight logic out to a DSP column and back adds routing delay that exceeds
the benefit of dedicated multiply hardware, especially for small constant
multiplications (475, 17669) that map efficiently to local LUT shift-add logic.

This empirically validates the original authors' decision to disable DSP and
hand-write the shift-and-add reduction. The `(* use_dsp48 = "no" *)` attribute
is a deliberate, correct optimization, not an oversight.

## Conclusion

DSP mapping of Barrett reduction is **rejected** for this FPGA target. The
baseline shift-and-add implementation is superior. Documented here so the
experiment is not repeated.

## Note for ASIC

This conclusion is FPGA-specific. On an ASIC, there are no fixed DSP columns and
no DSP routing penalty, so a synthesized multiplier may behave differently.
Worth re-testing if/when an ASIC flow is available.
