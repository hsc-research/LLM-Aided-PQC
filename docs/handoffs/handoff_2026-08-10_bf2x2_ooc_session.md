# Handoff: butterfly2x2 out-of-context session, 2026-08-10

Paste this at the start of a new chat. It assumes the reader knows the project
builds a correctness-gated LLM-driven RTL optimization agent for PQC
accelerators (ML-DSA and HQC, Artix-7 FPGA and ASAP7 7nm ASIC) and knows
nothing else. It supersedes nothing in the 2026-08-08 ASIC handoff; it
continues it.

---

## Ground rules for this conversation

1. Never quote a performance number that is not in a RESULTS OF RECORD table.
   If asked about a result and it is not there, say so rather than
   reconstructing it.
2. Distinguish measured from proposed. A next step in a findings doc is not a
   result.
3. Measurement configuration travels with the number: effort level, synthesis
   directives, corner, OOC mode, blackboxing, clock period, clock uncertainty,
   and which of the two Genus scripts was used.
4. Do not let a claimed delta smaller than known tooling sensitivity pass
   without flagging it. On Genus, effort setting alone moves achieved
   frequency by about 11 percent.
5. I run all commands locally and paste output. Give concise code and
   direction, not free-form RTL. No em dashes in any deliverable.
6. RTL edits follow: `.bak` backup, anchor-count assert, gate, KAT at all
   three security levels, synth, commit. Ask for explicit approval before any
   edit to a source file.
7. Watch for vacuity. Verify the files being synthesized are the files that
   changed. This session that check caught a real defect. See "The arm naming
   defect" below.
8. Do not guess. Confirm against the repo or the server before asserting.
9. If unsure whether something is established or proposed, ask.

---

## Environment

- Local: WSL Ubuntu on Windows, repo at `/mnt/c/PQC/hqc`, GitHub
  `hsc-research/LLM-Aided-PQC`.
- Remote: `ssh engr` (`engr-r940s01.engr.uidaho.edu`), Cadence Genus
  25.12-s067_1, ASAP7 PDK, project copy at `~/pqc/hqc/`. **The server tree is
  not a git checkout.**
- `ssh engr 'cmd'` prints a post-quantum key exchange warning to stderr on
  every call. Ignore it.
- `nohup ... &` over ssh returns immediately whether or not the process
  survived. Always confirm with `ps -eo pid,etime,args | grep -i [g]enus` and
  by reading the log, not by the absence of an error.
- Genus takes 30 to 60 seconds to start. A run that dies on a bad path still
  produces about a minute of silence first.

### The two synthesis scripts differ in ways that matter

| | `genus_asap7.tcl` | `genus_asap7_v2.tcl` |
|---|---|---|
| Timing report | `report timing`, one path | `report timing -nworst 20` |
| Stage stamps | none | `syn_generic`/`syn_map`/`syn_opt` START and DONE |
| `write_db` checkpoints | none | generic, mapped, final |
| Empty-OUTDIR guard | none | lines 60 to 63, aborts if OUTDIR non-empty |

Both set `syn_generic_effort`, `syn_map_effort`, `syn_opt_effort` to `high`.

`scripts/asap7_fmax.py` (50 lines) calls `genus_asap7.tcl`, not v2, and writes
every search point into one OUTDIR. It therefore cannot be pointed at v2
without also giving each point its own OUTDIR, or the v2 guard aborts the
second point. The script does correctly refuse to run unless HI meets and LO
violates, which is the bracket-asymmetry discipline the project needs.

---

## The arm naming defect, found and fixed this session

`asic/arms/bf2x2_baseline/` on the server contained **optimized** RTL, not
baseline. It was byte-identical to `agent/mldsa/mldsa_src/butterfly.v`, which
is the deeper-pipeline version carrying the `butterfly_dsp_pipeline` and
`butterfly_round2_areg` FPGA wins.

The two ML-DSA butterfly variants are distinguishable by line number, which is
the fastest way to tell them apart in a Genus log or a timing report:

| | `asic/arms/mldsa_baseline/butterfly.v` | `agent/mldsa/mldsa_src/butterfly.v` |
|---|---|---|
| `adder = adda + addb` | line 169 | line 174 |
| Genus operator name | `add_169_28` | `add_174_28` |
| `aj3` depth | `[4:0]` | `[6:0]` |
| `valid_sr` | 10 bits | 11 bits |
| Extra pipeline regs | none | `mult_p`, `sub_r`, `add_r`, `zeta_delay3` |
| `butterfly2x2.v` delay lines | `z2_sr`/`z3_sr` `[8:0]` | `[10:0]` |

The 78-hour full-chip run read `asic/arms/mldsa_baseline/`, confirmed from
`run_base/chip_base.log` and independently from the committed chip timing
report, which names `add_169_28`.

`bf2x2_baseline/` has been repopulated from `mldsa_baseline/` and verified by
md5 (`194207da29ff87473c6f7f002a7d2447` for `butterfly.v`,
`bd834d41f0a9143c1e40244d6a8fc716` for `butterfly2x2.v`, matching
`mldsa_baseline/`). Every run after 13:04 read the corrected arm.

**Generalisation for the findings doc:** the operator line number in a Genus
instance name is a free provenance check. If a report says `add_174_28` and
the run was supposed to read the baseline, the run read the wrong file.

---

## RESULTS OF RECORD

All rows: `butterfly2x2` out of context, ASAP7 7nm, `PVT_0P7V_25C`, effort
`high` at all three stages, `genus_asap7_v2.tcl`, `-nworst 20`, pre-layout,
memories not involved. Logs are on the server only, see "What is not committed".

Rows B1 to B3 used `sdc/butterfly2x2.sdc` **without** `set_clock_uncertainty`.
Rows B4 to B8 used the same file **with** uncertainty at 5 percent of period,
added this session to match the chip SDC. The old version is preserved on the
server as `sdc/butterfly2x2.sdc.bak`.

| # | Arm RTL | Period | Unc | Result | Path 1 endpoint | Wall | Cells | Total area | Power |
|---|---|---|---|---|---|---|---|---|---|
| B1 | optimized (`add_174`) | 2000 ps | no | MET 0 ps | `BF2_1_ajlen5_reg[23]/D` | 18m47s | 14342 | 46381.316 | 2.586 mW |
| B2 | baseline (`add_169`) | 2000 ps | no | MET 3 ps | `BF1_1_barrett_datai_reg[45]/D` | 17m19s | 13828 | 42255.899 | 2.456 mW |
| B3 | baseline | 2000 ps | yes | MET 1 ps | `BF1_1_ajlen2_INTT_reg[23]/D` | not captured | not captured | not captured | not captured |
| B4 | baseline | 1400 ps | yes | MET 0 ps | `BF1_1_ajlen2_INTT_reg[23]/D` | 14m52s | 14458 | 43949.280 | not captured |
| B5 | baseline | 900 ps | yes | MET 0 ps | `BF1_1_ajlen5_reg[23]/D` | not captured | not captured | not captured | not captured |
| B6 | baseline | 600 ps | yes | MET 0 ps | `BF2_2_aj4_reg[23]/D` | 21m53s | not captured | not captured | not captured |
| B7 | baseline | 400 ps | yes | **VIOLATED -168 ps** | `BF2_1_barrett_datai_reg[45]/D` | not captured | 20429 | 60928.779 | 15.331 mW |

B1 is on the wrong RTL for a baseline comparison but is a valid measurement of
the optimized variant. Keep it; do not compare it to B2 through B7 as if the
period were the only difference.

"not captured" means the number exists in a report on the server and was not
read during the session. It is retrievable, not lost.

### What does not exist yet

- **No Fmax for `butterfly2x2`.** The bracket 400 to 600 ps is proven (B7
  violates, B6 meets) but the binary search has not been confirmed to have run
  or completed. Do not convert any period in the table to a frequency and call
  it Fmax. B2 through B6 are the tool meeting a requested target, exactly like
  A1 on the chip.
- **No area or power series across the sweep.** Only B2, B4 and B7 have area,
  only B2 and B7 have power.
- **No optimized-arm sweep.** Every period point except B1 is baseline RTL.
- **No FPGA run on anything from this session.**
- **No KAT on anything from this session.** No RTL was edited. No `.bak`, no
  gate, no KAT was needed and none was run.

---

## Findings

### F-A: the block-level experiment achieves its cost goal

`butterfly2x2` out of context synthesizes in 15 to 22 minutes against 78 hours
1 minute for `combined_top`. Verified across five runs at four periods.
Turnaround is not monotonic in period: 14m52s at 1400 ps, 21m53s at 600 ps.

**Implication:** the advisor's instruction to reduce turnaround before
launching another chip run is satisfied. Exploration at block level is cheap.

### F-B: the block does not reproduce the chip critical path at 2000 ps

Same RTL by md5, same period, same PDK and corner, same effort. The chip binds
`BF2_1_aj4_reg[23]/D` through `add_169_28`. The block at 2000 ps binds
`barrett_datai_reg[45]` through `mul_170_29` (B2), or `ajlen2_INTT_reg[23]`
(B3) once uncertainty is matched. `add_169` appears zero times in the B2 and
B3 timing reports.

**This is not evidence the adder is fast at block level.** Every one of the 20
reported paths in B2 and B3 met at 1 to 3 ps. Genus optimized to the requested
period and stopped, so path ranking reflects where the tool chose to stop, not
where the design's limits are. The same caveat that applies to A1 applies
here.

### F-C: which operator binds is period-dependent, on identical RTL

| Period | `add_169` count in report | Rank of first `aj4` endpoint | Structure at that endpoint |
|---|---|---|---|
| 2000 ps | 0 | absent from top 20 | n/a |
| 1400 ps | 32 | Path 15, 2 ps slack | named `add_169_28` carry cells |
| 900 ps | 0 | Path 3, 0 ps slack | generic gates, no `FAx1`, no operator name survives |
| 600 ps | not counted | Path 1, 0 ps slack | not inspected |
| 400 ps | not counted | absent from top 5, multiplier binds | not inspected |

At 900 ps the path into `aj4_reg[22]` starts at `zeta_delay_reg[0]` and runs
through roughly 30 stages of `AOI21`, `OAI221`, `NAND3`, `MAJIxp5`,
`A2O1A1Ixp33`. The netlist shows one recognisable operand net,
`BF1_1_ajlen1[8]`. The operator boundary is gone; Genus dissolved and remapped
the arithmetic.

**Implication, and this is the scientifically interesting one.** The advisor's
sharper claim was that optimization opportunities are backend-dependent. This
sweep says they are also **constraint-dependent within one backend**. The
statement "Genus produced a ripple-carry adder for this RTL, this library, and
this timing constraint" is now supported by direct evidence for the third
clause, not just hedged. Verify the 600 ps and 400 ps rows before writing this
up, since two of the five cells above were not inspected.

### F-D: `FAx1` chains are not by themselves evidence of the adder

In B1 at 1400 ps, Path 2 is a chain of `FAx1` cells propagating `CI` to `CON`,
which looks exactly like the chip's ripple-carry finding. The netlist shows
those cells belong to `WALLACE_CSA_DUMMY_OP926`, a carry-save structure inside
the **multiplier**. The adder's cells in the same report are named
`BF2_2_add_169_28_g*`.

**Rule:** identify the operator by instance name or by netlist lookup of the
cell's input nets. Never by cell type. A `FAx1` chain can come from the
multiplier's Wallace tree, the adder, or the subtractor.

### F-E: the chip's path ranking below rank 1 is unrecoverable

`genus_asap7.tcl` line 60 is a bare `report timing`, so the chip report
contains exactly one path. No `.db` was written by that script, confirmed by
`ls` on both `out/chip_base/` and `run_base/`. The 78-hour run cannot be
re-reported without re-synthesizing, which the advisor has ruled out.

**Implication:** the question "where does the multiplier rank in the chip" has
no answer from existing artifacts. Any block-versus-chip comparison is rank 1
against rank 1 only. Future chip runs must use v2, or at minimum `report
timing -nworst 20` and a `write_db`.

### F-F: the cost of pushing past the limit

B7 against B2: period 400 ps against 2000 ps, cells 20429 against 13828 (up 48
percent), total area 60928.779 against 42255.899 (up 44 percent), power 15.331
mW against 2.456 mW (up 6.2x). And it still misses by 168 ps.

Caveat: B2 has no uncertainty and B7 does, so the two differ in more than
period. B4 (1400 ps, with uncertainty, 43949.280) is the cleaner area
comparison point against B7.

---

## What is not committed

**Nothing from this session is in git.** All artifacts are on the server,
which is not a checkout.

| Item | Location | State |
|---|---|---|
| B1 reports and log | server `out/bf2x2_probe/`, local `logs/asic/asap7_bf2x2_optvariant_20260810/` | pulled local, staged then unstaged, directory renamed, not committed |
| B2 to B7 reports and logs | server `out/bf2x2_*` and `run_bf2x2_*` only | not pulled |
| `butterfly2x2.sdc` (with uncertainty) | server `asic/asap7/sdc/`, local `asic/asap7/sdc/` | pulled local, not committed |
| `butterfly2x2.sdc.bak` (without uncertainty, backs B1 to B3) | server only | not pulled |
| `.gitignore` negation for `fullkat_run.log` | local | modified, not committed |
| `agent/mldsa/fullkat_run.log` | local | 53k lines newly tracked, not committed |

The blanket `*.log` rule in `.gitignore` still blocks the Genus run logs. The
`!agent/mldsa/fullkat_run.log` negation added this session covers only that
one file. Run logs need `git add -f` or their own negation.

Standing check before believing anything landed:
`git ls-files <dir> | wc -l` against `ls <dir> | wc -l`.

---

## Checklist

### Immediate, gates everything else

- [ ] Confirm whether the `asap7_fmax.py` binary search over 400 to 600 ps was
      ever launched. The command was issued at the end of the session and no
      output confirmed it. Check `ps -eo pid,etime,args | grep -i [g]enus` and
      `cat ~/pqc/hqc/asic/asap7/fmax_bf2x2.log`. If it did not start, relaunch.
- [ ] Pull B2 to B7 reports and run logs off the server into
      `logs/asic/asap7_bf2x2_<period>_20260810/`.
- [ ] Pull `butterfly2x2.sdc.bak` and save as a distinct filename so B1 to B3
      have their actual configuration recorded.
- [ ] Commit, with the SDC variant and the arm md5 named in the message.
- [ ] Verify with `git ls-files` per directory.

### Fill the gaps in the Results of Record

- [ ] Read the missing area, power and wall figures for B3, B5, B6 from the
      reports already on the server. No new runs needed.
- [ ] Inspect the 600 ps and 400 ps paths for operator identity, to complete
      the F-C table. Use netlist lookup, not cell type.

### Then, the actual experiment

- [ ] Pick the comparison period from the search result: the period where the
      baseline just misses. Hold it fixed for every arm thereafter.
- [ ] Decide whether the comparison period should be near the chip's operating
      point or near the block's limit. These give different answers about
      which operator is critical, per F-C, and the choice needs stating in the
      paper rather than being made implicitly.
- [ ] Only then test the two cycle-neutral candidates from the 2026-08-08
      handoff: (a) precompute the `ajlen1 < zeta_delay` mux select at line 244,
      the existing `flag_precompute` rule; (b) restructure the adder by
      directive or RTL. Approval required before either edit. Full protocol:
      `.bak`, anchor-count assert, gate, KAT at all three levels, synth,
      commit.
- [ ] Note that (a) targets the mux feeding `aj4`. At periods where the block
      binds through `barrett_datai` or `ajlen2_INTT`, that edit may measure as
      no effect even if it would help in context. A null result there is a
      false negative, not a finding.

### Carried over from 2026-08-08, untouched this session

- [ ] Four-way analysis: FPGA-to-ASIC path migration, the RTL edit selected
      from the ASIC report, the PPA tradeoff, and whether the same edit helps
      or hurts on FPGA. Item four needs an Artix-7 run on the modified RTL.
- [ ] HQC reproducible configuration. `genus_asap7_v2.tcl` line 40 is still a
      bare `read_hdl [glob $RTL_DIR/*.v]` with no defines. Any HQC run launched
      with it synthesizes a configuration no KAT has validated. Fix before any
      HQC ASAP7 run.
- [ ] HQC port frontier: unresolved VLOGPT-22 on `r1_internal` at
      `encrypt_parallel.v` line 410. Work lives at `engr:/tmp/armtest/` and
      `engr:~/pqc/hqc/asic/portfix_wip/`, neither in git, and `/tmp` clears on
      reboot.
- [ ] Record distinct root defects for HQC, not total parser error count.
- [ ] ML-KEM repository evaluation: Brno AXE / PQC / DiKy, the Zenodo release
      for "Two Birds, One Mask", and `chipsalliance/adams-bridge`.

### Paper and coordination, from the 2026-08-10 group meeting

- [ ] Send Sanjay the specific locations where the LLM made changes in the
      design, for the figures.
- [ ] Finish final ML-DSA runs and generate figures.
- [ ] Run HQC and report the agent's fix-and-run time.
- [ ] Work methodology and framework figures while runs are in flight.
- [ ] Dump synthesis jobs on the server before travelling Thursday.
- [ ] Update the paper with results Friday or Saturday.
- [ ] Repo cleanup with Zain and Sanjay before submission: clone to a new
      branch, strip notes, add framework figure and instructions.

Tracked but not owned by Lloyd: Zain is emailing Partha about a deadline
extension to end of month, and has an area-by-block script he offered to
share. The extension answers whether "all three security levels for HQC,
ML-DSA and soon ML-KEM" lands before or after the 15th.

---

## Open questions for the advisor

Carried forward, still unanswered:

1. Is a single-arm pre-layout snapshot with a flip-flop memory model worth
   reporting in the paper, or should the ASIC section stay a portability
   finding only?
2. Does "all three security levels" mean before the 2026-08-15 D&T deadline or
   after? The manuscript currently reports no ASAP7 result and says so.
3. Priority order between the D&T submission and starting ML-KEM.

New from this session:

4. The block-level experiment was meant to validate the adder finding at
   smaller hierarchy. It does so only at some periods, and at 900 ps the adder
   is not a recognisable adder any more. Does the constraint-dependence result
   (F-C) replace the adder finding as the claim, sit alongside it, or need
   more evidence before either is written up?
5. The chip's rank-2-and-below paths are unrecoverable (F-E). Is that
   acceptable for the paper, or does the ASIC section need a chip rerun with
   `-nworst 20` at medium effort?
