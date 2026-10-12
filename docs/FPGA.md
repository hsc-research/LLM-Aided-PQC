# FPGA reproduction

The historical FPGA studies use AMD Vivado 2025.2 with Artix-7
`xc7a200tfbg676-1`. Vendor software, supported OS libraries, device support,
and any required licensing are separate prerequisites. This guide does not
claim that hardware runs were repeated during the portable Python update.

## Prepare the environment

1. Follow [installation](REPRODUCE.md) and run the offline checks.
2. Load your Vivado installation's `settings64.sh`; confirm `vivado -version`.
3. Run `python3 -m agent doctor --json` and resolve the selected design's missing
   files. For ML-DSA, configure `MLDSA_ROOT` to the matching upstream tree.
   `VIVADO_BIN` can identify its simulator executables when needed.
4. Use a dedicated checkout. Preserve baseline sources and tracked `build/`
   inputs; do not use the legacy Makefile as an initialization step.

## Start with command inspection

```bash
python3 -m agent.run --target fpga --design hqc --dry-run
```

This shows the intended command without launching Vivado. It is not a source,
license, simulation, or implementation pass.

After completing the prerequisites, a top-level HQC measurement uses:

```bash
python3 -m agent.run --target fpga --design hqc
```

Use the [agent guide](../agent/README.md) to select supported designs and
understand source rollback. Adding `--dispatch` starts the supported proposal
workflow; it is not part of installation. Model-backed calls require the
optional dependency, explicit `PQC_ENABLE_LLM=1`, and credentials, and may
send design material to the external provider.

## Functional-check entry points

| Design | Entry point | Coverage to report |
|---|---|---|
| HQC joint KEM | `python3 agent/hqc/joint_kat_gate.py --all` | Shared-secret consistency at HQC-128/192/256; `--all` matters |
| ML-DSA | `python3 agent/mldsa/full_kat_gate.py` | Baseline key-generation tests from the external tree; selected vectors and levels must be recorded |
| ML-DSA edited sources | `python3 agent/mldsa/full_kat_gate.py agent/mldsa/mldsa_src` | Same tests with matching-basename RTL overrides |
| SLH-DSA | `python3 agent/slh_dsa/slh_kat_gate.py` | Configuration-specific differential signature check; inspect [current status](PROJECT_STATUS.md) before running |

Read the selected script's requirements before starting a long simulation.
No missing output, timeout, compilation failure, unsupported mode, or partial
vector run should be reported as a full pass. A passing ML-DSA key-generation
test does not validate signing and verification.

## Timing and reports

The historical flow rebuilds a complete design and uses a bounded post-route
period search. Preserve the report, tool status, source version, constraints,
and search bracket for each probe. The current search no longer downgrades DRC failures. It checks probe
completion, route status, reported setup WNS, and the requested clock period.
These software checks still require licensed-tool qualification and do not turn
a bounded timing search into signoff.

Read [RESULTS.md](RESULTS.md) before comparing runs. For a specific historical
number, follow its [findings entry](findings/INDEX.md) rather than choosing a
command from an unrelated experiment. Baseline and candidate must use the same
recipe, design scope, parameter set, and tool configuration.
