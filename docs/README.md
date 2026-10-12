# Documentation index

[Project home](../README.md) · [Learn](LEARN.md) · [Results](RESULTS.md) · [Run](REPRODUCE.md)

New here? Read **[Learn the project](LEARN.md)**, look at **[Results](RESULTS.md)**,
then follow **[Install and run](REPRODUCE.md)**. You do not need an EDA tool or
model API to understand the repo or run its Python checks.

## Understand the project

| Guide | What it answers |
|---|---|
| [Learn the project](LEARN.md) | What the repo does, what the four designs are, and why full-design timing matters |
| [Repository map](REPOSITORY_LAYOUT.md) | Where reference RTL, edited designs, test data, flow code and reports live |
| [Current design status](PROJECT_STATUS.md) | Which operations and tools are supported, and which checks remain open |
| [Results](RESULTS.md) | What was measured, what the results mean, and which claims were superseded |
| [Verification record](VERIFICATION.md) | Exact local test coverage, commands, fault controls and [evidence files](verification/README.md) |

## Run it

| Guide | Use it for |
|---|---|
| [Install and run](REPRODUCE.md) | A staged route from a clean checkout to source checks, RTL simulation and EDA runs |
| [Hardware handoff](HARDWARE_HANDOFF.md) | Prepare separate FPGA/ASIC baselines, preserve memory behavior, then measure matched candidates |
| [FPGA](FPGA.md) | Vivado setup, design selection, functional checks and timing measurement |
| [ASIC startup sources](ASIC_STARTUP.md) | Explicit ML-DSA/SLH baseline/candidate paths, boot protocols, evidence and remaining target gates |
| [ASIC synthesis](../asic/README.md) | Genus/DC manifests, libraries, constraints, output reports and qualification |
| [ASIC site admission](ASIC_ADMISSION.md) | Qualified adapter contract for structural checks and FF-memory evidence |
| [Whole-design controller](WHOLE_DESIGN.md) | Multi-path targeting, small edits, full-design rechecks and acceptance/rollback |
| [Existing agent workflows](../agent/README.md) | CLI entry points and the older one-round FPGA driver |
| [Local dashboard](DASHBOARD.md) | Read existing experiment logs in a local browser |

## Find a design

| Design | Source and test instructions | Current limits |
|---|---|---|
| ML-KEM | [Adam's Bridge inputs](../third_party/adams_bridge/README.md), [ACVP harness](../verification/mlkem_adams_bridge/README.md) | [Shared-core scope and entry points](PROJECT_STATUS.md#ml-kem-entry-points) |
| ML-DSA | [ML-DSA-OSH inputs](../third_party/mldsa_osh/README.md), [portable test guide](../verification/mldsa_osh/README.md), [run commands](REPRODUCE.md#ml-dsa) | [Source boundaries and coverage](PROJECT_STATUS.md#ml-dsa-entry-points) |
| HQC | [Preferred SAC 2026 source-only snapshot](../third_party/hqc_sac2026/README.md), [legacy run commands](REPRODUCE.md#hqc) | [New-baseline status](PROJECT_STATUS.md#hqc-preferred-source-baseline), [separate legacy review](PROJECT_STATUS.md#hqc-legacy-verification-boundary) |
| SLH-DSA | [Selected-mode checker](../agent/slh_dsa/README.md), [portable variant](../verification/slh_portable/README.md), [run commands](REPRODUCE.md#slh-dsa) | [Baseline boundary](PROJECT_STATUS.md#slh-dsa-baseline-boundary) |

## Review or extend the work

- [Agent status](AGENT_STATUS.md): implemented behavior and remaining work
- [Contribution guide](../CONTRIBUTING.md): checks before submitting changes
- [Documentation standard](DOCUMENTATION_STANDARD.md): how to record reproducible evidence
- [Release checklist](RELEASE_CHECKLIST.md): unresolved redistribution and license review
- [Security notes](../SECURITY.md): experimental-use and data-handling limits
- [Optimization taxonomy](02_optimization_taxonomy.md): earlier transformation families
- [Earlier architecture/onboarding notes](AGENT_ARCHITECTURE.md): historical design context;
  use the current [controller guide](WHOLE_DESIGN.md) for new integrations

## Historical records

These are retained records, not a current installation guide. Read the
[results guide](RESULTS.md) before quoting their numbers or rerunning a command.

- [Findings index](findings/INDEX.md): dated experiments, corrected ledgers and rejected edits
- [ML-DSA findings](findings/mldsa/), [HQC findings](findings/hqc/),
  [SLH-DSA findings](findings/slh-dsa/), [ASIC findings](findings/asic/)
- [Software update notes](UPDATE_NOTES.md): changes and limits at that update
- [Earlier results summary](01_results.md), [ASIC analysis](03_asic_ppa_analysis.md),
  [architecture](04_agent_architecture.md), [roadmap](ROADMAP.md) and
  [ASIC plan](2026-08-02_asic_game_plan.md)
- [Session handoffs](handoffs/) and [manuscript drafts](paper/)
- [Archived research README](archive/README_RESEARCH_LOG_2026-08-30.md)

When sources disagree, prefer the dated correction and its underlying report.
An archived result is not evidence that the current checkout has reproduced it.
