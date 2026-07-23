# FINDINGS: POLICY v2 rendezvous rubric — insertion-point selection, measured

**Verdict: rule encoding moves structural judgment (0/12 to 4/4); mechanical
execution is a separate and still-open failure mode.**

This document defines the criterion behind the "0/12 to 4/4" claim and points
at the log records that support it. It exists because the claim was previously
carried only as console observation.

## The criterion

Two independent things are scored, and they must not be conflated:

1. **Insertion-point selection (structural judgment).** Does the proposal's
   `design` field specify a pipeline cut on the OUTPUT side of the DSP
   multiplier (after `mult_p`, before `barrett_datai`), rather than on the
   INPUT side (registering `multa`/`multb`)? Input-side registration desyncs
   the mode mux and the `adda`/`suba` rendezvous inside `butterfly`, and is
   not repairable by consumer retapping — it is a structural error, not a
   tuning error.

2. **Edit outcome (mechanical execution).** Did the emitted str-replace pairs
   apply at unique anchors, and did the resulting netlist pass the full-KAT
   outer gate?

A proposal can be correct on (1) and still fail on (2). Every post-rule
proposal did exactly that. "Workable" in earlier informal notes meant (1)
only; that ambiguity is what this document removes.

## Pre-rule baseline: 0/12

From `FINDINGS_mldsa_latency_orchestrator_v0.md`: Sonnet (claude-sonnet-4-6),
3 runs / ~12 calls, 0 wins. Divergence-guided repair demonstrably steered tap
derivation — the model learned the chained-stage rule (FNTT/INTT +2, MULT +1,
ADD/SUB +0) across feedback rounds, and one attempt moved first divergence
from transaction #64 to #3328. But every attempt chose the same input-side
insertion point. Opus (claude-opus-4-8), 1 call, $0.245: `no_action` with the
correct structural reason, matching human analysis.

Conclusion recorded at the time: divergence-guided repair works for TAP
DERIVATION but not for INSERTION-POINT SELECTION.

## The rule

The POLICY v2 rendezvous rubric (commit `ff67ba0`) encodes the output-side
constraint directly in the orchestrator POLICY block. Commit order confirms
the separation: `ff67ba0` predates all records below.

## Post-rule: 4/4 on criterion (1), 0/4 on criterion (2)

Source: `agent/mldsa/latency_log.jsonl`, records at and after
`2026-07-12T00:04`. Four records carry a `design` field; all four specify
output-side insertion. The two `retries_exhausted` records at `00:05:34` and
`00:08:05` carry no `design` field — they are run terminators, not proposals,
and are correctly excluded from the denominator.

| ts | verdict | insertion point in `design` | failure mode |
|---|---|---|---|
| 2026-07-12T00:04:39 | apply_fail | `mult_p2` after `mult_p`, Barrett input delayed | anchor count 2 (`butterfly2x2.v` edit3) |
| 2026-07-12T00:05:04 | apply_fail | after `mult_p`, "output side of DSP multiplier", between `mult_p` and `barrett_datai` | anchor count 2 (`butterfly2x2.v` edit3) |
| 2026-07-12T00:05:34 | apply_fail | after `mult_p`, "output side of DSP multiplier", `mult_p2` between `mult_p` and `barrett_datai` | anchor count 0 (`butterfly.v` edit1) |
| 2026-07-12T00:08:05 | gate_fail | `mult_p2` after `mult_p`, Barrett input delayed | full-KAT divergence, localized by latency-agnostic bisect |

The `00:08:05` record additionally states the chained-stage arithmetic
correctly and unprompted: +2 for NTT modes (butterfly2x2 chains two stages),
+1 for MULT_MODE, +0 for ADD/SUB (multiplier bypassed). That is the round-2
rule being applied, not restated from feedback.

## What this shows

Encoding a structural rule as policy text moved a mid-tier model from 0/12 to
4/4 on insertion-point selection — the judgment that divergence-guided
iteration could not teach. Structural judgment is rule-transferable.

## What this does NOT show

No win. All four post-rule edits failed downstream: three on anchor mechanics
(non-unique or absent anchors), one at the correctness gate. The rule closed
the structural gap and left the mechanical one open. `butterfly` remains
CLOSED for pipelining on the separate ground that the residual path is
DSP-mux-bound (see `FINDINGS_mldsa_latency_orchestrator_v0.md`).

The 3 anchor failures are an orchestrator limitation (no anchor-uniqueness
pre-check before emission), not a model limitation, and are the obvious next
infrastructure fix.

## Reproduction

```bash
python3 -c "
import json
for l in open('agent/mldsa/latency_log.jsonl'):
    r = json.loads(l)
    if r.get('ts','') >= '2026-07-12T00:04' and r.get('design'):
        print(r['ts'], r['verdict'], '|', r['design'][:120])
"
```

Expect four records, all output-side.
