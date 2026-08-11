# FINDINGS: first completed ASAP7 full-chip synthesis, ML-DSA `combined_top` baseline

**Supersedes:** the "no ASAP7 result exists" statement in
`docs/findings/asic/2026-08-07_genus_portability_repair.md`. That document was
written at 22:30 on 2026-08-07 while this run was still in `syn_opt`. The run
completed at 23:52 the same evening. Rows R1 to R5 in that document are
retained and now have a committed log path.

Run started 2026-08-04 17:22. Completed 2026-08-07 23:52. Verdict `Normal
exit`, `Info=6, Warn=0, Error=0, Fatal=0`.

---

## RESULTS OF RECORD

Configuration for every row below: ML-DSA `combined_top`, ASAP7 7nm,
`PVT_0P7V_25C`, interconnect mode global, area mode physical library, clock
period 2000 ps, SDC `sdc/combined_top.sdc` with false paths on `sec_lvl*`,
`mode*`, `rst`, `start`, and I/O delay at 10 percent of period.
`syn_generic_effort`, `syn_map_effort`, and `syn_opt_effort` all `high`.
Memories modeled as flip-flop arrays, not black boxes. Pre-layout, no place
and route.

| # | Metric | Value | Log |
|---|---|---|---|
| A1 | Setup slack | MET, +1 ps | `logs/asic/asap7_chip_base_20260808/combined_top_p2000_timing.rpt` |
| A2 | Data path delay | 1882 ps (required 1882, setup 18, uncertainty 100) | as A1 |
| A3 | Binding path | `BF1_1_modei_reg[0]/CLK` to `BF2_1_aj4_reg[23]/D` | as A1 |
| A4 | Total cell count | 4,575,894 | `.../combined_top_p2000_area.rpt` |
| A5 | Total area | 16,891,822.277 (cell 12,800,297.782, net 4,091,524.495) | as A4 |
| A6 | Total power, vectorless | 1.612 W (leakage 0.067, internal 1.262, switching 0.283) | `.../combined_top_p2000_power.rpt` |
| A7 | Wall time, `syn_map` global mapping | 40:48:11 | `.../stage_summary.txt` |
| A8 | Wall time, `syn_opt` (`1ST_ST`) | 02:09:13 | as A7 |
| A9 | Wall time, cumulative | 78:29:21 | as A7 |
| A10 | Peak memory | 69.12 GB (during global mapping) | as A7 |

**These are not closure numbers.** A1 is MET at the requested period, which
means `syn_opt` optimized to the constraint and stopped. The achievable
period is below 2000 ps and is unknown. 2000 ps must not be converted to
500 MHz and reported as Fmax; that would be reporting the constraint back.
The project prohibition on projected Fmax applies here in the same form.

**What does not exist yet.** No optimized ML-DSA arm on ASAP7, so no
comparison. No HQC ASAP7 result of any kind. No place and route, so no
post-route numbers. No SAIF or VCD driven power, so A6 is vectorless with
default switching activity.

---

## F9. The binding structure is technology-dependent

**Observed.** On Artix-7 the ML-DSA baseline binds from
`DECODER/encode_mode_reg[1]` to `ENCODER/PISO_reg[117]`, a 256-bit
variable-shift serializer. On ASAP7 at 2000 ps the same RTL binds inside the
NTT butterfly, from `BF1_1_modei_reg[0]` to `BF2_1_aj4_reg[23]`.

**Breakdown of the ASAP7 path.** Of 1882 ps total, the segment from 542 ps to
1787 ps is a ripple-carry chain in `BF_CIRCUIT_BF2_1_add_169_28`: 16 `FAx1`
full adders with `CI` to `CON` carry propagation, 8 `MAJx2` majority gates,
and `INVxp33` inverters between stages at roughly 30 to 36 ps per stage. That
is **1245 ps, or 66 percent of the critical path, in one adder**.

**Verified** by reading the full path in the committed timing report.

**Interpretation.** On FPGA, adders map onto dedicated carry chains and are
fast, so this structure never appeared in any Artix-7 timing report. In 7nm
standard cells there is no carry chain, and the synthesizer inferred
ripple-carry rather than a lookahead or carry-select structure. The
bottleneck is therefore a property of the target technology and not of the
RTL alone.

**Implication.** An RTL edit selected against one backend's timing report
does not necessarily touch the other backend's binding structure. This is the
cross-technology analogue of the block-versus-chip result in
`FINDINGS_crossdesign_closure.md`: the tier at which a target is chosen
determines whether the edit can pay.

---

## F10. Area and power are dominated by the flip-flop memory model

**Observed.** Six inferred RAM instances account for 16,181,516 of the
16,891,822 total area, approximately **96 percent**:

| Instance | Module | Cell count | Total area |
|---|---|---|---|
| BRAM_0 | `dual_port_ram_WIDTH96_LENGTH4096` | 1,808,471 | 7,263,627.517 |
| BRAM_1 | `dual_port_ram_WIDTH96_LENGTH1024` | 552,862 | 1,946,145.189 |
| BRAM_2 | `..._1` | 558,695 | 1,953,407.027 |
| BRAM_3 | `..._2` | 558,585 | 1,957,536.490 |
| BRAM_4 | `..._3` | 320,369 | 1,093,302.406 |
| BRAM_5 | `..._4` | 563,419 | 1,967,497.594 |

Register power is 1.404 W of the 1.612 W total, **87 percent**.

**Implication.** A5 and A6 characterize the memory model, not the ML-DSA
datapath. A 7nm implementation would use compiled SRAM macros. Neither figure
should be quoted as an area or energy result for the accelerator. A1, A2, and
A3 are unaffected, because the critical path does not traverse the RAM
instances.

---

## F11. Runtime is dominated by technology mapping, and mapping cost is set by outliers

**Observed.** `syn_map` global mapping took 40:48:11. `syn_opt` at the same
`high` effort took 02:09:13. Mapping is therefore roughly **19 times** the
cost of optimization on this design.

Distributed mapping ran 52 partitions across three partitioning phases. Most
partitions returned in approximately 40 minutes. Four did not: `pbs_map_3` at
22.7 h, `pbs_map_2` at 24.0 h, `pbs_map_8` at 25.7 h, `pbs_map_5` at 33.6 h.
A phase cannot close until its slowest partition returns.

In the two partitions whose internal breakdown was logged, Logic Structuring
accounted for approximately 94 percent of partition runtime.

**Implication.** Memory is not the binding resource at 69.12 GB peak against
1006 GB available. Four levers are available for a shorter run, in expected
order of effect:

1. Blackbox or `dont_touch` the six RAM instances. They are 4.4M of 4.58M
   cells and are not on the critical path. This is a change to the
   measurement configuration and would make A4, A5, and A6 non-comparable
   with any previous or subsequent run, so both arms would need re-running.
2. Reduce `syn_map_effort` from `high`. Given F11, effort spent in mapping
   buys 19 times less than effort spent in optimization on this design.
3. Loosen the period. A1 shows the tool worked to a 1 ps margin, which is
   expensive.
4. Address the adder of F9. Logic Structuring is spending its time on a
   structure that a directive or an RTL change could remove.

**Not verified.** None of these four has been tried. Each is a hypothesis
about runtime, not a measured result.

---

## File map

| What | Where | Committed |
|---|---|---|
| Timing, area, gates, power reports | `logs/asic/asap7_chip_base_20260808/*.rpt` | yes |
| Full run log, 1.8 MB | `logs/asic/asap7_chip_base_20260808/chip_base.log` | yes |
| Stage timing summary, 40 lines | `logs/asic/asap7_chip_base_20260808/stage_summary.txt` | yes |
| Synthesized netlist, 582 MB | `engr:~/pqc/hqc/asic/asap7/out/chip_base/combined_top_p2000_netlist.v` | NO, deliberately excluded for size |
| Run directory | `engr:~/pqc/hqc/asic/asap7/run_base/` | NO |

---

## Next steps

1. Decide the memory model before running any second arm. Blackboxing changes
   A4, A5, and A6, so the baseline would need re-running to stay comparable.
2. If an optimized arm is wanted before 2026-08-15, it must start immediately
   at current settings, or start after applying levers 1 and 2 of F11 with the
   baseline re-run alongside it.
3. HQC ASAP7 remains blocked on the portability repairs of
   `2026-08-07_genus_portability_repair.md`.

## Open questions for the advisor

1. Is a single-arm pre-layout snapshot with a flip-flop memory model worth
   reporting, or should the ASIC section stay as a portability finding only?
2. Is the F9 ripple-carry result more valuable than a PPA comparison? It is a
   concrete, actionable target and it is technology-specific in a way the
   FPGA results are not.
3. For a second run, blackboxed memories or flip-flop arrays? The former is
   faster and more representative; the latter is what the current baseline
   used.
