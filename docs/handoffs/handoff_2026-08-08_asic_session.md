# Handoff: ASIC work session, 2026-08-08

Paste this at the start of a new chat. It assumes the reader knows the project
builds a correctness-gated LLM-driven RTL optimization agent for PQC
accelerators (ML-DSA and HQC, Artix-7 FPGA and ASAP7 7nm ASIC) but knows
nothing about the ASIC results below or the advisor exchange that produced
today's task list.

---

## Ground rules for this conversation

1. Never quote a performance number that is not in a RESULTS OF RECORD table.
   If asked about a result and it is not there, say so rather than
   reconstructing it.
2. Distinguish measured from proposed. A next step in a findings doc is not a
   result.
3. Measurement configuration travels with the number: effort level, synthesis
   directives, corner, OOC mode, blackboxing, clock period.
4. Do not let a claimed delta smaller than known tooling sensitivity pass
   without flagging it. On Genus, effort setting alone moves achieved
   frequency by about 11 percent.
5. I run all commands locally and paste output. Give concise code and
   direction, not free-form RTL. No em dashes in any deliverable.
6. RTL edits follow: `.bak` backup, anchor-count assert, gate, KAT at all
   three security levels, synth, commit. Ask for explicit approval before any
   edit to a source file.
7. Watch for vacuity. A gate can pass on files that were never edited. Verify
   that the files being synthesized are the files that changed.
8. If unsure whether something is established or proposed, ask.

---

## Environment

- Local: WSL Ubuntu on Windows, repo at `/mnt/c/PQC/hqc`, GitHub
  `hsc-research/LLM-Aided-PQC`, HEAD `f74be66`.
- Remote: `ssh engr` (`engr-r940s01.engr.uidaho.edu`), Cadence Genus 25.12,
  ASAP7 PDK, project copy at `~/pqc/hqc/`. **The server tree is not a git
  checkout.** Anything produced there exists in one place until copied back.
- Genus takes 30 to 60 seconds to start. Redirecting output to a log means
  nothing appears until the process exits, so check the log file directly
  rather than waiting on a pipe.
- `ssh engr 'cmd'` prints a post-quantum key exchange warning to stderr on
  every call. Ignore it.

---

## What happened before this session

### The first full-chip ASAP7 run completed

ML-DSA `combined_top` synthesized on ASAP7. Started 2026-08-04 17:22,
finished 2026-08-08 00:23. **78 hours 1 minute wall.** Normal exit, zero
errors.

Configuration: ASAP7 7nm, `PVT_0P7V_25C`, clock period 2000 ps,
`syn_generic_effort`, `syn_map_effort`, `syn_opt_effort` all `high`, memories
modeled as flip-flop arrays, pre-layout only, SDC
`sdc/combined_top.sdc` with false paths on `sec_lvl*`, `mode*`, `rst`,
`start`.

RESULTS OF RECORD (logs committed under
`logs/asic/asap7_chip_base_20260808/`):

| # | Metric | Value |
|---|---|---|
| A1 | Setup slack | MET, +1 ps |
| A2 | Data path delay | 1882 ps (required 1882, setup 18, uncertainty 100) |
| A3 | Binding path | `BF1_1_modei_reg[0]/CLK` to `BF2_1_aj4_reg[23]/D` |
| A4 | Cell count | 4,575,894 |
| A5 | Total area | 16,891,822.277 |
| A6 | Power, vectorless | 1.612 W |
| A7 | `syn_map` global mapping wall time | 40:48:11 |
| A8 | `syn_opt` wall time | 02:09:13 |
| A10 | Peak memory | 69.12 GB |

Two hard caveats that must travel with these numbers:

- **A1 is not a closure.** MET at +1 ps means the tool optimized to the
  requested period and stopped. The achievable period is below 2000 ps and is
  unknown. Do not convert 2000 ps to 500 MHz and call it Fmax. The project
  already retracted one set of projected-Fmax figures for the analogous error.
- **A5 and A6 characterize the memory model, not the datapath.** Six inferred
  RAM instances are 96 percent of area; register power is 87 percent of total.
  The critical path does not traverse them, so A1 to A3 are unaffected.

### The interesting finding

The critical path is in a different place than on FPGA. On Artix-7 the ML-DSA
baseline binds from `DECODER/encode_mode_reg[1]` to `ENCODER/PISO_reg[117]`,
a 256-bit variable-shift serializer. On ASAP7 it binds inside the NTT
butterfly.

Of the 1882 ps path, 542 ps to 1787 ps is a carry-propagation chain in
`BF_CIRCUIT_BF2_1_add_169_28`: 16 `FAx1` full adders with `CI` to `CON`
propagation, 8 `MAJx2` majority gates, `INVxp33` inverters between stages at
roughly 30 to 36 ps each. **1245 ps, 66 percent of the critical path, in one
adder.** The remaining 1787 to 1882 ps is `OAI22xp5`, `NOR2xp33`,
`AOI221xp5`, which is a mux and its select.

**Phrasing matters here and the advisor corrected it.** Do not write
"standard cells have no carry chain, so Genus produced a ripple adder."
Write: the FPGA implementation benefits from dedicated carry resources in the
CLBs (SLICEM, SLICEL, SLICEX), while the ASAP7 mapping exposed a long
standard-cell carry-propagation chain **for this RTL, this library, and this
timing constraint**. Genus may have selected that structure because of RTL
form, available cells, timing constraint, and area-power tradeoff.

### Source located

`agent/mldsa/mldsa_src/butterfly.v`:

- Line 174: `adder = adda + addb;` — a single arithmetic operation on 24-bit
  operands, **not** explicit bit-level carry logic. The tool chose the
  structure.
- `adda` and `addb` are mux-selected from several sources at lines 132 to 165,
  so the adder is shared across butterfly modes.
- Line 244: `aj4 <= (ajlen1 < zeta_delay) ? adder : ajlen1;` — the endpoint is
  fed by a mux whose **select is a 24-bit comparison**, which carries its own
  arithmetic.
- Both operands are registered unconditionally in one
  `always @(posedge clk)` block: line 189
  `zeta_delay <= (mode == INVERSE_NTT_MODE) ? DILITHIUM_Q - zeta : zeta;` and
  line 193 `ajlen1 <= ajlen;`. The reset branch above touches only
  `valid_sr`, so there are exactly **two assignment sites and no reset case**.

Hierarchy: `butterfly2x2.v` instantiates `butterfly` four times as `BF1_1`,
`BF1_2`, `BF2_1`, `BF2_2`. The ASAP7 path runs from `BF1_1` to `BF2_1`, so
**`butterfly2x2` is the correct out-of-context top**; `butterfly` alone will
not reproduce the path. Both files are self-contained.

`butterfly2x2` ports: `clk`, `rst`, `mode[2:0]`, `validi`, `datai[95:0]`,
`zetai[95:0]`, `acci[95:0]`, `datao[95:0]`, `valido`.

### Relevant history

The `butterfly` block already appears twice in the ML-DSA ledger as accepted
FPGA wins (`butterfly_dsp_pipeline`, `butterfly_round2_areg`) and is recorded
as **closed at a DSP floor** on FPGA. ASAP7 has reopened it for a different
reason. That is a concrete instance of the backend-dependence claim rather
than an assertion.

---

## The advisor's reply, which sets today's work

Dr. Abideen responded to a status email. His direction, summarized:

- The ripple-carry finding is at least as valuable as the PPA comparison and
  potentially more so scientifically. PPA tells us overheads; the critical
  path analysis explains **why** the design behaves differently across
  technologies. Sharper claim available: **optimization opportunities are
  backend-dependent, so an agent trained only on FPGA timing reports may
  select the wrong transformation for an ASIC implementation.**
- Memories will use the TSMC compiler for real tape-out. If the critical path
  passes through memories, the usual remedy is breaking memory blocks into
  smaller blocks; macro placement also shifts PPA in physical design.
- **Do not launch another unchanged 78-hour run.** Reduce turnaround first and
  validate the adder result at a smaller hierarchy.
- Lower mapping effort from high to medium for exploration if it substantially
  reduces runtime. Use high only for the final baseline and optimized runs
  that appear in the paper. Keep the 2 ns constraint for the direct
  comparison. Estimating achievable frequency is a separate, later, low
  priority experiment.
- On HQC: put all required defines, file ordering, and include paths into one
  reproducible configuration rather than relying on manual settings.
- Record the number of **distinct root defects**, not the total parser error
  count.
- Synthesize both FPGA and ASIC for **all three security levels** of HQC,
  ML-DSA, and eventually ML-KEM.
- ML-KEM is now in scope. Repos suggested: Brno AXE / PQC / DiKy on GitLab
  (unified ML-KEM and ML-DSA); the Zenodo release for "Two Birds, One Mask"
  (same authors, unified with side-channel protection); and
  `chipsalliance/adams-bridge` releases, which he thinks is worth trying.

---

## Today's task list, in order

### 1. Stand up the butterfly2x2 out-of-context experiment

Goal: turn a 78-hour experiment into a minutes-long one, and confirm the
critical path reproduces at block level.

Arm and SDC are not yet created. Files to copy:
`agent/mldsa/mldsa_src/butterfly.v` and `butterfly2x2.v` into
`engr:~/pqc/hqc/asic/arms/bf2x2_baseline/`.

SDC to write as `engr:~/pqc/hqc/asic/asap7/sdc/butterfly2x2.sdc`, modeled on
the existing `encoder.sdc`: `create_clock` from `$PERIOD_PS`, false paths on
`mode*` and `rst`, input delay at 10 percent of period on
`{datai* zetai* acci* validi}`, output delay at 10 percent on `all_outputs`.

Run with `scripts/genus_asap7_v2.tcl`, which reads `GENUS_TOP`,
`GENUS_SRCDIR`, `GENUS_PERIOD_PS`, `GENUS_OUTDIR`, `GENUS_SDC`, and
optionally `GENUS_PARAMS`. That script has stage stamps, an empty-OUTDIR
guard, and intermediate `write_db` checkpoints, unlike the original
`genus_asap7.tcl`.

First run is a loose probe at 2000 ps to find where the block lands and how
long it takes. **Verify the reported critical path matches A3**, from a
`BF1_*` register to a `BF2_*` register through the adder. If it does not
reproduce, the OOC boundary conditions differ from the in-context ones and
the experiment does not yet represent the finding.

### 2. Choose the comparison period

The full chip needed 1882 ps across two butterfly stages plus surrounding
logic. A single `butterfly2x2` out of context will be much faster, so 2000 ps
will likely meet with large slack and tell you nothing.

Pick a period where the **baseline just misses**, so a modified version has
room to show a difference. Then hold that period fixed for every arm.

### 3. Test cycle-neutral alternatives

Two candidates, addressing different segments of the same path.

**(a) Precompute the mux select.** `ajlen1 < zeta_delay` at line 244 becomes a
registered flag computed one cycle early from the pre-register values. Both
operands are assigned unconditionally at lines 189 and 193 in the same
clocked block, so the flag and the operands become valid on the same edge and
the consumer sees the same value on the same cycle. No cycle schedule change.
This is the project's existing `flag_precompute` rule, the same one that
transferred from ML-DSA to HQC. Two assignment sites to pair, no reset case.

One thing to watch: the flag expression duplicates
`DILITHIUM_Q - zeta`. Synthesis will probably share it, but check area in
the result.

**(b) Restructure the adder.** Carry-lookahead or carry-select, by Genus
directive or by RTL change. Targets the 1245 ps directly and is the larger
change.

Both are worth trying. (a) is more interesting for the paper because it
applies an existing rule to a target only the ASIC report revealed.

### 4. Run the four-way analysis the advisor asked for

For whichever edit wins:

1. Critical-path migration from FPGA to ASIC (already have A3 plus the
   Artix-7 binding path).
2. The RTL optimization selected from the ASIC report.
3. The resulting PPA tradeoff.
4. **Whether the same edit helps, hurts, or has no effect on FPGA.**

Item 4 is the one that extends the existing transfer story and it requires an
Artix-7 run on the modified RTL.

### 5. Make the HQC configuration reproducible

Currently the correct read requires `-define {SHARED=1 SHARED_ENCAP=1}`,
discovered by reading `hardware/joint_design/tcl/joint_design.tcl` lines 9 and
10. Without them Genus compiles `ifndef SHARED_ENCAP` branches the real build
never sees, producing errors that do not exist in the actual design.

`scripts/genus_asap7_v2.tcl` still has a bare
`read_hdl [glob $RTL_DIR/*.v]` with no defines. **Any HQC run launched with
it today would synthesize a configuration no KAT has ever validated.** This
must be fixed before any HQC ASAP7 run.

The advisor asked for defines, file ordering, and include paths in one
reproducible configuration rather than manual settings.

---

## Background on the HQC port, which is blocked but not today's priority

HQC will not elaborate in Genus. Five distinct defect classes found so far in
published, functionally correct RTL that closes on FPGA:

| Class | Genus code | Repair |
|---|---|---|
| Unindexed array in sensitivity list | VLOGPT-61 | `always @*` |
| Use before declaration | VLOGPT-20 | hoist declaration |
| Duplicate declaration | VLOGPT-22 | delete the later one |
| Macro expression in declaration range | VLOGPT-117 | bind to a localparam or existing parameter |
| Implicit net from a prior port connection | VLOGPT-22 / VLOGPT-86 | hoist declaration |

Roughly 30 edits applied across `state_ram.v`, `decap.v`, `decrypt.v`,
`encap.v`, and most of `encrypt_parallel.v`. Every one is either a
declaration reorder proven byte-identical under
`LC_ALL=C sort` diff, or a substitution of an expression for a name already
bound to that same expression. **None has been functionally tested.**

Work lives at `engr:/tmp/armtest/` with a snapshot at
`engr:~/pqc/hqc/asic/portfix_wip/`. Neither is in git and `/tmp` clears on
reboot.

Frontier: one unresolved VLOGPT-22 on `r1_internal` at
`encrypt_parallel.v` line 410, which has only one visible declaration, so the
mechanism is not yet identified.

**Error counts mislead.** `state_ram.v` reported 44 errors and had 4 real
defects; the rest was cascade from the parser losing sync. Progress is
measured by how far into the file the parser gets, not by the error count.
This also means the earlier survey figure of "102 instances in 13 files" is a
static count, not a count of distinct defects.

Before any HQC ASAP7 result can be reported: KAT at all three security
levels, and re-close the HQC FPGA baseline on the repaired source to confirm
it reproduces 9.12 ns, 109.6 MHz, WNS +0.072 exactly, mirroring the
`cd92639` control that validated the earlier portability fixes.

---

## Open questions the advisor has not yet answered

1. Is a single-arm pre-layout snapshot with a flip-flop memory model worth
   reporting in the paper, or should the ASIC section stay a portability
   finding only?
2. Does "all three security levels for HQC, ML-DSA and soon ML-KEM" mean
   before the IEEE Design & Test deadline of 2026-08-15, or after? The
   manuscript currently reports no ASAP7 result and says so explicitly.
3. Priority order between the D&T submission and starting ML-KEM.
