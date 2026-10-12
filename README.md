<p align="center"><img src="docs/assets/banner.svg" alt="LLM-Aided-PQC" width="100%"></p>

# LLM-Aided-PQC

**Use full-design timing reports to guide small RTL changes, then test and measure the complete design again.**

This is a hardware research repository for ML-KEM, ML-DSA, HQC and SLH-DSA.
It contains reference RTL, edited designs, functional test runners, FPGA/ASIC
measurement scripts, and the records of earlier experiments. An optional LLM
proposes edits; Python code applies them, runs checks, and restores rejected
changes. You can read results and run the software checks without a model API
or an EDA license.

## Start here

| I want to… | Read or run |
|---|---|
| Understand the project and the hardware flow | [Learn the project](docs/LEARN.md) |
| See what worked and what was actually tested | [Results](docs/RESULTS.md) → [verification record](docs/VERIFICATION.md) |
| Install and run it step by step | [Run guide](docs/REPRODUCE.md) or the [quick start](#quick-start) below |
| Prepare separate FPGA/ASIC baselines, then optimize each | [Hardware handoff](docs/HARDWARE_HANDOFF.md), [ASIC startup sources](docs/ASIC_STARTUP.md) |
| Find RTL, testbenches, scripts or logs | [Repository map](docs/REPOSITORY_LAYOUT.md) |
| Choose a design and check its limits | [Four-design status](docs/PROJECT_STATUS.md) |
| Browse all documentation | [Documentation index](docs/README.md) |

## What is available

All four design families have source baselines in the checkout. Their tests
and tool support differ; source availability does not mean that every
operation, parameter set or hardware flow has passed.

| Design | Source to start with | Recorded local verification |
|---|---|---|
| ML-KEM | [Adam's Bridge v2.0.3](third_party/adams_bridge/README.md), a **shared ML-KEM-1024 / ML-DSA-87 core with memories** | 80 official ACVP sample cases and 39,840 word/status checks passed with Verilator 5.032; [evidence and limits](docs/VERIFICATION.md#real-ml-kem-baseline-and-rtl-fault-rejection) |
| ML-DSA | [Pinned ML-DSA-OSH source and explicit corrected variants](verification/mldsa_osh/README.md) | Guarded baseline and guarded, encoder-corrected candidate each passed **210 cases**. Original malformed-hint acceptance and candidate signing failure remain recorded. [Evidence and limits](docs/VERIFICATION.md#real-ml-dsa-portable-variants) |
| HQC | [Pinned SAC 2026 source](third_party/hqc_sac2026/README.md) | Source-only import; no functional/PPA qualification or runner integration. [Earlier SAC 2023 flows and review](docs/PROJECT_STATUS.md#hqc-legacy-verification-boundary) remain separate |
| SLH-DSA | [Preserved SPHINCSLET sources and corrected-variant guide](verification/slh_portable/README.md) | Corrected baseline/candidate pairs at **SHA2-128f and SHA2-192f** passed one frozen fixture and live bit-flip rejection per run. Syntax-only variants failed; the other four SHA2 sets were not run. See [current simulation limits](docs/PROJECT_STATUS.md#slh-dsa-baseline-boundary) |

The ML-KEM test exercises only the ML-KEM API of the shared core. It does not
verify that core's ML-DSA function, or make its area a standalone ML-KEM result.
Tests with finite inputs are not certification, exhaustive equivalence, or
side-channel validation.

The dual-target goal is to qualify a baseline on each target before running its
AI-guided optimization loop. FPGA prefers BRAM-compatible inference; ASIC uses
generic RTL memory with standard-cell FF/logic mapping, without a macro compiler.
Source preparation and portable tests do not prove either mapping or licensed
Vivado/DC/Genus compatibility. **Four target-qualified baselines are not yet
complete; HQC SAC 2026 remains blocked and unqualified.** See the
[source-profile commands](docs/HARDWARE_HANDOFF.md#prepare-explicit-target-profiles-without-eda)
and [matched-run procedure](docs/HARDWARE_HANDOFF.md#record-a-fair-comparison).

Historical FPGA results are recorded for ML-DSA, HQC and SLH-DSA. **The new
whole-design controller and Genus/DC flow have software-test coverage, but no
new licensed-tool optimization or PPA result is claimed.** ASIC place-and-route
is not implemented. See [results and comparison rules](docs/RESULTS.md).

## Choose FPGA or ASIC sources

| Design | FPGA original / qualified portable sources | ASIC startup baseline | ASIC startup candidate |
|---|---|---|---|
| ML-KEM | [Pinned unified core](third_party/adams_bridge/README.md), variant `baseline` | Same existing generic-memory unified core via `baseline`; target qualification pending | No separately qualified candidate |
| ML-DSA | Pinned `third_party/mldsa_osh/upstream`; export `guarded-baseline` or `corrected-candidate` | [Frozen guarded startup tree](asic/rtl/mldsa_startup/guarded-baseline), variant `asic-startup-baseline` | [Frozen corrected startup tree](asic/rtl/mldsa_startup/corrected-candidate), variant `asic-startup-candidate` |
| SLH | Preserved `agent/slh_dsa/pristine` / `slh_src`; export the corrected same-mode pair | [Startup exporter](tools/export_slh_asic_verified.py), variant `asic-startup-baseline` through the target exporter | Same exporter, variant `asic-startup-candidate`; match `128f` or `192f` |
| HQC SAC 2026 | [Source-only import](third_party/hqc_sac2026/README.md) | Blocked/unqualified | Blocked/unqualified |

Recommended source preparation, without launching EDA:

```bash
# Preserved FPGA selection.
python3 tools/export_target_profiles.py --design mldsa --variant guarded-baseline \
  --target fpga --out build/profiles/mldsa-fpga
# New ASIC startup source baseline; candidate uses asic-startup-candidate.
python3 tools/export_target_profiles.py --design mldsa --variant asic-startup-baseline \
  --target asic --out build/profiles/mldsa-asic
python3 tools/export_target_profiles.py --design slh --variant asic-startup-baseline \
  --parameter-set 128f --target asic --out build/profiles/slh-128f-asic
python3 tools/export_target_profiles.py --design mlkem --variant baseline \
  --target asic --out build/profiles/mlkem-unified-asic
```

SLH generates each complete same-mode arm into its own exported
`source-bundle/rtl`; `asic/rtl/slh_startup` contains shared templates, not the
whole design. See [all selections, boot protocols and exact evidence](docs/ASIC_STARTUP.md).
The new ML-DSA/SLH startup sources have fresh finite RTL checks and generic FF
structural evidence. Licensed DC/Genus mapping and target-bound optimization
admission remain pending. ML-DSA has tested in-operation boot recovery; SLH
qualifies repeated boot while inactive only.

`asic/arms/` and `configs/mldsa_osh_asic.example.json` retain historical source
selections, not the new startup defaults. Use exported launch configurations
for new runs. Original FPGA source trees and historical paths stay in place.

## Quick start

Use Linux, Git, Python 3.10+ and `tclsh` (the Tcl interpreter used by some tests).
From a new checkout:

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

Expected: `smoke` prints `"status": "PASS"`, the test runner reports `OK`, and
the link checker reports zero errors. Optional simulator-dependent tests can
be skipped when their tools are absent; record skips with the result.
`doctor` may list missing EDA tools. It is an inventory, not a hardware pass.
None of these commands calls a paid API or starts vendor synthesis.

For OS packages, expected outputs, source-integrity checks, actual RTL tests
and troubleshooting, continue with the [staged run guide](docs/REPRODUCE.md).

## How an optimization is checked

1. Choose FPGA or ASIC, test that target's baseline, and measure the **complete
   design** under fixed constraints.
2. Read several worst timing paths and identify the RTL responsible for them.
3. Propose a small edit to those blocks.
4. Apply it in a controlled candidate tree and rerun the required functional tests.
5. Rebuild the complete candidate with the same target, tool, memory policy,
   constraints and source scope.
6. Keep the edit only if the measured result meets the timing, area and cycle
   requirements. Otherwise restore the previous source state.
7. After an accepted edit, inspect the new full-design paths before continuing.

Block-only timing is useful for diagnosis; it does not decide full-design
acceptance. [Learn the flow](docs/LEARN.md#why-start-with-the-complete-design).

### Whole-design-first optimization

The [controller guide](docs/WHOLE_DESIGN.md) explains manifests, test coverage,
critical-path mapping, command adapters, bounded edits and rollback. Start
with its read-only plan:

```bash
python3 -m agent.whole_design --config configs/whole_design.target.example.json
```

The target-bound example intentionally reports `BLOCKED` and exits nonzero until
qualified full-operation and mapped-memory adapters and real site inputs exist.
Do not add `--execute` until sources, checks, libraries,
constraints and adapters have been reviewed. The opt-in LLM proposer may send
RTL and timing reports to an external provider and incur charges.

### Choose the next run

| Stage | Requirements | Instructions |
|---|---|---|
| Verify source integrity | Python only | [Run guide: source checks](docs/REPRODUCE.md#3-check-the-reference-inputs) |
| Simulate RTL | Compatible simulator and the selected test data | [Run guide: RTL tests](docs/REPRODUCE.md#4-run-functional-rtl-tests) |
| Measure an FPGA design | AMD Vivado, device support and matching design inputs | [FPGA guide](docs/FPGA.md) |
| Measure ASIC logic at a fixed period | Cadence Genus or Synopsys Design Compiler, local libraries and reviewed constraints | [ASIC guide](asic/README.md) |
| Test an optimization loop | Qualified full-design test/measurement adapters; optional model access | [Whole-design controller](docs/WHOLE_DESIGN.md) |

## Repository at a glance

```text
hardware/                 Legacy HQC SAC 2023 RTL and testbenches
third_party/              Pinned Adam's Bridge, ML-DSA-OSH and HQC SAC 2026 inputs
agent/                    Python flows and scheme-specific candidate RTL
verification/             Functional test harnesses and their instructions
configs/                  Example constraints and flow configurations
docs/                     Learning, run guides, results and dated findings
build/                    Also contains TRACKED HQC source inputs; preserve them
asic/, logs/, synth_out/  ASIC flows, source snapshots and historical reports
```

[The full map](docs/REPOSITORY_LAYOUT.md) shows which directories are reference
inputs, editable candidates, run outputs and historical evidence. Source and
report paths are deliberately preserved so earlier experiments remain traceable.
Use a dedicated checkout for hardware runs; legacy build targets can replace
sources. The current `make clean` preserves tracked HQC `build/` inputs.

## Contributing and licensing

Run the checks in [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change.
Use [SECURITY.md](SECURITY.md) for research limits and data handling, and
[CITATION.cff](CITATION.cff) when citing an exact checkout.

See [LICENSE](LICENSE), [NOTICE](NOTICE) and the
[release checklist](docs/RELEASE_CHECKLIST.md). Keep upstream notices and pinned
source bytes intact. Review of historical vendor databases/logs and some
third-party notices remains open; retaining those files does not establish
permission to redistribute them. Tools, licenses, PDKs and cell libraries are
supplied separately.
