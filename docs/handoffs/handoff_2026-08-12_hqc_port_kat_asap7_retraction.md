# HANDOFF: HQC port completed and KAT-validated, ASAP7 closure invalidated, FPGA re-close

Session: 2026-08-12 afternoon through evening.
Continues: `docs/handoffs/handoff_2026-08-12_fpga_closure_blackbox_hqc_port.md`.
Branch: **`hqc-port-kat`**, pushed. Not merged to main.
Commits this session: `9fdfe2b`, `f553b40`, `b2ad3a0`, `74fbf29`, plus the
`encrypt_parallel.v` commit.

**Read this first:** two results from earlier in the week are now invalid or
in question. Section 3 retracts the ASAP7 closure pair. Section 4 has an
unexplained 0.31 ns regression on the HQC optimized FPGA arm. Do not quote
either until they are resolved.

---

## Ground rules

1. Never quote a number that is not in a RESULTS OF RECORD table.
2. Distinguish measured from proposed.
3. Measurement configuration travels with the number.
4. Flag any delta smaller than known tooling sensitivity.
5. I run all commands locally and paste output. Concise code and direction.
   No em dashes in any deliverable.
6. RTL edits: `.bak`, anchor-count assert, gate, KAT at all three levels,
   synth, commit. Explicit approval before editing a source file.
7. Watch for vacuity. Verify the files being synthesized are the files that
   changed.
8. Do not guess. Confirm against the repo, the server, or vendor docs.
9. Verify the file set is complete, not just that hashes match.
10. Read vendor documentation rather than guessing attribute names.
11. **New this session: verify the artifact under test carries the change,
    immediately before reading any result.** This failed four times this week.
    A one-line check (`wc -l build/joint_design/clog2.v`) caught the worst of
    them. See section 2.

---

## 1. The HQC Genus port is complete and KAT-validated

Findings doc: `docs/findings/asic/2026-08-12_hqc_genus_port.md`, F31 to F37,
committed. It documents **every edit at symbol level** with source and
destination lines, and the value-equality proof for each parameter
substitution at all three security levels. Read it before touching HQC RTL.

### State

| # | Result | Log |
|---|---|---|
| H1 | Genus parse, full tree, `ARM_READ_OK`, 0 errors | `logs/asic/hqc_portfix_20260812/a7read17.log` |
| H2 | Elaborate `hqc_kem_joint_design`, `ARM_ELAB_OK`, 0 errors, `hdl_error_on_blackbox true` | `.../a9elab2.log` |
| H3 | No unresolved references, no empty modules | `.../hqc_unresolved.rpt` |
| H5 | DRC clean after elaborate | `hqc_elab_drc.rpt` |
| H7 | Joint KAT `--all` PASS on ported source, 227s | `.../joint_kat_ported_20260812.log` |
| H8 | Cycle counts 45599 / 117619 / 232743 total, 4611 / 5485 / 9199 decode | as above |
| H9 | Identical to the pre-port control | as above |

### What was finished this session

`reed_solomon_encode.v`: hoisted `reg init_msg;` and `reg shift_msg;` above
first use at 75, anchored on `reg capture_cdw;`.

`v_minus_uy.v`: five `xor_add_*` hoists above first use at 145, anchored on
`reg poly_mult_on;`, plus one duplicate ` wire [RAMWIDTH-1:0] pm_out;`
removed.

`vect_set_random.v`: four hoists, `rand_mem_in`, `wr_en_rand`,
`pk_rand_addr`, `pk_rand_addr_reg`, anchored on
` wire [MEM_WIDTH-1:0] rmem_out_0, rmem_out_1;`.

`state_ram.v`: **no change needed.** The reported defect was a comment-block
false positive.

`encrypt_parallel.v`: 30 declaration hoists above line 183 anchored on
`reg [1:0] request_another_vector;`, one null statement removed, one duplicate
` wire [RAMWIDTH-1:0] pm_out;` deleted, and `sel_fw` dropped from the hoisted
`reg wen_fw, sel_fw, rd_fw;` because the file declares `sel_fw` standalone at
225 above its own first use at 239. Applied to `hardware/encap/` and
`build/joint_design/`.

### Elaborate needs a library

`a8_elab.tcl` failed with `LBR-163: No target technology library was loaded`.
That is not an RTL problem. `a9_elab.tcl` adds the ASAP7 lib and lef setup
lifted from `genus_asap7_v2.tcl` and works. Use `a9_elab.tcl`.

---

## 2. F35: `build/joint_design/` is the optimized arm, and it silently reverts

**This is the most important structural fact in this handoff.**

`synthesizer.py`'s `MODULE_SOURCES` defines the two HQC arms as two
directories with **zero files in common**:

| Arm key | Reads from |
|---|---|
| `hqc_joint_pristine` | `hardware/` |
| `hqc_joint_opt` | `build/joint_design/` |

So `build/joint_design/` is not a build artifact. It is the optimized arm, it
is tracked in git, and it carries the accepted optimization overrides.

`joint_kat_gate.py` `stage()` copies from `hardware/` into
`build/joint_design/` and then runs `git checkout -- build/joint_design/`,
which restores the **index** versions over the fresh copies. Consequence:
every tracked file there is immune to changes made in `hardware/` unless the
change is also staged with `git add`.

**This produced a false PASS.** The first KAT run after the port-back returned
PASS at all three levels while testing entirely pre-port source.
`build/joint_design/clog2.v` was 66 lines while `hardware/common/clog2.v` was
3. It was caught only by an explicit `wc -l` check afterward.

Same failure mode as the `a1a7ad2` incident, where the optimized arm was
silently pristine for three days.

**Procedure that works:** edit `build/joint_design/`, `git add` it, then run
the gate, then verify with `wc -l build/joint_design/clog2.v` (expect 3) and
`grep -n "reg sel_e" build/joint_design/encrypt.v` (expect ~187, not 391).

### The overrides, verified preserved

| File | Override |
|---|---|
| `encrypt.v` | `xor_add_addr_div` precomputed division |
| `encrypt_parallel.v` | same `xor_add_addr_div` |
| `fixed_weight.v` | registered `rejection_threshold_pass` |
| `fixed_weight_ct.v` | 25-bit `shake_ctx` packing `dout_shake_pass` |
| `v_minus_uy.v` | `flag_precompute` win, `uv_addr_0_mul_oob` / `uv_addr_1_oob` registered flags, commit `12d930d` |

Copying `hardware/`'s version over any of these reverts the optimization. Four
files needed in-place edits for this reason.

---

## 3. RETRACTION: the ASAP7 butterfly2x2 closure pair is invalid

### What the searches said

Both arms, `asap7_fmax.py`, TOL 5 ps, bracket 400 to 700, with
`Barrett_8380417.v` present, SDC with 5 percent uncertainty:

| Arm | Reported closure | Fmax |
|---|---|---|
| baseline | 583 ps | 1715.8 MHz |
| optimized | 592 ps | 1688.7 MHz |

Logs committed at `logs/asic/asap7_bf2x2_fmax_v2_base_20260812/` and
`..._opt_20260812/`, eight points each with area, gates, power and timing.

### Why it is invalid

A single-point run of the **optimized** arm at 583 ps, `genus_asap7_v2.tcl`,
same SDC, **MET at 0 ps** with data path 538 ps. Its own search reported 588
VIOLATED with data path 549 ps.

Same arm, tighter constraint, **11 ps shorter data path**, and it meets where
the looser constraint failed. Confirmed pattern across three independent runs:
588 fails, 583 passes, 592 passes.

**`asap7_fmax.py`'s binary search assumes monotonicity: if P fails, everything
below P fails.** F17S already established that assumption is false for this
flow. This is a direct counterexample. Every closure number the search has
produced is an **upper bound**, not a minimum. That applies to C-close
(578 ps), D-close (573 ps), and both v2 closures.

### What replaces it

A same-period head-to-head, which needs no monotonicity assumption:

| Period | Baseline | Optimized |
|---|---|---|
| 583 ps | MET 0 ps, 22160 cells, 63992 area | MET 0 ps, 22453 cells, 67687 area |

Both arms meet 583 ps. Optimized costs **+5.8 percent area** for no timing
benefit at that period.

**Withdrawn explanations.** I earlier attributed the 9 ps gap to capture
overhead, having found the baseline's endpoint on a `DFFHQx4_ASAP7_75t_SL`
(setup 7 ps) and the optimized on a `DFFHQNx1_ASAP7_75t_L` (setup 15 ps), with
both delivering 548 ps of data path. That analysis explained a gap that does
not exist. The cell-type observation is still true and may matter later, but
it is not the explanation for anything right now.

### Six probe points in flight at session end

Launched to map the meet/fail pattern rather than search it. All
`genus_asap7_v2.tcl`, same SDC, `nice -n 19`:

`bf2x2_base_p569b`, `bf2x2_opt_p569b`, `bf2x2_bas_p540`, `bf2x2_opt_p540`,
`bf2x2_bas_p555`, `bf2x2_opt_p555`.

Check:
```bash
ssh engr -n 'grep -m1 -H -E "^Path 1:" ~/pqc/hqc/asic/asap7/out/bf2x2_{bas,opt}_p5{40,55}/*_timing.rpt ~/pqc/hqc/asic/asap7/out/bf2x2_{base,opt}_p569b/*_timing.rpt 2>/dev/null'
```

**Note on the 540 and 555 directories:** each was launched twice by accident.
The second launch hit the empty-OUTDIR guard and was refused, so `run.log` in
those four directories contains only the guard error. The live run's output is
in `genus.log`. Read `genus.log`, not `run.log`, for those four.

### What the ASAP7 findings doc should say

Not yet written, deliberately, pending the six probes. The defensible content:

- Both arms meet 583 ps. Area and power at that point.
- Closure figures from `asap7_fmax.py` are upper bounds because the constraint
  response is non-monotonic. F17S plus the 583-versus-588 counterexample is the
  evidence.
- Do not report a closure period or a derived Fmax for either ASAP7 arm.
- The endpoint split from F15 and F25 reproduces with Barrett present: every
  baseline VIOLATED point binds `barrett_datai_reg`, every optimized VIOLATED
  point binds `mult_p_reg`. MET endpoints scatter across `aj5`, `ajlen5`,
  `barrett_datai`.
- Another F17S inversion in the optimized arm: 597 ps gives 66441 area against
  592's 67856 and 606's 67369.
- **`asap7_fmax.py` should not be used for ASAP7 closure again** without
  addressing the monotonicity assumption.

---

## 4. FPGA re-close: baseline reproduces, optimized regressed 0.31 ns

Both arms regenerated from current tracked sources at `regen_period_ns` 8.600,
OOC, then `fmax_search.py`.

### Baseline: control satisfied

```
iter 0: 9.0ns  -> WNS -0.081 (VIOL)
iter 1: 9.25ns -> WNS  0.215 (MET)
iter 2: 9.12ns -> WNS  0.072 (MET)
iter 3: 9.06ns -> WNS  0.043 (MET)
iter 4: 9.03ns -> WNS -0.346 (VIOL)
closing_period_ns 9.06, closing_fmax_mhz 110.4
```

**9.12 ns gives WNS +0.072, matching the ledger's canonical value exactly.**
The portability repairs are FPGA-neutral on the baseline arm. That is the
`cd92639`-style control the port needed, and it passes.

The search then found 9.06 also meets and closed there rather than 9.12. Not a
contradiction, just a lower probe than the original search made.

### Optimized: 0.31 ns worse than the ledger

```
iter 0: 8.6ns  -> WNS -0.283 (VIOL)
iter 1: 8.8ns  -> WNS -0.072 (VIOL)
iter 2: 8.9ns  -> WNS -0.067 (VIOL)
iter 3: 8.95ns -> WNS  0.066 (MET)
iter 4: 8.93ns -> WNS  0.047 (MET)
closing_period_ns 8.93, closing_fmax_mhz 112.0
```

Ledger says 8.62 ns / 116.0 MHz / WNS +0.006. Here 8.6 violates by 0.283.

**All five optimization overrides verified still present** in
`build/joint_design/` after the port. So this is not a lost optimization.

Two remaining candidates, untested:

1. The bracket. I used 8.2 to 9.0; the ledger used 8.0 to 9.5. The search
   never probed below 8.6, so it never tested the region where 8.62 lives.
   Given `fmax_search.py` shares the monotonicity assumption that just failed
   on Genus, this is a live possibility.
2. The repairs genuinely cost 0.31 ns on this arm. They cost the baseline
   nothing, and they are pure reorders plus proven-equal substitutions, so
   this would be surprising.

**A wide-bracket rerun was launched at session end** and reuses the existing
checkpoint, no regen needed:

```bash
cd /mnt/c/PQC/hqc && cat logs/asic/hqc_fpga_reclose_opt_wide_20260812.log
```

If it lands at 8.62, the port is neutral on both arms and the branch can merge.
If it lands near 8.93 again, the next step is a pre-port control: check out
`build/joint_design/` at `f553b40~1`, regen, and search with the identical
bracket. That isolates the port from the search.

**The branch does not merge until this resolves.**

---

## 5. HQC ASAP7 arms: baseline done, optimized outstanding

Goal is baseline-versus-optimized HQC PPA on ASAP7. That needs both
`asic/arms/hqc_baseline` and `asic/arms/hqc_optimized` ported.

### Baseline arm: complete

The arms turned out to be plain **unrepaired copies** of the same source, not
divergent trees. Every difference inspected was repair-shaped. So 19 files were
straight-copied from `asic/portfix_wip/`:

`clog2.v`, `decap.v`, `decrypt.v`, `encap.v`, `encrypt.v`,
`encrypt_parallel.v`, `fft_part1.v`, `fixed_weight.v`, `fixed_weight_ct.v`,
`fixed_weight_cww.v`, `hqc_rmdecod_findpeaks.v`, `hqc_rsdecod_elp.v`,
`hqc_rsdecod_roots.v`, `keygen.v`, `reed_muller_encode.v`,
`reed_solomon_encode.v`, `state_ram.v`, `v_minus_uy.v`, `vect_set_random.v`.

Read verified: **`ARM_READ_OK`, zero errors**, using
`/tmp/armread_base.tcl`, which is `a7_ordered.tcl` with the path substituted.

Note `state_ram.v` needed no repair in `portfix_wip/` but the arm's copy was
missing the four `always @*` conversions from the original session, so the copy
does repair it.

### Optimized arm: 22 files differ, 8 need in-place edits

```
clog2.v decap.v decrypt.v encap.v encrypt_parallel.v encrypt.v fft_part1.v
fixed_weight_ct.v fixed_weight_cww.v fixed_weight.v hqc_kem_joint_design.v
hqc_rmdecod_findpeaks.v hqc_rsdecod_elp.v hqc_rsdecod_err_val.v
hqc_rsdecod_roots.v keygen.v reed_muller_encode.v state_ram.v syncfifo.v
vect_set_random.v v_minus_uy.v xor_based_adder.v
```

Diff size against the ported tree, which indicates how much is optimization
versus missing repair:

| File | Lines differing |
|---|---|
| `fixed_weight_ct.v` | 100 |
| `v_minus_uy.v` | 25 |
| `reed_muller_encode.v` | 12 |
| `fft_part1.v` | 6 |
| `encrypt.v` | 4 |
| `reed_solomon_encode.v` | 4 |
| `fixed_weight.v` | 2 |
| `vect_set_random.v` | 2 |

The method that worked all session: for each file, diff the arm's copy against
`git show 913a5ac:asic/portfix_wip/<file>`. If the diff is purely
repair-shaped, copy the ported version. If it contains optimization content,
reapply the repairs in place with line-anchored literals and a count assert,
then prove pure reorder with
`diff <(LC_ALL=C sort a) <(LC_ALL=C sort b)`.

### The SDC does not exist yet

`hqc_kem_joint_design` has no SDC. Full port list, gathered:

Clock and control: `clk`, `rst`, `operation[1:0]`, `start`, `done`.
Keygen: `sk_seed_addr[3:0]`, `sk_seed[31:0]`, `sk_seed_wen`,
`pk_seed_addr[3:0]`, `pk_seed[31:0]`, `pk_seed_wen`, `keygen_out_type[1:0]`,
`keygen_out_en`, `keygen_out_addr`, `keygen_out`.
Encap: `m_in[31:0]`, `m_addr`, `m_wen`, `encap_out_type[1:0]`,
`encap_out_en`, `encap_out_addr`, `encap_out[127:0]`.
Public key and syndrome: `h_0`, `h_1`, `h_addr_0`, `h_addr_1`, `s_0`, `s_1`,
`s_addr_0`, `s_addr_1`.
Decap: `decap_in_type[1:0]`, `decap_in`, `decap_in_addr`, `decap_in_wen`,
`y_addr`, `y`, `u_0`, `u_1`, `u_addr_0`, `u_addr_1`, `v_0`, `v_1`,
`v_addr_0`, `v_addr_1`, `decap_out_en`, `decap_out_addr`, `decap_out`.

Model on `sdc/combined_top.sdc`: `create_clock` from `$PERIOD_PS`,
`set_clock_uncertainty` at 5 percent, `set_false_path` from the static and
async controls (`operation*`, `rst`, `start`, and the `*_wen` / `*_en` group),
`set_input_delay` and `set_output_delay` at 10 percent of period on the data
and address ports.

### The synthesis script still is not HQC-safe

`genus_asap7_v2.tcl` line 40 is still a bare
`read_hdl [glob $RTL_DIR/*.v]`, with no `-define {SHARED=1 SHARED_ENCAP=1}`
and no clog2-first ordering. **An HQC run launched through it today would
synthesize a configuration no KAT has validated.** Fold in the
`a7_ordered.tcl` approach behind an environment flag so the ML-DSA arms are
unaffected.

Also set `hdl_error_on_blackbox true` for HQC. Elaborate has already been
verified to pass with it set, so it costs nothing and prevents a repeat of the
Barrett defect at full-design scale.

### Caution on the eventual comparison

The ASAP7 closure search is unsound for this flow (section 3). Do not design
the HQC ASIC comparison around closure. Use fixed-period head-to-heads from
the start.

---

## 6. Everything not done

### Blocking the branch merge

- [ ] Resolve the optimized FPGA re-close, 8.93 versus the ledger's 8.62.
      Wide-bracket rerun in flight; pre-port control if that does not settle it.
- [ ] Merge `hqc-port-kat` to main only after that.

### Documentation

- [ ] **ASAP7 findings doc**, pending the six probes. Content sketched in
      section 3. Must include the closure retraction and the reason.
- [ ] **Supersession, both directions**, for C-close, D-close and the v2
      closures: banner on `docs/findings/asic/2026-08-10_bf2x2_ooc_fmax.md`,
      INDEX row change, struck-through rows with the reason.
- [ ] **F11 is used twice**, in `2026-08-02_asap7_transition` (flip-flop memory
      model) and `2026-08-08_asap7_chip_base_complete` line 104 (mapping
      runtime). Open since 2026-08-10.
- [ ] **Retracted projected-fmax figures still quoted in six docs.** Numbers
      113.6, 120.8, 128.3 MHz and the derived +12.9 percent.
      `grep -rn "113.6\|120.8\|128.3\|12.9%" docs/`
- [ ] `flow_sweep_log.jsonl` header note about retracted projected-fmax values.
- [ ] README note on the 65-versus-59 proposal count.

### Measurement

- [ ] Six ASAP7 probes, in flight.
- [ ] Wide-bracket FPGA optimized re-close, in flight.
- [ ] HQC optimized arm port, 8 files in place plus copies.
- [ ] HQC SDC.
- [ ] HQC synthesis script fix.
- [ ] B3, B5, B6 area and power, still unread on the server.

### Paper, deadline 2026-08-15

Five revisions drafted in the previous session, **still not applied**:

1. **ASIC Status** claims both accelerators elaborate and synthesize in Genus.
   HQC now does elaborate, so this can be updated upward, but it does not yet
   synthesize. State exactly that.
2. **Cross-Toolchain Portability Defects** reports 13 of 59 files and 102
   instances without separating source defects from tool configuration. F31
   shows file ordering alone cleared 8 of 10 VLOGPT-1 and 2 of 4 VLOGPT-117
   with no source edit. Add the distinction; it strengthens the finding.
3. **Discussion** cites "roughly 11 percent" effort sensitivity, which is F3
   from a doc the INDEX marks **SUPERSEDED (GPDK045)**. The figure is 10.9
   percent and was measured on 45 nm, not ASAP7.
4. **"Two of these repairs were themselves proposed and applied
   autonomously"** is not traceable to a Results of Record entry. Find the log
   and commit hash or cut the sentence.
5. **65 versus 59 proposal count** needs one clause explaining the filter if
   the public log shows 65.

Group meeting items, unchanged: send Sanjay the locations where the LLM made
changes for the figures; finish final ML-DSA runs and figures; methodology and
framework figures; repo cleanup with Zain and Sanjay.

### Scope judgment for the paper

The FPGA closure pair G1 and G2 (9.50 ns and 8.75 ns, 7.9 percent) is
unaffected by anything in this handoff and remains the headline. The ASIC
section is a portability contribution plus a same-period head-to-head, not a
closure comparison. An HQC ASAP7 PPA number is not plausible before the 15th
and the manuscript already says no ASAP7 result exists.

---

## 7. Open questions for the advisor

Carried:

1. Is a single-arm pre-layout snapshot with a flip-flop memory model worth
   reporting, or should the ASIC section stay portability only?
2. Does "all three security levels" mean before the 2026-08-15 deadline?
3. Priority between the D&T submission and starting ML-KEM.
4. F15 says a MET run's endpoint carries no design information, and the chip
   run A1 is a MET run. Does that weaken the chip section?
5. F16 puts the ripple-carry adder on the critical path at one constraint out
   of eight. Does that survive as a paper claim?
6. F22 shows repeat runs are not a control for this flow, since Genus is
   bit-deterministic. What does that change about claimed experimental rigor?

New this session:

7. **The ASAP7 closure search is unsound** because the constraint response is
   non-monotonic (section 3). Every ASIC closure figure in the project is an
   upper bound. Does the ASIC section drop closure entirely in favour of
   fixed-period comparisons, and does the same concern apply to the Vivado
   closures that produce G1, G2, M1, M2 and the HQC ledger? Nobody has tested
   whether Vivado behaves the same way, and that is a cheap experiment with
   large consequences.
8. **The port's root cause was substantially tool configuration**, not RTL
   defects (F31). Should the defect taxonomy separate the two, and does the
   portability contribution hold in its current form?
9. `encrypt_parallel.v` is repaired but covered by no test, because
   `PARALLEL_ENCRYPT` defaults to 0 everywhere. Is a build at
   `PARALLEL_ENCRYPT = 1` worth standing up?
10. Three source trees exist for HQC and only `build/joint_design/` is under
    test (F35). Two silent reversions have now been traced to this. Is
    collapsing the trees worth doing before the paper or after?
