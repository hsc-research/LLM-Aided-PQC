# LLM-Aided-PQC

A correctness-gated optimization agent for post-quantum cryptographic (PQC)
hardware. An LLM proposes equivalence-preserving RTL edits; deterministic code
verifies every change; a cryptographic correctness check gates every accepted
edit. The agent also decides when a bottleneck is not addressable at the RTL
level at all, and says so rather than forcing an edit.

Two NIST-standardized designs are studied: **ML-DSA** (GMU/Beckwith codebase)
and **HQC** (Yale/Deshpande codebase), both on Artix-7 `xc7a200tfbg676-1`.

---

## The contribution, in five sentences

1. **The model is structurally untrusted.** Deterministic code makes every
   checkable decision, and a broken edit cannot be accepted, because acceptance
   is gated on a check the model cannot touch.

2. **The gates themselves are validated by corruption before being trusted.**
   This caught a real hole in the `gen_c` gate immediately before the agent
   proposed a broken edit on exactly the comparison the gate was blind to.

3. **The contribution is not a new transformation.** It is an evidence-tagged
   rulebook, learned from roughly thirty gated experiments across two NIST
   standards, with every negative result documented, describing when each
   transformation helps, fails, or inverts.

4. **Block-level wins do not appear post-synthesis at the chip level; they
   appear post-route**, and the margin grows with constraint pressure.
   Post-route is the only valid top-level judge.

5. **The rules learned on ML-DSA transferred to HQC with zero retuning**:
   correct refusals, one gate-caught false positive, and an autonomous win, for
   sixteen cents of API spend.

---

## Headline results

### Full-chip, post-route (ML-DSA, `combined_top`)

The optimized design beats pristine at **every** measured corner. The margin
grows as the constraint tightens, consistent with the edits removing logic depth
the router would otherwise have to fight for.

| Corner | Pristine WNS / fmax | Optimized WNS / fmax | Delta |
|---|---|---|---|
| -1 grade, 5.00 ns (200 MHz stretch) | -10.318 / 65.3 MHz | -8.766 / 72.6 MHz | **+11.2%** |
| -1 grade, 8.60 ns | -5.995 / 68.5 MHz | -5.017 / 73.4 MHz | +7.2% |
| -3 grade, 8.62 ns (116 MHz GMU-comparable) | -1.974 / 94.4 MHz | -1.779 / 96.2 MHz | +1.9% |

Post-**synthesis** chip estimates showed the optimized design marginally *worse*
(a real, deterministic -0.244 ns regression, confirmed non-noise by a 3-run
variability check). Post-route reverses the sign. This is the single most
important methodological finding in the project: synthesis-stage chip estimates
mispredict the sign of the integration outcome.

### Block-level board, ML-DSA (out-of-context, 200 MHz target)

| Block | Baseline WNS | Final WNS | Status |
|---|---|---|---|
| `makehint` | -3.511 | **-0.485** | fanout N=8 optimum |
| `coeff_decomposer` | -1.247 | -1.196 | routing-bound residual |
| `gen_c` | -5.233 | **-1.264** | +58% fmax cumulative |
| `rejection_s` | -4.013 | -2.486 | closed: internal-merge bound |
| `usehint` | -2.542 | -2.542 | closed: ctr self-loop |
| `butterfly` | -3.802 | -2.793 | closed: DSP mux floor |
| `rejection_a` | -2.933 | -2.933 | fanout win reverted (composition inversion) |
| `rejection_y` | -4.470 | -3.511 | internal-merge bound |
| `decoder` | -4.806 | -4.299 | architectural residual |
| `encoder` | -2.900 | -2.837 | **the actual chip bottleneck** |

### HQC

12 KAT-verified optimizations (wins 4-15), all cycle-schedule neutral. `keygen`
is within roughly 0.1 ns of full timing closure at every security level. Full
table in [docs/01_results.md](docs/01_results.md).

### Cross-design transfer (ML-DSA rulebook -> HQC, zero retuning)

`transfer_orchestrator.py` imports the ML-DSA policy verbatim and applies it to
HQC blocks, gated by the HQC KAT. On first contact:

- **`encap`** — model recognized the fanout load-profile pattern, edit applied
  cleanly, **KAT passed**, synthesis showed -0.007 ns: noise. Auto-reverted as
  marginal. Correct rule, correct target, honest adjudication.
- **`keygen`** — **correct refusal**, citing the load-profile rule precisely:
  32-bit source with heterogeneous bit-slice loads, so fanout replication is
  excluded.
- **`decap`** — model proposed a flag precompute that was functionally wrong.
  The KAT caught it, auto-reverted, logged. First transfer false positive, and
  the gate did exactly its job.
- **`decap`, later run** — a genuine autonomous win: **+0.726 ns, for $0.037.**

---

## Can this agent optimize PQC cores? The honest answer

Split into the three things people actually mean by that question.

**1. Can it find and verify latency-preserving optimizations autonomously?
Yes, demonstrated.** It re-derived our best hand-tuned result (`makehint`) from
pristine RTL with no knowledge of the solution, landing within 7 ps — and we
proved that 7 ps is a real netlist difference, not tool variation (three
synthesis runs, bit-identical). It found new wins on blocks nobody had touched.
It correctly rejected unsound proposals. It correctly declared closed cones
instead of forcing edits.

**2. Can it verify latency-changing optimizations autonomously? Yes.** The
full-KAT gate plus latency-agnostic stream bisection catch *and localize* wrong
retiming reliably. This is arguably the strongest engineering contribution.

**3. Can it *design* pipelining autonomously? Not yet — and this is the honest
boundary.** It learns the retiming arithmetic from feedback. It does not reliably
choose *where to cut*. Encoding the rendezvous rubric moved the weaker model from
0/12 to 3/3 workable proposals, which is real progress and a real finding — but
the first accepted pipelining wins were frontier-model-designed with a human at
the gates. The correct label is **agent-assisted**, and this project states so
directly.

Chip-level absolute timing closure is **not** claimed. The chip bottleneck lives
in interconnect and congestion territory (the DECODER-to-ENCODER cone, PISO
organization) that out-of-context per-block synthesis structurally cannot see or
fix — consistent with GMU's own published statement that their critical path is
within the interconnect for the shared Keccak modules.

---

## Navigating this repository

### Start here

| Document | What it gives you |
|---|---|
| **[docs/REPRODUCE.md](docs/REPRODUCE.md)** | The full step-by-step playbook, from a fresh machine (WSL + Vivado, or native Linux) through correctness checks, timing, and a full agent flight. Sections 0-7 cover HQC; Part II (sections 8-10) covers ML-DSA. Verified from a clean checkout. |
| **[docs/01_results.md](docs/01_results.md)** | The verified optimizations, cross-level timing, measured PPA deltas. Start here for "what was done." |
| **[docs/02_optimization_taxonomy.md](docs/02_optimization_taxonomy.md)** | The rulebook. Transformation classes and the fingerprints that predict when each helps, fails, or inverts. The "theory" behind the wins, and the reusable artifact. |
| **[docs/04_agent_architecture.md](docs/04_agent_architecture.md)** | The agent pipeline, the gate catalog, and the flight-log narrative. How the model is kept structurally untrusted. |
| **[docs/03_asic_ppa_analysis.md](docs/03_asic_ppa_analysis.md)** | How each optimization class is expected to translate to an ASIC flow, including which trades reverse sign. |

### The primary sources

**[docs/findings/](docs/findings/)** holds the dated lab notes, split by scheme.
These are the primary-source records: every experiment, including every negative
result and every reverted edit. If a claim in the summary docs matters to you,
the findings file is where the evidence lives.

- **[docs/findings/mldsa/](docs/findings/mldsa/)** — 22 findings files. Notable
  entry points:
  - `FINDINGS_mldsa_postroute_acceptance.md` — the post-route acceptance rule
    and the full corner table. Read this before quoting any chip-level number.
  - `FINDINGS_mldsa_fullchip_integration.md` — where the chip bottleneck
    actually is, and the GMU comparison.
  - `FINDINGS_mldsa_precompute_boundaries.md` — when the precompute pattern
    works and when it fails. The sharpest statement of a rule's boundary
    conditions in the project.
  - `FINDINGS_mldsa_composition.md` — why block-level wins do not always survive
    composition (the `rejection_a` fanout inversion).
  - `FINDINGS_mldsa_fullkat_gate.md` — the outer gate, its construction, and its
    corruption validation.
  - `FINDINGS_mldsa_latency_orchestrator_v0.md` — the autonomous latency tier,
    and the model-capability comparison (Sonnet 12 calls, no convergence; Opus 1
    call, correct refusal).
  - `FINDINGS_mldsa_encoder_campaign.md` — the chip bottleneck attacked from four
    angles and closed at the RTL level. The boundary exemplar.
- **[docs/findings/hqc/](docs/findings/hqc/)** — HQC lab notes, plus
  `variants_archive/` (retained candidate RTL from the flag-precompute runs).

### Code

- **`agent/`** — the optimization agent and tooling.
  - `synthesizer.py`, `path_extractor.py`, `impl_runner.py` — synthesis, critical
    path extraction, post-route implementation.
  - `kat_gate.py` — the HQC correctness gate.
  - `optimizer_v2.py`, `loop_v21.py`, `edit_ops.py` — the proposal loop and the
    typed-edit harness that verifies it.
  - `dashboard.py` — live status, verdicts, running API spend.
  - **`agent/hqc/`** — the HQC tier, including `transfer_orchestrator.py`, which
    imports the ML-DSA policy verbatim and applies it to HQC blocks under the HQC
    KAT. This is the cross-design transfer experiment.
  - `flight_log.jsonl` — every flight, including no-actions, refusals, and
    negative results.
  - **`agent/mldsa/`** — the ML-DSA tier: `full_kat_gate.py` (the outer,
    full-design NIST KAT gate), `orchestrator.py` / `orchestrator_latency.py`,
    the per-block equivalence gates (`*_equiv_gate.py`), and `mldsa_src/` (the
    tracked override sources — every committed ML-DSA win lives here, never in
    the pristine tree).

- **`build/{keygen,encap,decap}/`** — the three elaborated HQC build trees that
  are synthesized and simulated.
- **`hardware/`** — the HQC RTL (Yale/Deshpande).
- **`synth_out/`** — synthesis reports, extracted critical paths, the cross-level
  matrix.

### A note on the pristine trees

Optimized RTL **never** lives in a pristine reference tree. ML-DSA overrides live
in `agent/mldsa/mldsa_src/` and are applied by basename at compile time. A `.bak`
file appearing next to a pristine source is a contamination signal — it means an
edit was applied in the wrong place. This rule exists because it was violated
once, caught, and documented
(`FINDINGS_mldsa_repro_and_pristine_integrity.md`).

---

## Reproducing anything here

Start with **[docs/REPRODUCE.md](docs/REPRODUCE.md)**. It assumes no prior
familiarity with the codebase and has been verified from a fresh clone.
