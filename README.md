# LLM-Aided-PQC

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![HDL](https://img.shields.io/badge/RTL-Verilog%20%7C%20VHDL-6f42c1.svg)](#supported-pqc-cores)
[![FPGA](https://img.shields.io/badge/FPGA-Artix--7-1f6feb.svg)](#results-at-a-glance)
[![ASIC](https://img.shields.io/badge/ASIC-ASAP7%20%2F%20Genus-b45309.svg)](#asic-flow)

**A correctness-gated, implementation-driven agent for optimizing post-quantum cryptographic RTL across FPGA and ASIC backends.**

The language model proposes an optimization, but it does not control the timing target, edit the accepted baseline directly, or decide whether a result is correct. Deterministic code maps implementation reports to RTL, applies typed edits, runs functional and schedule checks, measures post-implementation PPA, and accepts or reverts each candidate.

> **Artifact status.** The FPGA results and experiment ledgers are included. The ASIC scripts provide pre-layout ASAP7 synthesis support and require a licensed Cadence installation plus a local ASAP7 library. Some ML-DSA and SLH-DSA verification scripts also require separately obtained upstream source or simulation trees; these requirements are identified below.

<p align="center">
  <img src="docs/assets/pqc_agent_fpga_asic_framework.jpg" width="1000" alt="Closed-loop LLM-aided RTL optimization framework for PQC hardware across FPGA and ASIC flows">
</p>

## What this repository provides

- A **top-down, two-tier optimization flow** that starts from the integrated design, identifies its worst timing-path clusters, and descends to block-level analysis only when more internal detail is needed.
- A **typed RTL edit interface**. The model returns a structured operation rather than unrestricted Verilog.
- Independent **functional, timing-schedule, and PPA checks** before a candidate may replace the accepted baseline.
- FPGA synthesis, critical-path extraction, placement-and-route closure search, and result logging for AMD Artix-7.
- Pre-layout ASIC synthesis scripts for Cadence Genus and the ASAP7 predictive technology.
- Reproducible experiment records, including accepted changes, rejected changes, abstentions, superseded measurements, and negative results.
- Three PQC case studies spanning lattice-, code-, and hash-based cryptography.

## How the optimization loop works

1. **Implement the full design.** Run the selected FPGA or ASIC backend on the current accepted RTL.
2. **Parse and map reports.** Extract the top timing paths, PPA data, hierarchy, and source-level cones.
3. **Cluster critical paths.** Group related paths by source, destination, hierarchy, and logic structure.
4. **Select the analysis tier.** Work from the top-level cone when possible; synthesize a submodule only when the integrated report lacks sufficient detail.
5. **Plan a typed edit.** The LLM selects an admissible rule or proposes a new rule for review.
6. **Apply the edit deterministically.** Source locations, declarations, widths, driver relationships, and replacement counts are checked before the RTL is changed.
7. **Rebuild and admit or revert.** The full design is rerun. A candidate is retained only after functional, timing-schedule, and implementation-quality checks pass.

Block-level results are diagnostic. **Only an integrated top-level rerun can establish a reported optimization.**

## Supported PQC cores

| Scheme | Family | RTL used in this artifact | Verification scope | FPGA scope |
|---|---|---|---|---|
| **ML-DSA** | Lattice-based signature | GMU/Beckwith unified core with tracked overrides in `agent/mldsa/mldsa_src/` | Full key-generation KAT flow, 25 vectors at each of three security levels; block-level lockstep gates | Unified `combined_top` and selected submodules |
| **HQC** | Code-based KEM | Yale/Deshpande RTL under `hardware/`, with accepted build overrides | Full keygen → encapsulation → decapsulation chain at HQC-128/192/256; shared secrets must match | Joint KEM top and keygen/encap/decap blocks |
| **SLH-DSA** | Hash-based signature | SPHINCSLET-based pristine and accepted trees under `agent/slh_dsa/` | Differential sign/verify check against frozen pristine signatures for the evaluated parameter sets | Full `top`, SHA-256, and SHA-512 cones |

The SLH-DSA gate is differential: a pass means that the accepted RTL reproduces the frozen pristine signature and the vendor testbench reports successful verification. It is not an independent proof of the upstream implementation.

## Results at a glance

The table reports the best observed non-negative-WNS closing point from the bounded post-route search. These values are measured closure points under the recorded flow, not proofs of a global maximum frequency.

| Design | Baseline | Accepted | Change | Role of the agent |
|---|---:|---:|---:|---|
| ML-DSA `combined_top` | 70.2 MHz | **80.5 MHz** | **+14.7%** | Agent-localized critical cone; human-authored architectural replacement; gate-validated |
| HQC joint KEM | 109.6 MHz | **116.0 MHz** | **+5.8%** | Agent selected and applied a transferred typed rule |
| SLH-DSA 256f, SHA-2 | 75.5 MHz | **90.9 MHz** | **+20.4%** | Agent-proposed, human-approved carry-save rule; deterministic application and verification |

For SLH-DSA, all six evaluated parameter sets improve, from 4.4% to 20.4%. For ML-DSA, the frequency gain is partly offset by a constant 193-cycle increase over the evaluated key-generation vectors; the measured key-generation throughput gain is 13.1%. Canonical values, exact commands, commit identifiers, caveats, and superseded measurements are maintained in [`docs/findings/INDEX.md`](docs/findings/INDEX.md).

## Repository map

| Path | Purpose |
|---|---|
| `agent/` | Shared optimization infrastructure, typed edit operations, path analysis, closure search, dashboards, and logs |
| `agent/mldsa/` | ML-DSA gates, orchestrators, block tools, and accepted override sources |
| `agent/hqc/` | HQC KAT gates, transfer experiments, joint-top orchestration, and cycle measurement |
| `agent/slh_dsa/` | SLH-DSA pristine/accepted trees, differential gate, orchestrator, and six-configuration sweep |
| `agent/backends/` | Vivado and Genus backend abstractions |
| `hardware/` | HQC source RTL and testbench support |
| `build/` | Elaborated HQC build trees used by simulation and synthesis |
| `asic/` | ASAP7/Genus arms, scripts, constraints, and result records |
| `logs/` | Closure and implementation logs used by results of record |
| `docs/findings/` | Dated experiment records, including negative and superseded results |
| `docs/REPRODUCE.md` | Extended reproduction notes and historical troubleshooting |
| `docs/archive/README_RESEARCH_LOG_2026-08-30.md` | Archived version of the former root README |

## Quick start

### 1. Requirements

For the FPGA and agent flows:

- Linux or WSL2
- Python 3.10 or newer
- AMD Vivado **2025.2** with Artix-7 device support
- Git
- `anthropic` only when running the LLM proposal step
- `flask` only when running the dashboard

For the ASIC flow:

- Cadence Genus **25.12** or a compatible release
- A local ASAP7 Liberty/LEF installation
- Sufficient memory and runtime for large full-design synthesis jobs

### 2. Clone and create a Python environment

```bash
git clone https://github.com/hsc-research/LLM-Aided-PQC.git
cd LLM-Aided-PQC

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install anthropic flask
```

The hardware checks do not require an API key. The `anthropic` package is needed only for model-backed proposals, and `flask` is needed only for the optional dashboard.

### 3. Make Vivado available

```bash
source /tools/Xilinx/2025.2/Vivado/settings64.sh
vivado -version
```

Adjust the installation path for your machine. The scripts invoke `vivado`, `xvlog`, `xvhdl`, `xelab`, and `xsim` from the active environment.

## Run the HQC flow

HQC is the most self-contained case study in this repository.

### Full three-level functional check

```bash
python3 agent/hqc/joint_kat_gate.py --all
```

A successful run ends with:

```text
[hqc128] SS MATCH ... PASS
[hqc192] SS MATCH ... PASS
[hqc256] SS MATCH ... PASS
JOINT KAT GATE: PASS
```

The gate runs standalone key generation and encapsulation, then exercises the joint decapsulation design and compares the recovered shared secret with the encapsulation output.

### Extract and cluster critical paths

```bash
python3 agent/path_extractor.py hqc_joint_opt hqc128 20
```

For a block-level view, replace `hqc_joint_opt` with `keygen`, `encap`, `decap`, `fixed_weight`, or another registered module. The generated report is written under `synth_out/paths/`.

### Run one typed-edit flight

```bash
export ANTHROPIC_API_KEY=your_key_here
python3 agent/loop_v21.py keygen hqc192
```

A flight selects one non-exhausted critical-path cluster, asks the model for a typed proposal, checks and stages the edit, reruns synthesis, and reverts candidates that fail correctness or the improvement threshold. Review the resulting Git diff before committing anything.

### Run the top-level closure loop

Analysis and dispatch recommendation:

```bash
python3 agent/chip_orchestrator.py hqc
```

Automatic block dispatch, KAT, checkpoint regeneration, and top-level remeasurement:

```bash
python3 agent/chip_orchestrator.py hqc --dispatch
```

Top-level closure searches are expensive. The first command is the safer starting point because it shows the selected cone and target file before an edit is attempted.

## Run the ML-DSA flow

The repository stores accepted ML-DSA overrides, but the full gate expects a separately obtained pristine GMU/Beckwith tree containing `ref_combined/`, `common/`, and `KAT/`.

Before running the gate, set the local `ROOT` and, when needed, `VIVADO_BIN` values near the top of `agent/mldsa/full_kat_gate.py` to match your installation. This legacy path configuration is intentionally called out rather than hidden.

Pristine baseline:

```bash
python3 agent/mldsa/full_kat_gate.py
```

Accepted override tree:

```bash
python3 agent/mldsa/full_kat_gate.py agent/mldsa/mldsa_src
```

A shorter smoke run may be selected with `--vectors N`; the complete paper check uses all configured vectors and security levels.

Block-level path extraction follows the shared interface:

```bash
python3 agent/path_extractor.py decoder mldsa 20
```

The detailed ML-DSA setup, source ordering, mixed Verilog/VHDL handling, and pristine-tree rules are documented in [`docs/REPRODUCE.md`](docs/REPRODUCE.md) and [`docs/AGENT_ARCHITECTURE.md`](docs/AGENT_ARCHITECTURE.md).

## Run the SLH-DSA flow

The committed repository contains pristine and accepted SLH-DSA RTL trees. The current vendor simulation wrapper still expects a local simulation workspace and data directory. Configure `SIM_DIR`, `DATA`, and `DEFAULT_RTL` near the top of `agent/slh_dsa/slh_kat_gate.py` before running:

```bash
python3 agent/slh_dsa/slh_kat_gate.py agent/slh_dsa/slh_src
```

The six-configuration FPGA sweep is driven by:

```bash
python3 agent/slh_dsa/level_sweep.py
```

The sweep is compute-intensive and regenerates closure data. Read [`docs/findings/slh-dsa/2026-08-29_slh_dsa_level_sweep.md`](docs/findings/slh-dsa/2026-08-29_slh_dsa_level_sweep.md) before replacing results of record.

## ASIC flow

The ASAP7 flow is under `asic/asap7/`. The main Genus script reads the following environment variables:

```bash
export GENUS_TOP=<top_module>
export GENUS_SRCDIR=<absolute_or_relative_rtl_directory>
export GENUS_PERIOD_PS=<clock_period_in_ps>
export GENUS_OUTDIR=<empty_output_directory>
# Optional:
export GENUS_SDC=<constraint_file>
export GENUS_PARAMS=<elaboration_parameters>
export GENUS_HDL_DEFINES=<verilog_defines>
```

Set `TUT` at the top of `asic/asap7/scripts/genus_asap7_v2.tcl` to the directory containing your ASAP7 `lib/`, `lef/`, and `techlef/` trees, then run:

```bash
mkdir -p "$GENUS_OUTDIR"
genus -batch -files asic/asap7/scripts/genus_asap7_v2.tcl
```

The script writes mapped/final databases, netlists, and timing, area, gate, and power reports into `GENUS_OUTDIR`. Current ASIC results are pre-layout, and inferred memories may map to flip-flop arrays; they should be interpreted as matched comparative synthesis results rather than final macro-aware chip PPA.

## Optional dashboard

```bash
python3 agent/dashboard.py
```

Open `http://localhost:5000`. The dashboard is read-only and summarizes proposal logs, gate outcomes, closure records, and recorded API cost.

## Acceptance and measurement rules

- The LLM proposes; deterministic code applies and verifies.
- A source edit is not a result until the relevant functional gate passes.
- A block-level gain is not a chip-level gain.
- Frequency is reported only from a routed run with non-negative WNS.
- Projected frequency from a violated timing report is not a valid result.
- Schedule-changing edits require stronger review than cycle-preserving edits.
- A correct candidate with no measurable backend benefit is reverted.
- Negative and superseded results remain recorded so they are not repeated or silently reused.

The primary source for current numbers is [`docs/findings/INDEX.md`](docs/findings/INDEX.md). Older summaries may describe superseded experiments and should not be cited without checking the index.

## Reproducing the paper artifact

Start with these documents:

1. [`docs/findings/INDEX.md`](docs/findings/INDEX.md): canonical ledgers and status of each experiment.
2. [`docs/REPRODUCE.md`](docs/REPRODUCE.md): detailed setup and command history.
3. [`docs/02_optimization_taxonomy.md`](docs/02_optimization_taxonomy.md): typed transformation rules and exclusions.
4. [`docs/AGENT_ARCHITECTURE.md`](docs/AGENT_ARCHITECTURE.md): top-level and block-level orchestration.
5. [`docs/DOCUMENTATION_STANDARD.md`](docs/DOCUMENTATION_STANDARD.md): measurement, supersession, and evidence policy.

## Citation

The archival paper citation will be added after publication. Until then, cite the software artifact:

```bibtex
@software{alcorn2026llmaidedpqc,
  author  = {Lloyd Alcorn and Sanjay Deshpande and Malik Imran and
             Christine L. Page and Jakub Szefer and Zain Ul Abideen},
  title   = {{LLM-Aided-PQC}: Correctness-Gated RTL Optimization for
             Post-Quantum Hardware},
  year    = {2026},
  url     = {https://github.com/hsc-research/LLM-Aided-PQC},
  note    = {Research software and reproducibility artifact}
}
```

GitHub's **Cite this repository** menu reads the accompanying [`CITATION.cff`](CITATION.cff).

## Licensing and third-party RTL

The repository-level software is distributed under the [GNU General Public License v3.0](LICENSE). Included and modified third-party RTL may carry Apache-2.0, MIT, GPL, or other source-specific terms. Preserve all original headers and review [NOTICE](NOTICE) before redistribution. Do not assume that the repository-level license replaces a third-party file's original notice.

## Contributing

Issues and pull requests are welcome for:

- reproducibility fixes and portable path configuration;
- new FPGA or ASIC backends;
- additional PQC cores;
- typed optimization rules with explicit admissibility conditions;
- stronger functional, schedule, or formal verification; and
- independently reproduced results.

A contribution that changes RTL should include the baseline and candidate configuration, exact tool version, functional evidence, cycle or schedule evidence, implementation reports, and a clear accept/revert decision.

## Acknowledgments

This artifact builds on published open-source PQC accelerators and third-party hash cores. See [NOTICE](NOTICE) and the source headers for attribution. The repository preserves both successful and unsuccessful optimization attempts because the failure boundaries are part of the research result.
