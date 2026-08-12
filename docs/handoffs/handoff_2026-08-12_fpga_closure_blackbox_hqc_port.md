# HANDOFF: FPGA closure pair, the ASAP7 blackbox defect, and the HQC Genus port

Session: 2026-08-11 evening through 2026-08-12 afternoon.
Continues: `docs/handoffs/handoff_2026-08-11_bf2x2_ab_and_hqc_port.md`.
Commits this session: `8573480`, `90ec3b4`, `f8f05aa`, `c51d2da`. All pushed
to `origin/main`.

---

## Ground rules, carried forward and added to

1. Never quote a number that is not in a RESULTS OF RECORD table.
2. Distinguish measured from proposed. A next step is not a result.
3. Measurement configuration travels with the number.
4. Flag any delta smaller than known tooling sensitivity.
5. I run all commands locally and paste output. Concise code and direction.
   No em dashes in any deliverable.
6. RTL edits: `.bak`, anchor-count assert, gate, KAT at all three levels,
   synth, commit. Ask for explicit approval before any edit to a source file.
7. Watch for vacuity. Verify that the files being synthesized are the files
   that changed.
8. **Do not guess. Confirm against the repo, the server, or the vendor
   documentation before asserting.**
9. **New, learned expensively this session: verify the file set is complete,
   not just that the files match their hashes.** An arm whose md5s are correct
   can still be missing a module. See Part 2.
10. **New: when a tool attribute or command syntax is needed, read the vendor
    documentation rather than guessing the name.** Three consecutive guesses at
    a Genus attribute name failed this session and wasted an hour. The docs are
    at `/tools/cadence/installs/DDI251/GENUS251/doc/genus_attref/`, one HTML
    file per attribute, so `ls | grep` finds the right name directly.

---

## Part 1: the FPGA closure pair, G1 and G2. This is a real result.

`docs/findings/mldsa/2026-08-12_bf2x2_fpga_ooc_closure.md`, commit `90ec3b4`.

| # | Arm | Closing period | Fmax | WNS | Final bracket |
|---|---|---|---|---|---|
| G1 | baseline | 9.50 ns | 105.3 MHz | +0.011 | [9.38, 9.50] |
| G2 | optimized | 8.75 ns | 114.3 MHz | +0.004 | [8.62, 8.75] |

0.75 ns shorter closing period, 7.9 percent period reduction. Artix-7
`xc7a200tfbg676-1` -1, out of context, post-route closure, ExtraTimingOpt /
Explore / Explore, checkpoints at regen period 5.000 ns, five fixed iterations.
Two concurrent Vivado processes.

Three source files per arm including the unedited `Barrett_8380417.v`. Both
arms md5-verified. **Blackbox status verified zero**: Vivado's
`Report BlackBoxes` table is empty and the log contains no `Synth 8-3491` or
`8-6156`. That check is now mandatory, for reasons in Part 2.

`agent/fmax_search.py` does not assert its bracket. Both brackets here were
proven by reading the iteration list, and each closure has a VIOLATED point
immediately below it.

New findings F27 to F30 are in that doc. F29 is the interesting one for the
paper: the gain is pipelining, not logic optimization. LUT moves by 4 cells out
of 2920, DSP and BRAM are identical, flip-flops rise by 570 (+26.4 percent).

---

## Part 2: the ASAP7 series was measured on an incomplete design

**This is the most important thing in this handoff.**

`butterfly.v` line 81 instantiates `Barrett REDUCER(...)`.
`Barrett_8380417.v` defines four modules: `Barrett`, `DecoupledStage`,
`DecoupledStage_1`, `DecoupledStage_2`. That file was never placed in
`asic/arms/bf2x2_baseline` or `bf2x2_optimized`. `genus_asap7.tcl` reads
`[glob $RTL_DIR/*.v]`, so Genus found an instantiation with no source and,
under `hdl_error_on_blackbox false`, blackboxed all four silently.

Every C, D and E series row therefore measured a butterfly with its modular
reduction and three pipeline-stage modules absent.

**The signal was present and was misread.** `Unresolved 4` appears in every
gates report of both series. It was recorded in the findings doc and explained
as an accounting difference between the gates and area reports rather than
investigated. An unresolved instance is by definition a module the tool could
not find.

Superseded in both directions at commit `f8f05aa`: banner on
`docs/findings/asic/2026-08-10_bf2x2_ooc_fmax.md`, status changed, per-finding
markers on F15, F16, F19, F23, F24, F25, F26 (evidence withdrawn) and F18
(qualified), INDEX row changed, banners on both 2026-08-11 handoffs. Row data
left unstruck deliberately so the `Unresolved 4` evidence stays visible.

F17S, F20, F21, F22 survive because they concern the tool rather than the
design.

### The guard, F28

`genus_asap7.tcl` and `genus_asap7_v2.tcl` now set
`hdl_error_on_blackbox true` when the arm directory contains no `.vhd` files.
Mixed-language arms keep the tolerant setting, which the VHDL read-order
handling requires (F10).

Verified both directions before installation: on a Barrett-less two-file arm
elaborate fails with `CDFG-431` naming instance `REDUCER` at `butterfly.v`
line 81; on the complete three-file arm the attribute is set to true and
elaborate proceeds with zero `CDFG-431`.

**Note for wrappers:** Genus returns exit status 0 despite the elaboration
error. A caller checking only the return code will not notice.

### Replacement measurement, in flight at time of writing

Both arms now contain `Barrett_8380417.v`, md5 `1363d8ebe3a4eec1b210ef56ae4dd8b1`,
verified identical local and server.

```
ssh engr 'cat ~/pqc/hqc/asic/asap7/fmax_base_v2.log; echo ===; cat ~/pqc/hqc/asic/asap7/fmax_opt_v2.log'
```

Bracket 400 to 700 ps, TOL 5 ps, both ends proven on both arms:
baseline 700 MET / 400 VIOLATED -159 / 550 VIOLATED -25; optimized 700 MET /
400 VIOLATED -168. Roughly 40 to 60 minutes per point with two searches
sharing the machine.

**Worth watching:** at 400 ps the baseline violates by 159 ps and the optimized
arm by 168 ps, so the baseline is ahead at the tight end. In the superseded
blackboxed runs the optimized arm led at every violated point. One point is not
a trend, but adding Barrett may change the answer rather than shift both arms
equally. Report whatever the closures say.

When they converge: pull logs and reports, extract with the same TSV script
used for the C series, write a new findings doc with a fresh ID series (C, D, E
and G are taken; F is the findings series), and record it as superseding
nothing since the old rows are already superseded.

---

## Part 3: the HQC Genus port. Method, state, and how to continue.

### The mechanism that makes this tractable

**Cross-file parser-state contamination.** When one file fails to parse, later
files in `read_hdl` order inherit errors they do not have on their own. Proven
this session: `hqc_kem_joint_design.v` parsed clean alone with `clog2.v`
(`J_OK`), failed with 15 error sites when `fixed_weight_cww.v` was read between
them, and cleared completely once cww was fixed, without a single edit to the
joint design.

Consequences for method:

- **Only the first error in read order is trustworthy.** Everything after it is
  suspect.
- **Error counts are not a progress metric.** They rise when a file gets
  further and exposes more downstream. The metric is how deep into the read
  order the parser reaches.
- **Always fix the alphabetically first failing file, then re-run.** Later
  files often clear themselves.

### The read configuration

`asic/portfix_wip/a7_ordered.tcl`:

```tcl
set_db init_hdl_search_path /home/alco9414/pqc/hqc/asic/portfix_wip
set_db hdl_error_on_blackbox false
read_hdl -define {SHARED=1 SHARED_ENCAP=1} [concat [list <dir>/clog2.v] [lsort [glob <dir>/*.v]]]
puts ARM_READ_OK
exit
```

`clog2.v` is forced first because `CLOG2` is a macro with no include guard and
no `` `include `` in any consumer, so a bare glob leaves it undefined for files
read earlier. `lsort` makes the order deterministic.

### The CLOG2 macro replacement

The original `CLOG2` and `DIVCLOG2` were 30-deep ternary chains. Genus rejects
that expansion in parameter-default position, which was the root cause of a
whole class of failures. Replaced with:

```verilog
`define CLOG2(x) ((x <= 1) ? 1 : $clog2(x))
`define DIVCLOG2(x) ((x <= 1) ? 0 : $clog2(x))
```

**Equivalence proven, not assumed.** An `xrun` sweep over 0 to 70000 compared
each original macro against its replacement and reported zero mismatches. 70000
covers `N` at all three security levels, the largest argument in play. Do not
adopt a macro rewrite without this kind of sweep; the two definitions differ at
`x = 1` if the guard is omitted.

### The edit protocol that works

Python with line-anchored literals and a count assert per literal, run as a
file on the server rather than a heredoc through ssh.

```python
old = "\n<exact bytes including leading whitespace>\n"
assert s.count(old) == 1, ("name", s.count(old))
```

Then, for hoists and duplicate removals, prove pure reorder:

```bash
diff <(LC_ALL=C sort file.v.bak) <(LC_ALL=C sort file.v)
```

Zero output means only line positions changed.

**Five lessons, all learned the hard way, all caught by the assert so nothing
was ever corrupted:**

1. **Get exact bytes with `repr()`, not with `sed | cat -A` inside a `printf`
   loop.** A `printf "%s: "` prefix shifts the apparent indentation and I
   misread one leading space as two. Use:
   ```bash
   ssh engr 'cd <dir> && python3 -c "
   import re
   s=open(\"file.v\",encoding=\"utf-8\",newline=\"\").read()
   for m in re.finditer(r\"^.*\\bwire\\b[^;]*\\bSYMBOL\\b[^;]*;.*\$\", s, re.M):
       print(repr(m.group(0)))
   "'
   ```
2. **Backticks do not survive a heredoc piped through ssh.** Write the Python
   to a file on the server with a quoted delimiter (`<<"PYEOF"`), then run it.
3. **Trailing whitespace defeats a literal.** One declaration ended with two
   trailing spaces.
4. **Python `count` is substring-based.** Anchor every literal with a leading
   `\n`.
5. **Line numbers go stale after any edit.** Re-grep immediately before
   building a literal.

### Finding all hoists in a file at once

Rather than one error per round, this lists every signal declared after its
first use:

```bash
ssh engr 'cd ~/pqc/hqc/asic/portfix_wip && python3 -c "
import re,sys
s=open(sys.argv[1],encoding=\"utf-8\",newline=\"\").read()
lines=s.split(chr(10))
decls={}
for i,l in enumerate(lines,1):
    if re.match(r\"\\s*(?:reg|wire)\\b[^;]*;\", l):
        for name in re.findall(r\"\\b([a-z_][a-z_0-9]*)\\b\\s*(?:=[^,;]*)?\\s*[,;]\", l):
            decls.setdefault(name,i)
for name,dl in sorted(decls.items(), key=lambda x:x[1]):
    for i,l in enumerate(lines,1):
        if re.search(r\"\\b\"+name+r\"\\b\", l) and i!=dl:
            if i < dl: print(\"%-22s decl %d  first-use %d\" % (name, dl, i))
            break
" <file>.v'
```

**It produces false positives.** It matched `raddr_high_offset` in
`state_ram.v` at line 26, which is inside a prose comment block, not a real
use. Always confirm the reported first-use line is code before editing.

### Defect taxonomy observed

| Class | Genus code | Fix | Pure reorder? |
|---|---|---|---|
| Use before declaration | VLOGPT-20 | hoist declaration above first use | yes |
| Duplicate declaration | VLOGPT-22 | delete the duplicate, or hoist if it collides with an implicit wire | yes |
| Macro in bit-select or parameter range | VLOGPT-117, VLOGPT-1 | substitute an existing parameter, or add a new one | no |
| Missing declaration for a continuous assign | VLOGPT-20 | **add** a `wire` declaration above first use | no |
| Null statement (`x <= 0;;`) | VLOGPT-1 | drop the extra semicolon | no |
| Instance without a name | VLOGPT-58 | usually cascade, clears with the real defect | n/a |

Declaration-before-use is the dominant class by a wide margin: it appears in
`encrypt.v`, `encrypt_parallel.v`, `fixed_weight.v`, `fixed_weight_ct.v`,
`fixed_weight_cww.v`, `fft_part1.v`, `hqc_rmdecod_findpeaks.v`,
`hqc_rsdecod_elp.v`, `keygen.v`, `reed_muller_encode.v`, and
`reed_solomon_encode.v`. Eleven files.

### Files cleared this session

`encrypt_parallel.v` (six hoists plus a null statement), `fixed_weight.v`
(four macro substitutions, one parameter-default conversion, two hoists),
`fixed_weight_ct.v` (two parameter conversions, two hoists),
`fixed_weight_cww.v` (one parameter conversion, new `LOG_N` parameter, eight
macro substitutions, four hoists, one instance-parameter substitution),
`fft_part1.v` (one hoist), `hqc_rmdecod_findpeaks.v` (one added declaration),
`hqc_rsdecod_elp.v` (one added declaration), `hqc_rsdecod_roots.v` (one
duplicate removed), `keygen.v` (nine hoists), `reed_muller_encode.v` (four
hoists). `keccak_top.v` and `hqc_kem_joint_design.v` cleared as cascade with
no edits.

Frontier has moved from `encrypt_parallel.v` to `reed_solomon_encode.v`.

### Immediate next steps for the port

Two files remain, and the exact bytes are already known:

**`reed_solomon_encode.v`.** Hoist `reg init_msg;` (line 126) and
`reg shift_msg;` (line 127) above first use at 75. Anchor must be above line
75; line 71 is `assign cdw_out = {msg,cdw_bytes[N1-K-1:0]};` and is a
candidate, but confirm there is a declaration line above 75 to anchor to rather
than an assign.

**`state_ram.v`.** `reg [31:0] raddr_high_offset;` is at line 78. The reported
first use at line 26 is a comment and is a false positive. Re-derive its real
first use before deciding whether it needs anything.

Then re-run the tree and expect either `ARM_READ_OK` or one more round:

```bash
ssh engr 'cd ~/pqc/hqc/asic/portfix_wip && nice -n 19 genus -batch -no_gui -f a7_ordered.tcl > /tmp/a7read15.log 2>&1; grep -c "^Error" /tmp/a7read15.log; grep -n ARM_READ_OK /tmp/a7read15.log; grep -A3 -m1 "^Error" /tmp/a7read15.log'
```

Use `nice -n 19` while the ASAP7 searches are running.

### What `ARM_READ_OK` does and does not mean

It means the parse stage completed. It does not mean elaborate succeeds, that
synthesis runs, or that any number is available. Elaborate is a separate stage
and can fail on things parse accepts.

---

## The KAT problem, unresolved and still blocking

`agent/hqc/joint_kat_gate.py` stages from `hardware/joint_design/`,
`hardware/keygen/`, `hardware/decap/`, `hardware/encap/`, and
`hardware/common/*`. **It never reads `asic/portfix_wip/`.**

So no KAT covers any of the roughly 60 edits now in that tree. Running the gate
today would pass on pristine FPGA sources and prove nothing, which is the exact
vacuity failure ground rule 7 exists to prevent.

Three ways out, none done:

1. **Port the repairs back into `hardware/`** so the existing gate covers them.
   This is the real fix and the only path to a quotable HQC ASAP7 number. It
   changes the FPGA source tree, so it needs KAT at all three levels **and** an
   FPGA baseline re-close reproducing 9.12 ns, 109.6 MHz, WNS +0.072, mirroring
   the `cd92639` control.
2. Point a copy of the gate at `portfix_wip/`. Fast, but forks the harness.
3. Leave it. Then `portfix_wip/` is a portability demonstration only and no
   number from it is quotable.

The `en_e <= 0;;` null statement exists upstream in `hardware/encap/encrypt.v`
too, so at least one repair belongs in `hardware/` regardless.

**Realistic timeline:** parse may finish today. Elaborate and synthesis are
unknown. A KAT-gated HQC ASIC number is not plausible before the 15th. The
paper's ASIC Status section already claims no ASAP7 result and frames the ASIC
contribution as portability, and that framing survives without an HQC number.

---

## Everything not done

### Documentation

- [ ] **New findings doc for the ASAP7 v2 closure pair** once the searches
      converge. Fresh ID series. Must state the two-concurrent-searches
      configuration, which differs from the superseded runs that ran alone.
- [ ] **Findings doc for the HQC port**, covering the cross-file cascade
      mechanism, the CLOG2 replacement and its equivalence proof, the defect
      taxonomy table above, and the file-ordering-versus-source-defect
      distinction.
- [ ] **F11 is used twice**, in `2026-08-02_asap7_transition` (flip-flop memory
      model) and `2026-08-08_asap7_chip_base_complete` line 104 (mapping
      runtime). Unresolved since 2026-08-10.
- [ ] **Retracted projected-fmax figures still quoted in six docs**:
      `FINDINGS_mldsa_butterfly_round2_areg.md`,
      `FINDINGS_mldsa_butterfly_dsp_pipeline.md`,
      `FINDINGS_mldsa_board_closure.md`,
      `FINDINGS_mldsa_latency_orchestrator_v0.md`, and the INDEX summary line.
      The numbers are 113.6, 120.8, 128.3 MHz and the +12.9 percent derived
      from them, all products of the banned `1/(period - WNS)` formula. Grep:
      `grep -rn "113.6\|120.8\|128.3\|12.9%" docs/`
- [ ] `flow_sweep_log.jsonl` needs a header note about retracted projected-fmax
      values before public repo release.
- [ ] README documentation of the 65-versus-59 proposal count.

### Measurement

- [ ] ASAP7 v2 closure pair, in flight.
- [ ] Head-to-head at the baseline's closing period once both close, one point
      per arm. That is the categorical claim and is stronger than differencing
      two closures.
- [ ] B3, B5, B6 area and power, still unread on the server. Retrievable, no
      new runs needed.
- [ ] Optimized-sweep netlists from the superseded D series, never pulled.
      Low priority now that the series is superseded.

### Paper, deadline 2026-08-15

Five revisions were drafted this session and are **not yet applied**. The
Overleaf source contains none of the retracted numbers (verified by searching
for 12.9, 113.6, 128.3, 578, 573, 1729), so the blackbox problem does not touch
the manuscript. The five:

1. **ASIC Status** claims "both accelerators elaborate and synthesize in
   Genus". HQC does not yet elaborate. Replace with an ML-DSA-only claim plus a
   statement of HQC's current state.
2. **Cross-Toolchain Portability Defects** reports 13 of 59 files and 102
   instances without distinguishing genuine source defects from tool
   configuration. Forcing `clog2.v` first cleared 8 of 10 VLOGPT-1 and 2 of 4
   VLOGPT-117 with no source edits. A reviewer reproducing with a corrected
   read order gets a different number. Add the distinction; it strengthens the
   finding rather than weakening it.
3. **Discussion** cites "roughly 11 percent" effort sensitivity. That is F3
   from `2026-07-30_genus_asic_port.md`, which the INDEX marks
   **SUPERSEDED (GPDK045)**. The figure is 10.9 percent and was measured on a
   45 nm library, not ASAP7. Say so.
4. **"Two of these repairs were themselves proposed and applied autonomously"**
   is not traceable to a Results of Record entry. Memory says three files, the
   paper says two. Find the log and commit hash or cut the sentence.
5. **65 versus 59 proposal count.** The paper's internal arithmetic is
   consistent (19+1+5+1=26, 59-26=33, 14+1+18=33, and Table 3 sums correctly),
   but if the public log shows 65 the paper needs one clause explaining the
   filter.

Also from the 2026-08-10 group meeting, unchanged: send Sanjay the specific
locations where the LLM made changes for the figures; finish final ML-DSA runs
and generate figures; methodology and framework figures; repo cleanup with Zain
and Sanjay.

### On the butterfly block experiment and the paper

The composition finding (block wins do not compose into chip gains) must stay;
it is a real contribution. The butterfly block measurement is defensible
alongside it, and the justification is specific rather than convenient: A3
records the ASAP7 chip binding path as `BF1_1_modei_reg[0]/CLK` to
`BF2_1_aj4_reg[23]/D`, both endpoints inside `butterfly2x2`. The block being
measured is the block the chip binds in.

Two caveats to state rather than hide. F15 says a MET run's endpoint carries no
design information, and the chip run was MET at 2000 ps, so "the chip binds in
butterfly2x2" is really "when Genus stopped at 2000 ps, the last thing standing
was in butterfly2x2" — suggestive, not established, and establishing it needs a
chip-level bracket search at 78 hours per point. And the block has no chip
context: no surrounding fanout, no shared clock tree.

The framing that holds: the block experiment tests whether the agent's edit
improves the structure the chip binds in, measured by closure. Whether that
composes to a chip gain is a separate question the paper already answers
negatively for ML-DSA on FPGA. Presenting the block result as evidence the
agent works, while explicitly not claiming it predicts chip outcome, is
consistent with the composition finding rather than in tension with it.
