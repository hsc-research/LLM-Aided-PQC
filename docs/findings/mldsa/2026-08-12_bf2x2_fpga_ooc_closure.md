# FINDINGS: butterfly2x2 out-of-context closure on Artix-7, both arms

Date: 2026-08-12
Status: **CURRENT.**
Commit: pending

## Supersedes

Nothing directly. See the "Relation to prior butterfly numbers" section below
for what this does and does not replace. In particular it does **not**
supersede the retracted `+12.9%` figure, which concerns a different module
measured a different way, and which remains retracted on its own grounds.

## Scope warning, read before using any number here

These are FPGA numbers. The ASAP7 block-level results previously recorded in
`2026-08-10_bf2x2_ooc_fmax.md` (C, D and E series) were measured on arm
directories that **omitted `Barrett_8380417.v`**, leaving four unresolved
modules. Those results are under supersession and **no ASIC-versus-FPGA
comparison should be drawn until the ASAP7 re-measurement completes.** See
F27.

---

## RESULTS OF RECORD

All rows: `butterfly2x2` out of context, Artix-7 `xc7a200tfbg676-1` speed
grade -1, Vivado, post-route closure. Recipe fixed in `agent/fmax_search.py`:
`opt_design`, `place_design -directive ExtraTimingOpt`,
`phys_opt_design -directive Explore`, `route_design -directive Explore`.
Checkpoints built by `chip_orchestrator.regen_ckpt` at regen period 5.000 ns,
`synth_design -mode out_of_context`. Search is 5 fixed iterations, not a
tolerance. Two concurrent Vivado processes on one workstation.

Sources, three files per arm, identical except the two edited ones:
`Barrett_8380417.v` (unedited, shared, from the ML-DSA reference tree),
`butterfly.v`, `butterfly2x2.v`.

Arm md5, verified against the server copies used for the ASAP7 work:

| Arm | `butterfly.v` | `butterfly2x2.v` |
|---|---|---|
| baseline | `194207da29ff87473c6f7f002a7d2447` | `bd834d41f0a9143c1e40244d6a8fc716` |
| optimized | `744dac30669690e79fb1a1c8ed6932a2` | `b1bbd329e1cb793246b7799d30525f6f` |

**Blackbox status: zero.** Verified directly. Vivado's `Report BlackBoxes`
table is empty (header and separator rows only), and the log contains zero
instances of `Synth 8-3491` or `Synth 8-6156`. Log at `/tmp/bb_check.log`,
to be committed. This check exists because its absence is what invalidated
the ASAP7 series.

### G1, G2: the closure pair

| # | Arm | Closing period | Fmax | WNS at close | Final bracket | Log |
|---|---|---|---|---|---|---|
| G1 | baseline | **9.50 ns** | 105.3 MHz | +0.011 ns | [9.38, 9.50] | `logs/fpga/bf2x2_ooc_20260811/base_fpga2.log` |
| G2 | optimized | **8.75 ns** | 114.3 MHz | +0.004 ns | [8.62, 8.75] | `logs/fpga/bf2x2_ooc_20260811/opt_fpga2.log` |

**G2 vs G1: 0.75 ns shorter closing period, a 7.9 percent period reduction.**

Report the period. The Fmax column is `1000/period`, a unit conversion of a
measured closing period, not the retracted `1/(period - WNS)` projection.
Search resolution is 0.12 to 0.13 ns, so both periods are bounded, not exact.

### Bracket proof

`agent/fmax_search.py` does **not** assert its bracket, unlike
`asap7_fmax.py` (F12). Both brackets are therefore proven by reading the
iterations, not by the tool.

| Iter | Baseline period | Result | WNS | Optimized period | Result | WNS |
|---|---|---|---|---|---|---|
| 0 | 10.00 ns | MET | +0.018 | 10.00 ns | MET | +0.092 |
| 1 | 9.00 ns | VIOLATED | -0.180 | 9.00 ns | MET | +0.047 |
| 2 | 9.50 ns | MET | +0.011 | 8.50 ns | VIOLATED | -0.111 |
| 3 | 9.25 ns | VIOLATED | -0.312 | 8.75 ns | MET | +0.004 |
| 4 | 9.38 ns | VIOLATED | -0.167 | 8.62 ns | VIOLATED | -0.174 |

Both arms carry MET and VIOLATED points, and each closure has a VIOLATED
point immediately below it. The brackets hold.

### Utilization at closure

From `report_utilization` at each arm's own closing period.

| Metric | G1 baseline (9.50 ns) | G2 optimized (8.75 ns) | Delta |
|---|---|---|---|
| Slice LUTs | 2920 | 2924 | +4 (+0.14%) |
| LUT as Logic | 2820 | 2824 | +4 |
| LUT as Memory | 100 | 100 | 0 |
| LUT as Shift Register | 100 | 100 | 0 |
| Slice Registers (all FF) | 2155 | 2725 | **+570 (+26.4%)** |
| Block RAM Tile | 0 | 0 | 0 |
| DSP48E1 | 8 | 8 | 0 |

Baseline cell usage also records 340 `CARRY4`.

### Supporting series, first search attempt

A prior search over bracket [3.0, 9.0] produced no closure: the baseline
violated at all five points and the optimized arm met only on its final
iteration, so neither figure is a minimum. It is retained because the shared
periods are a direct head-to-head.

| Period | Baseline WNS | Optimized WNS | Optimized better by |
|---|---|---|---|
| 6.00 ns | -2.988 | -2.329 | 0.659 ns |
| 7.50 ns | -1.307 | -0.898 | 0.409 ns |
| 8.25 ns | -0.685 | -0.594 | 0.091 ns |
| 8.62 ns | -0.558 | -0.174 | 0.384 ns |
| 8.81 ns | -0.526 | +0.163 | 0.689 ns |

Logs: `logs/fpga/bf2x2_ooc_20260811/bf2x2_base_fpga.log` and
`bf2x2_opt_fpga.log`. **The 8.81 ns optimized point is not a closure** and
must not be quoted as one.

### What does not exist yet

- **No valid ASAP7 counterpart.** Re-measurement in flight. See F27.
- **No power figures.** `fmax_search.py` emits `report_utilization` only.
- **No per-point utilization for non-closing points.** The `.util` files
  exist for all ten points of the second run but only the two closing points
  are tabled here.
- **No KAT tied to these specific runs.** The RTL is the same tracked source
  the ML-DSA gates cover, but no gate was run as part of this measurement.
- **No chip-level FPGA re-measurement.** M1 and M2 stand unaffected; they are
  a different design (`combined_top`) and are not touched by anything here.

---

## F27. The ASAP7 block-level series measured an incomplete design

`butterfly.v` line 81 instantiates `Barrett REDUCER(...)`.
`Barrett_8380417.v` defines four modules: `DecoupledStage`,
`DecoupledStage_1`, `DecoupledStage_2` and `Barrett`. That file was never
placed in `asic/arms/bf2x2_baseline` or `asic/arms/bf2x2_optimized`, and
`genus_asap7.tcl` reads `[glob $RTL_DIR/*.v]`, so Genus found an
instantiation with no source. With `hdl_error_on_blackbox false` it
blackboxed it silently.

**Verification.** The gates report for every point of the C series records
`unresolved 4` with zero area. Setting `hdl_error_on_blackbox true` on the
same two-file arm produces `Could not resolve reference. [CDFG-431]`, naming
instance `REDUCER` at `butterfly.v` line 81, and refuses to elaborate.

**Implication.** C1 to C8, C-close, D1 to D8, D-close and the entire E series
measured a butterfly with its modular reduction and three pipeline-stage
modules absent. Within-arm comparisons were internally consistent because
both arms had the same hole, but no ASAP7 number from that work describes the
design, and F15's attribution of the limiting path to Barrett is not
supported, because the Barrett logic was never synthesized.

**The signal was present and was misread.** `unresolved 4` was recorded in
the findings doc for all eight points and explained as an accounting
difference between the gates and area reports rather than investigated. An
unresolved instance is by definition a module the tool could not find.

## F28. Genus now refuses to elaborate a Verilog-only arm with a missing module

`genus_asap7.tcl` and `genus_asap7_v2.tcl` now set
`hdl_error_on_blackbox true` when the arm directory contains no `.vhd` files.
Mixed-language arms keep the tolerant setting, which the VHDL read-order
handling above it requires (F10).

**Verification, both directions.** On the Barrett-less two-file arm,
elaborate fails with CDFG-431. On the complete three-file arm, the log shows
the attribute being set to true and elaborate proceeds with zero CDFG-431.

**Note for wrappers.** Genus returned exit status 0 despite the elaboration
error, so a caller checking only the return code would not notice. The search
driver happens to stop anyway because no timing report is produced.

## F29. The optimized arm's FPGA advantage is carried by registers, not logic

Between G1 and G2 the LUT count moves by 4 cells out of 2920, and DSP and
BRAM are identical. Flip-flops rise by 570, 26.4 percent.

**Implication.** The transformation is pipelining, not logic restructuring.
This is consistent in direction with what the source diff shows (`aj3` depth
`[4:0]` to `[6:0]`, `valid_sr` 10 to 11 bits, added `mult_p`, `sub_r`,
`add_r`, `zeta_delay3` registers, `z2_sr`/`z3_sr` `[8:0]` to `[10:0]`), and
the paper should say "pipelining" rather than "faster logic". Whether the
same mechanism carries on ASAP7 is now an open question, since the prior
ASIC evidence for it is withdrawn.

## F30. One point reproduced exactly across two independent searches

The optimized arm was evaluated at 8.62 ns in both the first and second
searches, in separate Vivado invocations from separately built checkpoints,
and reported WNS -0.174 both times.

**Implication.** Consistent with F22's finding of tool determinism on the
Genus side, now with one datapoint on the Vivado side. One point is not a
determinism study and should not be described as one.

---

## Relation to prior butterfly numbers

Three distinct measurements exist for butterfly-family blocks on FPGA. They
are not interchangeable and none supersedes another.

| Measurement | Module | Method | Constraint | Status |
|---|---|---|---|---|
| WNS ledger, 2026-07-11 | `butterfly` | synthesis WNS at fixed constraint | 200 MHz OOC | stands |
| `+12.9%` derived figure | `butterfly` | `1/(period - WNS)` projection | 200 MHz OOC | **retracted**, formula banned |
| G1, G2, this doc | `butterfly2x2` | binary search to post-route closure | search | **current** |

The retracted figure is not replaced by G1 and G2, because it concerns
`butterfly` and these concern `butterfly2x2`. Anyone needing a block-level
FPGA improvement figure should cite G2 versus G1 and name the module.

The `+1.009 ns` WNS improvement in the ledger (`-3.802` to `-2.793` on
`butterfly`) remains a valid measurement and is not affected.

---

## File map

| Item | Location | In git |
|---|---|---|
| Closure logs, both arms | `logs/fpga/bf2x2_ooc_20260811/{base,opt}_fpga2.log` | pending |
| First-attempt logs | `logs/fpga/bf2x2_ooc_20260811/bf2x2_{base,opt}_fpga.log` | yes |
| Utilization, 10 points | `/tmp/fsrch_bf2x2_*_fpga2_*.rpt.util` | **no, local /tmp only** |
| Timing summaries, 10 points | `/tmp/fsrch_bf2x2_*_fpga2_*.rpt` | **no, local /tmp only** |
| Blackbox verification log | `/tmp/bb_check.log` | **no, local /tmp only** |
| Search driver | `agent/fmax_search.py` | yes |
| Checkpoint builder | `agent/chip_orchestrator.py`, `regen_ckpt` | yes |
| Source keys | `agent/synthesizer.py`, `bf2x2_baseline` / `bf2x2_optimized` | yes |
| Arms | `asic/arms/bf2x2_{baseline,optimized}/` | yes |

`/tmp` on the local workstation does not survive a WSL restart, and did not
survive one during this work. Everything listed as `/tmp` only should be
copied into the repo before it is quoted.

---

## Next steps

1. Copy the ten `.rpt` and `.util` files and `bb_check.log` out of `/tmp` and
   commit them, before anything in this doc is cited.
2. Commit this doc and the two closure logs.
3. Record the supersession of the ASAP7 C, D and E series in both
   directions: banner on `2026-08-10_bf2x2_ooc_fmax.md`, strikethroughs on
   its Results of Record rows, INDEX row rewrite, and a note in both
   handoffs.
4. When the ASAP7 re-measurement closes, write its own doc and only then
   attempt any cross-backend statement.

## Open questions for the advisor

1. Does a block-level FPGA closure pair, with the chip-level M1/M2 pair
   already in hand, add enough to the paper to be worth a table, or is it
   better reported as one line supporting the chip result?
2. F29 says the FPGA gain is pipelining rather than logic optimization, at a
   cost of 570 flops. Is an area-for-frequency trade at that ratio the claim
   the paper wants to make about the agent?
3. Given F27, should the ASIC section be scoped down to the portability
   contribution for this submission, with the block-level PPA work held for
   the journal version?
