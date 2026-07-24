# FINDINGS: gate catch rate, measured across every logged edit attempt

**Verdict: 14 of 33 cleanly-applied LLM edits were functionally incorrect.
Stratified by tier the rate is 17% (latency-preserving) versus 100%
(latency-changing).**

This converts the paper's central claim from an anecdote into a measurement.
It uses only data already committed to the flight logs; no new runs.

## Scope

Four logs record RTL edit attempts and are included:

| Log | Tier | Gate |
|---|---|---|
| `agent/flight_log.jsonl` | latency-preserving | HQC block KAT |
| `agent/hqc/transfer_log.jsonl` | latency-preserving | HQC full KAT |
| `agent/mldsa/orchestrator_log.jsonl` | latency-preserving | ML-DSA lockstep equivalence |
| `agent/mldsa/latency_log.jsonl` | latency-changing | ML-DSA 75-vector full KAT + bisect |

Two logs are excluded because they record measurement, not edits:
`agent/chip_orchestrator_log.jsonl` (closure search and dispatch, 5 records)
and `agent/flow_sweep_log.jsonl` (directive search, 29 records).

`retries_exhausted` records are excluded from the denominator: they are run
terminators emitted after a proposal already logged its own verdict, not
separate proposals. There are 6, all in `latency_log`.

## Verdict semantics

Order of operations in `orchestrator.py` (identical in
`transfer_orchestrator.py`): apply under `assert count==1`, then gate
(line 264), then synthesis (line 270), then gain threshold (line 293).

Therefore:

- `apply_fail` — anchors non-unique or absent; **nothing was applied**
- `refused` — harness pre-check rejected the proposal; nothing applied
- `kat_fail` / `gate_fail` — applied cleanly, **failed correctness**
- `synth_fail` — applied, correct, failed synthesis
- `marginal_*` — applied, **passed correctness**, gain below 0.05 ns
- `ACCEPTED` — applied, passed correctness, gain at or above 0.05 ns

The load-bearing point is that `marginal_*` means the gate passed. A marginal
edit is a correct edit that was not worth keeping.

## Funnel

| Stage | N |
|---|---|
| LLM calls | 59 |
| Model declined (`no_action`) | 19 |
| Harness pre-check refused | 1 |
| Failed to apply (anchor mechanics) | 5 |
| Infrastructure bug (`superseded_float_bug`) | 1 |
| **Applied at unique anchors, reached the gate** | **33** |
| Failed the correctness gate | **14** |
| Failed synthesis | 1 |
| Correct and synthesizable | 18 |
| Accepted (gain at or above threshold) | 4 |

## The stratified result

| Tier | Applied | Gate failures | Rate |
|---|---|---|---|
| Latency-preserving | 23 | 4 | **17%** |
| Latency-changing | 10 | 10 | **100%** |

Every latency-changing edit the agent produced was functionally incorrect.
This holds even after the POLICY v2 rendezvous rubric moved insertion-point
selection from 0/12 to 4/4 (see
`FINDINGS_mldsa_policy_v2_insertion_point.md`): correct structural judgment
did not prevent a single one of those edits from being broken. Retiming a
multi-consumer datapath requires tracking consequences across files, and that
is a distinct and unsolved capability.

## What this does and does not license

**Supported.** Fourteen edits applied at unique anchors, were syntactically
valid Verilog, and were functionally wrong. A harness validating by
compilation or by testbench sampling would have admitted all fourteen into
the design.

**Not supported.** No claim that those fourteen would otherwise have been
*accepted as wins*. The gate runs before synthesis, so their timing was never
measured. The claim is about admission into the design, not about reported
improvement.

**Not supported.** No claim about a general LLM error rate. This is one
harness, two designs, one model family, and the proposals were shaped by a
constrained strategy menu and by accumulated priors.

## Yield, stated plainly

4 accepted from 33 applied is a 12% yield. The argument is not that the agent
is efficient. It is that a 12% yield is safe to run unattended precisely
because the gate is bidirectional and corruption-validated: the 14 incorrect
edits and the 14 correct-but-marginal edits were separated by measurement, not
by inspection.

## Reproduction

```bash
python3 - << 'EOF'
import json, collections
LOGS = {
    "agent/flight_log.jsonl":              "preserving",
    "agent/hqc/transfer_log.jsonl":        "preserving",
    "agent/mldsa/orchestrator_log.jsonl":  "preserving",
    "agent/mldsa/latency_log.jsonl":       "changing",
}
GATEFAIL = ("kat_fail", "gate_fail")
def applied(v):
    return v.startswith("marginal") or v in ("ACCEPTED", "synth_fail") or v in GATEFAIL

tier = collections.Counter()
total = collections.Counter()
for path, t in LOGS.items():
    for line in open(path):
        v = json.loads(line).get("verdict", "")
        if v == "retries_exhausted":
            continue
        total["calls"] += 1
        total[v.split("_")[0] if v.startswith("marginal") else v] += 1
        if applied(v):
            total["applied"] += 1
            tier[t + " applied"] += 1
            if v in GATEFAIL:
                total["gate_fail_total"] += 1
                tier[t + " gate_fail"] += 1
print("TOTALS:", dict(total))
print("BY TIER:", dict(tier))
EOF
```

Expect 59 calls, 33 applied, 14 gate failures; preserving 4/23, changing 10/10.
