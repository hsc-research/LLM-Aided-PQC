# Repository map

[Project home](../README.md) · [Documentation](README.md) · [Learn](LEARN.md) · [Run](REPRODUCE.md)

The research tree is kept compatible with existing scripts. The top-level
README and documentation index provide the maintained navigation; source
snapshots and dated reports retain their paths.

## Find the right kind of file

| If you need… | Start here |
|---|---|
| The main explanation | [README](../README.md) and [learning guide](LEARN.md) |
| Current support and actual checks | [Design status](PROJECT_STATUS.md) and [verification record](VERIFICATION.md) |
| Historical measured improvements | [Results guide](RESULTS.md), then [dated findings](findings/INDEX.md) |
| A command you can run now | [Staged run guide](REPRODUCE.md) |
| Command-line and optimization code | [Agent workflows](../agent/README.md), `agent/whole_design.py`, `agent/asic_synthesis.py` |
| Test harnesses and test data | [Harness index](../verification/README.md), `tests/`, and the design-specific source rows below |
| Tool configuration examples | [configs/](../configs/) and [ASIC setup](../asic/README.md) |

## Design source map

| Design | Reference inputs | Edited/experimental sources | Test entry point |
|---|---|---|---|
| ML-KEM | [Pinned Adam's Bridge](../third_party/adams_bridge/README.md) | No separate accepted optimized baseline; use an isolated copy when testing edits | [Independent ACVP harness](../verification/mlkem_adams_bridge/README.md) |
| ML-DSA | [Pinned ML-DSA-OSH](../third_party/mldsa_osh/README.md) | [FPGA overrides](../agent/mldsa/mldsa_src/), [ASIC arms](../asic/arms/) | [Run commands](REPRODUCE.md#ml-dsa) |
| HQC | [Preferred SAC 2026 snapshot](../third_party/hqc_sac2026/README.md); [legacy SAC 2023 reference](../hardware/) | Earlier tracked [operation/joint-design trees](../build/) and [ASIC arms](../asic/arms/) | [Source-only boundary and legacy commands](REPRODUCE.md#hqc) |
| SLH-DSA | [Pristine source/data](../agent/slh_dsa/pristine/) | [Edited source/data](../agent/slh_dsa/slh_src/) | [Selected-mode checker](../agent/slh_dsa/README.md) |

“Reference” means a preserved source version. It does not by itself mean
certified, fully tested or licensed-tool qualified. A candidate is not a new
baseline until its exact bytes pass the required checks and matched measurement.

## Sources and flow code

| Location | Role | Editing rule |
|---|---|---|
| `hardware/` | Legacy SAC 2023 HQC reference RTL and testbenches | Preserve the reference version used by an experiment |
| `third_party/adams_bridge/upstream/` | Pinned unified ML-KEM-1024 / ML-DSA-87 reference | Keep byte-exact; use a separate candidate tree for edits |
| `third_party/adams_bridge/integration/` | Whole-core memory wrapper and ordered source lists | Review measured boundary and tool settings |
| `third_party/hqc_sac2026/upstream/` | Preferred pinned SAC 2026 source-only HQC snapshot | Keep byte-exact; no qualified executable adapter supplied |
| `third_party/mldsa_osh/upstream/` | Pinned ML-DSA RTL, common data and KeyGen/Sign/Verify test inputs | Preserve baseline and retained license notices |
| `verification/mlkem_adams_bridge/` | Independent ML-KEM testbench and gate documentation | Checker inputs are immutable during optimization |
| `build/keygen/`, `build/encap/`, `build/decap/`, `build/joint_design/` | Tracked HQC experiment sources | These are inputs, despite the directory name |
| `agent/mldsa/mldsa_src/` | Modified ML-DSA RTL | Flows overlay files on the bundled reference or an explicit `MLDSA_ROOT` override |
| `agent/slh_dsa/pristine/` | SLH-DSA baseline RTL and data | Keep separate from edits |
| `agent/slh_dsa/slh_src/` | SLH-DSA modified RTL | Match the selected parameter set and test data |
| `asic/arms/` | Baseline and edited source snapshots for ASIC experiments | Identify the exact arm, missing inputs, and memory treatment |
| `asic/portfix_wip/` | Historical portability work | Not a validated release source set |
| `agent/backends/` | Existing Vivado and Genus adapters | Some workflows remain site-specific |
| `agent/port/` | Historical cross-tool portability experiments | Review their gates and source targets before running |

See [ASIC setup](../asic/README.md) for the portable ASIC entry point and
[project status](PROJECT_STATUS.md) for missing hardware inputs.

## New run outputs

| Location | Contents | Handling |
|---|---|---|
| `.pqc_runs/` | Isolated checks, candidate transactions, recovery snapshots and user-selected run reports | Local run state; inspect failed-run/recovery evidence before removing |
| `runs/asic/<tool>-<uuid>/` | New ASIC manifests, logs, generated Tcl, reports, netlists and `result.json` | Keep baseline/candidate runs separate |
| `build/mlkem_adams_bridge*/` | Default ML-KEM compilation/simulation workspaces | Generated outputs; distinct from the tracked HQC `build/` subtrees |
| `configs/*.local.json` | User-specific paths, tools and constraints | Ignored local configuration; keep secrets outside the checkout |

A filename such as `report.json` is meaningful only with its run directory,
source hashes and final status. Do not reuse old PASS output after a failed run.

## Results and records

- `agent/*.jsonl` and scheme subdirectories retain proposal and outcome logs.
- `logs/` and `synth_out/` retain implementation reports used in findings.
- `asic/results/` retains older ASIC runs, including limited block studies.
- `docs/verification/` stores shareable local test evidence and machine-readable records.
- `docs/findings/` explains individual experiments, corrections, and limits.
- `docs/handoffs/` records historical session state; it is not an install guide.
- `docs/paper/` contains historical manuscript drafts.

Tracked result files remain tracked even if a broad `.gitignore` pattern also
matches them. Do not delete an apparent build product until you have checked
whether a finding cites it.

## Legacy root scripts

The root `Makefile`, `project_poly_mult.tcl`, and `synth_*.tcl` files belong to
the original HQC/Vivado flow. They are retained because commands and scripts
may depend on their paths. They are not the offline quickstart or the new ASIC
entry point. Several root Tcl scripts contain machine-specific source paths.

The current `make clean` removes only `.Xil` and the named simulation project
directories; it preserves tracked `build/` files. Historical versions deleted
that tree. The legacy build targets can still replace edited RTL with reference
copies. Use a disposable checkout when investigating that flow.

A future directory move should update all Python, Tcl, Makefile, and document
references in the same change, then rerun the affected hardware flow. Moving
files merely for appearance would make existing experiments harder to repeat.
