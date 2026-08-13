# FINDINGS: butterfly2x2 on ASAP7 with Barrett present, and the retraction of ASIC closure

Date: 2026-08-12
Status: **CURRENT.**
Supersedes: `docs/findings/asic/2026-08-10_bf2x2_ooc_fmax.md` in full, which was
already superseded on the blackbox grounds recorded in its banner. This doc
adds the second reason: the search method itself is unsound for this flow.

## Supersedes, by ID

| Superseded | Where | Reason |
|---|---|---|
| C1 to C8, C-close (578 ps) | `2026-08-10_bf2x2_ooc_fmax.md` | four modules blackboxed, and closure search unsound |
| D1 to D8, D-close (573 ps) | same | same |
| E1 to E6 | same | same |
| J-close (583 ps), K-close (592 ps) | this doc, section 2 | closure search unsound; retracted in the same document that reports them |

---

## RESULTS OF RECORD

All rows: `butterfly2x2` out of context, ASAP7 7nm, `PVT_0P7V_25C`, effort
`high` at `syn_generic` / `syn_map` / `syn_opt`, Genus 25.12-s067_1, SDC
`asic/asap7/sdc/butterfly2x2.sdc` with `set_clock_uncertainty` at 5 percent of
period, pre-layout, no blackboxes.

**Arms, three files each**, `Barrett_8380417.v` (md5
`1363d8ebe3a4eec1b210ef56ae4dd8b1`, unedited, shared), `butterfly.v`,
`butterfly2x2.v`:

| Arm | `butterfly.v` | `butterfly2x2.v` |
|---|---|---|
| baseline | `194207da29ff87473c6f7f002a7d2447` | `bd834d41f0a9143c1e40244d6a8fc716` |
| optimized | `744dac30669690e79fb1a1c8ed6932a2` | `b1bbd329e1cb793246b7799d30525f6f` |

Both tracked at `asic/arms/bf2x2_{baseline,optimized}/`.

Scripts: search points under `asap7_fmax.py` calling `genus_asap7.tcl`; single
probes under `genus_asap7_v2.tcl`. F38 establishes these produce identical
results.

### Section 1: the same-period head-to-head. This is the defensible result.

No monotonicity assumption. Each row is one arm at one period, both arms
measured under `genus_asap7_v2.tcl`.

| # | Period | Baseline result | Optimized result | Baseline log | Optimized log |
|---|---|---|---|---|---|
| P1 | 540 ps | VIOLATED -44 ps | VIOLATED -34 ps | `logs/asic/asap7_bf2x2_probes_20260812/bas_p540/` | `.../opt_p540/` |
| P2 | 555 ps | VIOLATED -17 ps | VIOLATED -22 ps | `.../bas_p555/` | `.../opt_p555/` |
| P3 | 569 ps | VIOLATED -8 ps | VIOLATED -18 ps | `.../base_p569b/` | `.../opt_p569b/` |
| P4 | 583 ps | **MET -0 ps** | **MET 0 ps** | `.../bas_p583/` | `.../opt_p583/` |

Each directory holds `*_timing.rpt`, `*_gates.rpt`, `*_area.rpt`,
`*_power.rpt`, `*_netlist.v` and `genus.log`.

**The arms cross.** At 540 ps the optimized arm is ahead by 10 ps. At 555 and
569 ps the baseline is ahead, by 5 and 10 ps. At 583 ps both meet. There is no
period in this set where the optimized arm holds an advantage that persists.

### Section 2: PPA at every measured point

Cells, area and total power are read from the `*_gates.rpt` and `*_power.rpt`
of each run. Area is in the library's units. Power is vectorless.

**Baseline**, search points at `logs/asic/asap7_bf2x2_fmax_v2_base_20260812/`,
probes at `logs/asic/asap7_bf2x2_probes_20260812/`:

| # | Period | Result | Slack | Cells | Total area | Total power | Source |
|---|---|---|---|---|---|---|---|
| J1 | 400 ps | VIOLATED | -159 ps | 24794 | 52455.574 | 77.81 mW | search |
| J2 | 540 ps | VIOLATED | -44 ps | 22631 | 47881.886 | 52.30 mW | probe |
| J3 | 550 ps | VIOLATED | -25 ps | 22592 | 47634.376 | 50.89 mW | search |
| J4 | 555 ps | VIOLATED | -17 ps | 22381 | 47287.489 | 50.58 mW | probe |
| J5 | 569 ps | VIOLATED | -8 ps | 22460 | 47256.229 | 49.19 mW | search and probe, identical |
| J6 | 578 ps | VIOLATED | -1 ps | 22362 | 46505.301 | 47.92 mW | search |
| J7 | 583 ps | MET | -0 ps | 22160 | 46014.247 | 46.86 mW | search and probe, identical |
| J8 | 588 ps | MET | 0 ps | 21916 | 45923.034 | 45.75 mW | search |
| J9 | 625 ps | MET | 0 ps | 20797 | 43745.365 | 40.66 mW | search |
| J10 | 700 ps | MET | 0 ps | 20437 | 41762.952 | 34.46 mW | search |

**Optimized**, search points at `logs/asic/asap7_bf2x2_fmax_v2_opt_20260812/`:

| # | Period | Result | Slack | Cells | Total area | Total power | Source |
|---|---|---|---|---|---|---|---|
| K1 | 400 ps | VIOLATED | -168 ps | 27179 | 58115.880 | 80.67 mW | search |
| K2 | 540 ps | VIOLATED | -34 ps | 23408 | 51546.948 | 54.50 mW | probe |
| K3 | 550 ps | VIOLATED | -28 ps | 23224 | 51150.606 | 53.15 mW | search |
| K4 | 555 ps | VIOLATED | -22 ps | 23243 | 51252.316 | 52.73 mW | probe |
| K5 | 569 ps | VIOLATED | -18 ps | 23099 | 50673.315 | 51.04 mW | probe |
| K6 | 583 ps | MET | 0 ps | 22453 | 49577.832 | 48.73 mW | probe |
| K7 | 588 ps | VIOLATED | -1 ps | 23035 | 50068.886 | 48.79 mW | search |
| K8 | 592 ps | MET | 0 ps | 22905 | 49638.951 | 47.45 mW | search |
| K9 | 597 ps | MET | 0 ps | 22101 | 48718.195 | 46.05 mW | search |
| K10 | 606 ps | MET | 0 ps | 22686 | 49282.966 | 46.59 mW | search |
| K11 | 625 ps | MET | 0 ps | 22140 | 48128.230 | 43.22 mW | search |
| K12 | 700 ps | MET | 0 ps | 21471 | 45959.426 | 36.63 mW | search |

### Section 3: the cost of the optimization at 583 ps

Both arms meet. Directly comparable, same period, same script, same SDC.

| Metric | J7 baseline | K6 optimized | Delta |
|---|---|---|---|
| Result | MET -0 ps | MET 0 ps | none |
| Cells | 22160 | 22453 | +293 (+1.3%) |
| Total area | 46014.247 | 49577.832 | +3563.6 (**+7.7%**) |
| Total power | 46.86 mW | 48.73 mW | +1.87 mW (**+4.0%**) |

**The optimized arm costs 7.7 percent area and 4.0 percent power for no timing
benefit at this period.** On ASAP7, at this constraint, the optimization is a
net loss.

### What does not exist

- **No ASIC closure figure.** See F39. Every closure number this project has
  produced on Genus is an upper bound, not a minimum.
- **No post-layout data.** Everything is pre-layout.
- **No chip-level ASAP7 optimized run.** All ASAP7 optimized numbers are block
  level.
- **No power measured with real switching activity.** Vectorless throughout.
- **No KAT tied to these runs.** No ML-DSA RTL was edited, so none was required.

---

## F38. The v1 and v2 scripts produce identical results

`base_p569b` (probe, `genus_asap7_v2.tcl`) and the search's 569 ps point
(`asap7_fmax.py` calling `genus_asap7.tcl`) report 22460 cells, 47256.229 area
and 4.91898e-02 W. `bas_p583` and the search's 583 ps point report 22160,
46014.247 and 4.68567e-02 W. Both pairs agree to every digit.

**Implication.** The two scripts differ in reporting depth and checkpoint
writing, not in synthesis outcome, so results measured under either are
comparable. This removes the concern that the 583 ps head-to-head mixed
scripts, and it extends F22's determinism finding across script variants.

## F39. RETRACTION: the ASAP7 closure search is unsound

`asap7_fmax.py` bisects on the assumption that if period P violates, every
period below P violates. **That assumption is false for this flow.**

**The counterexample, from committed logs.** The optimized arm's search reports
588 ps VIOLATED at -1 ps (`logs/asic/asap7_bf2x2_fmax_v2_opt_20260812/`). A
standalone probe of the same arm at **583 ps, a tighter constraint, MET at
0 ps** (`logs/asic/asap7_bf2x2_probes_20260812/opt_p583/`). The design meets a
period 5 ps shorter than one it failed.

**Consequence.** The searches reported 583 ps for the baseline and 592 ps for
the optimized arm. Both are **upper bounds on the minimum period**, not minima.
The same applies to the superseded C-close (578 ps) and D-close (573 ps).

**Do not report a closure period or a derived Fmax for any ASAP7 arm.** Use
same-period comparisons, which need no monotonicity assumption.

## F40. The optimized arm's area is non-monotonic in period

K9 at 597 ps reports 22101 cells and 48718.195 area. K10 at 606 ps, a looser
constraint, reports 22686 cells and 49282.966 area. Looser constraint, larger
implementation.

Also K7 at 588 ps reports 23035 cells against K8 at 592 ps reporting 22905:
tighter constraint, fewer cells.

**Implication.** This is the same signature as F17S and it is the mechanism
behind F39. The tool's optimization outcome is not a monotone function of the
constraint, so neither timing nor area can be assumed to improve as the
constraint relaxes. Any conclusion drawn from a single pair of points on this
flow needs a same-period control.

## F41. The endpoint split reproduces with Barrett present

Every baseline VIOLATED point binds a `barrett_datai_reg` endpoint. Every
optimized VIOLATED point binds a `mult_p_reg` endpoint. Verified across
P1 to P3 for both arms plus the search points.

| Period | Baseline endpoint | Optimized endpoint |
|---|---|---|
| 540 ps | `BF2_2_barrett_datai_reg[36]` | `BF1_2_mult_p_reg[43]` |
| 555 ps | `BF2_2_barrett_datai_reg[34]` | `BF1_2_mult_p_reg[43]` |
| 569 ps | `BF2_1_barrett_datai_reg[41]` | `BF2_1_mult_p_reg[37]` |
| 583 ps | `BF2_2_barrett_datai_reg[38]` (MET) | (MET) |

**Implication.** F15 and F25 claimed this split when Barrett was blackboxed,
and the claim was withdrawn on those grounds. It now reproduces on the complete
design, so the structural observation stands on new evidence: the two arms are
limited by different structures, and the optimization moved the limiter from
the Barrett reduction path to the multiplier pipeline register it added.

This is the one claim from the superseded doc that survives, and it survives
because it was re-measured rather than reinstated.

## F42. Adding Barrett raises power roughly fivefold

The superseded C5 (578 ps, blackboxed) reported 9.757 mW. J6 (578 ps, complete)
reports 47.92 mW.

**Implication.** A useful sanity check on the blackbox diagnosis: the missing
modules were a large fraction of the design's switching activity, which is
consistent with `Barrett_8380417.v` containing a modular reduction and three
pipeline stage modules. Any number from the superseded series understated
power by roughly a factor of five.

---

## The FPGA result is unaffected

G1 and G2 in `docs/findings/mldsa/2026-08-12_bf2x2_fpga_ooc_closure.md` were
measured on Artix-7 with `Barrett_8380417.v` present and blackbox status
verified zero. **They were not re-run today and stand unchanged:** G1 baseline
9.50 ns, G2 optimized 8.75 ns, a 7.9 percent period reduction.

Nothing in this document changes them. What this document does add is that the
Vivado closure search shares the monotonicity assumption that failed on Genus,
and a counterexample was observed on the HQC arm today (see the HQC port doc,
appendix). G1 and G2 should therefore also be read as upper bounds.

**The cross-backend statement the paper can now make**, and its limits:

| Backend | Baseline | Optimized | Direction |
|---|---|---|---|
| Artix-7, closure | 9.50 ns | 8.75 ns | optimized faster |
| ASAP7, same-period at 583 ps | MET | MET, +7.7% area, +4.0% power | no timing benefit, worse PPA |

The optimization helps on FPGA and does not help on ASIC. That is a
backend-dependence result, and it is the same conclusion F6 reached on the HQC
`v_minus_uy` arms under a different library.

---

## File map

| Item | Location | In git |
|---|---|---|
| v2 search logs and reports, both arms | `logs/asic/asap7_bf2x2_fmax_v2_{base,opt}_20260812/` | yes |
| Eight probe directories | `logs/asic/asap7_bf2x2_probes_20260812/` | yes |
| Arms | `asic/arms/bf2x2_{baseline,optimized}/` | yes |
| Search driver | `asic/asap7/scripts/asap7_fmax.py` | yes |
| Genus scripts | `asic/asap7/scripts/genus_asap7{,_v2}.tcl` | yes |
| SDC | `asic/asap7/sdc/butterfly2x2.sdc` | yes |
| Genus `.db` checkpoints | server only, deliberately not committed | no |

Checkpoints were excluded: eighteen files, 80 percent of the raw size,
regenerable, and cited by no result.

## Next steps

1. Do not run `asap7_fmax.py` for ASAP7 closure again until F39 is addressed.
2. Test whether Vivado's `fmax_search.py` shows the same non-monotonicity on a
   design where it can be checked cheaply. One counterexample already exists on
   the HQC arm; a deliberate test would settle whether G1, G2, M1, M2 and the
   HQC ledger need the same caveat.
3. Decide whether the paper reports ASIC block PPA at all, given F39 and the
   583 ps result showing the optimization is a net loss on this backend.

## Open questions for the advisor

1. F39 makes every project closure figure an upper bound. Does the paper drop
   closure language in favour of same-period comparisons, and does that change
   how M1, M2 and the HQC ledger are described?
2. Section 3 shows the ML-DSA butterfly optimization costs 7.7 percent area and
   4.0 percent power on ASAP7 for no timing benefit. Is that reported as a
   backend-dependence finding, or does the ASIC section stay portability only?
3. F41 reproduces the endpoint split that F15 claimed and lost. Is a
   re-measured structural finding acceptable to cite, given its first version
   was withdrawn?
