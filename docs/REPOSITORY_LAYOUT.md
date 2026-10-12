# Repository layout

The research tree is kept compatible with existing scripts. The top-level
README and documentation index provide the maintained navigation; source
snapshots and dated reports retain their paths.

## Sources and flow code

| Location | Role | Editing rule |
|---|---|---|
| `hardware/` | HQC reference RTL and testbenches | Preserve the reference version used by an experiment |
| `build/keygen/`, `build/encap/`, `build/decap/`, `build/joint_design/` | Tracked HQC experiment sources | These are inputs, despite the directory name |
| `agent/mldsa/mldsa_src/` | Modified ML-DSA RTL | Existing flows overlay files on a separately supplied upstream tree |
| `agent/slh_dsa/pristine/` | SLH-DSA baseline RTL and data | Keep separate from edits |
| `agent/slh_dsa/slh_src/` | SLH-DSA modified RTL | Match the selected parameter set and test data |
| `asic/arms/` | Baseline and edited source snapshots for ASIC experiments | Identify the exact arm, missing inputs, and memory treatment |
| `asic/portfix_wip/` | Historical portability work | Not a validated release source set |
| `agent/backends/` | Existing Vivado and Genus adapters | Some workflows remain site-specific |
| `agent/port/` | Historical cross-tool portability experiments | Review their gates and source targets before running |

See [ASIC setup](../asic/README.md) for the portable ASIC entry point and
[project status](PROJECT_STATUS.md) for missing hardware inputs.

## Results and records

- `agent/*.jsonl` and scheme subdirectories retain proposal and outcome logs.
- `logs/` and `synth_out/` retain implementation reports used in findings.
- `asic/results/` retains older ASIC runs, including limited block studies.
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
