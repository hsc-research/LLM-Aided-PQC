# FINDINGS: autonomous latency-tier orchestrator v0 — butterfly round-3

**Verdict: block CLOSED for pipelining; orchestrator validated as loop, no win.**
Post round-2 baseline: WNS -2.793, critical path modei→DSP PCIN (2 levels, 73% logic)
— the DSP input-select mux, at or near the DSP intrinsic floor.

## What was built
agent/mldsa/orchestrator_latency.py: autonomous latency-changing tier.
Loop: full-KAT pre-check → path extraction → LLM proposes multi-file pipeline
edit set (JSON, per-file anchored str-replace) → atomic apply → full-KAT (600s
timeout) → on FAIL: automatic latency-agnostic stream bisection, first divergent
transaction fed back to the model → bounded retries → on PASS: synth + accept
threshold (0.05ns) → git-reset on all failure paths. Cost tracking per API call
(tokens + USD) logged to latency_log.jsonl; live dashboard (agent/dashboard.py)
shows status, verdicts, and running spend.

## Results
- Sonnet (claude-sonnet-4-6), 3 runs / ~12 calls: 0 wins. Divergence-guided
  repair demonstrably steered tap derivation: the model learned the chained-stage
  rule (FNTT/INTT +2, MULT +1, ADD/SUB +0) across feedback rounds, and one
  attempt moved first divergence from transaction #64 to #3328 (all NTT modes
  correct, ADD retap was the remaining error, fixed by policy rule 7). But every
  attempt chose the same unworkable insertion point: registering the multiplier
  INPUTS (multa/multb), which desyncs the mode mux and adda/suba rendezvous
  inside butterfly — not repairable by consumer retapping.
- Opus (claude-opus-4-8), 1 run / 1 call / $0.245: no_action, with the correct
  structural reason — registering the DSP operand desyncs the index-matched
  additive delay lines. Same conclusion as human analysis, reached in one call
  vs Sonnet's repeated attempts.

## Bugs found and fixed in the loop itself
1. JSON truncation crash → retry-with-error-feedback + max_tokens 8000.
2. Sim hang on broken done-handshake edits burned 15+ min → 600s gate timeout,
   timeout counts as gate_fail with per-vector progress recorded.
3. Silent apply failures consumed retries invisibly → apply_fail now printed,
   logged, and git-reset before retry.
4. (Process) never run manual gates/checkouts on mldsa_src while the
   orchestrator is live — shared tracked files and run log.

## Conclusions
1. Divergence-guided repair works for TAP DERIVATION (the arithmetic of
   retiming) but not for INSERTION-POINT SELECTION (the structural judgment);
   Sonnet repeatedly proposed input-side registration that output-side analysis
   rules out.
2. Model capability comparison on identical task+prompt: Sonnet 12 calls no
   convergence; Opus 1 call correct refusal ($0.245). Frontier-model judgment
   substitutes for iteration budget.
3. butterfly is CLOSED: human rounds 1-2 banked +1.009ns (-3.802→-2.793,
   113.6→128.3 MHz, +12.9%); remaining path is DSP-mux-bound.
