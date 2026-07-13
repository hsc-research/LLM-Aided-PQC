# Publication Roadmap — what makes this agent distinct

## The claim
Not "an LLM that edits RTL" — a correctness-gated agent with an EVIDENCE-TAGGED
TRANSFORMATION CALCULUS: every strategy in POLICY carries validated
applicability conditions (n= counts, exclusions, and the structural tests that
gate them), accumulated from 30+ gated experiments across two NIST PQC
standards, with every negative documented. The agent's priors are themselves a
research artifact: they encode when each transformation helps, fails, or
inverts, and they were LEARNED from the loop, not assumed.

## Validated calculus (as of 2026-07-11, all in orchestrator POLICY)
1. flag_precompute: source must have a parallel registered copy; never a
   self-loop endpoint. (n=5 W / 1 N)
2. constant_lut: domain <=8b AND binding-mode attribution first. (1 W / 1 N)
3. sign_select: only on sign-extract idioms; explicit-compare ternaries
   serialize at all widths 13-24b. (2 W / 2 N)
4. max_fanout: narrow reg + homogeneous CE bank pays; wide/heterogeneous
   loses; composition can invert it. (4 W / 3 N)
5. width narrowing: logic-bound path + written bound proof. (1 W)
6. pipelining: output-side cuts only; rendezvous test before proposing;
   total shift = per-stage shift x chained instances, per mode. (2 W / 5 N)
7. Gates must be corruption-validated before first use. (caught 1 real hole)

## Remaining experiments toward the papers (priority order)
1. CROSS-DESIGN TRANSFER (the generalization claim): run the ML-DSA-trained
   priors autonomously on unclaimed HQC blocks (encap cones). If the calculus
   transfers to a different codebase with zero re-tuning, that is the headline
   autonomy result. Cheap: existing orchestrator + HQC KAT gate.
2. ADVISOR ACCEPTANCE SEQUENCE: block equivalence -> block timing ->
   full-chip integration -> full-chip functional -> top-level timing, for the
   top 3 wins (gen_c chain, butterfly chain, makehint chain). Composition
   study covered step 3 partially; full-chip timing not yet measured.
3. MODEL-CAPABILITY TABLE: extend Sonnet-vs-Opus beyond butterfly — one
   latency-tier run each on a block with a KNOWN workable cut (synthetic or
   coeff_decomposer revisit) to separate "can derive taps" from "can pick
   cuts" per model, with cost per outcome.
4. decoder architectural residual: out of calculus scope; document as the
   boundary exemplar, do not chase.

## Infrastructure inventory (all committed)
Two-tier orchestrator (latency-preserving autonomous + latency-changing with
divergence-guided repair), corruption-validated gate suite (block lockstep,
latency-tolerant block, full-KAT 75-vector), latency-agnostic stream
bisection, cost-tracked API loop, live dashboard, 23 findings docs + INDEX,
complete flight logs including every refusal and regression.

## Model attribution and case-study framing (required for honest reporting)
Per advisor guidance: report the Sonnet/Opus comparison as a CONTROLLED CASE
STUDY on one task, not a general model-capability ranking (one stronger-model
call cannot establish a broad ranking). The stronger result is FEEDBACK-DRIVEN
POLICY REFINEMENT: failed attempts exposed a reusable pipeline-cut rule
(output-side insertion + rendezvous test); encoding it moved the standard
model from 0 workable designs (12 calls) to 3/3 workable proposals. Artifacts
retained for before/after analysis: prompts and rejection reasons in
latency_log.jsonl, token counts and costs per call in the same records.
Describe the pipelining stage as AGENT-ASSISTED latency optimization (human
guidance designed the first accepted edits; agent infrastructure verified)
unless a later run independently selects the cut and produces accepted RTL.
The HQC result is CROSS-DESIGN TRANSFER EVIDENCE, not generalization across
arbitrary accelerators; next confirmation target is an additional PQC design
(per advisor, immediate action).

Three tiers were used, and the distinction is a finding within this case study:
- claude-sonnet-4-6 (API, in-loop): all autonomous latency-preserving wins;
  on latency-changing edits it derives retap arithmetic under divergence
  feedback but repeatedly fails insertion-point selection (12 calls, 0 wins
  on butterfly round-3).
- claude-opus-4-8 (API, in-loop, 1 call, $0.245): correctly REFUSED the
  unworkable block with the same structural reasoning as manual analysis.
- claude-fable-5 (chat interface, human-in-loop): designed every
  latency-changing win (butterfly rounds 1-2) and the judgment-heavy
  latency-preserving wins of the final sessions (gen_c sample_addr precompute,
  gen_c/makehint fanout profile, coeff_decomposer width narrowing, and the
  sign_select/S-LUT negative probes), with the human operating gates,
  terminal, and accept/revert authority. Fable 5 also root-caused the
  chained-stage retap rule via the stream-bisection method it designed.
The paper should report this as: insertion-point and load-profile judgment
currently requires frontier-model reasoning (Fable 5 interactive / Opus
refusal-quality); mid-tier models suffice for the constrained autonomous
tier. "Human-in-loop" in this project means human-operated verification
around frontier-model design reasoning — the human never designed an edit.
