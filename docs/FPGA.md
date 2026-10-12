# FPGA reproduction

[Project home](../README.md) · [Documentation](README.md) · [Run guide](REPRODUCE.md) · [Results](RESULTS.md)

The historical FPGA studies use AMD Vivado 2025.2 with Artix-7
`xc7a200tfbg676-1`. Vendor software, supported OS libraries, device support,
and any required licensing are separate prerequisites. This guide does not
claim that hardware runs were repeated during the portable Python update.

The `hqc` / `hqc_baseline` design keys and legacy joint gate below still use
SAC 2023-derived sources. The preferred [SAC 2026 HQC snapshot](../third_party/hqc_sac2026/README.md)
is a separate source-only import with no qualified executable adapter. These
commands and historical results do not verify that newer snapshot.

For newly corrected ML-DSA/SLH variants, use the [hardware handoff](HARDWARE_HANDOFF.md)
first. Legacy commands do not automatically select the staged corrections.
Current portable functional evidence is separate from vendor-tool qualification.

## Prepare the environment

1. Follow [installation](REPRODUCE.md) and run the offline checks.
2. Load your Vivado installation's `settings64.sh`; confirm `vivado -version`.
3. Run `python3 -m agent doctor --json` and resolve the selected design's missing
   files. ML-DSA defaults to the pinned bundled ML-DSA-OSH tree; use
   `MLDSA_ROOT` only when intentionally selecting another matching tree.
   Run `python3 tools/check_mldsa_sources.py` to verify the bundled inputs.
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
| ML-DSA | `python3 agent/mldsa/full_kat_gate.py` | Bundled baseline KeyGen: 25 vectors at each of II/III/V by default, 75 total; report any reduced `--vectors` coverage |
| ML-DSA portable corrected variants | [Run and export instructions](HARDWARE_HANDOFF.md#ml-dsa-export-the-passing-derivatives) | 210 full-design cases per named derivative; no new Vivado implementation or automatic legacy dispatch routing |
| ML-DSA edited sources | `python3 agent/mldsa/full_kat_gate.py agent/mldsa/mldsa_src` | Same tests with matching-basename RTL overrides |
| SLH-DSA pristine baseline | Explicit command below | SHA2-128f vendor-output comparison plus testbench verify match; not an independent FIPS 205 oracle |
| SLH-DSA current candidate | `python3 agent/slh_dsa/slh_kat_gate.py` | SHA2-192f complete vendor-stream comparison against its pinned 192f reference and verify match; not independent FIPS 205 validation |
| SLH-DSA portable corrected pairs | [Run and export instructions](HARDWARE_HANDOFF.md#slh-dsa-keep-mode-and-derivative-together) | Both arms passed the fixed fixture and live rejection control at 128f and 192f; vendor implementation remains the next stage |

Read the selected script's requirements before starting a long simulation.
No missing output, timeout, compilation failure, unsupported mode, or partial
vector run should be reported as a full pass. A passing ML-DSA key-generation
test does not validate signing and verification.

Use this command from the repository root for the unchanged SLH-DSA baseline:

```bash
python3 agent/slh_dsa/slh_kat_gate.py agent/slh_dsa/pristine
```

ML-DSA requires `xvhdl`, `xvlog`, `xelab` and `xsim`; SLH-DSA requires the
last three. The [ML-DSA source import](../third_party/mldsa_osh/README.md) and
[SLH source/hash checks](PROJECT_STATUS.md#slh-dsa-baseline-boundary) do not
constitute new simulation passes. The SLH frozen streams include a padded
message tail; do not treat a stream match as an independently checked bare
standard signature. The gate supports all six SHA2 modes with fixed hashes,
unchanged vendor inputs and complete byte comparison; SHAKE is unsupported.
Both selected candidate and pristine setup reach missing `xvlog` here. Icarus
and Verilator reject vendor duplicate declarations in the unchanged `FSM.v`.
A separate [portable Icarus route](REPRODUCE.md#slh-dsa) has passing,
explicitly sensitivity-corrected 128f/192f derivatives; those are not unchanged
Vivado results. Fresh Vivado simulation and Vivado/DC/Genus qualification remain
pending. See the [gate contract](../agent/slh_dsa/README.md).

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
