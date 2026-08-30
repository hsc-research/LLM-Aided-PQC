# FINDINGS: SLH-DSA security-level sweep and the SHA-512 rule application

Date: 2026-08-29
Status: **CURRENT.**

**Supersedes:** the single-configuration framing of
`docs/findings/slh-dsa/2026-08-27_slh_dsa_csa_win.md`. S1 and S2 in that
document remain valid as measurements but are no longer the SLH-DSA figures of
record, because the 128f closure was re-measured under the sweep harness at a
different bracket and because the design now carries a second accepted edit.
That document gets a banner pointing here.

Commit: `d7041a4`.

---

## Summary

The carry-save rule the agent proposed and validated at 32 bit on
`sha256_core` was applied without modification to the structurally identical
64 bit adder in `sha512_core`, which binds at the 192 and 256 parameter sets.
Every one of the six SLH-DSA parameter sets now improves, from 4.4 to 20.4
percent.

Two sweeps establish the attribution. Sweep 1 carried the SHA-256 edit only.
Sweep 2 added SHA-512. The 192 and 256 configurations are flat in sweep 1 and
gain in sweep 2, which localizes the effect to the edited core rather than to
any incidental change.

---

## RESULTS OF RECORD

Configuration for every row: SPHINCSLET `top`, SHA-2 (`SHAKE` undefined),
Artix-7 `xc7a200tfbg676-1` speed grade -1, `-mode out_of_context`, post-route,
recipe ExtraTimingOpt / Explore / Explore fixed in `fmax_search.py`.
Constraints: false paths on `rstn`, `i_FSM_start`, `i_msg_in_size*`.
`HD.CLK_SRC` unset, matching M1/M2 and the HQC pair. Memories inferred.
Signature memory is external to `top` and excluded.

Each closure is a five-iteration bounded search terminated on iteration count.
**Every value below is an upper bound on the closing period, not a proven
minimum.** Brackets were proven in both directions before each search (F12).

### Closure, all six parameter sets

| # | Config | Baseline | Accepted | Delta | Baseline log |
|---|---|---|---|---|---|
| S12 | 128s | 11.62 ns / 86.1 MHz | 11.12 ns / 89.9 MHz | **+4.4 pct** | `logs/closure/slh_levels_20260829/fsrch_slh_128s_baseline_11.62.rpt` |
| S13 | 128f | 11.62 ns / 86.1 MHz | 10.43 ns / 95.9 MHz | **+11.4 pct** | `.../fsrch_slh_128f_baseline_11.62.rpt` |
| S14 | 192s | 13.00 ns / 76.9 MHz | 10.93 ns / 91.5 MHz | **+19.0 pct** | `.../fsrch_slh_192s_baseline_13.0.rpt` |
| S15 | 192f | 13.00 ns / 76.9 MHz | 10.93 ns / 91.5 MHz | **+19.0 pct** | `.../fsrch_slh_192f_baseline_13.0.rpt` |
| S16 | 256s | 13.00 ns / 76.9 MHz | 11.49 ns / 87.0 MHz | **+13.1 pct** | `.../fsrch_slh_256s_baseline_13.0.rpt` |
| S17 | 256f | 13.25 ns / 75.5 MHz | 11.00 ns / 90.9 MHz | **+20.4 pct** | `.../fsrch_slh_256f_baseline_13.25.rpt` |

The 128 configurations carry the SHA-256 edit only, because SHA-512 is not
instantiated at that security level. The 192 and 256 configurations carry
both.

### Utilization at each arm's closing period

| # | Config | Metric | Baseline | Accepted | Delta |
|---|---|---|---|---|---|
| S18 | 128f | Slice LUT | 8,144 | 8,118 | -0.3 pct |
| S19 | 192f | Slice LUT | 18,601 | 19,046 | +2.4 pct |
| S20 | 256f | Slice LUT | 19,032 | 19,185 | +0.8 pct |
| S21 | 128f | Slice Reg | 6,793 | 6,791 | -2 |
| S22 | 192f | Slice Reg | 15,926 | 15,931 | +5 |
| S23 | 256f | Slice Reg | 16,307 | 16,308 | +1 |
| S24 | all three | BRAM, DSP | unchanged | unchanged | 0 |

BRAM is 6 at 128f and 8 at 192f and 256f. DSP is 0 throughout. Utilization is
read at each arm's own closing period, matching the M1/M2 convention, so part
of the LUT difference is constraint pressure rather than the edit. The
2026-08-27 iso-frequency pair (S3 to S10) isolates the edit at 128f.

### Two-stage attribution

| Config | Baseline | SHA-256 edit only | Both edits |
|---|---|---|---|
| 192s | 76.9 MHz | 75.8 MHz | 91.5 MHz |
| 192f | 76.9 MHz | 76.9 MHz | 91.5 MHz |
| 256s | 76.9 MHz | 76.9 MHz | 87.0 MHz |
| 256f | 75.5 MHz | 90.9 MHz | 90.9 MHz |

Sweep 1 is preserved at
`agent/slh_dsa/level_sweep_results_sha256only.jsonl`; the live results file
contains both sweeps in order.

### Determinism

| # | Observation | Evidence |
|---|---|---|
| S25 | Every baseline reproduced exactly across both sweeps, from independently staged scratch trees | 192s, 192f, 256s at 13.00 ns; 256f at 13.25 ns |
| S26 | 256f reproduced in **both** arms across sweeps: 13.25 and 11.00 ns each time | `level_sweep_results.jsonl` records 12/13 and 20/21 |

S26 is the strongest determinism datapoint in the project: two complete
closure searches on the same configuration, in different sweeps, produced
identical closing periods on both arms.

### What does not exist yet

- **No wide-bracket verification** of any of the twelve closing periods.
- **No ASIC arm.** Cadence license server unreachable since approximately
  2026-08-18.
- **No SHAKE256 arm.** All twelve measurements are the SHA-2 family.
- **No absolute correctness proof.** The gate is differential against a golden
  signature produced by the pristine arm at each configuration.
- **No constant-time static check.** Cycle-schedule invariance only.
- **Two 128f baselines disagree.** The 2026-08-27 standalone run measured
  11.98 ns and the sweep measured 11.62 ns from identical source. The
  brackets differed, (10.0, 13.0) against (10.0, 14.0), so the searches
  sampled different periods. Unresolved.

---

## F49. The rule generalized across operand width without modification

**Observed.** After the SHA-256 edit, the 192 and 256 configurations were
flat: 192s regressed 1.4 percent, 192f and 256s were unchanged. Reading the
binding paths showed why. Those configurations bind on
`DUT_SHA512/HASH_BM/SHA512/w_mem_inst` into `a_reg_reg[61]`, a 64 bit
register, not on SHA-256 at all. `setting.v` defines `HASH2 = "SHA512"` for
`PARAM_192` and `PARAM_256` and leaves it undefined at `PARAM_128`.

`sha512_core.v` contains `t1 = h_reg + sum1 + ch + k_data + w_data`, the same
five-operand sum as `sha256_core.v` at twice the width. The planner, given the
validated rule, matched all four stated preconditions on the 192f cone:
CARRY4 = 17 against a threshold of 6, depth 29 against 12, five addends
against three, and route 47 percent against the 70 percent logic-bound
condition. It applied three 3:2 compressor stages at 64 bit width.

**Verified.** Gate PASS at 192f, signature byte-identical to the golden frozen
from the pristine arm. Closure S14 through S17.

**Implication.** The rule was validated once at 32 bit and then transferred to
a 64 bit instance with no change to the rule text, no change to the
preconditions, and no human authorship of the transformation. This is a
stronger generality claim than the original validation, and it was obtained at
the cost of two model calls.

## F50. An edit can pay on a cone it does not touch

**Observed.** 256f gained 20.4 percent from the SHA-256 edit alone, before
SHA-512 was ever edited, and gained nothing further from the SHA-512 edit. Its
baseline binds on SHA-512 at 13.25 ns. Its accepted arm binds on
`DUT_SHA256/HASH_BM/SHA256` at 11.00 ns.

**Verified.** Both arms converge cleanly. Baseline: 13.0 violated by 100 ps
with 3 failing endpoints, 12.0 violated by 979 ps with 92. Accepted: 11.0 met
at WNS +0.002, 10.75 violated by 463 ps with 37. Both reproduced exactly in a
second sweep (S26).

**Interpretation.** The two hash cores share placement and routing resources
inside `hash_tile`. Shortening the SHA-256 logic relieved congestion enough for
the SHA-512 path to route 2.25 ns faster, after which SHA-256 became the
tighter of the two and bound.

**Implication.** RQ2's framing, that the primary evidence is whether the
edited structure ceases to bind, has an exception. Here the edited structure
was never binding and the design still gained. Chip-level measurement is the
only honest judge in both directions: block wins may fail to compose upward
(ML-DSA), and edits may pay sideways through shared implementation resources.

## F51. Rule status must survive supersession in the prompt text

**Observed.** `carry_chain_csa_reduction` was resolved to `validated` in the
ledger, but `proposed_rules()` returned the last record per `rule_id`, and
`resolve_rule` writes the placeholder `"(resolution record)"` into the `rule`
field. The planner therefore received a validated rule with no rule text,
labelled as an untested hypothesis, and correctly declined to use it. It then
proposed a near-duplicate rule, `csa_multi_addend_reduction`, which was never
applied and has been marked superseded.

**What was done.** Records are now merged per `rule_id`, taking the text from
the proposing record and the status from the latest. The injection block
renders status per rule and cites the measured evidence for validated ones.
`proposed_rules()` also filters `superseded`, not only `refuted`.

**Verified.** The re-run applied the rule and cited its validated status. Cost
of the defect: two wasted model calls and one spurious rule.

**Implication.** This extends F48 in the opposite direction. F48 recorded that
an unvalidated candidate can be presented as validated. F51 records that a
validated rule can silently revert to unvalidated. Status is only load-bearing
if it survives every record transformation between the ledger and the prompt.

---

## Rule ledger

| rule_id | Status | Evidence |
|---|---|---|
| `carry_chain_csa_reduction` | **validated** | 32 bit: S1 to S2 and S3 to S10. 64 bit: S14 to S17 |
| `csa_multi_addend_reduction` | superseded | Never applied, no measurement. See F51 |

SLH-DSA campaign cost across ten calls: median $0.039, maximum $0.063, total
$0.389. The maximum is the `FSM.v` abstention, whose cost is driven by a 47 kB
context rather than by difficulty.

---

## File map

| What | Where | Committed |
|---|---|---|
| Sweep driver | `agent/slh_dsa/level_sweep.py` | yes |
| Sweep results, both sweeps in order | `agent/slh_dsa/level_sweep_results.jsonl` | yes |
| Sweep 1 snapshot, SHA-256 edit only | `agent/slh_dsa/level_sweep_results_sha256only.jsonl` | yes |
| Per-config golden signatures | `agent/slh_dsa/gate/levels/SIG_*.hex` | yes |
| Closure reports, all twelve arms | `logs/closure/slh_levels_20260829/` | yes |
| Tracked RTL carrying both edits | `agent/slh_dsa/slh_src/` | yes |
| Rule ledger | `agent/learned_rules.jsonl` | yes |
| Post-synth checkpoints | `/mnt/c/PQC/slh_test/*.dcp` | NO, size |

---

## Next steps

1. Wide-bracket verification. Twelve closing periods, none verified.
2. Resolve the two 128f baselines, 11.98 against 11.62.
3. `level_sweep.py` regenerates a golden whenever it runs a baseline arm. It
   should refuse to overwrite an existing one.
4. Run the planner on a memory-bound cone to record the abstain verdict inside
   a single design.
5. SHAKE256 family, six further configurations.
6. ASIC arm, blocked on the license server.

## Open questions for the advisor

1. Which SLH-DSA configuration should carry the paper's headline number? 256f
   is the largest gain but its accepted arm closes at WNS +0.002.
2. Does F50 need its own treatment in the paper, or is a sentence in RQ2
   sufficient?
