# Install and reproduce

This guide separates Python tooling checks from RTL simulation and hardware
implementation. A clean Python test run does not reproduce the FPGA or ASIC
results. See [project status](PROJECT_STATUS.md) before choosing a design.

## 1. Get a checkout and Python

The supported setup path is a Linux shell with Git and Python 3.10 or newer.
On Debian/Ubuntu, install the base packages if they are missing:

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
```

Use the repository root as the working directory. Several research scripts
still resolve paths relative to it. Keep a separate checkout for new hardware
experiments so they cannot overwrite a recorded baseline.

The Python checks below need no third-party packages; some flow tests also use
`tclsh`, provided by the Tcl package. Once Git and Python are
installed and this checkout is available, they run offline. Installing optional
packages or downloading upstream hardware inputs requires network access.

## 2. Run the offline checks

```bash
python3 -m agent --help
python3 -m agent doctor --json
python3 -m agent smoke
python3 -m unittest discover -s tests -v
python3 -m compileall -q agent tools tests
python3 tools/check_docs.py
```

- `doctor` inventories optional executables and design inputs. Read missing
  requirements before attempting a hardware run. It does not contact an LLM,
  launch synthesis, or prove that a license server is usable.
- `smoke` exercises the edit machinery in temporary files.
- The unit tests check Python behavior, including rejected edits and parsed
  reports. They do not replace a simulator or formal equivalence check.
- `check_docs.py` checks local Markdown link targets; it does not verify remote
  websites or whether an old experiment's result is correct.

Record the checkout with `git rev-parse HEAD` when reporting a test or result.
A missing optional tool should be reported as missing, not as a failed RTL
check or a passing hardware experiment.

## 3. Optional Python installation

Direct `python3 -m agent` commands work from the checkout without installation.
For an editable package installation:

```bash
python3 -m pip install --no-build-isolation --no-deps -e .
```

This local installation requires a suitable `setuptools` already installed.
Without it, use the checkout commands or install build prerequisites first.
Install extras only for the feature you
intend to use:

```bash
python3 -m pip install -e '.[dashboard]'
# Optional, for intentionally running a paid model-backed experiment:
python3 -m pip install -e '.[llm]'
```

The LLM extra is not needed for setup, tests, log review, or synthesis. Do not
put API keys in Git, prompts, or result logs. Existing model-backed scripts
can send RTL and timing reports to a provider and incur charges; review the
script, intended inputs, and run budget before starting one. Model-backed
commands additionally require `PQC_ENABLE_LLM=1` and `ANTHROPIC_API_KEY` in the
process environment. Keep credentials outside the checkout. The quickstart
never starts a paid experiment.

## 4. Choose a hardware flow

### FPGA with AMD Vivado

Read [FPGA.md](FPGA.md). The historical records used Vivado 2025.2 and Artix-7
`xc7a200tfbg676-1`. Install the vendor tools separately and follow the vendor's
supported OS and library requirements. Source the `settings64.sh` belonging to
your installation and confirm `vivado -version`.

Do not create compatibility symlinks between different major versions of
system libraries. Earlier local setup notes included such a workaround; it is
not part of this installation guide. WSL-specific historical paths are not
portable defaults.

### ASIC with Synopsys Design Compiler or Cadence Genus

Read the [ASIC guide](../asic/README.md). Supply a licensed tool installation,
permitted target libraries, source inputs, and timing constraints locally.
A generated Tcl file or dry run demonstrates preparation only. It does not
establish successful elaboration, mapped area, timing, or power.

## 5. Preserve source snapshots and results

- `build/` contains tracked HQC RTL. Legacy Makefile
  build targets can replace it. The current `make clean` preserves tracked
  `build/` inputs and removes only named simulation workspaces.
- Keep baseline and edited sources separate. Do not copy edited RTL into a
  baseline directory.
- Do not overwrite historical reports to make a new run appear reproduced.
  Use a new output directory and record the source commit, exact command,
  tool version, library, constraints, and check coverage.
- Review `git status --short` after running a research script.
- Follow [RESULTS.md](RESULTS.md) when comparing measurements.

## Troubleshooting

| Symptom | Next check |
|---|---|
| `No module named agent` | Run from the checkout root or install the package in the active environment |
| `No module named flask` or `anthropic` | Install the corresponding optional extra only if that feature is needed |
| `vivado`, `dc_shell`, or `genus` missing | Load the tool environment provided by your institution/vendor, then rerun `doctor` |
| `/mnt/c/PQC/...` path missing | A historical script still needs local path configuration; consult the per-design status before editing paths |
| ML-DSA testbench, KAT files, or ROM data missing | Obtain the matching upstream inputs; do not substitute an empty file or omit the check |
| Old report exists after a failed tool run | Treat it as stale; use a new output directory and inspect the process exit status |
| No signature or shared-secret output | Treat the run as failed or incomplete; missing output is never a passing comparison |

If a result cannot be reproduced, report the first missing input or failed
stage and attach its log. Do not replace an unrun result with an estimate.
