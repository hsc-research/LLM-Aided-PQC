# Install and run

[Project home](../README.md) · [Documentation](README.md) · [Learn](LEARN.md) · [Results](RESULTS.md)

Run from the repository root. Start with stages 1–3; they do not need an EDA
license or a model API. Stage 4 runs real RTL when its simulator is available.
Stages 5–6 need hardware-tool setup. Stage 7 is an optional optimization flow.
A Python test pass does not reproduce an FPGA or ASIC result.

| Stage | What it establishes | Main output |
|---|---|---|
| 1–2. Setup and software checks | Python tools and checked software behavior work in this checkout | Audit JSON, test summary, link-check summary |
| 3. Reference input checks | Selected pinned source/data bytes are intact | Integrity-check result |
| 4. RTL simulation | The selected operations and inputs pass that checker | Simulator logs and run-specific verdict |
| 5. FPGA measurement | The exact design was implemented under the recorded FPGA settings | Timing, utilization and implementation reports |
| 6. ASIC synthesis | The exact design was synthesized at a fixed constraint | Source manifest, netlist, timing/area reports and `result.json` |
| 7. Optimization | An edited full design passes its tests and measured acceptance rules | Candidate outcome and retained/restored sources |

Use a dedicated checkout for hardware runs. Do not run `make` as a general
initialization step: legacy targets can replace tracked HQC RTL under `build/`.
See the [repository map](REPOSITORY_LAYOUT.md) before moving or cleaning files.

## 1. Get a checkout and Python

Use a Linux shell, Git, Python 3.10+ and Tcl. On Debian/Ubuntu, install these
packages if they are missing:

```bash
sudo apt-get update
sudo apt-get install git python3 python3-venv tcl
```

Then:

```bash
git clone https://github.com/hsc-research/LLM-Aided-PQC.git
cd LLM-Aided-PQC
python3 --version
python3 -m venv .venv
source .venv/bin/activate
git rev-parse HEAD
```

Save the commit ID with your results. Direct `python3 -m agent` commands work
from this checkout without installing the package. Installing OS packages and
optional Python extras needs network access; the software checks themselves
do not download dependencies or contact a model.

## 2. Run the offline checks

```bash
python3 -m agent --help
python3 -m agent doctor --json
python3 -m agent list --json
python3 -m agent smoke
python3 -m unittest discover -s tests -v
python3 -m compileall -q agent tools tests
python3 tools/check_docs.py
```

| Command | Expected result | What it does not prove |
|---|---|---|
| `doctor --json` | `audit_status: completed`, with discovered tools and explicit blockers | No license checkout, synthesis or simulation is performed |
| `list --json` | Four design entries with support descriptions | It does not rerun the listed verification evidence |
| `smoke` | `status: PASS` for preview, apply, rollback and bad-edit rejection | This is a temporary Python edit test, not RTL simulation |
| `unittest` | `OK`; inspect and report any skipped simulator-dependent tests | Mock EDA tests do not establish real hardware results |
| `compileall` | Exit 0; normally no output with `-q` | Syntax compilation does not test behavior |
| `check_docs.py` | Zero local-link errors | It does not fetch remote URLs or verify result claims |

The test suite needs `tclsh` for Tcl checks. Some tests exercise installed open
simulators when present; absent optional tools may cause explicit skips. Do
not report a skipped check as passed. A missing EDA executable in `doctor` is
an environment prerequisite, not an RTL failure.

## 3. Check the reference inputs

These commands validate pinned source/data files and do not run upstream
programs or launch EDA tools:

```bash
python3 third_party/adams_bridge/integration/verify_sources.py
python3 tools/check_mldsa_sources.py
```

- [Adam's Bridge](../third_party/adams_bridge/README.md) includes the unified
  ML-KEM-1024 / ML-DSA-87 RTL, memories and selected official ACVP samples.
- [ML-DSA-OSH](../third_party/mldsa_osh/README.md) includes mixed-language RTL,
  three testbenches, KAT files and `common/zetas.txt`.
- [SLH-DSA's checker](../agent/slh_dsa/README.md) verifies its selected mode,
  protected testbench/input files and frozen expected output during setup.
- The preferred [HQC SAC 2026 snapshot](../third_party/hqc_sac2026/README.md)
  is source-only, with a pinned inventory of 126 unchanged files. No runnable
  verification/synthesis integration is supplied. Earlier HQC experiment
  sources remain separate in the [repository map](REPOSITORY_LAYOUT.md#design-source-map).

Integrity failure must be resolved before simulation. Restore the exact
pinned inputs; do not generate replacement answers or empty ROM data. Preserve
source snapshots and use separate copies for candidates.

## 4. Run functional RTL tests

Choose one design first. Read its current [status](PROJECT_STATUS.md) and
[recorded evidence](VERIFICATION.md), then confirm the required simulator.
These tests do not need a paid LLM. Missing tools, compilation failures,
timeouts, incomplete output and mismatches are not passes.

### ML-KEM

Requires a compatible Verilator installation with timing support and its C++
build tools. The recorded run used Verilator 5.032. No tool is installed by
the runner. Icarus 12 rejects this upstream SystemVerilog source.

```bash
python3 tools/run_mlkem_adams_bridge_kat.py --help
python3 tools/run_mlkem_adams_bridge_kat.py --simulator verilator \
  --work-dir .pqc_runs/reproduce-mlkem
```

Inspect `.pqc_runs/reproduce-mlkem/report.json` and the recorded compile/simulator
logs. Success requires all **80 cases / 39,840 word/status checks** to complete
and the gate to exit 0. `--prepare-only` deliberately returns nonzero because
preparing vectors is not a simulation pass. Use a fresh run directory when
comparing source versions.

Coverage is ML-KEM-1024 only, including KeyGen, encapsulation, decapsulation,
key-input checks and five implicit-rejection samples. The hardware also contains
ML-DSA-87; this test does not validate that function or produce ML-KEM-only
area. Read the [harness contract](../verification/mlkem_adams_bridge/README.md)
and [test limitations](VERIFICATION.md#real-ml-kem-baseline-and-rtl-fault-rejection).

### ML-DSA

The [portable full-design runner](../verification/mldsa_osh/README.md) has two
explicit passing variants. Use GHDL with synthesis/Verilog support, Verilator,
a C++ compiler and make. The recorded toolchain uses GHDL 6.0.0 with pinned
compatibility-library sources and a specifically recorded Verilator build;
[tool identities and setup](verification/mldsa-portable-2026-10-12/toolchain.json)
are part of the evidence. A default Icarus full-datapath run did not complete,
so select Verilator explicitly for the qualified route.

```bash
# Guarded baseline: all 210 cases.
python3 agent/mldsa/portable_kat_gate.py --simulator verilator \
  --canonical-hints --verify-mutations

# Candidate with both explicit corrections: all 210 cases.
python3 agent/mldsa/portable_kat_gate.py --simulator verilator \
  --override agent/mldsa/mldsa_src --encoder-fallthrough \
  --canonical-hints --verify-mutations
```

Expected for each: overall `PASS`, exit 0, and complete counts of 75 KeyGen,
45 Sign, 45 upstream Verify, 12 one-bit tamper cases and 33 canonical-encoding
controls/negatives. Upstream Verify has 9 valid and 36 invalid cases;
flag 0 means accept, flag 1 reject. The added canonical set has 18 valid
controls and 15 invalid cases. Inspect the printed private run directory's
`result.json`, source hashes and simulator logs.

The original baseline passes the 165 upstream cases but fails an added
malformed-hint check. The original 14-file candidate also fails that check
and stalls during signing. The two flags above select semantic corrections
in staged copies; they do not alter the pinned originals or make their
retained failures disappear. Bounded partial-word testbench adaptations and
GHDL translation are also recorded. See [exact evidence](VERIFICATION.md#real-ml-dsa-portable-variants).

The optional [GHDL setup helper](../tools/bootstrap_mldsa_ghdl.py) downloads
hash-pinned official Debian packages into a chosen local directory. It needs
network access, `dpkg-deb` and a compatible Linux x86-64 runtime; it does not
install system packages:

```bash
python3 tools/bootstrap_mldsa_ghdl.py --prefix /tmp/pqc-ghdl
export PATH="/tmp/pqc-ghdl/bin:$PATH"
```

Install/configure Verilator and its C++ build tools separately. The focused
guide explains the recorded build-specific precompiled-header setting;
it is not an RTL fix. Full passing runs are two-state and use pinned upstream
KAT answers, not an independently authenticated complete ACVP corpus. There
is no full four-state or FIPS 204 certification claim.

For the next FPGA/ASIC stage, [export both passing derivatives](HARDWARE_HANDOFF.md#ml-dsa-export-the-passing-derivatives).
Do not measure the old candidate directory or historical ASIC source list
and attach the corrected variant's verification evidence to it.

The separate legacy Vivado gate is **KeyGen-only** and requires `xvhdl`,
`xvlog`, `xelab` and `xsim`:

```bash
python3 agent/mldsa/full_kat_gate.py
python3 agent/mldsa/full_kat_gate.py agent/mldsa/mldsa_src
```

It defaults to 25 vectors per level (75 total); `--vectors` deliberately
reduces coverage. `MLDSA_ROOT` / `--root` overrides must be recorded. Neither
this legacy gate nor the existing optimization adapter automatically selects
the guarded variants or proves signing/verification coverage.

A separate 400-vector Icarus arithmetic-block test remains available:

```bash
python3 tools/check_hdl_smoke.py --output .pqc_runs/hdl-smoke.json
```

It requires the baseline and two injected faults to behave as expected.
That block-only result is independent of the new full-design runs.

### HQC

**The preferred [SAC 2026 baseline](../third_party/hqc_sac2026/README.md) is
source-only and unverified.** It has no supported executable adapter yet.
The commands below target the **older SAC 2023-derived experiment trees**;
they must not be used as evidence for the new source snapshot.

The existing Vivado gate runs standalone KeyGen and encapsulation to generate
inputs, then exercises the joint design's decapsulation/re-encryption path.
It checks shared-secret consistency, not all three joint API operations.
Select both the source set and all three security levels explicitly:

```bash
# Reference joint design
python3 agent/hqc/joint_kat_gate.py --source-key hqc_joint_pristine --all

# Current edited joint design
python3 agent/hqc/joint_kat_gate.py --source-key hqc_joint_opt --all
```

Expected: a shared-secret match for HQC-128/192/256, then the final `JOINT KAT
GATE: PASS` verdict and exit 0. Without `--all`, the direct gate tests HQC-128
only. The gate prints its private run-artifact directory under `.pqc_runs/`.
A shared-secret match is internal consistency; both sides can share a defect.
It is not an independent official known-answer comparison. Static review found unused
rejection-check flags. A staged dynamic rejection probe is **inconclusive**:
changing an input file did not establish that the DUT loaded the changed
ciphertext, and an instrumented attempt produced unknown values. This is not
a confirmed live rejection failure or a pass. The legacy gate does not
establish that invalid ciphertexts are rejected correctly. Read the [exact legacy-source finding](PROJECT_STATUS.md#hqc-legacy-verification-boundary)
before treating this design as a verified baseline.

### SLH-DSA

The selected-mode differential gate requires Vivado's `xvlog`, `xelab` and
`xsim`. It preserves the source tree's SHA2 parameter selection:

```bash
# Unchanged pristine SHA2-128f baseline
python3 agent/slh_dsa/slh_kat_gate.py agent/slh_dsa/pristine

# Current SHA2-192f candidate
python3 agent/slh_dsa/slh_kat_gate.py
```

The gate supports matching frozen references for all six SHA2 sets; SHAKE is
unsupported. It compares the entire vendor output stream, including a padded
message tail, and requires the testbench's verify match. This is differential
evidence, not an independent FIPS 205 KAT. Never switch the candidate's mode
or regenerate a golden stream just to obtain a pass.

Unmodified vendor duplicate declarations prevent a direct Icarus/Verilator
build. A [separate portable runner](../verification/slh_portable/README.md)
stages hash-recorded Icarus adaptations and a live signature-corruption test:

```bash
python3 tools/check_slh_portable.py --rtl-dir agent/slh_dsa/pristine \
  --output .pqc_runs/slh-portable-pristine-128f.json
```

The syntax-only pristine 128f variant has **failed** output/verification checks;
that command must not be presented as an expected passing baseline. The
explicitly corrected baseline and candidate each passed at 128f and at 192f,
using one frozen fixture and a live signature-bitflip rejection check per run:

```bash
python3 tools/check_slh_portable.py --rtl-dir agent/slh_dsa/pristine \
  --parameter-set 128f --fix-auth-sensitivity \
  --output .pqc_runs/slh-portable-baseline-128f.json
python3 tools/check_slh_portable.py --rtl-dir agent/slh_dsa/slh_src \
  --parameter-set 128f --fix-auth-sensitivity \
  --output .pqc_runs/slh-portable-candidate-128f.json

python3 tools/check_slh_portable.py --rtl-dir agent/slh_dsa/pristine \
  --parameter-set 192f --fix-auth-sensitivity \
  --output .pqc_runs/slh-portable-baseline-192f.json
python3 tools/check_slh_portable.py --rtl-dir agent/slh_dsa/slh_src \
  --parameter-set 192f --fix-auth-sensitivity \
  --output .pqc_runs/slh-portable-candidate-192f.json
```

Expected: 2,141 matching words for corrected 128f, or 4,463 for corrected
192f; normal verification flag 0, rejection flag 1 after the captured-signature
mutation, and overall exit 0. The option changes a hash-pinned authentication
path sensitivity list in each staged copy; original sources and frozen
references stay unchanged. Explicit parameter selection changes only staged
configuration copies. The [four-run evidence matrix](HARDWARE_HANDOFF.md#slh-dsa-keep-mode-and-derivative-together)
links the passing source pairs and exact no-EDA export commands for hardware
measurement. These are not unchanged-source or FIPS 205 conformance results. The syntax-only
192f run matched all words but failed valid-signature verification; its
negative control is unqualified. The other four SHA2 sets were not executed.
Compilation, matching bytes alone and partial output are not passes. Read the
[portable variant guide](../verification/slh_portable/README.md) for all
transformations and [current status](PROJECT_STATUS.md#slh-dsa-baseline-boundary)
for exact completed coverage.

## 5. Measure an FPGA design

Start with the [hardware handoff](HARDWARE_HANDOFF.md) to select the exact
verified source derivative. The commands below do not silently redirect
legacy flows to new corrected sources.

Requires AMD Vivado, supported OS libraries and the selected FPGA device files.
The historical records used Vivado 2025.2 and Artix-7 `xc7a200tfbg676-1`.
Source your installation's `settings64.sh`, confirm `vivado -version`, and
resolve the design's inputs before launching. Do not create compatibility
symlinks between incompatible major system-library versions.

```bash
# Command preview: does not launch Vivado.
python3 -m agent.run --target fpga --design hqc --dry-run

# Actual legacy SAC 2023 HQC design measurement: launches Vivado.
python3 -m agent.run --target fpga --design hqc
```

The preview does not validate licenses or source coverage. Read
[FPGA setup and timing](FPGA.md) and the [agent workflow](../agent/README.md)
for the selected design's checks, output records and existing dispatch support.
SLH-DSA generic dispatch is unavailable; ML-KEM is a separate baseline route.
For ML-KEM baseline-only OOC synthesis, use its
[wrapper-specific launch instructions](../third_party/adams_bridge/README.md#launch-preparation).

An implementation pass and timing report are separate from a functional pass.
For a historical result, follow its exact [finding](findings/INDEX.md), source
revision and constraints rather than substituting the latest default command.

## 6. Measure ASIC logic with Genus or DC

Use the [hardware handoff](HARDWARE_HANDOFF.md) for verified derivative exports
and matched baseline/candidate source configuration.

Requires a licensed Cadence Genus or Synopsys Design Compiler installation,
permitted target libraries, a reviewed source list and timing constraints.
This is fixed-period, pre-layout logic synthesis, not ASIC place-and-route.

Choose a matching example:

- [ML-KEM/ML-DSA unified design](../configs/mlkem_adams_bridge_asic.example.json)
- [ML-DSA complete design](../configs/mldsa_osh_asic.example.json)
- [Butterfly block only](../configs/butterfly_asic.example.json)

For example, copy the unified design's configuration and edit the local copy:

```bash
cp configs/mlkem_adams_bridge_asic.example.json configs/mlkem_adams_bridge_asic.local.json
```

Supply actual library paths, tool/version, corner, period, memory model and
site IO/load/uncertainty settings as described in the [ASIC guide](../asic/README.md).
Genus uses `.lib` libraries; DC needs genuine compiled `.db` libraries. Only
then inspect the generated flow:

```bash
python3 -m agent.run --target asic --synth-tool genus \
  --config configs/mlkem_adams_bridge_asic.local.json --dry-run
```

A dry run still requires real declared input/library files. The unconfigured
example is expected to fail rather than invent libraries or skip missing
modules. It does not execute the site Tcl or elaborate RTL.

After reviewing the generated command and Tcl, remove `--dry-run` to run
Genus; replace `genus` with `dc` to choose Design Compiler. There is no silent
fallback between vendors. Outputs go to a fresh `runs/asic/<tool>-<uuid>/`
directory; inspect `result.json`, source hashes, logs and original reports.
`MEASURED` is a parsed tool result, not equivalence, signoff or publication approval.

## 7. Configure an optimization experiment

Start with the [whole-design controller](WHOLE_DESIGN.md), which tests and
measures the full design before and after a small edit:

```bash
python3 -m agent.whole_design --config configs/whole_design.example.json
```

Expected for this unconfigured template: **`BLOCKED` and a nonzero exit** with
missing site inputs listed. This is an intentional guard. Copy it to
`configs/whole_design.local.json`, supply complete test/source manifests,
qualified measurement commands and reviewed path-to-RTL mapping, then rerun
the plan. `CONFIGURED_NOT_RUN` means static setup is present, not that EDA or
functional verification passed.

Only use `--execute` after reviewing those inputs and possible tool/API costs.
The existing FPGA `--dispatch` path is a separate, older one-round workflow;
read the [agent guide](../agent/README.md) before using it.

### Optional Python installation and model use

No package installation is needed for the checkout commands. An editable
installation, with suitable `setuptools` already available, is:

```bash
python3 -m pip install --no-build-isolation --no-deps -e .
pqc-agent smoke
```

Install extras only for an intended feature:

```bash
python3 -m pip install -e '.[dashboard]'
# Only for an intentionally configured model-backed experiment:
python3 -m pip install -e '.[llm]'
```

The LLM extra additionally needs `PQC_ENABLE_LLM=1` and `ANTHROPIC_API_KEY` in
the process environment. Model calls can send RTL/report excerpts to an
external provider and incur charges. Review the inputs and budget; never put
credentials in Git, prompts or result logs. Setup, tests, report review and
standalone synthesis do not need a model key.

## Preserve a useful result

Keep baseline and candidate separate. Write a new output directory and record:

- Source commit, local changes and input hashes
- Exact command, environment overrides and tool version
- Design top, parameter set, operations and completed test count
- Device/library, corner, constraints and memory treatment
- Final exit status, verdict and original report paths

Review `git status --short` after running a research script. Do not overwrite
historical reports or treat stale output as a new result. Follow
[comparison rules](RESULTS.md#fair-comparisons) and the
[evidence-writing standard](DOCUMENTATION_STANDARD.md).

## Troubleshooting

| Symptom | Next step |
|---|---|
| `No module named agent` | Run from the checkout root or install the package in the active environment |
| `tclsh` missing | Install the OS Tcl package before the complete software test suite |
| Optional `flask` or `anthropic` missing | Install only the extra required for the feature you intend to run |
| Simulator or vendor tool missing | Load/install the appropriate tool separately, then rerun `doctor` |
| `/mnt/c/PQC/...` missing | A legacy script needs local path configuration; follow the selected design guide |
| ML-DSA vectors, ROM data or testbench missing | Run `check_mldsa_sources.py`; check an unintended `MLDSA_ROOT` override and restore pinned inputs |
| SLH mode/reference/input rejection | Match the selected SHA2 mode and unchanged protected inputs; SHAKE remains unsupported |
| `BLOCKED` from the controller template | Supply the missing real site inputs; do not create placeholders to force a pass |
| Stale report after failure | Use a fresh output directory and inspect the process exit status |
| Missing signature or shared secret | Treat the simulation as incomplete or failed, never a passing comparison |

Report the first missing prerequisite or failing stage and preserve its log.
Do not replace an unrun measurement with an estimate.
