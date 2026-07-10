# LLM-Aided-PQC

A correctness-based optimization agent for post-quantum cryptographic (PQC)
hardware. An LLM proposes equivalence-preserving RTL edits, deterministic code
verifies every change, and a cryptographic correctness check (a full
keygen/encap/decap simulation across all three security levels) gates every
accepted edit. The agent also decides when a bottleneck is not addressable at
the RTL level at all. HQC is the first complete case study.

## Reproducing the results

Everything you need to clone, set up, and reproduce the correctness checks, the
timing results, and an agent run is in the docs folder:

- **[docs/REPRODUCE.md](docs/REPRODUCE.md)**, the full step-by-step playbook,
  from a fresh machine (WSL + Vivado on Windows, or native Linux) through the
  KAT correctness check, per-board timing, and a full agent flight. It also
  documents the environment setup gotchas and manual-simulation details. The
  clone-and-run flow has been verified from a clean checkout.

## Documentation

- **[docs/README.md](docs/README.md)**, the documentation index.
- **[docs/01_results.md](docs/01_results.md)**, the verified optimizations,
  cross-level timing, and measured resource deltas.
- **[docs/02_optimization_taxonomy.md](docs/02_optimization_taxonomy.md)**, the
  transformation classes and the fingerprints that predict when each helps.
- **[docs/03_asic_ppa_analysis.md](docs/03_asic_ppa_analysis.md)**, how each
  optimization class is expected to translate to an ASIC flow.
- **[docs/04_agent_architecture.md](docs/04_agent_architecture.md)**, the agent
  pipeline, gate catalog, and flight-log narrative.
- **[docs/findings/hqc/](docs/findings/hqc/)** and **[docs/findings/mldsa/](docs/findings/mldsa/)**, raw dated lab notes, split by scheme. HQC also has [variants_archive/](docs/findings/hqc/variants_archive/), retained candidate RTL variants from the flag-precompute optimization runs.
