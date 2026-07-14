# FINDINGS: full post-route PPA (advisor request — power + area, not just timing)

Matched pair, identical settings: xc7a200tfbg676-1, 5.0 ns constraint
(200 MHz target), post-route (synth -> opt -> place -> phys_opt -> route).

| Metric | Pristine | Optimized | Delta |
|---|---|---|---|
| WNS | -10.318 ns | -8.766 ns | +1.552 ns |
| Achievable Fmax | 65.3 MHz | 72.6 MHz | +11.2% |
| Slice LUTs | 54,233 | 54,090 | -143 (-0.3%) |
| Slice Registers | 29,117 | 30,344 | +1,227 (+4.2%) |
| Total on-chip power | 3.469 W | 3.567 W | +2.8% |
| Dynamic power | 3.327 W | 3.424 W | +2.9% |
| Static power | 0.142 W | 0.143 W | ~0 |

## Interpretation
The optimization trade is explicit: +11.2% frequency bought with +4.2%
registers and +2.8% power, at slightly FEWER LUTs. The register/power increase
is structural, not incidental — the accepted wins are pipeline stages,
precompute registers, and fanout replicas, all of which add flops to shorten
paths. LUTs fall slightly because several wins (width narrowing, sign-select
on sign-extract idioms) remove combinational logic.

## Methodology caveats (state these when reporting)
1. Power is Vivado VECTOR-LESS estimation (default switching activity). Valid
   for A/B comparison of two variants of the same design under identical
   settings; NOT valid as an absolute wattage claim. A SAIF-driven run from
   real KAT simulation activity would be needed for absolute numbers.
2. Constraint matters: an over-constrained run at 2.0 ns (500 MHz) INVERTED
   the timing result (pristine -12.179 vs optimized -12.677) and inflated
   power ~2.4x on both variants. Over-constraint makes the router thrash and
   is not a valid reporting corner. All reportable numbers use 5.0 ns.
3. Iso-frequency power was NOT measured. Do not claim energy-per-operation
   improvement without running the optimized design at the pristine Fmax.
