# ASIC Game Plan: ASAP7 Genus-to-Innovus

Written 2026-08-02 after Dr. Abideen's redirection. This supersedes the
GPDK045 approach entirely.

**Target: D&T submission August 15. Measurements must be done by August 10 to
leave writing time.**

---

## What changed, and what it invalidates

| Was | Now | Consequence |
|---|---|---|
| GPDK045 45 nm | **ASAP7 7 nm** | A1-A4 retracted, not deleted. Different library, not comparable. |
| Memories blackboxed (F2) | **Flip-flop arrays** | F2 reversed. Validating RTL-to-GDS matters more than iteration speed. SRAM macros come later. |
| Synthesis only | **Genus + Innovus** | Pre-layout and post-route reported separately. |
| "Verilog-2001 violations" | **"cross-tool RTL portability defects"** | Standard interpretation unconfirmed. Needs an independent linter. |
| F3 = noise floor | **tool-configuration sensitivity** | Not a threshold below which deltas are meaningless. Pin every setting and any delta is valid. |
| Full-chip primary, encoder fallback | unchanged, but encoder is **supporting evidence only** | If full-chip fails, report explicitly as a block-level cross-backend transfer study. |

**Kill the two GPDK045 full-chip runs.** They are 38 hours in on a library we
are no longer using, with memories blackboxed against instruction.

---

## The framework Abideen actually wants

One agent, parameterized by target platform:

```
platform = fpga   ->  Vivado synthesis + implementation
platform = asic   ->  Genus logic synthesis + Innovus place-and-route
```

`agent/backends/` is the skeleton. It needs an Innovus stage, ASAP7 support,
and a config object carrying every setting that must match across arms
(effort, clock period and uncertainty, library and corner, hierarchy,
flattening, retiming).

---

## Week plan

### Day 1 (Mon Aug 3): re-establish a valid baseline

1. Kill the GPDK045 runs. Get the ASAP7 files from Abideen and clone
   `hsc-research/tutorial_innovus`.
2. Read the tutorial's Genus and Innovus scripts before writing anything.
   They define the reference flow; do not invent a parallel one.
3. Run the tutorial end to end on its own example first. Confirm the flow
   works before introducing PQC RTL.
4. One HQC block through ASAP7 Genus, memories as flip-flop arrays. Record
   runtime, cell count, area, and whether the critical path is flop-to-flop.

**Exit criterion:** one block closes in Genus on ASAP7 with a valid path.

### Day 2 (Tue Aug 4): finish RTL normalization

5. Fix the gate per Abideen: accept when the targeted diagnostic disappears,
   no new diagnostic appears, and KAT passes. Do not reject a correct partial
   repair because an unrelated defect remains.
6. Finish the 9 remaining HQC files. `fixed_weight.v` by hand if the loop
   still stalls.
7. Run an independent linter (Verilator `--lint-only`, or Icarus) across the
   normalized files to confirm or retract the standards claim.

**Exit criterion:** all HQC files elaborate in Genus. Language claim either
confirmed by a second tool or softened in every document.

### Day 3 (Wed Aug 5): FPGA neutrality, then the common artifact

8. Re-measure FPGA Fmax on the normalized RTL and compare against the
   committed baseline. If anything moved, flag it before it reaches the paper.
9. Make the normalized RTL the single source both Vivado and Genus read.
   Fixes F7: optimized RTL currently lives only in regenerable `build/`.

**Exit criterion:** normalized RTL is the common artifact, FPGA numbers
verified unchanged or the change documented.

### Day 4-5 (Thu-Fri Aug 6-7): the actual experiment

10. Profile ONE isolated full-chip ML-DSA run on ASAP7. No concurrency.
    Record inferred-memory sizes, register and instance counts, hierarchy and
    flattening settings, CPU utilization, and whether the server swaps.
    Concurrent wall-clock is not a runtime measurement.
11. If tractable: full-chip baseline vs optimized, identical settings, Genus
    then Innovus.
12. If not tractable: encoder block on ASAP7, both arms, and state plainly
    that full-chip ASIC improvement remains unverified.

**Exit criterion:** one baseline-vs-optimized ASIC comparison with every
setting pinned and recorded.

### Day 6 (Sat Aug 8): Innovus

13. Post-route timing, area, power on whichever scope closed. Abideen is
    helping here.
14. Report Genus pre-layout and Innovus post-route as separate numbers. Never
    merge them.

### Day 7 (Sun Aug 9): write

15. Results of Record rebuilt for ASAP7. Old GPDK045 rows struck through with
    the reason.
16. Related Work and Methodology drafts. Neither depends on the measurements.

---

## Standing rules for every ASIC number

1. **Identical settings across arms.** Effort, clock period and uncertainty,
   library and corner, hierarchy, flattening, retiming. Encode this as an
   assertion in the TCL and in the backend config, not as a convention.
2. **Pre-layout and post-route are different numbers.** Label them.
3. **Accept only MET.** Never project Fmax from a violated run.
4. **Verify the bracket.** The encoder search returned 2.047 ns for both arms
   because the lower bound never violated. That is the bracket floor, not a
   measurement. The driver must FAIL loudly if LO never violates.
5. **Check the critical path endpoint.** A path terminating at a blackbox or a
   memory pin is not measuring the design.
6. **Record the config with the number**, in the same row.

---

## Terminology corrections to apply everywhere

- "cross-tool RTL portability defects", not "Verilog-2001 violations"
- F3 is "tool-configuration sensitivity", not a noise floor
- "baseline" and "optimized", never "pristine"
- Genus results are "pre-layout"; Innovus results are "post-route"

---

## Open items not on the critical path

- VLOGPT-22 phantom duplicate on `vect_set_random.v` still unexplained
- Defect survey needs re-deriving under the corrected probe configuration
- Dashboard unreachable from the Windows browser (VPN plus WSL mirrored networking)
- Repository reorganization
- SRAM macro integration, memory splitting, aspect ratio and mux ratio
  handling. Abideen flags this as likely where the PQC critical path lands.
  After the flow works, not before.
- New server arriving

---

## The claim this plan supports

"An assurance-guided framework that optimizes verified PQC RTL under
correctness gating, parameterized across FPGA and ASIC backends, with results
measured to post-route closure on both."

Not supported until the work above is done: any ASIC performance claim, and
any implication that block-level ASIC results predict chip-level ones.
