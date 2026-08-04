> **SUPERSEDED 2026-08-03.** The ML-DSA chip-level numbers in this document
> (82.7 MHz optimized, +17.8%) were measured in Vivado's default pinned flow
> before commit `23c5672` moved `regen_ckpt` to out-of-context mode. Both arms
> were re-closed in OOC on 2026-08-03. Current canonical results are M1 (70.2
> MHz) and M2 (80.5 MHz), +14.7%, in `docs/findings/INDEX.md`, ML-DSA
> chip-level ledger. Commit `3edd76a`.

# ML-DSA Full-Chip PPA: Pristine vs Optimized (Post-Route, Measured)

All numbers post-route at each build's own timing-closed operating point
(binary-searched closure, WNS >= 0), Artix-7 xc7a200tfbg676-1 (speed grade
-1), Vivado 2025.2, recipe: opt_design, place ExtraTimingOpt, phys_opt
Explore, route Explore. No projections from violated runs appear anywhere
in this document. "Optimized" = all committed block wins plus the banked
encoder architecture.

## Timing (post-route critical-path frequency, closed)

| Build | Closing period | Post-route Fmax | Timing closed |
|---|---|---|---|
| Pristine | 14.25 ns | 70.2 MHz | yes (WNS +0.15) |
| Optimized | 12.73 ns | 78.6 MHz | yes (WNS +0.158) |

Improvement: +12.0% post-route Fmax. Independently consistent with the
in-progress Minerva (GMU-tool) partial result on the optimized build
(83.33 MHz, is_complete=0, different search strategy set; final
Minerva numbers for both builds pending — no gap attribution until then,
per direction).

## Area

| Build | LUT | FF | DSP | BRAM |
|---|---|---|---|---|
| Pristine | 53,127 | 29,079 | 16 | 29 |
| Optimized | 53,543 | 30,078 | 16 | 29 |

Delta: +0.8% LUT, +3.4% FF (pipeline and precompute registers), DSP and
BRAM identical. UPDATED 2026-07-24: area re-pulled at the confirmed 12.09 ns
closure point (was 12.73 ns / 53,309 / 30,034).

## Latency (measured, not derived: full FIPS-204 KAT runs, 25 vectors x 3
security levels, average KeyGen cycles per operation)

| Level | Pristine cycles | Optimized cycles | Added | Added % |
|---|---|---|---|---|
| ML-DSA-44 (II) | 4,872 | 4,990 | +118 | +2.4% |
| ML-DSA-65 (III) | 8,291 | 8,424 | +133 | +1.6% |
| ML-DSA-87 (V) | 14,033 | 14,226 | +193 | +1.4% |

Sources of added latency: butterfly DSP pipeline (+1 cycle FNTT/MULT, +2
INTT per pass), banked encoder insert stage (+1), gen_c/decoder/rejection
precompute registers (latency-preserving by construction; contribute 0).

## Net throughput (wall-clock per operation = cycles / Fmax)

| Level | Pristine | Optimized | Net |
|---|---|---|---|
| II | 69.4 us | 62.0 us | -10.7% time (+12.0% throughput) |
| III | 118.1 us | 104.6 us | -11.4% time (+12.9% throughput) |
| V | 199.9 us | 176.7 us | -11.6% time (+13.1% throughput) |

UPDATED 2026-08-03: recomputed at the OOC closure points M1 (70.2 MHz,
14.25 ns) and M2 (80.5 MHz, 12.43 ns). Prior rows used the pinned-flow 82.7
MHz figure, now retired; see the ML-DSA chip-level ledger in
`docs/findings/INDEX.md`. Cycle counts are unchanged (measured from KAT runs,
KeyGen only). The optimized arm executes more cycles per operation but closes
at a high enough frequency that wall-clock time still falls at every security
level.

## Power / Energy

No power figures are currently on record for the OOC closure points.
`fmax_search.py` emits `report_utilization` only, so the M1/M2 runs of
2026-08-03 produced no power data.

The previous figures (pristine 1.286 W at 14.25 ns, optimized 1.480 W at
12.73 ns) are retired: both are pinned-flow, and the optimized figure was
taken at 12.73 ns, which matches neither the retired 12.09 ns closure nor
the current M2 closure at 12.43 ns.

Power and energy-per-operation remain HELD pending the SAIF/VCD-based flow
(Eop = Pavg x Ncycles / f with real KAT switching activity) per advisor
guidance. Note that vectorless power in OOC excludes I/O entirely, so an OOC
power number is not comparable to a pinned one even at the same period.

## Notes for reuse
- Pipeline-register count per edit is documented in the corresponding
  findings docs (butterfly: mult_p + sub_r; encoder: samples/insert
  stage; full list in docs/findings/mldsa/).
- KAT cycle scope: KeyGen only (the full-KAT gate exercises the keygen
  pipeline; SigGen/SigVer cycle counts require the upstream sign/verify
  testbenches and are future work).
- Comparison language for GMU numbers: same-family reference comparison;
  their 116 MHz is Artix-7 -3 via Minerva search; ours is -1. Exact
  Minerva repo+commit to be pinned before any citation.
