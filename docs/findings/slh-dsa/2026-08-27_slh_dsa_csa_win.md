> **PARTIALLY SUPERSEDED 2026-08-29** by
> `docs/findings/slh-dsa/2026-08-29_slh_dsa_level_sweep.md`. S1 to S11
> remain valid measurements. They are no longer the SLH-DSA figures of
> record: 128f was re-measured under the sweep harness at a different
> bracket, and a second accepted edit now covers SHA-512.

# FINDINGS: SLH-DSA first agent win, rule book extended by the agent

Date: 2026-08-27
Status: **CURRENT.**

**Supersedes:** the "what does not exist yet" section of
`docs/findings/slh-dsa/2026-08-25_slh_dsa_bringup.md`, which recorded a
baseline-only measurement with no optimized arm. The baseline figures in that
document (S1 below) remain valid and are re-stated here. That document gets a
banner pointing here.

Commits: `1223184`, `24108e2`, and the iso-frequency logs commit.

---

## Summary

The ML-DSA POLICY, transferred verbatim, returned `no_action` on SLH-DSA. The
agent then proposed a new candidate rule from the RTL and the path structure,
applied it, passed the functional gate, and improved chip closure by 14.3
percent at slightly reduced area.

This is the first time the rule book grew from a design rather than only being
applied to one.

---

## RESULTS OF RECORD

Configuration for every row: SPHINCSLET `top`, `PARAM_128F`, SHA-2
(`SHAKE` undefined), Artix-7 `xc7a200tfbg676-1` speed grade -1,
`-mode out_of_context`, post-route, recipe ExtraTimingOpt / Explore / Explore
fixed in `fmax_search.py`. Constraints: `slh.xdc`, false paths on `rstn`,
`i_FSM_start`, `i_msg_in_size*`. `HD.CLK_SRC` unset (same as M1/M2 and the HQC
pair, so the three designs are comparable on this point). Memories inferred,
not blackboxed. Signature memory is external to `top` and excluded.

### Closure pair

| # | Arm | Closing period | Fmax | WNS | Log |
|---|---|---|---|---|---|
| S1 | baseline (pristine SPHINCSLET) | 11.98 ns | 83.5 MHz | +0.180 | `logs/closure/slh_128f_sha2_20260825/fsrch_slh_128f_sha2_11.98.rpt` |
| S2 | optimized (CSA on `t1_logic`) | 10.48 ns | 95.4 MHz | +0.065 | `logs/closure/slh_csa_20260825/fsrch_chipv2_slh_dsa_16598_10.48.rpt` |

**S2 vs S1: +14.3 percent Fmax.**

**Both are upper bounds, not proven minima.** Each is a five-iteration binary
search terminated on iteration count, not convergence. No wide-bracket
verification has been run. The delta between two upper bounds measured under
one recipe is the defensible claim; neither absolute value is a proven minimum.

### Iso-frequency pair, both arms at 11.98 ns

Placed and routed at the baseline closing period so area is attributed to the
edit rather than to constraint pressure.

| # | Metric | Baseline | Optimized | Delta | Log |
|---|---|---|---|---|---|
| S3 | WNS | +0.180 | +0.383 | +0.203 ns | `logs/closure/slh_iso_20260827/slh_iso_base.rpt`, `slh_iso_11.98.rpt` |
| S4 | Slice LUT | 8,130 | 8,027 | **-1.3 pct** | `.../slh_iso_base.util`, `.../slh_iso_11.98.util` |
| S5 | LUT as Logic | 8,042 | 7,939 | -103 | as S4 |
| S6 | LUT as Memory | 88 | 88 | 0 | as S4 |
| S7 | Slice Registers | 6,793 | 6,791 | -2 | as S4 |
| S8 | Block RAM Tile | 6 | 6 | 0 | as S4 |
| S9 | DSP | 0 | 0 | 0 | as S4 |
| S10 | Total on-chip power | 0.222 W | 0.224 W | see note | `.../slh_iso_base.pwr`, `.../slh_iso_11.98.pwr` |

**S10 is vectorless and must not be quoted as a power result.** No SAIF or VCD,
default switching activity, OOC excludes I/O. The 2 mW difference is inside
estimation noise. The defensible statement is that power is unchanged, not that
it rose 0.9 percent. This follows the retirement of vectorless power in
`mldsa/postroute_ppa`.

**S3 control.** The baseline reproduced WNS +0.180 at 11.98 ns in the
standalone iso flow, matching its `fmax_search.py` closure measurement exactly.
The two flows therefore agree and S1 through S10 are mutually comparable.

### Determinism control

| # | Observation | Log |
|---|---|---|
| S11 | All five baseline search iterations bit-identical across two runs from independently regenerated checkpoints built from different source tree locations | `logs/closure/slh_128f_sha2_20260825/`, `chip_orchestrator_log.jsonl` |

11.5 -> -0.239, 12.25 -> +0.171, 11.88 -> -0.018, 12.07 -> +0.100,
11.98 -> +0.180, reproduced exactly. Extends the ML-DSA synthesis determinism
result to a full regen-plus-place-and-route cycle on a third design.

### What does not exist yet

- **No wide-bracket verification** of either closing period.
- **No ASIC arm.** Cadence license server has been down since approximately
  2026-08-18, so no Genus run of any kind.
- **Single configuration.** 128f SHA-2 only. Five other parameter sets and the
  entire SHAKE256 family are untouched.
- **No absolute correctness proof.** The gate is differential: the golden
  signature was produced by unmodified SPHINCSLET RTL. It proves the edit
  changed nothing observable, not that the design is correct.
- **No constant-time verification.** The framework figure draws this as a
  mandatory gate. It does not exist in any orchestrator.
- **Area and power not measured at S2's own closing period** beyond the
  utilization already in the closure logs.

---

## F46. The rule book declined correctly, then extended itself

**Observed.** The ML-DSA POLICY was transferred verbatim, including its
ML-DSA-specific FORBIDDEN entries (`coeff_decomposer`, unpipelined DSP), so
that any rule failing to fire would fail on its own stated conditions rather
than because the menu had been rewritten to fit a new design.

It returned `no_action` twice, on `sha256_core` and on `FSM`, rejecting all
five strategies against their stated preconditions:

| Strategy | Precondition | Why unmet on SLH-DSA |
|---|---|---|
| `max_fanout_16` | route >= ~70 pct | 53.9 pct |
| `constant_lut` | domain <= 8 bits | 32 bits |
| `sign_select` | sign-extract idiom | absent |
| `shifter_mux_reduce` | proven closed shift set | absent |
| `flag_precompute` | flag-computable pre-register expression | carry chain not so driven |

**Verified** by re-running with the classifier's steering note removed. The
first run included a note telling the model that no menu entry applied; the
second did not, and the model still walked all five and rejected each on
structural facts. The second run is the one that carries evidential weight.

**Not a coverage gap in the menu alone.** The top-10 post-route board shows all
ten paths inside SHA-256 across two instances:

| Cone | Paths | Slack | Structure |
|---|---|---|---|
| `hash_tile_md0/HASH_BM/SHA256` | 8 | +0.180 | 16 levels, CARRY4=8 |
| `hash_tile_md0/HASH_SM/SHA256` | 2 | +0.315 | 19 levels, CARRY4=9 |

No FSM cone appears. The five strategies had zero applicable targets anywhere
in SLH-DSA's timing-critical logic, so the decline was structurally correct and
not a failure of judgement.

**Implication.** A rule set derived from lattice and code-based arithmetic
declines cleanly outside its domain rather than fabricating an edit. That is a
stronger transfer result than a marginal win would have been.

## F47. Carry-save reduction beats the dedicated carry chain on Artix-7

**Observed.** Given that the menu had nothing, the agent proposed one candidate
rule from the RTL and the path structure:

> `carry_chain_csa_reduction`: when a deep carry-chain path (>=12 levels,
> CARRY4 >= 6) implements a multi-operand addition (>=3 addends) in a single
> carry-ripple tree, replace it with a carry-save adder tree that reduces to
> two operands before the final carry-propagate add, keeping all register
> boundaries identical.

Applied to `sha256_core.v` `t1_logic`, where five operands
(`h_reg + sum1 + ch + w_data + k_data`) were summed in one chain. The edit
introduces three 3:2 compressor stages and a single two-operand final add.
Latency-neutral: one combinational `always @*` block before and after, no
register boundary moved.

**Verified.** Gate PASS, produced signature bit-identical to the golden
reference. Closure S1 -> S2. Iso-frequency S3 through S10.

**Mechanism.** The binding path moved from `HASH_BM/SHA256` to
`HASH_SM/SHA256`, which was the second cone on the pre-edit board at +0.315.
The edit removed the first cone as the limiter and the second now binds. This
is the same signature as the HQC accepted edit, where the binding path moved
from `V_MINUS_UY` to the shared Keccak state RAM.

**Prediction was wrong, recorded as such.** The expectation stated before the
run was that CSA would lose on Artix-7, because CARRY4 is dedicated silicon at
roughly 40 ps per 4 bits while a LUT-based compressor tree pays full LUT and
routing delay per level. The measurement contradicted this. The likely
mechanism is that the CSA form exposes independent XOR and majority terms that
Vivado packs into existing LUT6 resources, so the tree costs almost no
additional logic (S5: 103 LUTs fewer at matched frequency) while the carry
chain shortens.

**Scope limit.** The target file `sha256_core.v` is borrowed Secworks SHA-256
code, not SPHINCSLET-authored. The result is that the agent optimized
third-party IP shipped inside a published accelerator.

## F48. The proposal loop needs explicit unvalidated framing

**Observed.** On first injection of the candidate rule, the model described it
in its verdict as "the validated [slh_dsa] rule." It had been proposed minutes
earlier and had zero supporting measurements. The `rules_prompt_block()` header
describes learned rules as evidence-backed, which is true for distilled rules
and false for unresolved candidates.

**What was done.** The injection block was hardened to state that candidates
are untested hypotheses with zero supporting measurements, that they are not
validated or evidence-backed, and that the model must never describe them as
validated.

**Verified.** The subsequent run's verdict no longer made the claim.

**Implication.** Any mechanism that surfaces proposals alongside validated
rules must carry status in the text the model reads, not only in the record
structure. A status field in JSON is invisible to the reasoning that uses it.

---

## Rule ledger

`agent/learned_rules.jsonl`, append-only, resolution recorded in both
directions.

| rule_id | Status | Evidence |
|---|---|---|
| `carry_chain_csa_reduction` | **validated** | S1 -> S2, gate PASS, S3-S10 |

Cost: 3 Sonnet calls for the decline, the proposal, and the applied edit.
Token usage recorded per call in `agent/slh_dsa/slh_orchestrator_log.jsonl`.

---

## File map

| What | Where | Committed |
|---|---|---|
| Closure logs, baseline | `logs/closure/slh_128f_sha2_20260825/` | yes |
| Closure logs, optimized | `logs/closure/slh_csa_20260825/` | yes |
| Iso-frequency logs, both arms | `logs/closure/slh_iso_20260827/` | yes |
| Pristine RTL plus sha256 manifest | `agent/slh_dsa/pristine/`, `pristine_rtl.sha256` | yes |
| Tracked RTL the agent edits | `agent/slh_dsa/slh_src/` | yes |
| Functional gate and golden signature | `agent/slh_dsa/gate/`, `slh_kat_gate.py` | yes |
| Block orchestrator | `agent/slh_dsa/slh_orchestrator.py` | yes |
| Top-N board extractor and board | `agent/slh_dsa/path_board.py`, `path_board.json` | yes |
| Checkpoint regen | `agent/slh_dsa/regen_slh_ckpt.py` | yes |
| Rule ledger | `agent/learned_rules.jsonl` | yes |
| Post-synth checkpoints | `/mnt/c/PQC/slh_test/*.dcp` | NO, size |
| Simulation working tree | `/mnt/c/PQC/slh_sim/` | NO, regenerable |

---

## Next steps

1. Wide-bracket verification of S1 and S2. Both are search upper bounds.
2. Re-run the agent on the new binding cone (`HASH_SM/SHA256`). It is the same
   `sha256_core.v` and the CSA edit is already applied to both instances, so a
   second win there needs a different rule.
3. Extend to the other five parameter sets and the SHAKE256 family.
4. Constant-time verification. Claimed in the framework figure and in the paper
   text, implemented nowhere.
5. ASIC arm, blocked on the Cadence license server.

## Open questions for the advisor

1. Does SLH-DSA go into the D&T paper as a third scheme, given it is
   Dr. Deshpande's own RTL?
2. Is a differential gate sufficient, or should external KAT vectors be
   obtained to make it absolute?
3. The win is in borrowed Secworks SHA-256 code rather than SPHINCSLET-authored
   RTL. Does that need framing in the paper, and how?
