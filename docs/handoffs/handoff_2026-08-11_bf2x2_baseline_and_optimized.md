> **SUPERSEDED 2026-08-12.** Every ASAP7 butterfly2x2 number below was measured
> with `Barrett_8380417.v` missing from the arm directory, leaving four modules
> blackboxed (`Unresolved 4` in every gates report). Do not quote 578 ps,
> 573 ps, the E-series head-to-head, or anything derived from them. See the
> banner on `docs/findings/asic/2026-08-10_bf2x2_ooc_fmax.md` and F27 in
> `docs/findings/mldsa/2026-08-12_bf2x2_fpga_ooc_closure.md`.

# HANDOFF: bf2x2 ASAP7 baseline closure, findings doc, optimized sweep

Session: 2026-08-10 evening through 2026-08-11 early morning. Continues: `docs/handoffs/handoff_2026-08-10_bf2x2_ooc_session.md` Findings of record: `docs/findings/asic/2026-08-10_bf2x2_ooc_fmax.md` Commits this session: `0465d11`, `21a976c`, `0c93891`, `24e370d`, plus the optimized sweep below, not yet committed.

---

## What was done, in order

1. **Baseline Fmax search completed and verified.** Bracket \[400, 600\] ps, TOL 5 ps, both ends proven. Closed at **578 ps** (C-close). Eight-point sweep C1 to C8, each with area, gates, power, timing reports.  
2. **Provenance repaired.** Arm md5-verified against `mldsa_baseline`. Driver located at `asic/asap7/scripts/asap7_fmax.py` (handoff's path was wrong by one directory). `.gitignore` line 93 was a bare `asap7/`, silently blocking the entire ASAP7 tree from git; narrowed to `asic/asap7/{run,out,work}/` so scripts and SDC are now trackable.  
3. **Everything pulled and committed to `main`, pushed to `origin`.** Fmax logs, 32 per-point reports, JSON, both Genus tcl scripts, both SDCs (with and without clock uncertainty, diff-verified to differ by exactly one line), the 78-hour chip base logs and its findings doc, both handoffs, and all eight per-point netlists (19M raw, \~2.5M packed).  
4. **Findings doc written**, `docs/findings/asic/2026-08-10_bf2x2_ooc_fmax.md`, F15 through F21. Headline: F15, only VIOLATED points reveal the true limiter (Barrett/multiplier path); every MET point's endpoint is an artifact of where Genus stopped, not a design property. This weakens what can be claimed from A1 (the chip run), which is a MET point.  
5. **INDEX.md updated**, new row marked CURRENT, anchor-verified insert.  
6. **Optimized arm built and launched.** `bf2x2_optimized/` created from `mldsa_optimized/`, md5-verified (`744dac30...` / `b1bbd329...`, matches `agent/mldsa/mldsa_src/` exactly). Bracket widened to \[350, 600\] since the optimized variant was expected to close faster. Same script (v1), same SDC, same effort. Converged overnight.

## New result: optimized butterfly2x2 sweep

**Not yet in a Results of Record table below. This section is the raw log only, per rule 1, until it is read into a table with the required columns.**

ASAP7 Fmax: butterfly2x2  src=.../bf2x2\_optimized  bracket \[350, 600\] ps

  period=600ps  MET  slack=0ps  (1665s)

  period=350ps  VIOLATED  slack=-215ps  (3260s)

  period=475ps  VIOLATED  slack=-95ps  (3263s)

  period=538ps  VIOLATED  slack=-19ps  (2399s)

  period=569ps  VIOLATED  slack=-5ps  (2187s)

  period=584ps  MET  slack=0ps  (1613s)

  period=577ps  MET  slack=0ps  (1888s)

  period=573ps  MET  slack=0ps  (1923s)

RESULT butterfly2x2: min period 573 ps \-\> Fmax 1746.2 MHz

Log location: `~/pqc/hqc/asic/asap7/fmax_bf2x2_opt.log` (server, not yet pulled). Reports: `~/pqc/hqc/asic/asap7/out/bf2x2_fmax_opt/` (server, not yet pulled).

**The critical caveat, before this becomes a claim: 578 ps (baseline) versus 573 ps (optimized) is a 5 ps gap, and TOL is 5 ps.** F17 already demonstrated that 3 ps of separation (578 vs 581\) produced a measurable area inversion, meaning the flow's own run-to-run variation exceeds 3 ps. A 5 ps gap sits at that same floor. **This is not yet distinguishable from noise.** Do not report "+0.9% Fmax" or any derived percentage until the area and power at 573 ps are read and compared against the C5 to C8 pattern. If 573 ps shows higher area or power than 578 ps, the way 581 ps did against 578 ps in F17, that is direct evidence the two periods are not distinguishable and the correct statement is "no measurable difference within the search's resolution," not a win.

Arm-level provenance is solid regardless of the outcome: `adder = adda + addb` sits at line 174 in the optimized `butterfly.v` versus line 169 in baseline, confirmed by `grep -n`, so `add_174_*` versus `add_169_*` in any Genus log is a reliable arm identifier independent of the md5 check.

---

## Progress against the standing checklist

| Item | Status |
| :---- | :---- |
| Baseline bf2x2 ASAP7 closure | **Done.** 578 ps, C-close, committed |
| Baseline sweep artifacts (area/gates/power/timing, all 8 pts) | **Done.** Committed |
| Baseline netlists | **Done.** Committed `0c93891` |
| Findings doc, RTL-standard-compliant | **Done.** `2026-08-10_bf2x2_ooc_fmax.md` |
| INDEX.md updated | **Done.** |
| ASAP7 scripts/SDC trackable in git | **Done.** Gitignore fixed |
| Optimized arm built | **Done.** md5-verified |
| Optimized Fmax search | **Done, converged.** 573 ps. Not yet pulled, read, or tabled |
| Optimized area/power/gates read and tabled | **Not started** |
| A/B delta assessed against F17 floor | **Not started.** This is the actual gating step before any claim |
| HQC ASAP7 read\_hdl defect repair | **Not resumed this session** |
| B3, B5, B6 area/power (v2-script baseline runs) | **Still unread on server** |
| F11 double-claim (INDEX vs chip doc numbering) | **Still open, unresolved** |
| Netlists for optimized sweep | **Not pulled** |

---

## Next steps, in the order they gate each other

1. Pull the optimized log and all per-point reports off the server, same pattern as the baseline pull. Nothing from this run is committed yet.  
2. Read area/gates/power for all eight optimized points into a table, same extraction script used for `bf2x2_sweep.tsv`.  
3. Compare 578 ps (C5) against 573 ps (new) on area and power, the same way F17 compared 578 against 581\. This determines whether the sweep shows a real difference or another floor-level artifact.  
4. Only after step 3: decide whether the paper can claim an ASIC-side butterfly result at all, and in what form.  
5. Commit the optimized sweep, write its Results of Record rows (D-series suggested, since C is taken), and extend or supersede the 08-10 findings doc rather than starting a fresh one, since it is the same block and the same week.  
6. Separately, and not gating the above: resolve the F11 double-claim in INDEX.md, and read B3/B5/B6 off the server.

---

## Open questions for the advisor, unchanged plus one

Carried from `2026-08-10_bf2x2_ooc_fmax.md`, all five still open. Add:

6. If the optimized sweep's delta does not clear the measurement floor (F17), is a documented null result at ASIC block level, alongside the chip-level FPGA win, an acceptable pairing for the D\&T submission, or does the ASIC section need to stay a portability-only contribution as originally scoped in question 1?

