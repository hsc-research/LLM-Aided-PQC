# ASIC Findings Addendum: v_minus_uy Arm Comparison

Date: 2026-07-31
Branch: `asic-genus-port`
Appends to `docs/findings/asic/2026-07-30_genus_asic_port.md`

---

## Results of Record (additions)

| # | Design | Config | Effort | Min period | Fmax | Log | Date |
|---|---|---|---|---|---|---|---|
| A3 | `v_minus_uy` HQC-128 | **baseline** | high | 0.711 ns | 1406.59 MHz | `asic/results/fmax_vmu_baseline.log` | 2026-07-31 |
| A4 | `v_minus_uy` HQC-128 | **optimized** (flag_precompute) | high | 0.746 ns | 1340.31 MHz | `asic/results/fmax_vmu_optimized.log` | 2026-07-31 |

Corner: GPDK045 SVT, `slow_vdd1v0_basicCells.lib`, PVT 0.9 V / 125 C,
pre-layout, zero wire load, no blackboxes (module instantiates no memory).

**A4 vs A3 delta: -4.7% Fmax (optimized slower).**

Arms differ only by the `flag_precompute` edit recorded in
`agent/hqc/transfer_log.jsonl` (verdict `ACCEPTED`, 2026-07-12). Verified by
diff: the only differing lines are the two `_oob` register declarations, their
two assignments, and the two rewritten `assign uv_in_*` statements. Both arms
carry identical portability fixes (F4, F5).

---

## Finding F6: the accepted FPGA edit does not transfer to ASIC at block level

**Observed.** The `flag_precompute` edit that produced a +0.726 ns WNS
improvement on FPGA (`transfer_log.jsonl`, decap, WNS -2.233 -> -1.507)
produces a 4.7% Fmax *reduction* at the ASIC block level.

**Why this is not a regression claim.** The delta is smaller than the known
tooling sensitivity: effort setting alone moves Fmax by 10.9% on this flow
(F3). A 4.7% difference does not clear that bar and must not be reported as
evidence that the optimization hurts.

**Mechanism.** The measured critical path in both arms runs
`XOR_BASED_ADDER_state_reg[1]/CK` -> `XOR_BASED_ADDER_in_addr_reg[8]/D`,
entirely inside the `xor_based_adder` submodule. The `flag_precompute` edit
touches the `uv_in_0` / `uv_in_1` comparator logic, which is not on that path.
The edit was therefore never positioned to improve this measurement.

**Constraint-dependent crossover.** The arms invert depending on how tight the
constraint is:

| Period | A3 baseline slack | A4 optimized slack | Better arm |
|---|---|---|---|
| 5.000 ns | 3496 ps | 3707 ps | optimized |
| 2.750 ns | 1246 ps | 1457 ps | optimized |
| 1.625 ns | 202 ps | 337 ps | optimized |
| 1.062 ns | 58 ps | 3 ps | baseline |
| 0.781 ns | 14 ps | 2 ps | baseline |
| 0.711 ns | 0 ps (MET) | -3 ps (VIOLATED) | baseline |

The optimized arm is consistently better under loose constraints and worse at
the floor. Under loose constraints the comparator is on the reported path and
the precompute helps; as the constraint tightens, synthesis restructures and
the adder's internal path becomes binding, at which point the extra registers
and update logic are pure cost.

**Implication.** This is the ASIC analogue of the established FPGA rule that
block-level acceptance does not predict chip-level outcome. It also shows that
"which arm is faster" is not a property of the edit alone; it is a property of
the edit and the constraint together. Reporting a single Fmax per arm hides
this. Search traces should be published, not just endpoints.

**Status:** measured, single module, single security level. Not generalized.

---

## Finding F4: use-before-declaration, second instance

`v_minus_uy.v` had five symbols (`xor_add_addr`, `xor_add_en`,
`xor_add_out`, `xor_add_out_addr`, `xor_add_out_valid`) declared at lines
233-238 and first used at line 145. Same defect class as F1 in `poly_mult.v`.

Fix: hoisted the six-line declaration block above first use. Verified pure
reordering by `LC_ALL=C sort` diff. KAT PASS at HQC-128/192/256.

**Two of two modules examined carry this defect.** This appears systemic in the
codebase rather than incidental, and is worth quantifying across all RTL and
reporting upstream.

## Finding F5: duplicate declaration

`v_minus_uy.v` declared `wire [RAMWIDTH-1:0] pm_out;` twice (lines 136 and
225), differing only in leading whitespace. Genus rejects with `VLOGPT-22`;
Vivado accepts silently. Pre-existing defect, present in the initial import.

Fix: removed the line-225 duplicate. KAT PASS at HQC-128/192/256.

### Emerging defect taxonomy

| Code | Defect | Fix template | Seen in |
|---|---|---|---|
| `VLOGPT-20` | Use before declaration | Hoist declaration above first use | `poly_mult`, `v_minus_uy` |
| `VLOGPT-22` | Duplicate declaration | Remove the redundant one | `v_minus_uy` |
| `VLOGPT-117` | Macro expansion in port range | (cascade artifact so far, no true instance) | - |
| `VLOGPT-37` | `initial` block / reg initial value | Ignored by Genus; verify reset covers the signal | `poly_mult`, `mem_dual` |
| `VLOGPT-506` | `ram_style` attribute | Discarded; drives the blackbox decision | `mem_dual` |

**Diagnostic rule.** Genus aborts on the first error cluster and everything
after it is cascade noise. Always resolve the first error in the log
(`grep -n -m 1 -B 8 "Error"`) and re-run before interpreting anything else.
Two diagnostic cycles were lost to violating this.

---

## Finding F7: optimized RTL lives only in regenerable directories

**Observed.** `hardware/decap/v_minus_uy.v` contains the baseline. The
optimized version exists only in `build/decap/v_minus_uy.v` and
`build/joint_design/v_minus_uy.v`. `git log -- hardware/` shows only two
commits: the initial import and a portability fix. No agent-applied
optimization has ever been committed to the authoritative source tree.

**Why this is dangerous.** `build/` is generated by `make build_decap`, which
copies from `hardware/`. Running that target silently reverts every accepted
optimization. The joint-composition regression previously diagnosed
(glob overwrote per-block wins) is the same failure class.

**Current mitigation.** The optimized variants are committed in `build/`, so
they are recoverable from git history even if overwritten on disk. The commit
`12d930d` is the authoritative record of the `flag_precompute` edit, along
with the exact old/new text stored in `agent/hqc/transfer_log.jsonl`.

**Required fix (not yet done).** Either move optimized variants into tracked
source (`rtl/hqc/optimized/`), or store them as patches applied by the build,
so that no `make` invocation can destroy a result.

**Rule effective immediately.** Before quoting any optimization result, verify
that the file synthesized is the file intended, and record the commit hash
alongside the number. A gate can pass on files that were never edited.

---

## Resolved: log reconciliation

The README's 59 gated proposals figure is **correct and reproducible**.
Source of record: `docs/findings/FINDINGS_gate_catch_rate.md`.

| Log | Records |
|---|---|
| `agent/flight_log.jsonl` | 7 |
| `agent/hqc/transfer_log.jsonl` | 15 |
| `agent/mldsa/orchestrator_log.jsonl` | 21 |
| `agent/mldsa/latency_log.jsonl` | 22 |
| Total | 65 |
| Less 6 terminator records (post-verdict, not separate proposals) | **59** |

Excluded by design: `chip_orchestrator_log.jsonl` (5, closure/dispatch) and
`flow_sweep_log.jsonl` (29, directive search). Both record measurement, not
edit attempts. The two `flight_2026*.log` files are human-readable transcripts
containing 1 verdict each, already counted in `flight_log.jsonl`.

A prior draft of this document flagged a 59-vs-48 discrepancy. That was an
error in the recount: `latency_log.jsonl` was omitted. No action needed.

## Next steps

1. Reconcile the proposal count against all six log files.
2. Run the arm comparison on a module where the agent's edit is actually on
   the binding path. F6 shows `v_minus_uy` was not such a case.
3. Chip-level ASIC arm comparison on `hqc_kem_joint_design`, which is where
   the FPGA +1.9% was measured. Expect many more portability defects at that
   scale.
4. Repository reorganization: consolidate logs, gitignore `build/`, move
   optimized RTL into tracked source. Requires its own session and a KAT run
   to verify nothing broke.

**Deferred:** Innovus place-and-route, ML-DSA ASIC retarget, Xcelium ASIC gate.
