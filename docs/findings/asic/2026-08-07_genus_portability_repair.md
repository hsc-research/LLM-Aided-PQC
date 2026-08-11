# FINDINGS: HQC cross-toolchain portability repair for Genus elaboration

**Status: IN PROGRESS.** Work is in `/tmp/armtest` on `engr` and is not
committed. Nothing in this document changes any FPGA number.

Session date: 2026-08-07, approximately 17:30 to 22:30 Pacific.

---

## RESULTS OF RECORD

| # | Design | Config | Effort/Directives | Metric | Value | Log path | Date |
|---|---|---|---|---|---|---|---|
| R1 | ML-DSA `combined_top` | ASAP7, period 2000 ps, SDC `combined_top.sdc`, OOC N/A | `syn_generic_effort high`, `syn_map_effort high`, `syn_opt_effort high` | `syn_map` global mapping elapsed | 40:48:11 | `~/pqc/hqc/asic/asap7/run_base/chip_base.log` (server, NOT COMMITTED) | 2026-08-07 |
| R2 | ML-DSA `combined_top` | as R1 | as R1 | cumulative elapsed at end of `syn_map` | 75:55:54 | as R1 | 2026-08-07 |
| R3 | ML-DSA `combined_top` | as R1 | as R1 | peak memory during global mapping | 69.12 GB | as R1 | 2026-08-07 |
| R4 | ML-DSA `combined_top` | as R1 | as R1 | distributed mapping partitions | 52 | as R1 | 2026-08-07 |
| R5 | ML-DSA `combined_top` | as R1 | as R1 | slowest single partition elapsed | 33.6 h (`pbs_map_5`) | as R1 | 2026-08-07 |

**Not results.** No frequency, area, or power figure was produced today. The
`syn_opt` stage began at approximately 21:09 and has not completed;
`~/pqc/hqc/asic/asap7/out/chip_b` is empty.

**What does not exist yet.** No HQC ASAP7 elaboration. No HQC ASAP7 synthesis.
No KAT run against any repaired file. No commit of any repair. No Results of
Record row for the composition closure figures (69.0 / 69.5 MHz) discussed
elsewhere. R1 to R5 are read from a log on a server tree that is not a git
checkout and must be copied and committed before they may be quoted.

---

## Terminology

| Term | Means |
|---|---|
| repair | An edit to RTL made solely so a stricter front end will parse it |
| pure reorder | An edit for which `LC_ALL=C sort` of before and after are byte-identical |
| identical-value substitution | Replacing an expression with a name bound to that same expression in the same scope |
| cascade | An error reported only because the parser lost sync on an earlier real defect |
| frontier | The line number of the first real error in the current read |

---

## F1. The correct read configuration is `SHARED=1 SHARED_ENCAP=1`

**Observed.** `hardware/joint_design/tcl/joint_design.tcl` lines 9 and 10 set
both defines for the Vivado fileset. The Genus read script had no `-define`,
so it was compiling `ifndef SHARED_ENCAP` branches that the real build never
sees.

**Done.** Test script rewritten as
`read_hdl -define {SHARED=1 SHARED_ENCAP=1} [glob ...]`.

**Verified.** With the defines set, the `start_encap` redeclaration at
`decap.v` line 864 disappeared, because `start_encap` is correctly the port
declared at line 184 inside the `ifdef SHARED_ENCAP` block.

**Implication.** `scripts/genus_asap7_v2.tcl` still has a bare
`read_hdl [glob $RTL_DIR/*.v]`. Any HQC run launched with it would synthesize
a configuration that no KAT has ever validated. This must be fixed before any
HQC ASAP7 run.

---

## F2. Error counts do not measure progress; the frontier does

**Observed.** Across nine read iterations the reported error count moved
44, 34, 34, 20, 21, 24, 23, 70, 67, 23, 22 while the frontier advanced
monotonically: `state_ram.v` 122, 228, 278, 378, then `decap.v` 332, 422,
862, then `decrypt.v` 191, then `encap.v` 247, 328, 507, 516, 562, then
`encrypt_parallel.v` 209.

**Verified.** `state_ram.v` reported 44 errors and contained four defects.
Every other error was cascade.

**Implication.** The defect survey figure of 102 instances in 13 files is a
static count, not a count of distinct defects. The two numbers should not be
conflated in the paper.

---

## F3. Five distinct defect classes, not one

| Class | Genus code | Example | Repair |
|---|---|---|---|
| C1 unindexed array in sensitivity list | VLOGPT-61 | `always @(din or dout_internal)` | `always @*` |
| C2 use before declaration | VLOGPT-20 | `sel_uv` used 328, declared 561 | hoist declaration |
| C3 duplicate declaration | VLOGPT-22 | `pm_out` at 413 and 549 | delete the later |
| C4 macro expression in declaration range | VLOGPT-117 | `wire [\`CLOG2(X)-1:0] ...` | bind to a localparam or existing parameter |
| C5 implicit net from prior use | VLOGPT-22 / VLOGPT-86 | `count_hash_inputs` used at 544, declared 562 | hoist declaration |

**Implication.** The current D&T text describes these as
"declaration-ordering and related surface issues." C1 and C4 are not that.
C1 is a sensitivity-list conformance difference and C4 is a macro-folding
difference in a declaration context. The description in the paper undercounts
the finding.

---

## F4. Repairs applied and how each was verified

All in `/tmp/armtest`. None committed. None KAT-tested.

| File | Repairs | Class | Verification |
|---|---|---|---|
| `state_ram.v` | 4 sensitivity lists at 122, 228, 278, 378 | C1 | file parses standalone, 0 errors |
| `decap.v` | 2 `\`CLOG2(X)` to `LOGX` | C4 | `LOGX` bound to `\`CLOG2(X)` at line 88, same module |
| `decap.v` | 6 declarations hoisted | C2 | sorted-diff pure reorder |
| `decap.v` | 4 declarations hoisted | C2 | sorted-diff pure reorder |
| `decap.v` | 3 uses bound to new `LOG_M_WORDS` localparam | C4 | identical expression, declaration placed above first use |
| `decrypt.v` | 4 declarations hoisted | C5 | sorted-diff pure reorder |
| `encap.v` | 2 declarations hoisted | C2 | sorted-diff pure reorder |
| `encap.v` | `LOG_HASH_RD` and `LOG_M_WORDS` localparams, 6 uses | C4 | identical expression; line count +2 only |
| `encap.v` | `sel_uv` hoisted, 3 `\`CLOG2(RAMDEPTH)` to existing `LOG_RAMDEPTH` | C2, C4 | sorted-diff; `LOG_RAMDEPTH` already used in port list at line 180 |
| `encap.v` | `u_v_reg` hoisted | C2 | sorted-diff pure reorder |
| `encap.v` | 4 declarations hoisted | C2 | sorted-diff pure reorder |
| `encap.v` | `count_hash_inputs` hoisted with its commented predecessor | C5 | sorted-diff pure reorder |
| `encrypt_parallel.v` | `pm_out` duplicate at 549 deleted | C3 | line count 1193 to 1192; survivor at 413 has identical width and type |
| `encrypt_parallel.v` | 5 declarations hoisted | C2 | sorted-diff pure reorder |
| `encrypt_parallel.v` | `sel_fw` removed from multi-signal declaration | C3 | present at 195 and in the 209 line in `ep.bak2`, taken before any hoist |

**Not yet repaired.** `r1_internal` in `encrypt_parallel.v` at line 410
reports VLOGPT-22 with only one visible declaration. Mechanism not yet
identified. This is the frontier.

---

## F5. Three declarations carry initializers

`reg sel_e = 0;`, `reg [LOG_WEIGHT_ENC-1:0] fw_addr, fw_addr_reg = 0;`, and
`reg [LOG_HASH_RD-1:0] total_shake_input_count = HASH_RAMDEPTH;` were moved.

**Verified as pure reorders by sorted diff.** Not verified as
behaviour-preserving in simulation. Reg initializers are simulation-only for
ASIC synthesis, so position should not affect synthesized hardware, but this
is an argument and not a measurement. The KAT run will settle it.

---

## F6. Multi-signal declarations move signals that were not the target

Hoisting `reg wen_fw, sel_fw, rd_fw;` to fix `rd_fw` also moved `wen_fw` and
`sel_fw`. Moving `sel_fw` exposed a duplicate declaration at line 195 that
had been latent.

**Verified pre-existing**, not introduced: `ep.bak2`, taken before any hoist
in that file, shows `sel_fw` declared at both 195 and 209.

**Implication for the agent-feature idea.** An automated hoist template must
either move only the named signal, by splitting the declaration, or record
that it moved siblings. A sorted diff will not catch a latent duplicate that
the move exposes, because no line content changed.

---

## F7. ML-DSA `combined_top` mapping is feasible but slow; the outliers set the clock

`syn_map` completed after 52 partitions across three partitioning phases.
Most partitions returned in roughly 40 minutes. Four did not: `pbs_map_2` at
24.0 h, `pbs_map_8` at 25.7 h, `pbs_map_3` at 22.7 h, and `pbs_map_5` at
33.6 h. A phase cannot close until its slowest partition returns, so four
outliers set a 41-hour global mapping stage.

**Verified** from the stage summary table in `chip_base.log`.

**Not verified.** Whether `syn_opt` completes at all. It began at
approximately 21:09 on 2026-08-07 and relaunched eight super-threading
servers.

**Implication.** Memory is not the constraint at 69.12 GB peak against
1006 GB available. The design is mapping-bound. If a second attempt is made,
the lever is the clock period, not the machine: at 2000 ps the reported slack
during mapping was around -215 ns, roughly two orders of magnitude from
closure, and Logic Structuring consumed 94 percent of per-partition runtime
in the two partitions whose breakdown was logged.

---

## F8. Arms are staged and differ correctly

`asic/arms/hqc_baseline` 58 files, `asic/arms/hqc_optimized` 59 files.
Baseline list deduplicates two byte-identical copies of `clog2.v`, preferring
the non-shake256 path, matching `synthesizer.py`.

Vacuity probe: `build/joint_design/v_minus_uy.v` contains 6 flag/oob matches
against 0 in `hardware/decap/v_minus_uy.v`, so the composition is live and
not silently reverted.

Arms differ in 15 files plus `mem_single_dist.v` present only in optimized:
9 SWAP block wins, 4 declaration-hoist repairs applied previously, 1
registered pm client select in `hqc_kem_joint_design.v`, and 1 `decap.v`
SHAKE tie-off under SHARED_ENCAP.

**Implication for the paper.** The current text describes the HQC optimized
arm as nine win-carrying leaf modules plus one memory swap. The arm carries
more than that. The description should be widened.

---

## File map

| What | Where | Committed |
|---|---|---|
| Working repairs, 58 files | `engr:/tmp/armtest/` | NO. `/tmp` is cleared on reboot |
| Snapshot taken mid-session | `engr:~/pqc/hqc/asic/portfix_wip/` | NO. Predates the `encap.v` and `encrypt_parallel.v` repairs |
| Read-test script with defines | `engr:/tmp/armtest/a5.tcl` | NO |
| Per-iteration read logs | `engr:/tmp/armtest/a*.log`, `t*.log` | NO |
| Staged arms | `engr:~/pqc/hqc/asic/arms/hqc_{baseline,optimized}/` | NO |
| Arm manifest with md5 and source commit | `engr:~/pqc/hqc/asic/arms/MANIFEST.txt` | NO |
| Hardened Genus script | `engr:~/pqc/hqc/asic/asap7/scripts/genus_asap7_v2.tcl` | NO |
| HQC SDC | `engr:~/pqc/hqc/asic/asap7/sdc/hqc_joint.sdc` | NO |
| ML-DSA run log | `engr:~/pqc/hqc/asic/asap7/run_base/chip_base.log` | NO |

The server tree `~/pqc/hqc` is **not a git checkout**. Everything above exists
in exactly one place.

---

## Next steps, in the order that unblocks the most

1. Copy `/tmp/armtest` off `/tmp` and into the repo on a branch. `/tmp`
   survives until the next reboot and the server has rebooted twice since
   May.
2. Resolve `r1_internal` in `encrypt_parallel.v` line 410. This is the
   frontier.
3. Continue the read loop until `ARM_READ_OK` appears.
4. Add `-define {SHARED=1 SHARED_ENCAP=1}` to `genus_asap7_v2.tcl` (F1).
5. Run the KAT at HQC-128, HQC-192, and HQC-256 on the repaired source.
   Nothing repaired today has been functionally tested.
6. Re-close the HQC FPGA baseline on the repaired source and confirm it
   reproduces 9.12 ns, 109.6 MHz, WNS +0.072, mirroring the `cd92639`
   control. Until this passes, the repairs are not established as
   FPGA-neutral.
7. Copy `chip_base.log` into the repo so R1 to R5 have a committed log path.
8. Apply the same repairs to `hqc_optimized`, where `decap.v`,
   `encap.v`, and `encrypt_parallel.v` differ from baseline. The repairs must
   be equivalent in both arms or the comparison is invalid.

---

## Open questions for the advisor

1. `sel_uv_int` in `encap.v` is written to 0 at fifteen sites and never read.
   `sel_uv` is a separate register read at line 328. Is `sel_uv_int` dead
   code from a variant, or was it intended to be set somewhere? This does not
   block the repairs, since both signals are declared, but it looks like a
   latent defect in the published design.
2. The `K+` and `K-` forms of `\`CLOG2((K±(32-K%32)%32)/32)` both appear in
   `decap.v`, the `K-` form only in the port declaration at line 186 and the
   `K+` form in three body uses. Intentional, or a typo in the original?
3. Given the August 15 deadline and that the manuscript reports no ASAP7
   result, how much further should this be pushed before the deadline?
