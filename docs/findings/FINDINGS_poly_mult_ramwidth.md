# Findings: poly_mult RAMWIDTH Sweep and Pipeline Closure

**Module:** `poly_mult`
**Date:** May 29–30, 2026
**Author:** Lloyd Alcorn
**Target:** Xilinx Artix-7 xc7a200tfbg676-1, 200 MHz (5.000 ns), OOC synthesis

## Objective

Explore the `RAMWIDTH` parameter of `poly_mult` as a PPA optimization knob.
`RAMWIDTH` sets the datapath width of the polynomial-multiply accumulator and
is documented in the source as requiring a power-of-two value (`W_BY_Y` must be
a power of 2 for optimized synthesis).

## Method

For each width, the parameter was changed with a single `sed` substitution
(no manual RTL edits), then synthesized via `agent/synthesizer.py`. Cycle counts
were measured by simulating the standalone `poly_mult` testbench
(`agent/poly_mult_cycle_tb_*.v`) and reading the `Total Clock Cycles` print.
No API calls were used for the sweep itself.

## Area / Timing Results (HQC-128)

| RAMWIDTH | LUTs | FFs | BRAM | DSP | Fmax (MHz) | WNS (ns) | Timing |
|----------|------|-----|------|-----|------------|----------|--------|
| 32       | 446  | 189 | 1    | 0   | 199.9      | -0.003   | Fail   |
| 64       | 681  | 245 | 2    | 0   | 192.0      | -0.209   | Fail   |
| 96       | 1467 | 301 | 3    | 0   | 89.0       | -6.234   | Fail   |
| **128 (baseline)** | **1363** | **368** | **4** | **0** | **203.3** | **+0.080** | **PASS** |
| 256      | 4433 | 623 | 7    | 0   | 175.8      | -0.687   | Fail   |

- RAMWIDTH=96 collapses timing (89 MHz): confirms the power-of-two requirement.
- RAMWIDTH=256 is strictly worse: 3.25x area and worse timing.
- Narrowing the datapath (32, 64) cuts area sharply but misses timing.

## Cycle Count Results (HQC-128)

| Version | RAMWIDTH | Cycles | vs Baseline |
|---------|----------|--------|-------------|
| Baseline | 128 | 9,443 | 1.00x |
| Narrowed | 64 | 18,620 | 1.97x |
| Narrowed + pipeline | 32 | 36,974 | 3.92x |

Halving RAMWIDTH roughly doubles cycle count, as expected: a narrower datapath
processes fewer bits per cycle and needs proportionally more cycles.

## LLM-Assisted Timing Closure (RAMWIDTH=32)

RAMWIDTH=32 missed timing by only 3 ps (WNS = -0.003 ns). A single constrained
API call (claude-sonnet-4-5) was asked to add ONE pipeline register to the shift
critical path without changing ports, signal widths, or RAMWIDTH. Result:

| Metric | RAMWIDTH=32 | + pipeline |
|--------|-------------|------------|
| WNS (ns) | -0.003 | +0.011 (timing met) |
| FFs | 189 | 232 (+43, expected for one stage) |
| LUTs | 446 | 446 |
| Fmax (MHz) | 199.9 | 200.4 |

## HQC-192 and HQC-256 (RAMWIDTH=64, no API)

| Param | LUTs | FFs | BRAM | Fmax (MHz) | WNS (ns) | Timing |
|-------|------|-----|------|------------|----------|--------|
| HQC-192 | 715 | 249 | 2 | 214.6 | +0.341 | PASS |
| HQC-256 | 706 | 223 | 2 | 207.0 | +0.169 | PASS |

Both met timing directly from the sweep with no further modification.

## Conclusion

The RAMWIDTH sweep maps a clear area-time tradeoff, but **narrowing RAMWIDTH is
not a valid standalone optimization** because it increases cycle count (up to
3.92x at width 32). This violates the fixed-cycle-count invariant required for
constant-time behavior. The result is documented as a characterization of the
design space, not as an adopted optimization.

**Next target:** optimizations that preserve cycle count, e.g. the Barrett
reduction critical path.
