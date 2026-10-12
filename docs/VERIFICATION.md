# Verification record

Verified locally on 2026-10-12 using Python 3.12.14. These checks validate
software safeguards, one bundled ML-DSA RTL block, and the ML-KEM-1024 API
of the pinned unified Adam's Bridge accelerator. They do not establish new
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
git diff --check -- . \
  ":!third_party/adams_bridge/upstream" \
  ":!third_party/mldsa_osh/upstream" \
  ":!third_party/adams_bridge/test_vectors/NIST_ACVP_README.upstream.md"
```

- Final normal and optimized Python: **321 tests passed, zero skipped** in
  each run with Icarus and Verilator available on the test environment's `PATH`.
  Many tests use mocked EDA processes and Tcl syntax checks. These counts are
  software/harness evidence, not 321 independent cryptographic or vendor-tool runs.
- Final documentation check: **214 local links passed** across 92 Markdown files.
- Compilation, installed CLI smoke, JavaScript syntax and first-party diff checks passed.
  Pinned upstream files retain their original whitespace for byte-for-byte provenance;
  they are excluded from the whitespace check above.
  JavaScript syntax was checked with Node.js v24.19.0.
- The strict historical-number inventory exited 0: **271 classified citations**
  across **90 files**, with **157 warning-only unclassified frequency citations**.
  This is an inventory check, not independent reproduction of those measurements.
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

## Real ML-KEM baseline and RTL-fault rejection

The pinned Adam's Bridge v2.0.3 source (commit
`b77e3d899e828d626cfc2a0d26a6b5704cc121e0`) is a unified
ML-KEM-1024 / ML-DSA-87 accelerator with generic SRAM models. The local
qualification exercises its **ML-KEM-1024 API only**. Public FIPS 203 ACVP
samples are pinned to ACVP-Server commit
`975de31eb83d87039ec88934fdc47d8c312b892d`.

Under **Verilator 5.032**, the untouched reference compiled and exited cleanly:

- **80 cases and 39,840 exact word/status checks passed**, comparing 159,040
  output bytes.
- Coverage: 25 KeyGen, 25 encapsulation, 10 decapsulation, 10 encapsulation-key
  checks and 10 decapsulation-key checks; five decapsulation cases exercise
  implicit rejection.
- Two real-DUT diagnostic controls, changing an expected word or an input seed
  bit in isolated command streams, produced the expected output mismatches.
- A separate isolated candidate inserted a synthesizable one-bit fault into
  `abr_ctrl.sv`'s encapsulation-key output path. Compilation succeeded; the
  first KeyGen case produced `0xca23098c` instead of `0xca23098d` at register
  `0xb000`. The simulator exited nonzero and the gate exited **1**. The same
  official commands, protected wrapper and independent testbench were used.
  Reference inputs remained unchanged. This is a rejected faulty candidate,
  not an optimization or PPA gain.

See the [baseline record](verification/mlkem-adams-bridge-acvp-2026-10-12.json),
[baseline output](verification/mlkem-adams-bridge-acvp-2026-10-12.txt),
[RTL-fault record](verification/mlkem-adams-bridge-rtl-fault-2026-10-12.json)
and [fault output](verification/mlkem-adams-bridge-rtl-fault-2026-10-12.txt).
The [gate runner](../tools/run_mlkem_adams_bridge_kat.py) records input hashes,
case accounting and isolated run artifacts. Reproduce the reference run with:

```sh
python3 tools/run_mlkem_adams_bridge_kat.py --simulator verilator \
  --work-dir build/mlkem_adams_bridge_verilator
```

Verilator is two-state; some upstream assertions are disabled under its
configuration. The independent harness output, AHB, timeout and accounting
checks remain active. Icarus 12 rejects upstream unpacked parameter arrays.
Cycle figures include reset settling, AHB transfers and polling, rather than
isolated core latency. Finite ACVP samples do not establish NIST certification,
ML-DSA-87 preservation, exhaustive equivalence, four-state behavior,
constant-time execution, leakage resistance or physical fault resistance.
Any eventual area figure must identify the whole unified engine and memories.

## Source completeness and other scheme gates

- The [ML-DSA input bundle](../third_party/mldsa_osh/README.md) contains **106
  unmodified upstream files / 3,300,503 bytes**, pinned to
  `751009199ac081091a9059805e6921453bde0154`. Offline checks validate every
  Git blob, SHA-256, byte count and the shape of 75 KeyGen vectors. The default
  uses this bundle; `MLDSA_ROOT` remains an override. `zetas.txt` is present and
  staged by the new ASIC example. Existing ASIC portability edits are retained.
  No new full-design ML-DSA simulation ran; the local driver covers KeyGen only,
  not the bundled but unexecuted SigGen/SigVer tests or FIPS 204 conformance.
- The [SLH selected-mode gate](../agent/slh_dsa/README.md) selects the existing
  pinned vendor-output reference for each of the six SHA2 parameter sets.
  The 192f candidate and 128f pristine configuration remain unchanged. Tests
  cover reference/input/testbench/configuration tampering, stale or incomplete
  outputs and source changes. These are harness tests. Real gate invocations
  passed setup checks then stopped at missing `xvlog`; Icarus and Verilator
  rejected duplicate declarations in unchanged vendor RTL. No fresh SLH RTL
  pass is claimed. SHAKE remains unsupported; golden streams include the
  padded message tail and are not independent FIPS 205 KATs.
- HQC retains its legacy 128/192/256 shared-secret consistency gates. These are
  not independent standardized known-answer responses, and no new full-design
  HQC simulation ran for this update.

## Whole-design controller evidence

The [whole-design controller](WHOLE_DESIGN.md) and command adapters are
software-tested with synthetic measurements and trusted subprocess fixtures.
Tests cover baseline verification before measurement, immutable inputs,
bounded typed edits, complete-design remeasurement, declared operation-cycle
and area/timing guards, repeated-attempt rejection, and rollback/history
failures. Legacy block-filter outcomes no longer become learned successes
before durable full-design acceptance.

Built-in adapters cover the opt-in LLM proposer, existing ASIC measurement
runner and exact ML-DSA 75-case KeyGen profile. Vendor timing-path extraction
and ownership mapping require site qualification; normalized FPGA measurement
still needs a site adapter. No paid proposer, licensed optimization loop,
new end-to-end vendor flow, or measured PPA gain was established by these tests.
A trusted adapter's declaration does not prove complete source or test coverage.

## Not run and remaining limits

- No Vivado synthesis, place-and-route, or full-design HQC/ML-DSA/SLH simulation
- No licensed Genus or Design Compiler run; no ASIC physical/signoff run
- No paid model/API calls or hosted GitHub Actions
- No ML-DSA Sign/Verify qualification or unified Adam's Bridge ML-DSA-87 qualification
- No independent FIPS 205 validation or SHAKE-family SLH gate
- HQC gates check legacy shared-secret consistency, not independent standardized
  known-answer responses

Private workspaces and proposal guards support cooperating experiments. They
are not a hostile-code security sandbox. The recorded block and ML-KEM fault
checks do not establish the sensitivity of every other gate or prove
constant-time operation.
