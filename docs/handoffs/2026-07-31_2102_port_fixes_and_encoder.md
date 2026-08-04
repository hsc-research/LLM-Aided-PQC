> **NOTE 2026-08-03.** The ML-DSA figures in this handoff (82.7 MHz, +17.8%)
> were pinned-flow and are retired. Current: M1 70.2 / M2 80.5 MHz, +14.7%,
> OOC, in `docs/findings/INDEX.md`. Retained as a dated record of what was
> known at the time; numbers below are not edited.

# Handoff: LLM-Aided-PQC, ASIC/Genus Port, 2026-07-31 (evening)

Supersedes `docs/handoffs/2026-07-31_1339_asic_genus_port.md`. Read that one
first for environment setup, then this for current state.

---

## Ground rules

1. **Never quote a performance number that is not in a RESULTS OF RECORD table**
   in `docs/findings/`. If asked about a result you cannot find there, say so.
2. **Distinguish measured from proposed.** Next steps are not results.
3. **Cite IDs** (A1, F3, ...) not bare numbers.
4. **Measurement configuration travels with every number**: effort, corner,
   blackboxing, place-and-route or not.
5. **Flag any delta smaller than 10.9%**, the known Genus effort sensitivity (F3).
6. Lloyd runs all commands locally and pastes output. Concise code and
   directions, not free-form RTL. **No em dashes.**
7. RTL edits: `.bak` -> anchor assert -> gate -> KAT at all three levels ->
   commit. Ask before editing any source file.
8. **Watch for vacuity.** Verify the files being synthesized are the files that
   changed.
9. Be concise. Lloyd is usage-constrained.

---

## RUNNING RIGHT NOW (check this first)

**ML-DSA encoder arm comparison**, launched 19:50 PDT, expected done ~22:00.

```bash
ssh engr 'cat ~/pqc/hqc/asic/out/enc_arms.log'
ssh engr 'ps -u alco9414 -o pid,etime,pcpu,args | grep enc_fmax | grep -v grep'
```

Binary search on `encoder`, both arms, bracket 2.0 to 5.0 ns, **high effort**,
tolerance 0.05 ns. About 11 minutes per point, so roughly one hour per arm.
Script `asic/encwork/run_arms.sh`, driver `asic/encwork/enc_fmax.py`, TCL
`asic/encwork/enc_fmax.tcl`. Outputs in `asic/out/enc_baseline/` and
`asic/out/enc_optimized/`.

**Known single data point already measured:** baseline at 5.000 ns is MET with
368 ps slack, area 7061.958 um^2, 2812 cells, path
`di_buffer_reg[50]/CK -> di_uncentered_buffer_reg[68]/D` (flop to flop, valid).
Zero blackboxes.

**A hazard to check before trusting results:** a duplicate standalone 5 ns run
may have been launched into the same `enc_baseline/` directory. Confirm only
one `python3 enc_fmax.py` and one `genus` are running. A second Genus writing
the same report filename would corrupt a search point.

When it finishes, results go in a RESULTS OF RECORD table as A5 (baseline) and
A6 (optimized), with the search traces.

---

## What changed today

### Autonomous port-fix loop, built and working

New: `agent/port/` containing `fix_templates.py` (defect taxonomy with autonomy
flags), `port_gate.py` (three-stage gate), `propose_fix.py` (model call plus
deterministic apply), `run_port_fix.py` (orchestration), `sweep_fixes.py`
(file list driver), `port_log.jsonl` (evidence).

**Three files fixed autonomously, no human inspection of the diff:**

| File | Code | Result | Commit |
|---|---|---|---|
| `reed_solomon_encode.v` | VLOGPT-20 | ACCEPTED, 2 symbols | `908745d` |
| `fft_part1.v` | VLOGPT-20 | ACCEPTED, 4 symbols | `e9996b0` |
| `reed_muller_encode.v` | VLOGPT-20 | ACCEPTED, 6 lines, 2 clusters in one pass | `14daf81` |

All three: stage 1 sorted diff pure reorder, stage 2 Genus accepts, stage 3 HQC
KAT PASS at 128/192/256.

### The gate design, and why each stage exists

No single check is sufficient. This is the core methodological point.

| Stage | Catches | Structurally misses |
|---|---|---|
| 1. `LC_ALL=C sort` diff | added, removed, altered lines | a hoist into a procedural block is a pure reorder AND illegal Verilog |
| 2. Genus re-read | scope and syntax violations | a semantic change that still parses |
| 3. KAT at 3 levels | semantic change | nothing relevant, but slow |

A deletion cannot be checked by stage 1 at all, so `VLOGPT-22` fixes get a
two-stage gate. That is recorded explicitly in the log as
`("pure_reorder", None, "skipped: ...")` so a record can never imply a check
that did not run.

### Design decisions forced by real failures

- **The model returns line ranges, never text.** Asking it to reproduce
  trailing whitespace caused two spurious stage-1 failures. Deterministic code
  moves the original bytes.
- **Destination must be at module scope AND strictly above first use.** The
  model once moved a declaration from line 385 to 383 while the use was at 234.
  Module scope alone was an insufficient specification.
- **Deletions permitted only for VLOGPT-22.** A hoist proposal that included a
  deletion would skip stage 1, the strongest check. Now refused.
- **Multiple moves applied bottom-up** so line numbers stay valid.
- **Probe matches `^Error` only.** Warnings (VLOGPT-37) were being read as the
  first error and triaged as unknown codes.
- **`parse_check.tcl` sets `hdl_search_path`.** Without it, includes fail and
  produce defect-shaped artifacts.
- **Genus stays resident after `read_hdl`.** Both probe and stage 2 now
  background it, poll the log, then `pkill -f parse_check.tcl`. Blocking cost
  15 minutes per defective file.

### Taxonomy status

| Code | Name | Autonomous | Note |
|---|---|---|---|
| VLOGPT-20 | use before declaration | **yes** | 3 files fixed |
| VLOGPT-22 | duplicate declaration | **no**, downgraded today | see below |
| VLOGPT-61 | array in sensitivity list | no | `always @(*)` changes sensitivity, not a reorder |
| CDFG-238 | mixed blocking/non-blocking | no | changes semantics by design |
| VLOGPT-37 | reg initial value | n/a | warning, Genus ignores it |
| VLOGPT-506 | ram_style attribute | n/a | warning, drives blackbox decision |

**VLOGPT-22 was downgraded because the model reasoned from a false premise.**
On `vect_set_random.v` Genus reported redeclaration of `rand_mem_in` and
`wr_en_rand`, but only ONE declaration of each exists in the file and neither
appears in the included `keccak_pkg.v` (verified by grep, empty result). The
model proposed deleting the only declarations present. **The source of the
reported duplicate is not understood and should be investigated before this
class is re-enabled.**

### ML-DSA now elaborates in Genus

Three fixes, all applied identically to both arms and to the reference tree at
`/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src`:

- `combined_top.v`: hoisted `a_generated`, `a_generated_during`,
  `op_done_ntty` to module scope (F8)
- `ntt_fifo_piso.v`: eight blocking assignments converted to non-blocking (F9)
- Added 16 `.vhd` files plus `common/mldsa_params.v` to both arms (F10). ML-DSA
  is a **mixed-language design**; the Keccak core is VHDL and a Verilog-only
  glob silently blackboxed it.

**VHDL package read order is load-bearing**: `sha3_pkg.vhd` and
`keccak_pkg.vhd` must be read before their users. Alphabetical glob fails.

Full KAT PASS 25/25 vectors, 70.8 s, after the fixes.

### Backend abstraction (Phase 1, what Abideen asked for)

`agent/backends/{base,vivado,genus}.py`. `optimize_once()` takes an optional
`backend` argument; default `None` preserves every existing call site on
Vivado. `assert_comparable()` refuses to compare results across backends or
configs, making F3 a runtime error rather than a convention.

**Not yet tested end to end.** The server has been busy.

### Dashboard

`agent/dashboard.py` now reads `agent/port/port_log.jsonl` as a new tier,
"Cross-toolchain port fixes". Maps `file` to block and `code` to strategy.

**Cannot currently be viewed.** `localhost:5000` and `10.0.0.122:5000` both
fail from the Windows browser, probably the university VPN capturing routes
combined with WSL mirrored networking. Flask itself binds fine
(`host="0.0.0.0"` now). Untested theory: disconnecting the VPN would fix it,
but that would drop the server connection.

---

## Full-chip ML-DSA: abandoned for now

A single synthesis point at 10 ns, high effort, ran **1 hour 53 minutes and
never advanced past `pre_to_gen_setup`**, which is before `syn_generic` proper.
12 partitions, 16.8 GB peak memory. Killed.

Extrapolating, one point is 6 to 12 hours, so a search is 48 to 96 hours across
two arms. Not achievable before the deadline.

**Note the bottleneck is elaboration and partitioning, not optimization**, so
lowering effort may not help. That is untested. If someone wants to settle it,
run one full-chip point at medium effort overnight purely for feasibility.

Consequence: the ML-DSA ASIC arc is **block-level**, and F6 already established
that block-level results do not predict chip-level ones. This must be stated as
a limitation, not glossed. The FPGA chip-level result (+12.0% post-route) still
stands on its own target.

---

## Unfinished work

### HQC port fixes, 9 of 12 files remaining

```bash
cd /mnt/c/PQC/hqc
python3 agent/port/sweep_fixes.py <basename>.v
```

| File | Path under `hardware/` | Status |
|---|---|---|
| `fixed_weight.v` | `common/fixed_weight/` | **3 instances** (`din_shake`, `sel_ctx`, `start_red`). Loop fixes one or two per call, then stage 2 fails on the rest and reverts the good work. **Do by hand.** |
| `state_ram.v` | `common/shake256/rtl/` | VLOGPT-61, needs human |
| `vect_set_random.v` | `keygen/` | VLOGPT-22, premise unclear, needs human |
| `fixed_weight_ct.v` | `common/fixed_weight/` | untried |
| `fixed_weight_cww.v` | `common/fixed_weight/` | untried |
| `keygen.v` | `keygen/` | untried, 9 instances |
| `encap.v` | `encap/` | untried, 9 instances |
| `encrypt.v` | `encap/` | untried, 27 instances |
| `encrypt_parallel.v` | `encap/` | untried, 24 instances |
| `decap.v` | `decap/` | untried, 26 instances |

**The structural problem to solve first.** Stage 2 asks "is the file now
clean?" when it should ask "are the symbols I moved now clean?". A correct
partial fix gets reverted because a different, untouched defect still exists.
Multi-instance files cannot converge until this changes. The fix is to check
only the moved symbols and let the round loop handle the rest, at the cost of
accepting a file that still fails to elaborate until the last round.

Opus was tried on `fixed_weight.v` and did not solve it either; output varied
run to run. Model is recorded in `usage.model` from now on.

### FPGA neutrality NOT yet verified

The three accepted fixes edited `hardware/` and propagated to all four `build/`
directories, **which is what Vivado synthesizes for the FPGA results.** KAT
proves behavioral identity and the sorted diff proves textual identity, but
**nobody has re-measured Fmax on the FPGA side.**

Expected to be neutral, since declaration order should not affect synthesis.
But "should" is not evidence, and a shifted number would be a reproducibility
problem for results already reported in the abstract.

Do this once, after all port fixes are in, not per file. Re-run
`fmax_search.py` on a block using the fixed files and compare against the
committed baseline. If unchanged, state it as a verified claim in the findings.

### Defect survey may need re-deriving

`docs/findings/asic/2026-07-31_defect_survey.md` claims **13 of 59 files, 102
instances**, confirmed by Genus and by an independent static checker
(`asic/scripts/declcheck.py`).

That sweep ran **without** `hdl_search_path` set. Adding it changed results on
`vect_set_random.v`. The VLOGPT-22 errors survived the change, so the headline
may hold, but **it has not been re-derived under the corrected probe
configuration** and it is currently committed as a finding.

### A revert bug in `run_port_fix.py`

On gate failure it restores `hardware/` and the build copies, but the
`fixed_weight.v` build copies were left modified after a failed run and needed
`git checkout`. Check `git status --short build/` after any failure.

---

## Next steps, priority order

1. Read the encoder results, record as A5 and A6 with search traces, write the
   findings doc.
2. Fix stage 2 to check moved symbols only, then finish the 9 HQC files.
3. `fixed_weight.v` by hand (3 moves, same three gates).
4. Verify FPGA neutrality of the port fixes.
5. Re-derive the defect survey under the corrected probe.
6. Test the backend abstraction end to end.
7. Investigate the VLOGPT-22 phantom duplicate on `vect_set_random.v`.
8. Related Work and Methodology drafting. **This has a real deadline and does
   not depend on any remaining measurement.**

**Deferred:** Innovus place-and-route, full-chip ML-DSA, Xcelium ASIC gate,
repository reorganization.

---

## RESULTS OF RECORD (ASIC), unchanged today

GPDK045 SVT slow, 0.9 V / 125 C, pre-layout, zero wire load.

| # | Design | Config | Effort | Min period | Fmax | Log |
|---|---|---|---|---|---|---|
| A1 | `poly_mult` HQC-128 | baseline, mem blackboxed | high | 1.281 ns | 780.49 MHz | `asic/results/fmax_poly_mult.log` |
| A2 | `poly_mult` HQC-128 | baseline, mem blackboxed | medium | 1.438 ns | 695.65 MHz | `asic/results/fmax_poly_mult_medium.log` |
| A3 | `v_minus_uy` HQC-128 | baseline | high | 0.711 ns | 1406.59 MHz | `asic/results/fmax_vmu_baseline.log` |
| A4 | `v_minus_uy` HQC-128 | optimized | high | 0.746 ns | 1340.31 MHz | `asic/results/fmax_vmu_optimized.log` |

A1 vs A2 is a **control** (effort sensitivity, F3), not a result.
A4 vs A3 is **-4.7%**, inside the effort noise floor, so **not** a regression
claim (F6).

## FPGA reference numbers, established, do not re-derive

- ML-DSA optimized 82.7 MHz vs baseline 70.2 MHz, +17.8%, reproduced twice
- ML-DSA encoder banked ACC+FIFO: chip post-route 73.4 -> 78.6 MHz, +12.0% vs
  baseline (commit `dca29bc`)
- HQC optimized 116.0 MHz vs baseline 114.8 MHz, +1.9% post-route
- 59 gated proposals, 33 applied, 14 functionally incorrect. Reconciled: 65
  records across four logs less 6 terminators. Script in
  `docs/findings/FINDINGS_gate_catch_rate.md` reproduces 59/33/14 exactly.

## D&T constraints

5,000 words including references and bios. Each figure or table counts ~200
words. **Max 12 references.** Title max 9 words. At least 15% tutorial content.
Over-length submissions are auto-rejected. Lloyd owns Related Work and
Methodology/Design; Deshpande takes Intro/Background; Evaluation is joint.
Due August 15.
