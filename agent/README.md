# Agent workflows

[Project](../README.md) · [Documentation](../docs/README.md) · [ASIC tools](../asic/README.md)

## Entry points

| Command | Purpose |
|---|---|
| `python3 -m agent.run --target fpga --design hqc` | Top-level Vivado measurement and target recommendation |
| Add `--dispatch` | One supported edit, test, rebuild, and acceptance round |
| `python3 -m agent.run --target asic --synth-tool genus --config FILE` | Genus fixed-period measurement |
| Replace `genus` with `dc` | Design Compiler fixed-period measurement |
| `python3 agent/hqc/joint_kat_gate.py --all` | HQC joint-design consistency test at all three levels |

`chip_orchestrator.py` remains the FPGA driver. `run.py` selects the flow; `asic_synthesis.py` handles ASIC configuration, Tcl generation, report parsing, and run records. Legacy `backends/` and `asic/asap7/` scripts remain for historical reproduction; the new runner does not use their hard-coded SSH or PDK configuration.

## Candidate protection

`run_safety.py` snapshots source scopes and the checkpoint before dispatch. Rejection, failed checks, non-improving timing, exceptions, and timeouts restore the original state, including paired changes, new files, and pre-existing uncommitted content. Accepted RTL remains in the working tree for review; the driver does not commit to Git. Logs remain outside the restored scopes. A checkout lock prevents two top-level drivers from colliding.

HQC joint testing stages the effective integrated-synthesis sources in a private workspace instead of restoring Git HEAD or overwriting live sources. Both required HDL defines are set together. The gate records source hashes; the parent driver checks the effective source selection before and after verification and implementation.

## Scope and limits

HQC checks shared-secret consistency, not independent official response vectors. ML-DSA uses the existing key-generation testbench. SLH-DSA compares frozen reference outputs. Recorded cycles are evidence; there is no universal constant-time proof or general cycle-profile admission check in this driver.

Use a dedicated checkout. Legacy standalone optimizers may still use shared temporary paths or Git restores; the new transaction wraps top-level dispatch, not every direct invocation. See [migration and validation notes](../docs/UPDATE_NOTES.md).
