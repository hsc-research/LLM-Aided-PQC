# FINDINGS: HQC Genus portability port, complete and KAT-validated

Date: 2026-08-12
Status: **CURRENT.** Continues `2026-08-07_genus_portability_repair.md` and
`2026-07-31_defect_survey.md`.
Supersedes: nothing. Extends the defect survey with a root-cause distinction
that survey did not draw.

Commits: `ac80306`, `888898c`, `9fdfe2b`, `f553b40`, and the
`encrypt_parallel.v` commit on branch `hqc-port-kat`.

---

## Summary

The HQC joint KEM design now parses and elaborates in Cadence Genus 25.12 on
ASAP7, with `hdl_error_on_blackbox true`, zero errors, no unresolved
references and no empty modules. The joint KAT gate passes at all three
security levels with cycle counts identical to the pre-port control.

Two things this establishes that the earlier defect survey did not:

1. **A large fraction of the apparent "defects" were tool configuration, not
   RTL defects.** Forcing `clog2.v` first in `read_hdl` order cleared 8 of 10
   VLOGPT-1 and 2 of 4 VLOGPT-117 with no source edit at all.
2. **The remaining edits are semantically neutral by construction**, and the
   KAT confirms it rather than discovering it.

---

## Terminology

| Term | Means |
|---|---|
| pure reorder | `diff <(LC_ALL=C sort a) <(LC_ALL=C sort b)` is empty. Only line positions changed |
| hoist | Moving a declaration above its first use. Always a pure reorder |
| cascade | Errors in a file caused by an earlier file failing to parse, which clear without editing that file |
| frontier | The alphabetically first file still failing. The only trustworthy error |

---

## RESULTS OF RECORD

| # | Metric | Value | Log |
|---|---|---|---|
| H1 | Genus parse, full tree | `ARM_READ_OK`, 0 errors | `logs/asic/hqc_portfix_20260812/a7read17.log` |
| H2 | Genus elaborate, `hqc_kem_joint_design` | `ARM_ELAB_OK`, 0 errors, `hdl_error_on_blackbox true` | `logs/asic/hqc_portfix_20260812/a9elab2.log` |
| H3 | Unresolved references | none | `logs/asic/hqc_portfix_20260812/hqc_unresolved.rpt` |
| H4 | Empty modules | none | as above |
| H5 | Design rules after elaborate | no max_transition, no max_capacitance violations | `hqc_elab_drc.rpt` |
| H6 | Joint KAT, pre-port control | PASS hqc128/192/256, 222s | gate stdout |
| H7 | Joint KAT, ported source | PASS hqc128/192/256, 227s | gate stdout |
| H8 | Cycle counts, ported | 45599 / 117619 / 232743 total; 4611 / 5485 / 9199 decode | gate stdout |
| H9 | Cycle counts, control | identical to H8 | gate stdout |
| H10 | Parse with `encrypt_parallel.v` from `build/` | `ARM_READ_OK`, 0 errors | `/tmp/epread3.log`, pull pending |

H6 and H9 are the control arm. H7 and H8 are the treatment. The cycle counts
being identical is the strongest available evidence short of formal
equivalence checking.

### What does not exist yet

- **No FPGA re-close.** The repairs have not been shown timing-neutral on
  Artix-7. The control to reproduce is 9.12 ns, 109.6 MHz, WNS +0.072,
  mirroring the `cd92639` control that validated the earlier portability
  fixes.
- **No HQC ASAP7 synthesis.** Elaborate succeeds; synthesis has never been
  run.
- **No validation of `encrypt_parallel.v`.** `PARALLEL_ENCRYPT` defaults to 0
  everywhere, so no test at the default setting elaborates that file.
- **No baseline/optimized HQC ASIC arms.** Only one source tree exists.

---

## F31. The root cause was `read_hdl` file ordering, not RTL

`CLOG2` and `DIVCLOG2` are macros defined in `clog2.v`. No consumer contains
an `` `include ``, and the macros have no include guard. Genus makes a macro
visible only from the point `read_hdl` processes its defining file onward.
`genus_asap7_v2.tcl` used a bare `read_hdl [glob $RTL_DIR/*.v]`, giving
filesystem order, so every file read before `clog2.v` saw `` `CLOG2 `` as
undefined.

Forcing `clog2.v` first and sorting the rest:

```tcl
read_hdl -define {SHARED=1 SHARED_ENCAP=1} \
  [concat [list $RTL_DIR/clog2.v] [lsort [glob $RTL_DIR/*.v]]]
```

dropped VLOGPT-1 from 10 to 2 and VLOGPT-117 from 4 to 2 with **no source
edit**. `lsort` makes the order deterministic, which matters because
filesystem order is not stable across machines.

**Implication for the paper.** The Cross-Toolchain Portability Defects section
currently reports 13 of 59 files and 102 instances without separating genuine
source defects from tool configuration. A reviewer reproducing with a correct
read order gets a different number. Drawing the distinction strengthens the
finding: it identifies a class of apparent portability failure that is
recoverable by configuration alone, which is more actionable than a raw defect
count.

## F32. Cross-file parser-state contamination makes error counts useless

When one file fails to parse, later files in read order inherit errors they do
not have on their own.

**Proven, not assumed.** `hqc_kem_joint_design.v` parsed clean when read alone
with `clog2.v`. It failed with 15 error sites when `fixed_weight_cww.v` was
read between them. It cleared completely once `fixed_weight_cww.v` was fixed,
with no edit to the joint design at all. `keccak_top.v` cleared the same way.

Consequences, all of which shaped the method:

- Only the first error in read order is trustworthy.
- Error counts rise when a file gets further and exposes more downstream. They
  are not a progress metric. The metric is how deep into the read order the
  parser reaches.
- The correct loop is: fix the alphabetically first failing file, re-run,
  re-triage.

Observed directly: after repairing `encrypt.v`, the error count went from 26
to 45 while the frontier advanced from line 88 to line 793. After repairing
`v_minus_uy.v`, the count went 20 to 21 while the frontier moved to the next
file entirely.

## F33. The CLOG2 macro rewrite, and why it needed proof

The original macros were 30-deep ternary chains. Genus rejects that expansion
in parameter-default position, which was the root cause of an entire defect
class. Replaced with:

```verilog
`define CLOG2(x) ((x <= 1) ? 1 : $clog2(x))
`define DIVCLOG2(x) ((x <= 1) ? 0 : $clog2(x))
```

**Equivalence proven by sweep, not by inspection.** An `xrun` sweep over
x = 0 to 70000 compared each original macro against its replacement and
reported zero mismatches. 70000 covers `N` at all three security levels, which
is the largest argument in play.

The guard matters: the two definitions differ at `x = 1` if it is omitted.
`$clog2(1)` is 0, the original chain returns 1. Do not adopt a macro rewrite
of this kind without the sweep.

## F34. Every edit is semantically neutral by construction

Across the port, every edit falls into one of five classes:

| Class | Why it cannot change behaviour |
|---|---|
| Hoist a declaration above its first use | Pure reorder, proven per file by `LC_ALL=C sort` diff |
| Delete an identical duplicate declaration | Both declarations have the same type and width; Verilog semantics are unchanged |
| Add a `wire` declaration for a net that was implicit | An implicit net is 1 bit; the added declaration is also 1 bit, so the width the design sees is unchanged |
| Remove an empty statement (`x <= 0;;`) | A null statement has no effect. Verilog-2001 disallows it inside `begin-end`; Vivado accepted it |
| Substitute a value-equal expression | Each substitution proven equal at all three security levels, see F33 and the table in the next section |

The KAT result (H7, H8) confirms this rather than discovering it. That
ordering matters: the argument was constructed before the gate was run.

**One exception, recorded honestly.** In `encrypt_parallel.v`, `sel_fw` was
dropped from a hoisted `reg wen_fw, sel_fw, rd_fw;` line because the file
declares `sel_fw` standalone below, above its own first use. That is a
removal of a name from a declaration, not a reorder. It is safe because the
signal remains declared once with the same type, but it is not covered by any
of the five classes above and no test exercises the file.

---

## Every edit, by file

### Configuration, not source

| Item | Change |
|---|---|
| `read_hdl` invocation | `clog2.v` forced first, remainder `lsort`ed. Captured in `asic/portfix_wip/a7_ordered.tcl` |
| `-define` | `{SHARED=1 SHARED_ENCAP=1}`, taken from `hardware/joint_design/tcl/joint_design.tcl` lines 9 and 10. Without them Genus compiles `ifndef SHARED_ENCAP` branches the real build never sees |
| `hdl_error_on_blackbox` | `true` for elaborate. See F28 and the ASAP7 blackbox defect |

### `clog2.v`

Macro replacement per F33. 67 lines to 3. Applied in three locations:
`asic/portfix_wip/`, `hardware/common/`, `hardware/common/shake256/rtl/`, and
`build/joint_design/`. The two `hardware/` copies were verified byte-identical
to each other before the change.

### `encrypt.v`

The largest single file. Repairs in two rounds.

Round one, 2026-08-11, in `asic/portfix_wip/`: hoisted `r1_internal`,
`pm_rd_addr`, `xor_add_addr`, `u_cpy_addr`, `wen_fw`/`rd_fw`; then the
11-line declaration block formerly at 392 to 402 (`hs_in_0`, `hs_in_1`,
`sel_r1`, `sel_r2`, `sel_e`, `r2_internal`, `error`, `loc_addr`/`r1_e_rd_addr`,
`pm_out`, `start_poly_mult_r2h`, `start_poly_mult_sr2`, `done_poly_mult`);
then `u_out`, `pm_out`, `add_out`, `add_out_addr`, `xor_add_en`,
`xor_add_out`, `xor_add_out_addr`, `en_r1`, `en_r2`, `done_fw_transfer`,
`r2_done`; then `wen_u`, `sel_r1_hr2`, `start_fw_transfer`.

Removed the null statement `en_e <= 0;;`.

A `pm_out` duplicate was created by an intermediate hoist and removed in the
same pass.

Round two, 2026-08-12, in `build/joint_design/`: 29 declaration lines hoisted
above line 183, anchored on `reg [1:0] request_another_vector;`. The
`build/` copy carries the accepted `xor_add_addr_div` optimization override,
verified present after the edit.

Two scanner false positives were identified and **not** edited: the `hs_*`
group at lines 117 to 121 is commented out, and `shake_din` at 122 is a port
declaration.

### `encrypt_parallel.v`

2026-08-11: hoisted `r1_internal`, `r2_internal_hr2`, `r2_internal_sr2`. The
mechanism was an implicit net created by a port connection at line 367 that
collided with the explicit declaration at 410.

2026-08-12 earlier session: six further hoists plus a null statement.

2026-08-12 this session, applied to both `hardware/encap/` and
`build/joint_design/`: 30 declaration lines hoisted above line 183, one null
statement removed, one duplicate ` wire [RAMWIDTH-1:0] pm_out;` deleted
(identical width to the hoisted declaration), and `sel_fw` dropped from the
hoisted line per the exception in F34.

**This file is not elaborated by the default build.** `PARALLEL_ENCRYPT`
defaults to 0 in `decap.v` line 134, `encap.v` line 133, and
`hqc_kem_joint_design.v` line 108, and nothing overrides it except one
testbench. It was repaired anyway so the published design is Genus-clean at
both parameter settings; a portability claim with one core excluded is a
weaker claim.

### `fixed_weight.v`

**One parameter-default conversion.** `parameter LOG_WEIGHT = \`CLOG2(WEIGHT)`
became an explicit ternary returning 7, 7, 8 for hqc128, hqc192, hqc256.
`WEIGHT` is 66, 100, 131 at those levels and `$clog2` of those is 7, 7, 8.
Value-equal.

**Four macro substitutions**, all `` `CLOG2(WEIGHT) `` replaced by
`LOG_WEIGHT`, which is now bound to exactly that value:

| Line | Before | After |
|---|---|---|
| 238 | `wire [\`CLOG2(WEIGHT)-1:0] addr_ctx_0,addr_ctx_1;` | `wire [LOG_WEIGHT-1:0] ...` |
| 239 | `reg [\`CLOG2(WEIGHT):0] wr_addr_ctx, rd_addr_ctx;` | `reg [LOG_WEIGHT:0] ...` |
| 243 | `assign addr_ctx_0 = wr_addr_ctx[\`CLOG2(WEIGHT)-1:0];` | `... [LOG_WEIGHT-1:0];` |
| 244 | `assign addr_ctx_1 = rd_addr_ctx[\`CLOG2(WEIGHT)-1:0];` | `... [LOG_WEIGHT-1:0];` |

**Two hoists**, both to after `reg [31:0] shake_output_counter;` at 232:
`reg [1:0] sel_ctx;` from line 387, and `reg start_red =0;` from line 560.

In `build/joint_design/` the same two plus `reg [31:0] count_reg = 0;`,
anchored on `reg [4:0] state = 0;`. That copy carries a registered
`rejection_threshold_pass` override, verified preserved.

### `fixed_weight_ct.v`

**Two parameter-default conversions:**

| Parameter | Was | Now | Check |
|---|---|---|---|
| `LOG_WEIGHT` | `\`CLOG2(WEIGHT)` | 7 / 7 / 8 | `WEIGHT` = 66 / 100 / 131, `$clog2` = 7 / 7 / 8 |
| `LOG_W_CTX` | `\`CLOG2(WEIGHT*NO_OF_CTX*NUM_OF_FW_VEC)` | 9 / 9 / 10 | product per level, `$clog2` matches |

**Two hoists**, to around `reg [31:0] shake_output_counter;` at 222:
`reg start_red =0;` from line 544, and `reg [1:0] sel_ctx;` from line 364.

In `build/joint_design/` the same two, anchored on
`reg [31:0] shake_output_counter;`. That copy carries a 25-bit `shake_ctx`
memory override packing `dout_shake_pass` alongside the data, verified
preserved.

### `fixed_weight_cww.v`

The most heavily edited file, and the one whose failure was contaminating
`hqc_kem_joint_design.v` per F32.

**One parameter-default conversion.** `LOG_WEIGHT = \`CLOG2(WEIGHT)` to
7 / 7 / 8, same check as `fixed_weight.v`.

**One new parameter.** `LOG_N` = 15 / 16 / 16, against `N` of
17669 / 35851 / 57637 where `$clog2` gives 15 / 16 / 16. Added because
`` `CLOG2(N) `` appeared in eight declaration ranges that Genus rejects.

**Eight macro substitutions:**

| Line | Before | After |
|---|---|---|
| 203 | `reg [\`CLOG2(WEIGHT)-1:0] addr_bc;` | `reg [LOG_WEIGHT-1:0] addr_bc;` |
| 263 | `wire [\`CLOG2(WEIGHT)-1:0] addr_0,addr_1;` | `wire [LOG_WEIGHT-1:0] ...` |
| 264 | `reg [\`CLOG2(WEIGHT):0] wr_addr, rd_addr;` | `reg [LOG_WEIGHT:0] ...` |
| 278 | `wire [\`CLOG2(N)-1:0] mem_in_0, mem_in_1;` | `wire [LOG_N-1:0] ...` |
| 279 | `wire [\`CLOG2(N)-1:0] mem_out_0, mem_out_1;` | `wire [LOG_N-1:0] ...` |
| 280 | `wire [\`CLOG2(N)-1:0] mem_comp;` | `wire [LOG_N-1:0] mem_comp;` |
| 281 | `wire [\`CLOG2(N)-1:0] dout_shake_reduced;` | `wire [LOG_N-1:0] ...` (also hoisted) |
| 316 | `reg [\`CLOG2(N)-1:0] n_minus_i, n_minus_i_reg;` | `reg [LOG_N-1:0] ...` (also hoisted) |

**One instance-parameter substitution.** `mem_dual` instance `loca_mem`:
`.WIDTH(\`CLOG2(N))` became `.WIDTH(LOG_N)`. Value-equal, but this is the one
substitution that would have silently changed a memory width had `LOG_N` been
wrong, which is why the three-level check above was run explicitly.

**Four hoists**, all to after `reg [31:0]dout_shake_reg;` at 214:
`n_minus_i`/`n_minus_i_reg` from 316, `count` from 314,
`dout_shake_reduced` from 281, `dout_reduced_valid` from 330.

### `fft_part1.v`

**Two declaration lines hoisted**, six symbols, from lines 136 and 137 to
after `reg done;` at line 51, above first use at line 64:
`wire [7:0] gf_in1, gf_in2, gf_out;` and
`reg [7:0] gf_out_d1, gf_out_d2, gf_out_d3;`.

`hardware/decap/fft_part1.v` already had these correctly placed and needed no
change, which is why it appears in the divergence list but not the port-back
list.

### `hqc_rmdecod_findpeaks.v`

Added `wire last_din;`. The signal is driven by
`assign last_din = cnt_in[6:1]==63 & din_valid_i;`, a comparison, so it is
1 bit, matching the implicit width. Neutral per F34.

### `hqc_rsdecod_elp.v`

Added `wire last_cnt;`. Driven by
`assign last_cnt = (cnt==(2*PARAM_DELTA-1));`. Same argument.

### `hqc_rsdecod_roots.v`

Removed a duplicate `wire fft_done;`. Both declarations were bare, untyped
and identical.

### `keygen.v`

**Nine declarations hoisted** to after `wire [MEM_WIDTH-1:0] rand_out_1;` at
line 187, from three separate locations:

| From | Declaration |
|---|---|
| 404 | ` wire [MEM_WIDTH-1:0] pm_out;` |
| 405 | ` wire [\`CLOG2(N_MEM/MEM_WIDTH) - 1:0] pm_rd_addr;` |
| 406 | ` wire pm_rd_en;` |
| 408 | ` wire [MEM_WIDTH-1:0] add_out;` |
| 409 | ` wire [\`CLOG2(N_MEM/MEM_WIDTH) - 1:0] add_out_addr;` |
| 410 | ` wire add_out_valid;` |
| 332 | `wire [LOG_WEIGHT-1:0] y_addr;` |
| 700 | `reg [LOG_WEIGHT-1:0] x_addr, x_addr_reg = 0;` |
| 701 | `reg x_transfer_done;` |

Note the `` `CLOG2 `` uses here were left in place. They sit in declaration
ranges rather than parameter defaults, which the rewritten macro (F33) handles
correctly.

### `reed_muller_encode.v`

**Four declarations hoisted** to after `wire [N1-K-1:0] cdw_out_int;` at line
63: `reg init;`, `reg shift_cdw;`, `reg wr_en;` from lines 103 to 105, and
`reg [LOG_N1_BYTES-1:0] count_cdw_bytes = 0;` from line 107. First use is at
line 99 in `assign addr = (cdw_out_en)? cdw_out_addr : count_cdw_bytes;`.

### `reed_solomon_encode.v`

Two hoists, `reg init_msg;` and `reg shift_msg;` from lines 126 and 127 to
after `reg capture_cdw;` at line 69, above first use at 75. Pure reorder
verified.

### `v_minus_uy.v`

Five hoists: `xor_add_en`, `xor_add_addr`, `xor_add_out`, `xor_add_out_addr`,
`xor_add_out_valid`, moved above first use at 145, anchored on
`reg poly_mult_on;`.

In `asic/portfix_wip/` one duplicate ` wire [RAMWIDTH-1:0] pm_out;` was
removed; the `hardware/` and `build/` copies had only one declaration and
needed no removal.

`build/`'s copy carries the accepted `flag_precompute` win (commit `12d930d`,
the `uv_addr_0_mul_oob` and `uv_addr_1_oob` registered flags), verified
preserved. Copying `hardware/`'s version over it would have reverted the only
accepted HQC optimization.

### `vect_set_random.v`

Four hoists: `rand_mem_in`, `wr_en_rand`, `pk_rand_addr`, `pk_rand_addr_reg`,
anchored on ` wire [MEM_WIDTH-1:0] rmem_out_0, rmem_out_1;` above first use at
145.

`din_shake` was a scanner false positive: it is an `output wire` in the port
list at line 86.

`wr_en_rand` was already declared `reg`, so the hoist also cleared four
VLOGPT-86 "net not allowed in this context" errors on its procedural
assignments without any type change.

### `state_ram.v`

**No change.** The reported defect on `raddr_high_offset` at line 78 with a
first use at line 26 was a false positive: lines 20 to 26 are the GPL header
and a prose comment block.

### `keccak_top.v`, `hqc_kem_joint_design.v`

**No change.** Both cleared as cascade once upstream files were fixed. See
F32.

---

## F35. Three source trees had diverged, and only one is under test

There are three copies of the HQC source:

| Tree | Role |
|---|---|
| `hardware/` | The nominal source |
| `build/joint_design/` | What the KAT gate and the FPGA flow actually read. **Tracked in git**, carries the accepted optimization overrides |
| `asic/portfix_wip/` | The Genus port working tree |

`joint_kat_gate.py` `stage()` copies from `hardware/` into
`build/joint_design/` and then runs `git checkout -- build/joint_design/`,
which restores the tracked versions over the fresh copies. The comment calls
this "tracked overrides win over pristine copies", which is intended for the
optimization overrides, but the effect is that **every tracked file in that
directory is immune to changes made in `hardware/`.**

This was discovered the expensive way. The first KAT run after the port-back
returned PASS at all three levels while testing entirely pre-port source.
`build/joint_design/clog2.v` was 66 lines when `hardware/common/clog2.v` was 3.

The fix is to stage the `build/joint_design/` changes with `git add` before
running the gate, so the checkout restores from an index that already holds
them.

**This is the same failure mode as the `a1a7ad2` incident**, where the
optimized arm was silently reverted to pristine for three days by the
untracked build tree and `stage()` regeneration. It is the fourth instance of
the general pattern this week: the artifact under test was not the artifact
that changed. The others were the ASAP7 Barrett blackbox, the `bf2x2_baseline`
arm mispopulation, and this KAT.

**Standing rule that follows:** immediately before reading any result, verify
the artifact under test carries the change. A cheap, specific check beats a
plausible assumption. Here it was `wc -l build/joint_design/clog2.v`.

## F36. Defect taxonomy observed

| Class | Genus code | Fix | Pure reorder? |
|---|---|---|---|
| Use before declaration | VLOGPT-20 | hoist above first use | yes |
| Duplicate declaration | VLOGPT-22 | delete the duplicate, or hoist if it collides with an implicit wire | yes |
| Implicit net from a prior port connection | VLOGPT-22, VLOGPT-86 | hoist the explicit declaration above the port connection | yes |
| Procedural assignment to an implicit net | VLOGPT-86 | usually clears with the hoist if the declaration is already `reg` | yes |
| Macro in bit-select or parameter range | VLOGPT-117, VLOGPT-1 | substitute an existing parameter, or add one | no |
| Missing declaration for a continuous assign | VLOGPT-20 | add a `wire` declaration above first use | no |
| Null statement (`x <= 0;;`) | VLOGPT-1 | drop the extra semicolon | no |
| Unindexed array in sensitivity list | VLOGPT-61 | `always @*` | no |
| Instance without a name | VLOGPT-58 | usually cascade | n/a |

Declaration-before-use is the dominant class by a wide margin: it appears in
`encrypt.v`, `encrypt_parallel.v`, `fixed_weight.v`, `fixed_weight_ct.v`,
`fixed_weight_cww.v`, `fft_part1.v`, `hqc_rmdecod_findpeaks.v`,
`hqc_rsdecod_elp.v`, `keygen.v`, `reed_muller_encode.v`,
`reed_solomon_encode.v`, `v_minus_uy.v` and `vect_set_random.v`. Thirteen
files.

Vivado accepts all of these. None is a functional bug on FPGA.

## F37. The edit protocol, and four ways it nearly failed

Python with line-anchored literals and a count assert per literal, written to
a file on the server rather than piped as a heredoc. Then
`diff <(LC_ALL=C sort a) <(LC_ALL=C sort b)` to prove pure reorder.

Four failure modes hit this session. **All four fired the assert, so nothing
was ever silently corrupted**, which is the protocol working as designed.

1. **Trailing whitespace.** `wire [M-1:0] r1_internal; ` has a trailing space.
   Get exact bytes with `repr()` immediately before building the literal.
2. **Python `count` is substring-based, not line-based.**
   `"wire x;\n"` matches inside `" wire x;\n"`. Anchor every literal with a
   leading `\n`.
3. **Line numbers go stale after any edit.** A literal built from a line
   number reported two edits ago will not match. Re-derive immediately before
   use.
4. **Sort order versus strip order.** `sort | tr -d ' \t'` and
   `tr -d ' \t' | sort` give different results; the first appears to show
   content changes where there are none. Strip before sorting.

A fifth, from the earlier session: backticks do not survive a heredoc piped
through ssh. Write the script to a file with a quoted delimiter first.

---

## Readiness for an HQC ASAP7 run

Elaborate succeeds, so synthesis can start. Three things must be in place
first.

1. **The read configuration must carry the defines and the ordering.**
   `genus_asap7_v2.tcl` line 40 is still a bare
   `read_hdl [glob $RTL_DIR/*.v]`. A run launched through it today would
   synthesize a configuration no KAT has validated. Fold in the
   `a7_ordered.tcl` approach, ideally behind an environment flag so the ML-DSA
   arms are unaffected.
2. **`hdl_error_on_blackbox` must be `true`.** The arm is Verilog-only so it
   qualifies under F28. Elaborate has already been verified to pass with it
   set, so this costs nothing and prevents a repeat of the Barrett defect at
   full-design scale.
3. **An SDC for `hqc_kem_joint_design`.** None exists. Model it on
   `combined_top.sdc`: `create_clock` from `$PERIOD_PS`,
   `set_clock_uncertainty` at 5 percent, false paths on static configuration
   and async control, I/O delay at 10 percent of period each side.

### What is still missing for true ASIC PPA

The stated goal is baseline-versus-optimized HQC PPA on ASAP7. That needs two
arms, and **only one source tree exists.** The FPGA ledger's HQC pair is
`hqc_joint_pristine` and `hqc_joint_opt`, built from the arm definitions in
`asic/arms/hqc_baseline` and `asic/arms/hqc_optimized` per `MANIFEST.txt`,
which differ in 15 files plus `mem_single_dist.v`.

Both arms need the same portability repairs applied before either can be
synthesized, and the arms must be verified to differ only in the intended 15
files afterward. That is the next concrete task, and it is not small: the
repairs must be reapplied to two more trees whose layouts will differ again,
exactly as they did between `hardware/` and `build/joint_design/`.

---

## File map

| Item | Location | In git |
|---|---|---|
| Port working tree | `asic/portfix_wip/` | yes |
| Read configuration | `asic/portfix_wip/a7_ordered.tcl` | yes |
| Elaborate configuration | `asic/portfix_wip/a9_elab.tcl` | yes |
| Parse and elaborate logs | `logs/asic/hqc_portfix_20260812/` | yes |
| Unresolved and hierarchy reports | same directory | yes |
| Ported FPGA source | `hardware/`, 12 files | yes, branch `hqc-port-kat` |
| Ported build tree | `build/joint_design/`, 11 files | yes, same branch |
| `encrypt_parallel.v` substituted read log | `/tmp/epread3.log` on server | **no, pull pending** |
| KAT stdout, control and treatment | not captured to a file | **no** |

Two gaps to close: the `epread3.log` pull, and capturing the KAT stdout for
both runs so H6 through H9 have log paths rather than transcript quotes.

---

## Next steps

1. Pull `epread3.log` and capture KAT output to files so every Results of
   Record row has a committed log path.
2. FPGA re-close on the ported source. Reproduce 9.12 ns, 109.6 MHz,
   WNS +0.072. If it moves, the port is not timing-neutral and the branch does
   not merge.
3. Merge `hqc-port-kat` to main only after step 2.
4. Apply the repairs to `asic/arms/hqc_baseline` and `asic/arms/hqc_optimized`,
   then verify the two arms differ only in the 15 intended files.
5. Write the HQC SDC and fold the ordering and defines into the synthesis
   script.
6. Then, and only then, an HQC ASAP7 synthesis pair.

---

## Open questions for the advisor

1. The port's root cause was substantially a `read_hdl` configuration problem
   rather than RTL defects (F31). Does the portability contribution hold in
   its current form, and should the defect taxonomy separate "cross-tool RTL
   defects" from "tool configuration"? The honest framing is that both exist
   and the paper currently conflates them.
2. `encrypt_parallel.v` is repaired but untested, because no build at
   `PARALLEL_ENCRYPT = 1` has ever been run. Is a build at that setting worth
   standing up, or is documenting the gap sufficient?
3. F35 records that the build tree, not the nominal source tree, is what every
   test and flow actually reads. That has now caused two silent reversions in
   this project. Is collapsing the trees worth doing before the paper, or
   after?
