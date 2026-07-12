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
