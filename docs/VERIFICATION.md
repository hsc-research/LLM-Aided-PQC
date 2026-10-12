# Verification record

Verified locally on 2026-10-12 using Python 3.12.14. These checks validate
software safeguards and one bundled RTL block; they do not establish new
FPGA/ASIC PPA results or complete cryptographic compliance.

## Portable software checks

Run from the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 -O -m unittest discover -s tests -v
python3 -m compileall -q agent tools tests
python3 tools/check_docs.py
python3 tools/check_numbers.py --strict
python3 -m agent smoke
python3 -m agent doctor --json
node --check agent/dashboard_static/app.js
git diff --check
```

- Normal and optimized Python: **203 tests passed** in each run. These include
  mocked EDA processes and Tcl syntax checks, not licensed vendor-tool runs.
- Documentation snapshot before adding this report: **157 local links passed**.
  After adding this report, **159 local links passed** across 90 Markdown files.
- Compilation, installed CLI smoke, JavaScript syntax and diff checks passed.
  JavaScript syntax was checked with Node.js v24.19.0.
- The strict historical-number inventory exited 0: 259 classified citations
  and **154 warning-only unclassified frequency citations**. This is an
  inventory check, not an independent reproduction of those measurements.
- `doctor` completed its audit; missing tools and unsupported scheme/configuration
  combinations remain explicitly blocked. Audit completion does not mean all
  prerequisites are available.

Editable installation was also tested in a local virtual environment with
preinstalled setuptools, without dependency downloads:

```sh
python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --no-index --no-build-isolation --no-deps -e .
.venv/bin/pqc-agent smoke
```

## Real HDL check and negative controls

The optional [HDL smoke runner](../tools/check_hdl_smoke.py) reuses the existing
`coeff_decomposer` testbench and deterministic vector generator. It stages
candidate copies in temporary directories and never rewrites tracked RTL.
With Icarus Verilog compiler **12.0 (stable)** and runtime **12.0 (stable)**:

- Baseline: 200 vectors at `sec_lvl=2` and 200 at `sec_lvl=3`, **400 total**, passed.
- Live arithmetic fault: `dob <= a1_2` changed to `dob <= a1_2 ^ 1` in a copy;
  rejected for an output mismatch with gate exit 1.
- Boundary fault: the `Q` constant changed from 8380417 to 8380416 in a copy;
  rejected for an output mismatch with gate exit 1.
- The mutation checks stop at the first failing level. A compile failure or
  missing simulator is not counted as successful corruption detection.
- SHA-256 checks confirmed that all tracked RTL/testbench/generator inputs
  remained unchanged.

Reproduce with an ordinary Icarus installation on `PATH`:

```sh
python3 tools/check_hdl_smoke.py --output .pqc_runs/hdl-smoke.json
```

A relocated installation can use `--iverilog`, `--vvp`, and `--ivl-base`.
The runner exits 0 only when the baseline and both negative controls behave
as expected. Missing tools produce `UNAVAILABLE` and exit 2; verification
failures produce a nonzero exit. It never installs tools or downloads code.
The checked-in [machine-readable record](verification/hdl-smoke-2026-10-12.json)
contains versions, input hashes, vector counts and outcomes, without private
installation paths or vendor logs. The local record was regenerated using
this checked-in runner.

## Not run and remaining limits

- No Vivado synthesis, place-and-route, or full-design HQC/ML-DSA/SLH simulation
- No licensed Genus or Design Compiler run; no ASIC physical/signoff run
- No paid model/API calls or hosted GitHub Actions
- ML-KEM remains absent; ML-DSA full KeyGen verification needs its external tree
- The checked-in SLH configuration selects 192f; the frozen SHA2-128f gate
  explicitly rejects that mismatch
- HQC gates check legacy shared-secret consistency, not independent standardized
  known-answer responses

Private workspaces and proposal guards support cooperating experiments. They
are not a hostile-code security sandbox. One block's successful corruption
checks do not establish the sensitivity of every other gate or prove
constant-time operation.
