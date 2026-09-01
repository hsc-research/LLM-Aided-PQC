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
   Each gate must reject an injected boundary fault and a live-branch
   arithmetic fault before it is used autonomously. This caught a real hole in
   a Fisher-Yates comparison; after repair, the gate correctly rejected the
   same unsafe precomputation when the agent proposed it.

3. **The contribution is not a new transformation.** It is an evidence-tagged
   rulebook, learned from 59 gated proposals across two NIST standards, with
   every negative result documented, describing when each transformation
   helps, fails, or inverts.

4. **Chip-level closure is claimed, and it is measured, not projected.**
   Every frequency below is a true closing frequency: binary-searched period,
   fully routed, non-negative slack. Block-level acceptance does not predict
   chip-level outcome, so post-route closure is the only valid judge.

5. **The rules learned on ML-DSA transferred to HQC with zero retuning**:
   correct refusals, two gate-caught false positives, and an autonomous win,
   for $0.52 of API spend.

---

## Headline results

### Full-chip, post-route (ML-DSA, `combined_top`)

| Stage | Closing Fmax | Note |
|---|---|---|
| Baseline | 70.2 MHz | pristine |
| Composed block edits | 69.0 MHz | accepted block wins alone regress chip closure |
| Architectural rewrite | **80.5 MHz** | **+14.7% vs. baseline** |

The composed-block-edits step is the key negative result: every individual
edit passed its block-level gate, but composing them moved chip closure
*down*. The true bottleneck was a 256-bit variable-shift serializer invisible
to block-level runs. The agent's chip-level loop localized this cone itself,
resolving the binding path to the encoder's PISO register and dispatching to
`encoder.v`; the banked, word-aligned rewrite that fixed it was hand-authored,
and the gates validated the result. **Targeting was autonomous; authoring was
not.**

After the rewrite the design closes at 80.5 MHz and binds on the challenge
sampler (`ctr0_reg[1]/C` -> `CHALLENGE_SAMPLER/C_SIPO_reg[426]/R`), no longer
on the encoder cone. Keccak/SHAKE256 bound the design at the intermediate
71.4 MHz closure step and remains the binding cone for HQC below.

| | Baseline | Optimized | Delta |
|---|---|---|---|
| Closed Fmax | 70.2 MHz | 80.5 MHz | **+14.7%** |
| Throughput | 5,003 ops/s | 5,659 ops/s | **+13.1%** |
| LUT | 53,127 | 53,543 | +0.8% |
| FF | 29,079 | 30,078 | +3.4% |
| DSP / BRAM | 16 / 29 | 16 / 29 | unchanged |
| KeyGen cycles (level V) | 14,033 | 14,226 | +1.4% |

### Block-level board, ML-DSA (out-of-context, 200 MHz target)

| Block | Baseline WNS | Final WNS | Status |
|---|---|---|---|
| `makehint` | -3.511 | **-0.485** | flag-precompute + fanout N=8 (biggest single win, +51% fmax) |
| `gen_c` | -5.233 | **-1.264** | +58% fmax, cumulative across 3 edits (autonomous fanout, hand-guided precompute, fanout) |
| `rejection_s` | -4.013 | -2.486 | constant-LUT win, +1.53 ns |
| `rejection_y` | -4.470 | -4.230 | sign-select win, WNS-neutral, -251 LUTs |
| `coeff_decomposer` | -1.247 | -1.196 | width-narrowing win, threshold-bound |
| `butterfly` | -3.802 | -2.793 | pipeline cut, hand-authored, DSP floor closed |
| `usehint` | -2.542 | -2.542 | closed: ctr self-loop, no win |
| `decoder` | — | — | sign-select regressed at 13-20 b; strategy excluded on this profile |
| `encoder` | see chip trajectory above | — | the actual chip bottleneck; hand-authored architectural rewrite |

`rejection_a` is not independently re-verified in this pass; see
`docs/findings/mldsa/` before citing it.

### The funnel, both designs

| Stage | Count | Note |
|---|---|---|
| Proposed | 59 | 65 raw log records minus 6 `retries_exhausted` (retries within one proposal, not distinct proposals) |
| Applied | 33 | 26 not applied (refused / synth-fail / apply-fail) |
| Functionally correct | 19 | 14 of the 33 applied were functionally incorrect, caught only by the gate |
| Committed | 4 | 15 of the 19 correct edits showed no gain and reverted with a recorded boundary |

By lane: latency-preserving, 4 of 23 incorrect. Latency-changing, **10 of 10
functionally incorrect** and none committed.

### Pipelining insertion-point rule

A mid-tier model went 0/12 on selecting where to cut a pipeline stage.
Encoding a rendezvous rubric moved it to **4/4** on insertion-point selection,
but all four still failed downstream (3 anchor mismatches, 1 gate failure).
Structural judgment is rule-transferable; cross-file consequence tracking is
not.

### HQC

`agent/hqc/transfer_orchestrator.py` imports the ML-DSA rulebook verbatim and
applies it to HQC blocks under the HQC KAT, with zero retuning.

- 15 logged transfer attempts, **1 accepted**: `decap`, flag-precompute,
  **+0.726 ns for $0.037**. Total transfer spend across all 15 attempts:
  **$0.52**.
- 2 gate-caught false positives (`decap` flag-precompute, `fixed_weight`
  max_fanout), both structurally plausible and both caught only by the KAT.
- Chip-level: a closing frequency of 114.3 MHz was reached with the binding
  path resolved to `SHAKE256/data_path_instance/state_ram_instance`,
  confirming Keccak as HQC's binding cone.

Full experiment-by-experiment detail is in `docs/findings/hqc/`; this section
states only what is directly reconciled against `agent/hqc/transfer_log.jsonl`
and the chip-level log as of 2026-07-24. Older summary numbers in
`docs/01_results.md` (dated 2026-06-12) predate this work and should not be
cited without re-verification.

---

## Can this agent optimize PQC cores? The honest answer

Split into the three things people actually mean by that question.

**1. Can it find and verify latency-preserving optimizations autonomously?
Yes, demonstrated.** It re-derived our best hand-tuned result (`makehint`)
from pristine RTL with no knowledge of the solution, landing within 7 ps of
the hand-authored version — independently confirmed as a real netlist
difference and not tool jitter (three synthesis runs, bit-identical). It
found new wins on blocks nobody had touched. It correctly rejected unsound
proposals.

**2. Can it verify latency-changing optimizations autonomously? Yes.** The
full-KAT gate reliably caught every one of the 10 latency-changing edits the
agent produced, all of which were functionally incorrect. This is arguably
the strongest engineering result in the project: the assurance layer works
even where the proposal layer does not.

**3. Can it *design* pipelining or chip-level architectural rewrites
autonomously? Not yet, and this is the honest boundary.** The chip-level loop
reliably *localizes* the bottleneck cone: it correctly identified the
encoder's PISO register as the binding path at 69.0 MHz and dispatched to the
right file. It did not author the fix. The banked rewrite that closed the
design to 80.5 MHz was hand-written and then validated by the same gates the
agent uses. The correct label for this result is **agent-localized,
human-authored, gate-validated** — targeting is autonomous, architectural
authorship is not.

Chip-level absolute timing closure **is** claimed: 80.5 MHz, binary-searched,
fully routed, non-negative slack, out-of-context flow (WNS +0.029). What is not claimed is that the agent
authored the edit that reached it.

---

## Navigating this repository

### Start here

| Document | What it gives you |
|---|---|
| **[docs/REPRODUCE.md](docs/REPRODUCE.md)** | The full step-by-step playbook, from a fresh machine (WSL + Vivado, or native Linux) through correctness checks, timing, and a full agent flight. Sections 0-7 cover HQC; Part II (sections 8-10) covers ML-DSA. |
| **[docs/01_results.md](docs/01_results.md)** | ⚠ Dated 2026-06-12, predates the chip-closure trajectory above. Do not cite HQC or chip-level numbers from this file without cross-checking `agent/*.jsonl` first. |
| **[docs/02_optimization_taxonomy.md](docs/02_optimization_taxonomy.md)** | The rulebook. Transformation classes and the fingerprints that predict when each helps, fails, or inverts. |
| **[docs/04_agent_architecture.md](docs/04_agent_architecture.md)** | The agent pipeline, the gate catalog, and the flight-log narrative. |
| **[docs/03_asic_ppa_analysis.md](docs/03_asic_ppa_analysis.md)** | How each optimization class is expected to translate to an ASIC flow. ASIC flows are in progress; no ASIC results exist for this agent yet. |

### The primary sources

**[docs/findings/](docs/findings/)** holds the dated lab notes, split by
scheme. These are the primary-source records: every experiment, including
every negative result and every reverted edit. **If a claim in this README or
in any summary document matters to you, the dated findings file is the source
of truth, not the summary.**

- **[docs/findings/mldsa/](docs/findings/mldsa/)** — dated findings files,
  including the encoder campaign, the rejection/makehint session, the fanout
  load-profile study, and the pipelining insertion-point rubric.
- **[docs/findings/hqc/](docs/findings/hqc/)** — HQC lab notes, including the
  cross-design transfer experiment writeup.

### Code

- **`agent/`** — the optimization agent and tooling.
  - `chip_orchestrator_log.jsonl` — the chip-level closure trajectory: closing
    frequency, worst-path resolution, and dispatch target at each step. This is
    the primary source for every chip-level number in this README.
  - `flight_log.jsonl`, `mldsa/orchestrator_log.jsonl`,
    `mldsa/latency_log.jsonl`, `hqc/transfer_log.jsonl` — every proposal, every
    verdict, including no-actions, refusals, and negative results. This is the
    primary source for the funnel numbers above.
  - `synthesizer.py`, `path_extractor.py`, `impl_runner.py` — synthesis,
    critical-path extraction, post-route implementation.
  - `kat_gate.py` — the HQC correctness gate.
  - `optimizer_v2.py`, `loop_v21.py`, `edit_ops.py` — the proposal loop and the
    typed-edit harness that verifies it.
  - **`agent/hqc/`** — the HQC tier, including `transfer_orchestrator.py`.
  - **`agent/mldsa/`** — the ML-DSA tier: `full_kat_gate.py`, `orchestrator.py`
    / `orchestrator_latency.py`, the per-block equivalence gates
    (`*_equiv_gate.py`), and `mldsa_src/` (the tracked override sources — every
    committed ML-DSA win lives here, never in the pristine tree).

- **`build/{keygen,encap,decap}/`** — the three elaborated HQC build trees that
  are synthesized and simulated.
- **`hardware/`** — the HQC RTL (Yale/Deshpande).
- **`synth_out/`** — synthesis reports and extracted critical paths.

### A note on measurement validity

`agent/flow_sweep_log.jsonl` contains exploratory sweep records using a
projected-fmax formula, `1/(period - WNS)`, computed under heavy
over-constraint. **This formula has been formally retracted as a measurement
method** and produces unreliable numbers under the conditions in that file.
Nothing in this README derives from it. The only valid closing-frequency
method used anywhere in this repository is the binary-search procedure in
`fmax_search.py`, OOC synthesis mode, accepting only `Slack (MET)` results.

### A note on the pristine trees

Optimized RTL **never** lives in a pristine reference tree. ML-DSA overrides
live in `agent/mldsa/mldsa_src/` and are applied by basename at compile time.
A `.bak` file appearing next to a pristine source is a contamination signal —
it means an edit was applied in the wrong place. This rule exists because it
was violated once, caught, and documented
(`FINDINGS_mldsa_repro_and_pristine_integrity.md`).

---

## Reproducing anything here

Start with **[docs/REPRODUCE.md](docs/REPRODUCE.md)**. It assumes no prior
familiarity with the codebase and has been verified from a fresh clone.
