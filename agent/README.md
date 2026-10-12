# Agent workflows

[Project](../README.md) · [Documentation](../docs/README.md) · [ASIC tools](../asic/README.md)

See [agent status and next improvements](../docs/AGENT_STATUS.md) for the current
dispatch coverage, objective and feedback gaps, and a prioritized roadmap.

The new [whole-design controller](../docs/WHOLE_DESIGN.md) implements bounded
critical-path-guided search with full-design admission, latency and area guards,
and explicit adapter qualification. Use its read-only plan before execution.
The older FPGA driver below remains a one-round, design-specific entry point.

## Entry points

| Command | Purpose |
|---|---|
| `python3 -m agent doctor --json` | Inspect optional tools, design inputs, and current blockers without running hardware tools |
| `python3 -m agent list --json` | List four-scheme support and verification limits |
| `python3 -m agent smoke` | Exercise edit preview, application, rejection, and restoration in temporary files |
| `python3 -m agent.run --target fpga --design hqc` | Top-level Vivado measurement and target recommendation |
| `python3 -m agent.whole_design --config FILE` | Read-only plan for the new whole-design controller; add `--execute` only after adapter qualification |
| Add `--dispatch` | One supported edit, test, rebuild, and acceptance round |
| `python3 -m agent.run --target asic --synth-tool genus --config FILE` | Genus fixed-period measurement |
| Replace `genus` with `dc` | Design Compiler fixed-period measurement |
| `python3 agent/hqc/joint_kat_gate.py --all` | HQC joint-design consistency test at all three levels |

The offline commands above use only the Python standard library. The regression
suite also uses `tclsh`; see [installation](../docs/REPRODUCE.md). Model-backed
runs additionally require the `llm` extra, `PQC_ENABLE_LLM=1`, and an API key.
They may send design excerpts and reports to the configured provider.

The chip driver verifies the baseline before synthesis or dispatch, then checks
that the same source bytes survive verification and measurement. HQC baseline
checks explicitly select the pristine joint-design manifest; candidate checks
use the optimized manifest.

`chip_orchestrator.py` remains the FPGA driver. `run.py` selects the flow; `asic_synthesis.py` handles ASIC configuration, Tcl generation, report parsing, and run records. Legacy `backends/` and `asic/asap7/` scripts remain for historical reproduction; the new runner does not use their hard-coded SSH or PDK configuration.

## Candidate protection

`run_safety.py` snapshots source scopes and the checkpoint before dispatch. Rejection, failed checks, non-improving timing, exceptions, and timeouts restore the original state, including paired changes, new files, and pre-existing uncommitted content. Accepted RTL remains in the working tree for review; the driver does not commit to Git. Logs remain outside the restored scopes. A checkout lock prevents two top-level drivers from colliding.

HQC joint testing stages the effective integrated-synthesis sources in a private workspace instead of restoring Git HEAD or overwriting live sources. Both required HDL defines are set together. The gate records source hashes; the parent driver checks the effective source selection before and after verification and implementation.

## Scope and limits

HQC checks shared-secret consistency, not independent official response vectors. ML-DSA uses the existing key-generation testbench. The standalone [SLH-DSA checker](slh_dsa/README.md) selects the actual SHA2 parameter set and compares its entire frozen vendor stream. All six SHA2 sets are supported, including the current 192f candidate; SHAKE is rejected. Vendor testbench, inputs and reference hashes are pinned. No fresh RTL pass or independent FIPS 205 validation is claimed. The historical six-mode sweep is a separate experiment record. Recorded cycles are evidence; there is no universal constant-time proof or general cycle-profile admission check in this driver.

Use a dedicated checkout. The top-level transaction protects its configured
scopes; do not assume every legacy standalone entry point has equivalent
protection. Source snapshots remain under `.pqc_runs/` if an abrupt kill or
power loss prevents restoration. See [migration and validation notes](../docs/UPDATE_NOTES.md).
