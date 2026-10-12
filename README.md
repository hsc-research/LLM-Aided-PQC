<p align="center"><img src="docs/assets/banner.svg" alt="LLM-Aided-PQC" width="100%"></p>

<p align="center">
<a href="#quick-start">Quick start</a> · <a href="docs/README.md">Documentation</a> ·
<a href="agent/README.md">Agent</a> · <a href="asic/README.md">Genus / DC</a> ·
<a href="docs/findings/INDEX.md">Results of record</a>
</p>

# LLM-Aided-PQC

**Report-guided RTL optimization for post-quantum cryptographic hardware.**

Start from existing RTL, locate a top-level timing bottleneck, and ask an LLM to propose a constrained edit. Deterministic code applies the edit, runs design-specific tests, rebuilds the complete design, and evaluates the result. Investigate a submodule only when top-level evidence justifies it.

The repository contains FPGA experiments for ML-DSA/Dilithium, HQC, and SLH-DSA/SPHINCSLET, plus ASIC synthesis experiments. It now also includes a pinned, Apache-2.0 [Adam's Bridge ML-KEM-1024 reference](third_party/adams_bridge/README.md), a unified ML-KEM/ML-DSA engine whose ML-KEM-1024 API passed 80 official ACVP sample cases locally. Licensed-tool synthesis remains unrun. Historical measurements and their limitations remain in the [findings index](docs/findings/INDEX.md). This software update does not regenerate or certify those results.

For setup, begin with [offline checks](#quick-start) and the
[installation guide](docs/REPRODUCE.md). Check [design coverage](docs/PROJECT_STATUS.md)
before running hardware tools. [Release review](docs/RELEASE_CHECKLIST.md) remains
open for historical vendor databases/logs and third-party notices; this update
does not clear those files for redistribution.

## Current capabilities

| Flow | Tool | Status |
|---|---|---|
| FPGA measurement and supported edit dispatch | AMD Vivado | Existing design-specific flow with transactional rollback and source checks |
| Fixed-period ASIC logic synthesis | Cadence Genus | Configurable generated flow; licensed site qualification required |
| Fixed-period ASIC logic synthesis | Synopsys Design Compiler | New generated flow; mock-tested, licensed qualification required |
| Whole-design optimization controller | FPGA / Genus / DC adapters | Offline-tested bounded search; real tool and path-mapping qualification required |
| ASIC place-and-route | Not implemented | No physical-design result claimed |

> [!IMPORTANT]
> This is research software. Functional tests cover exercised inputs, not all-input equivalence, constant-time security, or physical leakage. Some legacy FPGA scripts retain site-specific external source paths. EDA tools, licenses, PDKs, and target cell libraries must be supplied separately. Historical binary design snapshots remain in the repository pending review.

## Framework

<img src="docs/assets/framework.svg" alt="Top-down RTL optimization with separate FPGA and ASIC evidence" width="100%">

**Measure → locate → propose → apply → check → rebuild → decide.**

The FPGA driver snapshots all configured source trees and its checkpoint before dispatch. A rejected or failed candidate restores the pre-run files, including existing local changes. Candidate source hashes must remain unchanged across testing and implementation. HQC joint simulation now stages a private workspace rather than copying over the live candidate.

These safeguards protect cooperating workflows, not hostile executables. Use a dedicated checkout; do not run unrelated jobs in it concurrently. The standalone ASIC runner measures a supplied RTL version. The separate [whole-design controller](docs/WHOLE_DESIGN.md) can coordinate proposals, correctness checks, matched full-design measurements, and acceptance through explicitly configured adapters. Its built-in LLM proposer is opt-in. Actual site tools, complete design tests and timing-path ownership must be qualified before execution.

## Quick start

Use Python 3.10 or newer. From a checkout, these commands need no EDA license,
API key, or third-party Python package:

```bash
git clone https://github.com/hsc-research/LLM-Aided-PQC.git
cd LLM-Aided-PQC
python3 -m venv .venv
source .venv/bin/activate
python3 -m agent doctor --json
python3 -m agent list --json
python3 -m agent smoke
python3 -m unittest discover -s tests -v
python3 tools/check_docs.py
```

The tests use `tclsh` for Tcl checks. See [installation](docs/REPRODUCE.md) for
OS packages and optional Python extras. `doctor` reports missing hardware
dependencies; an offline smoke pass is not an RTL simulation or PPA result.

### Whole-design-first optimization

Use the [whole-design guide](docs/WHOLE_DESIGN.md) for the new bounded search:
verify the baseline, inspect several complete-design critical paths, select a
small responsible RTL region, propose an edit, then verify and remeasure the
entire candidate. Only measured improvements under the fixed constraints are
retained. Block-only gains never decide acceptance.

```bash
# Read-only preparation. The example deliberately reports missing site inputs.
python3 -m agent.whole_design --config configs/whole_design.example.json
```

Configure the actual source closure, correctness coverage, libraries, tool
settings and reviewed timing-path extractor before using `--execute`.
Built-in helpers cover opt-in LLM proposals, ASIC measurements, and the existing
ML-DSA KeyGen gate. FPGA normalized measurement still requires a site adapter.
Offline controller tests do not establish a working end-to-end vendor flow.

### FPGA

Use Python 3.10 or later on Linux, a working Vivado installation, and the source dependencies in the [reproduction guide](docs/REPRODUCE.md). Model calls additionally require the `llm` extra, `PQC_ENABLE_LLM=1`, and `ANTHROPIC_API_KEY`; never commit credentials. Such calls can send RTL and timing reports to an external provider and incur charges.

```bash
# Show the intended command without launching Vivado.
python3 -m agent.run --target fpga --design hqc --dry-run

# Measure the complete design and recommend a target. This launches Vivado.
python3 -m agent.run --target fpga --design hqc

# One supported proposal, test, and full-design reimplementation round.
python3 -m agent.run --target fpga --design hqc --dispatch
```

HQC top-level candidate verification requests all three security levels. Direct `joint_kat_gate.py` calls still default to HQC-128. ML-DSA's full-design test exercises key generation; SLH-DSA's [standalone differential gate](agent/slh_dsa/README.md) now selects the matching frozen reference for all six SHA2 sets, including the unchanged 192f candidate; no fresh RTL pass or independent FIPS 205 validation is claimed. SLH-DSA's generic dispatch remains unavailable. Read the [agent guide](agent/README.md) before automated runs.

### Choose an ASIC synthesis tool

Copy and edit [the example configuration](configs/butterfly_asic.example.json). Supply `ASAP7_LIB_DIR` for Genus `.lib` files or `ASAP7_DB_DIR` for matching compiled DC `.db` files, and review the example SDC. Libraries must come from your own installation.

```bash
# Inspect generated Tcl. Declared input and library files must exist.
python3 -m agent.run --target asic --synth-tool genus \
  --config configs/butterfly_asic.example.json --dry-run

# Cadence Genus
python3 -m agent.run --target asic --synth-tool genus \
  --config configs/butterfly_asic.example.json

# Synopsys Design Compiler
python3 -m agent.run --target asic --synth-tool dc \
  --config configs/butterfly_asic.example.json
```

### ML-KEM reference baseline

[Adam's Bridge v2.0.3](third_party/adams_bridge/README.md) is pinned with license,
source hashes, a whole-core wrapper including memories, and 80 official FIPS203
ACVP cases. Its area scope is the unified ML-KEM-1024 / ML-DSA-87 accelerator.
The [recorded baseline run](docs/verification/mlkem-adams-bridge-acvp-2026-10-12.json)
passed all 80 cases and 39,840 checks with clean Verilator 5.032 exits, including
five implicit rejections. This is sampled RTL evidence, not NIST certification,
ML-DSA verification, four-state simulation, or a synthesis/PPA result.
Source import is complete; full RTL simulation and vendor qualification are
separate gates. It is not yet an automatic LLM optimization target.

```bash
# No EDA required: verify unchanged upstream files and vector integrity.
python3 third_party/adams_bridge/integration/verify_sources.py

# Full ACVP simulation, requiring a compatible installed Verilator.
python3 tools/run_mlkem_adams_bridge_kat.py --simulator verilator

# Baseline-only OOC synthesis. Supply your FPGA part and chosen target period.
# 10 ns is an example constraint, not a measured performance result.
vivado -mode batch \
  -source third_party/adams_bridge/integration/vivado_synth.tcl \
  -tclargs "$FPGA_PART" 10 runs/mlkem-adams-baseline-synth
```

The simulation gate returns nonzero when blocked, not compiled, timed out, or
incorrect. Icarus currently rejects upstream SystemVerilog. For ASIC, copy
[the full-design example](configs/mlkem_adams_bridge_asic.example.json), supply
your own `.lib`/`.db` libraries and reviewed timing/load settings, then use
`python3 -m agent.run --target asic --synth-tool genus --config <your-config>`
or select `dc`. See the [baseline setup](third_party/adams_bridge/README.md#launch-preparation)
for exact preparation steps and comparison boundaries.

`--synth-tool` overrides the configuration's `synthesis_tool`. Missing tools or licenses fail the run; there is no fallback to another vendor. See [ASIC setup, units, and outputs](asic/README.md).

## Documentation

| Need | Start here |
|---|---|
| Agent entry points and verification scope | [Agent README](agent/README.md) |
| Genus or Design Compiler configuration | [ASIC README](asic/README.md) |
| Fresh setup and hardware limits | [Installation](docs/REPRODUCE.md), [FPGA guide](docs/FPGA.md), [design coverage](docs/PROJECT_STATUS.md) |
| Historical measurements | [Result-reading guide](docs/RESULTS.md), then [dated findings](docs/findings/INDEX.md) |
| Source and experiment navigation | [Repository layout](docs/REPOSITORY_LAYOUT.md) |
| Transformation rules | [Optimization taxonomy](docs/02_optimization_taxonomy.md) |
| New-design onboarding | [Architecture guide](docs/AGENT_ARCHITECTURE.md) |
| Fixes, tests, and remaining limits | [Update notes](docs/UPDATE_NOTES.md) |
| All guides | [Documentation hub](docs/README.md) |

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The regression suite uses temporary files, mock tool executables, and Tcl command stubs. It requires Python and `tclsh`, but no API key or EDA license. It does not establish actual synthesis, simulation, PPA, or compatibility with every EDA release.

## Licensing and attribution

See [LICENSE](LICENSE), [NOTICE](NOTICE), and the [release checklist](docs/RELEASE_CHECKLIST.md). Preserve upstream source headers and licensing terms. Existing records distinguish human-authored changes, agent-selected rules, and agent-proposed extensions. The imported ML-KEM reference has explicit provenance; its 80-case ML-KEM RTL evidence is recorded, while licensed-tool/PPA qualification remains open.

[CONTRIBUTING.md](CONTRIBUTING.md) covers checks and RTL changes;
[SECURITY.md](SECURITY.md) covers research limits and data handling. Cite the
exact checkout using [CITATION.cff](CITATION.cff).

`build/` contains tracked HQC experiment inputs. The current `make clean`
preserves them; legacy build targets can still replace sources. See the
[layout guide](docs/REPOSITORY_LAYOUT.md) before regenerating a tree.
