> **SUPERSEDED 2026-08-12.** Every ASAP7 butterfly2x2 number below was measured
> with `Barrett_8380417.v` missing from the arm directory, leaving four modules
> blackboxed (`Unresolved 4` in every gates report). Do not quote 578 ps,
> 573 ps, the E-series head-to-head, or anything derived from them. See the
> banner on `docs/findings/asic/2026-08-10_bf2x2_ooc_fmax.md` and F27 in
> `docs/findings/mldsa/2026-08-12_bf2x2_fpga_ooc_closure.md`.

# Handoff: bf2x2 optimized A/B, determinism, HQC Genus port, 2026-08-11

Paste this at the start of a new chat. It assumes the reader knows the project
builds a correctness-gated LLM-driven RTL optimization agent for PQC
accelerators (ML-DSA and HQC, Artix-7 FPGA and ASAP7 7nm ASIC) and knows
nothing else.

Continues: `docs/handoffs/handoff_2026-08-10_bf2x2_ooc_session.md` and the
overnight optimized-sweep handoff.
Findings of record: `docs/findings/asic/2026-08-10_bf2x2_ooc_fmax.md`, which
now covers both arms.
Commits this session: `b5c1bcc`, `a62e217`, `7913455`, `ac80306`, `c39960a`.
All pushed to `origin/main`.

---

## Ground rules for this conversation

1. Never quote a performance number that is not in a RESULTS OF RECORD table.
   If asked about a result and it is not there, say so rather than
   reconstructing it.
2. Distinguish measured from proposed. A next step in a findings doc is not a
   result.
3. Measurement configuration travels with the number: effort, corner, OOC
   mode, blackboxing, clock period, clock uncertainty, and which Genus script.
4. Flag any claimed delta smaller than known tooling sensitivity. On Genus,
   effort setting alone moves achieved frequency by about 11 percent (F3).
5. I run all commands locally and paste output. Concise code and direction,
   not free-form RTL. No em dashes in any deliverable.
6. RTL edits follow: `.bak`, anchor-count assert, gate, KAT at all three
   security levels, synth, commit. Ask for explicit approval before any edit
   to a source file.
7. Watch for vacuity. Verify the files being synthesized are the files that
   changed.
8. **Do not guess. Confirm against the repo or the server before asserting.**
   This was added mid-session after several wrong inferences.
9. If unsure whether something is established or proposed, ask.

---

## Environment

- Local: WSL Ubuntu, repo `/mnt/c/PQC/hqc`, GitHub `hsc-research/LLM-Aided-PQC`.
- Remote: `ssh engr` (`engr-r940s01.engr.uidaho.edu`), Genus 25.12-s067_1,
  ASAP7 PDK, copy at `~/pqc/hqc/`. **Not a git checkout.**
- The PQ key-exchange warning on every `ssh` call is noise. Ignore it.
- `nohup ... &` over ssh returns whether or not the process survived. Confirm
  with `ps -eo pid,etime,args | grep -i [g]enus` and by reading the log.
- Genus takes 30 to 60 seconds to start, so a run that dies on a bad path
  still produces a minute of silence first.
- Stage stamps: `grep -E "^===== \[" <log>`. Plain `grep "====="` also matches
  Genus banner rows and is useless.

### Script equivalence, established this session

`genus_asap7.tcl` (v1) and `genus_asap7_v2.tcl` (v2) differ only in: a
`GENUS_PARAMS` conditional on `elaborate`, the empty-OUTDIR guard (v2 lines
60 to 63), stage stamps, `write_db` checkpoints, and `-nworst 20` on the
timing reports. **They produce identical synthesis results** (F22). v2 is
preferred for anything whose path ranking matters; v1 is what
`asap7_fmax.py` calls.

`asap7_fmax.py` writes every search point into one OUTDIR, so it cannot be
pointed at v2 without also giving each point its own OUTDIR, or the guard
aborts point two. Still unresolved, still F21.

---

## Part 1: the butterfly2x2 A/B is done

### Headline

At **573 ps**, identical configuration, the **baseline violates by 6 ps and
the optimized arm meets**. Both reproduced on independent runs. Cost is
+5.3 percent area, +5.5 percent power, +668 flops.

That is the defensible claim, and it is categorical rather than numerical.
The two arms' own closure periods are 578 ps (baseline) and 573 ps
(optimized), a 5 ps gap equal to the search TOL, which is why the same-period
head-to-head was run instead of differencing the closures.

### The arms

| | baseline | optimized |
|---|---|---|
| Path | `asic/arms/bf2x2_baseline` | `asic/arms/bf2x2_optimized` |
| Source of truth | `asic/arms/mldsa_baseline` | `agent/mldsa/mldsa_src` |
| `adder = adda + addb` | line 169 | line 174 |
| Genus operator name | `add_169_*` | `add_174_*` |
| Sequential cells | 2361 | 3029 |
| `aj3` depth | `[4:0]` | `[6:0]` |
| `valid_sr` | 10 bits | 11 bits |
| Extra pipeline regs | none | `mult_p`, `sub_r`, `add_r`, `zeta_delay3` |
| `butterfly2x2.v` delay lines | `z2_sr`/`z3_sr` `[8:0]` | `[10:0]` |

**Two free provenance checks.** The operator line number in any Genus log
(`add_169` vs `add_174`), and the sequential cell count in any gates report
(2361 vs 3029). Either one identifies the arm without an md5.

### What is in the findings doc

`docs/findings/asic/2026-08-10_bf2x2_ooc_fmax.md` now carries:

- C1 to C8 and C-close: baseline sweep, closure 578 ps.
- D1 to D8 and D-close: optimized sweep, closure 573 ps, bracket 350 to 600.
- E1 to E6: the 573 ps head-to-head plus determinism repeats at 573, 578, 581.
- F15 to F21 from the prior session, plus F22 to F26 and F17S added today.

### New findings, in brief

- **F22. Genus is deterministic here.** Four independent pairs reproduce every
  reported field bit-identically, including across v1 and v2. Repeat runs are
  not a useful control for this flow; a single run is the measurement.
- **F17S supersedes F17.** F17 called the 578/581 area and power inversion a
  nondeterminism signature and inferred a 3 ps reproducibility floor. F22
  disproves the mechanism: the inversion reproduces exactly. The correct
  statement is that PPA is exact at a given period but **not monotonic in
  period over small intervals**, so nearby periods must not be differenced to
  infer a trend. The 3 ps floor claim is withdrawn.
- **F23.** The 573 ps head-to-head, above.
- **F24.** The optimized arm's advantage is **an added pipeline stage, not
  combinational optimization**. Baseline VIOLATED points bind
  `barrett_datai_reg`; optimized VIOLATED points bind `mult_p_reg`. The
  difference is exactly `barrett_datai <= mult_result` becoming
  `mult_p <= mult_result` then `barrett_datai <= mult_p`. Say "pipelining" in
  the paper, not "faster".
- **F25.** F15 reproduced on the optimized arm: all four VIOLATED points carry
  `mul` on `Path 1`, all four MET points carry none. A MET run's endpoint
  carries no information about the design, which includes the 78-hour chip run
  A1.
- **F26.** F16 reproduced: `add_174` appears on `Path 1` at 600 ps only, 14
  cells, mirroring `add_169` at 600 ps only, 12 cells. The adder is not the
  limiter on either arm.

### Committed artifacts

| Item | Location |
|---|---|
| Optimized sweep, 8 points, reports + JSON + log | `logs/asic/asap7_bf2x2_fmax_opt_20260811/` |
| Baseline 573 ps | `logs/asic/asap7_bf2x2_base_p573_20260811/` |
| Baseline 573 ps repeat | `logs/asic/asap7_bf2x2_base_p573_r2_20260811/` |
| Optimized 573 ps repeat | `logs/asic/asap7_bf2x2_opt_p573_r2_20260811/` |
| Baseline 578 ps repeat | `logs/asic/asap7_bf2x2_base_p578_r2_20260811/` |
| Baseline 581 ps repeat | `logs/asic/asap7_bf2x2_base_p581_r2_20260811/` |

### Still open on the butterfly work

- **Optimized sweep netlists not pulled.** Eight files, server only, at
  `~/pqc/hqc/asic/asap7/out/bf2x2_fmax_opt/`. The baseline equivalents were
  committed at `0c93891`.
- **`asic/arms/bf2x2_optimized/` may not be in git.** Not verified. The
  baseline arm is tracked.
- **B3, B5, B6 area and power** still unread on the server. Retrievable, no
  new runs needed.
- **No FPGA run on the optimized arm from this work.** Item four of the
  advisor's four-way analysis is untouched.
- **F11 is used twice**, in `2026-08-02_asap7_transition` (flip-flop memory
  model) and `2026-08-08_asap7_chip_base_complete` line 104 (mapping runtime).
  Still unresolved.

---

## Part 2: HQC Genus port, substantial progress

### The root cause was file ordering, not source defects

`CLOG2` is a macro defined in `clog2.v` with no include guards and no
`` `include `` in any consumer. Genus makes a macro visible only from the point
`read_hdl` processes its defining file onward, and the bare
`read_hdl [glob *.v]` gave filesystem order. Forcing `clog2.v` first cleared
8 of 10 VLOGPT-1 and 2 of 4 VLOGPT-117 **with no source edits at all**.

The working configuration is committed at `asic/portfix_wip/a7_ordered.tcl`:

```tcl
set_db init_hdl_search_path <dir>
set_db hdl_error_on_blackbox false
read_hdl -define {SHARED=1 SHARED_ENCAP=1} [concat [list <dir>/clog2.v] [lsort [glob <dir>/*.v]]]
puts ARM_READ_OK
exit
```

`lsort` makes the order deterministic. This is most of what the advisor asked
for when he said to put defines, file ordering, and include paths into one
reproducible configuration.

**Implication worth carrying into the findings doc:** some fraction of the
roughly 30 hand edits from the prior session were chasing symptoms of a
configuration problem. That does not make them wrong, but the ordering fix is
the higher-leverage change and should be tried before hand edits on any
future file.

### `PARALLEL_ENCRYPT` defaults to 0

`decap.v` 134, `encap.v` 133, `hqc_kem_joint_design.v` 108, and the same lines
in the FPGA tree under `hardware/`. Nothing overrides it except one testbench.
So **the real build instantiates `encrypt`, not `encrypt_parallel`**. Both
still have to parse because `read_hdl` compiles every file in the glob, but
only `encrypt.v` is elaborated by the design.

### `encrypt.v` is clean

The parser now clears it entirely. Repairs applied, all declaration hoists to
a block after `wire [LOG_WEIGHT_ENC-1:0] rd_addr_error_loc;` plus one syntax
fix:

`r1_internal`, `pm_rd_addr`, `xor_add_addr`, `u_cpy_addr`, `wen_fw`/`rd_fw`,
the 11-line declaration block formerly at 392 to 402, `u_out`, `pm_out`,
`add_out`, `add_out_addr`, `xor_add_en`, `xor_add_out`, `xor_add_out_addr`,
`en_r1`, `en_r2`, `done_fw_transfer`, `r2_done`, `wen_u`, `sel_r1_hr2`,
`start_fw_transfer`. Plus removal of a null statement, `en_e <= 0;;` became
`en_e <= 0;`.

Backup is `encrypt.v.orig` on the server, matching the committed WIP snapshot.

### `encrypt_parallel.v` is the current frontier

Done today: `r1_internal`, `r2_internal_hr2`, `r2_internal_sr2` hoisted to
lines 186 to 188. Then ten more declarations hoisted after
`wire [M-1:0] r2_internal_sr2;`: `pm_rd_addr`/`pm_rd_addr_sr2`,
`pm_rd_en`/`pm_rd_en_sr2`, `add_out`/`add_out_sr2`,
`add_out_addr`/`add_out_addr_sr2`, `add_out_valid`/`add_out_valid_sr2`,
`xor_add_addr`, `xor_add_out`, `xor_add_out_addr`, `xor_add_out_valid`,
`loc_addr_sr2`.

Frontier moved from line 432 to line 830. Remaining, all located, all the same
classes already handled in `encrypt.v`:

| Symbol | Declared at | Needs |
|---|---|---|
| `xor_add_en` | 618 | hoist above first port-connection use |
| `en_r1` | 655 | hoist |
| `en_r2` | 656 | hoist |
| `start_fw_transfer` | 857 | hoist |
| `done_fw_transfer` | 858 | hoist |
| `r2_done` | 959 | hoist |
| `en_e <= 0;;` at line 676 | | drop one semicolon |

Exact bytes: `  wire xor_add_en;` (two leading spaces), `reg en_r1;` and
`reg en_r2;` (none), ` reg start_fw_transfer;` and ` reg done_fw_transfer;`
(one leading space), `reg r2_done =0;` (none, note the space before `=0`).

Anchor to hoist to: `\nwire [M-1:0] r2_internal_sr2;\n`.

Backup is `encrypt_parallel.v.bak`.

**Prediction, not a result:** after that edit the file should read, and
`ARM_READ_OK` should print. The `CLOG2`-in-reg-range errors at 432 to 435 were
cascade and already cleared themselves, exactly as they did in `encrypt.v`.

### The edit protocol that works here

Python with line-anchored literals and a count assert per line:

```python
old = "\n<exact bytes including leading whitespace>\n"
assert s.count(old)==1, ("count", repr(old), s.count(old))
```

Three lessons, all learned the hard way today, all of which the assert caught
so nothing was ever corrupted:

1. **Trailing whitespace defeats a literal.** `wire [M-1:0] r1_internal; ` has
   a trailing space. Run `cat -A` on the target line before writing the
   literal.
2. **Python's `count` is substring, not line, based.** `"wire x;\n"` matches
   inside `" wire x;\n"`. Anchor every literal with a leading `\n`.
3. **Line numbers go stale after any edit.** Re-grep immediately before
   building a literal, never reuse a number from an earlier turn.

---

## The KAT problem, unresolved and blocking

`agent/hqc/joint_kat_gate.py` stages from `hardware/joint_design/`,
`hardware/keygen/`, `hardware/decap/`, `hardware/encap/`, and
`hardware/common/*`. **It never reads `asic/portfix_wip/.`**

So no KAT covers any of the roughly 45 edits now in that tree. Running the
gate today would pass on pristine FPGA sources and prove nothing, which is the
exact vacuity failure ground rule 7 exists to prevent.

Three ways out, none done:

1. **Port the repairs back into `hardware/`** so the existing gate covers
   them. This is the real fix and the only path to an HQC ASAP7 number. It
   changes the FPGA source tree, so it needs KAT at all three levels **and**
   the FPGA baseline re-close reproducing 9.12 ns, 109.6 MHz, WNS +0.072,
   mirroring the `cd92639` control.
2. Point a copy of the gate at `portfix_wip/`. Fast, but forks the harness.
3. Leave it. Then `portfix_wip/` is a portability demonstration only and no
   number from it is quotable.

Note the `en_e <= 0;;` null statement exists upstream in
`hardware/encap/encrypt.v` too, so at least one repair belongs in `hardware/`
regardless.

---

## Checklist, in gating order

### HQC, to get a run moving

- [ ] Apply the six hoists plus the semicolon to `encrypt_parallel.v`. Bytes
      and anchor are above.
- [ ] Rerun `a7_ordered.tcl`. Confirm `ARM_READ_OK` prints.
- [ ] If it does not, the remaining errors are in `control_path.v` (20 hits,
      all warnings as of the last run) or new territory. Re-triage with the
      grep pattern used all session.
- [ ] Pull `encrypt_parallel.v` and the new logs back and commit. Nothing on
      the server is a checkout.
- [ ] **Before any HQC synthesis run:** decide which of the three KAT paths
      above to take. A synthesized netlist from an untested tree produces no
      quotable number.
- [ ] `genus_asap7_v2.tcl` line 40 is still a bare
      `read_hdl [glob $RTL_DIR/*.v]` with no defines and no clog2-first
      ordering. Any HQC run launched through it today synthesizes a
      configuration no KAT has validated. Fix before use, ideally by folding
      in the `a7_ordered.tcl` approach behind an env flag so the ML-DSA arms
      are unaffected.
- [ ] Record **distinct root defects**, not total parser error counts. Today's
      counts moved non-monotonically all session while real progress was
      strictly forward; the honest metric is how far into the file the parser
      reaches.

### Butterfly cleanup

- [ ] Pull and commit the eight optimized-sweep netlists.
- [ ] Verify `asic/arms/bf2x2_optimized/` is tracked.
- [ ] Read B3, B5, B6 area and power off the server.
- [ ] Apply the three text edits specified at the end of the findings doc if
      not already done: the F17 supersession banner and strikethroughs, the
      "what does not exist yet" strikethroughs, and the INDEX row rewrite.
- [ ] Grep for the retracted claim:
      `grep -rn "reproducibility floor\|run-to-run variation" docs/ README.md`
- [ ] Resolve the F11 double-claim.

### Paper and coordination, from the 2026-08-10 group meeting

- [ ] Send Sanjay the specific locations where the LLM made changes, for the
      figures.
- [ ] Finish final ML-DSA runs, generate figures.
- [ ] Run HQC, report the agent's fix-and-run time.
- [ ] Methodology and framework figures while runs are in flight.
- [ ] Dump synthesis jobs on the server before travelling Thursday.
- [ ] Update the paper with results Friday or Saturday.
- [ ] Repo cleanup with Zain and Sanjay: clone to a branch, strip notes, add
      framework figure and instructions.

Tracked but not owned: Zain is emailing Partha about an extension to end of
month, and has an area-by-block script he offered to share.

---

## Open questions for the advisor

Carried, still unanswered:

1. Is a single-arm pre-layout snapshot with a flip-flop memory model worth
   reporting, or should the ASIC section stay a portability finding only?
2. Does "all three security levels" mean before the 2026-08-15 D&T deadline?
3. Priority order between the D&T submission and starting ML-KEM.
4. F15 says a MET run's endpoint carries no information, and A1 is a MET run.
   Does that weaken the chip section, and should the chip doc point to F15?
5. F16 puts the ripple-carry adder on the critical path at one constraint out
   of eight. Does that survive as a paper claim?

New today:

6. F22 shows repeat runs are not a control for this flow, since Genus is
   bit-deterministic. Does that change what the paper claims about
   experimental rigor, given the correctness gate is functional rather than a
   synthesis-repeatability check?
7. F24 says the optimized arm's ASIC advantage comes from an added pipeline
   register, not combinational optimization, and the FPGA ledger records the
   same edits as wins. Is the honest framing that the agent found a pipelining
   transformation that transfers across backends, and does that strengthen or
   weaken the backend-dependence claim?
8. The HQC port's root cause was a `read_hdl` file-ordering problem, not RTL
   defects. Does the portability contribution still hold in its current form,
   and should the defect taxonomy separate "cross-tool RTL defects" from
   "tool configuration"?
