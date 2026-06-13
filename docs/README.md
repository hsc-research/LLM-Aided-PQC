# HQC RTL Optimization — Documentation

LLM-aided Power/Performance/Area (PPA) optimization of the open-source HQC
post-quantum KEM RTL (Deshpande et al., Yale, SAC 2023) targeting a Xilinx
Artix-7 `xc7a200tfbg676-1` at 200 MHz (5.000 ns), out-of-context synthesis,
across all three security levels (HQC-128 / 192 / 256).

Every accepted RTL change in this project passes a Known-Answer Test (KAT) gate:
the full keygen → encap → decap simulation chain must reproduce matching shared
secrets at all three security levels before the change is committed.

## Where to start

| Document | Contents |
|----------|----------|
| [01_results.md](01_results.md) | The verified optimizations, the cross-level timing table, and measured PPA deltas. Start here for "what was done." |
| [02_optimization_taxonomy.md](02_optimization_taxonomy.md) | The classification of optimization patterns, the fingerprints that predict success or regression, and the negative results. The "theory" behind the wins. |
| [03_asic_ppa_analysis.md](03_asic_ppa_analysis.md) | How each class of optimization translates from FPGA to an ASIC flow, including which trades reverse sign. |
| [04_agent_architecture.md](04_agent_architecture.md) | The LLM-driven optimization agent: pipeline, safety gates, and the supervised flight log. |
| [findings/](findings/) | Original dated lab notes, preserved verbatim. Primary-source records of individual experiments. |

## Quick status

- 15 KAT-verified timing optimizations, all cycle-schedule neutral.
- keygen meets timing within roughly 0.1 ns at all three security levels.
- Every RTL logic-depth critical-path cluster across keygen and encap has been
  eliminated or attributed; the remaining negative slack is placement/routing
  bound (memory endpoints, high-fanout broadcast nets) rather than logic depth.
- The optimization agent is operational: it selects targets from critical-path
  clusters, proposes typed edits through an assertion-gated harness, measures
  per-cluster gain, and reverts non-improvements autonomously.

## Repository layout (relevant paths)

- `agent/` — the optimization agent and supporting tooling (code only).
- `build/{keygen,encap,decap}/` — the three elaborated build trees that are
  synthesized and simulated.
- `synth_out/` — synthesis reports, extracted critical paths, the cross-level
  matrix.
- `docs/` — this documentation.
