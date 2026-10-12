# Verification record

[Project home](../README.md) · [Documentation](README.md) · [Run guide](REPRODUCE.md) · [Results](RESULTS.md)

Verified locally on 2026-10-12 using Python 3.12.14. These checks validate
software safeguards, corrected full-design ML-DSA variants and separate block
checks, the ML-KEM-1024 API of the pinned unified Adam's Bridge accelerator,
and corrected SLH-DSA 128f/192f portable derivatives. They do not establish new FPGA/ASIC PPA results
or complete cryptographic compliance.

## Find the evidence

- [Machine-readable records and simulator output](verification/README.md)
- [Checker source and instructions](../verification/README.md)
- [Current design coverage and open limits](PROJECT_STATUS.md)
- [Staged reproduction commands](REPRODUCE.md)

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
  ":!third_party/hqc_sac2026/upstream" \
  ":!third_party/adams_bridge/test_vectors/NIST_ACVP_README.upstream.md" \
  ":!docs/verification/*.txt" \
  ":!docs/verification/**/*.patch" \
  ":!verification/mldsa_osh/encoder_fallthrough.v" \
  ":!verification/mldsa_osh/generated/*.v"
```

- Latest normal and optimized (`python3 -O`) Python suite: **359 tests passed,
  zero skipped** in each run, with the available simulator tools on `PATH`.
  Many tests use mocked EDA processes and Tcl syntax checks. These counts are
  software/harness evidence, not 359 independent cryptographic or vendor-tool runs.
- Repository documentation checker: **585 local links passed** across **97
  Markdown files**. A separate expanded audit also included scheme harness and
  imported-package READMEs: **674 local links across 106 files**, zero errors.
  External URLs and unmodified upstream documentation were not network-validated.
- The five focused documentation-checker tests passed. Python compilation,
  CLI smoke and first-party documentation whitespace checks passed.
  Pinned source snapshots, recorded patches and saved simulator output retain their original whitespace
  for provenance; they are excluded from the first-party whitespace check above.
- Documented no-EDA export commands passed for both ML-DSA derivatives
  (35 ordered design files each) and all four SLH mode/variant combinations
  (29 design files each). Every SLH bundle checksum passed and both modes
  reported qualified same-parameter partners. These source-copy checks do
  not establish hardware-tool elaboration or measurements.
- The strict historical-number inventory exited 0: **280 classified citations**
  across **112 tracked Markdown files**, with **163 warning-only unclassified
  frequency citations**. This is an inventory check, not independent reproduction
  of those measurements. It does not scan newly untracked files.
- Read-only command checks passed for CLI help, `doctor`, `list`, `smoke`, both
  ML-KEM/ML-DSA source-integrity checks, gate help and the FPGA command preview.
  The unconfigured whole-design example correctly returned `BLOCKED`, exit 1,
  with no adapter execution.
- `doctor` completed its audit; missing tools and unsupported scheme/configuration
  combinations remain explicitly blocked. Audit completion does not mean all
  prerequisites are available.

This is the final recorded software/documentation snapshot for this update.
Any subsequent code change needs the relevant rerun. JavaScript syntax was
rechecked with Node.js v24.19.0; no dashboard JavaScript was changed.

The earlier editable installation was tested in a local virtual environment with
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

- The [ML-DSA input bundle](../third_party/mldsa_osh/README.md) contains 106
  unmodified upstream files / 3,300,503 bytes, pinned to
  `751009199ac081091a9059805e6921453bde0154`. Source integrity and required ROM
  data are checked separately from the [actual portable runs below](#real-ml-dsa-portable-variants).
  The original baseline/candidate failures remain recorded; passing corrected
  derivatives do not relabel those originals as fully verified.
- The [SLH selected-mode gate](../agent/slh_dsa/README.md) supports six pinned
  SHA2 vendor references. Original tracked sources, testbench, inputs and
  expected streams remain unchanged. Vivado execution is unrun. Actual
  portable-variant results are [separately recorded below](#real-slh-dsa-portable-variants);
  support for six modes is not evidence of six completed runs.
- The preferred [HQC SAC 2026 snapshot](../third_party/hqc_sac2026/README.md)
  contains 126 unchanged upstream files / 1,459,138 bytes with a pinned manifest.
  This is source-copy integrity only. No upstream program, simulation, synthesis,
  executable adapter or functional/PPA result is supplied for it.
- HQC retains its separate legacy SAC 2023-derived 128/192/256 consistency gates. These are
  not independent standardized known-answer responses. Static review found
  unused rejection-check flags. The staged dynamic rejection probe is
  **inconclusive**: a changed input file and unchanged output did not establish
  that the DUT loaded the mutation; an instrumented attempt produced unknown
  values. Do not cite this as a confirmed live rejection failure or a pass.
  Repair and complete qualification remain unfinished. No repaired derivative
  is a verified baseline. See the [exact legacy source finding](PROJECT_STATUS.md#hqc-legacy-verification-boundary);
  the [read-only review record](verification/hqc-readonly-review-2026-10-12.json) preserves the diagnostic evidence.
  Unfinished harness/repair additions are not supported published commands.

## Real ML-DSA portable variants

Two explicit corrected variants pass **210 cases each**:

| Variant | Evidence |
|---|---|
| Pinned baseline plus canonical-hint guard | [Result](verification/mldsa-portable-2026-10-12/baseline_canonical_pass/result.json), [logs and hashes](verification/mldsa-portable-2026-10-12/baseline_canonical_pass/) |
| 14-file candidate plus encoder fallthrough repair and canonical-hint guard | [Result](verification/mldsa-portable-2026-10-12/candidate_corrected_pass/result.json), [logs and hashes](verification/mldsa-portable-2026-10-12/candidate_corrected_pass/) |

Each run completes 75 KeyGen, 45 Sign and 45 upstream Verify cases, plus 12
one-bit signature/message/context/public-key mutations and 33 reset-based
canonical-hint controls/negatives. The upstream Verify set contains **9 valid
and 36 invalid** cases. The added canonical set contains 18 valid controls
and 15 invalid cases. The hardware verification flag is active-high failure:
0 accepts, 1 rejects. The added cases are not new official ACVP vectors.

The stronger checks exposed failures in the original sources:

- [Original baseline](verification/mldsa-portable-2026-10-12/baseline_upstream_failure/result.json):
  all 165 upstream cases pass, but only 11 of 12 tamper cases are correctly
  rejected. A malformed ML-DSA-87 hint encoding is accepted, so the full
  stronger suite fails.
- [Original candidate Sign](verification/mldsa-portable-2026-10-12/candidate_sign_failure/result.json):
  75 KeyGen cases pass, but Sign produces no completed cases before its
  20-million-cycle watchdog. The separate [Verify run](verification/mldsa-portable-2026-10-12/candidate_verify_failure/result.json)
  passes the 45 upstream cases but fails the same added malformed-hint check.
- The corrected candidate retains the banked encoder with an explicit
  fallthrough repair; it does not silently replace it with the upstream encoder.
  A [four-state block comparison](verification/mldsa-portable-2026-10-12/encoder-fallthrough-cycle-result.json)
  passes 18 configurations and two mode-switch sequences, including cycle-exact
  output/knownness checks over 2,278 words under a legal occupancy envelope.
  This is bounded block evidence, not arbitrary-stream or full-core equivalence.
- The guard also has [1,350 standalone four-state checks](verification/mldsa-portable-2026-10-12/guard_four_state_pass/result.json)
  and an [independent 9,371-encoding review](verification/mldsa-portable-2026-10-12/independent-hint-guard-review.json).
  These do not turn the full datapath into a four-state-qualified design.

The [toolchain record](verification/mldsa-portable-2026-10-12/toolchain.json)
identifies GHDL 6.0.0 and its official GHDL 5.0.1 Synopsys compatibility-source
inputs. The preserved Verilator build reports runtime 5.49 and launcher
`vUNKNOWN-built20260516-4e853d8`; use its recorded executable hashes rather
than inferring a released version. The complete Icarus datapath attempt
[did not complete](verification/mldsa-portable-2026-10-12/icarus_full_datapath_timeout/result.json).
The full passing evidence is therefore two-state Verilator simulation.

The pinned upstream RTL and vectors remain unchanged. Staged adaptations
include declaration placement, the GHDL-generated Keccak netlist, watchdogs,
and bounded capture/input packing for partial final hint words in the upstream
testbenches. The canonical-hint guard and encoder correction are explicit
semantic derivatives. See the [focused guide](../verification/mldsa_osh/README.md)
for every transformation and the diagnostic failures.

An [independent source/log audit](verification/mldsa-portable-2026-10-12/independent-review.json)
checks both complete case sets, source/input/executable hashes, original
failures and source exports. It is an audit of the recorded full-design runs,
not a second independent full-design simulation.

The full-design reference answers are pinned upstream KAT files; the current
run does not independently authenticate the entire official corpus. No FIPS
204 certification, exhaustive correctness, constant-time/leakage proof,
full four-state qualification or new FPGA/ASIC PPA is claimed. Exact tested
Verilog source exports are available for the [next hardware stage](HARDWARE_HANDOFF.md).

## Real SLH-DSA portable variants

The [Icarus runner](../verification/slh_portable/README.md) stages explicit,
hash-recorded adaptations and requires both complete frozen-stream comparison
and successful RTL verification. It then corrupts one bit in captured signature
memory before the real RTL verifier consumes it. It does not regenerate the
reference or replace the verifier with a Python comparison.

| Variant | Completed result |
|---|---|
| Syntax-only pristine SHA2-128f | [FAIL](verification/slh-portable-syntax-128f-2026-10-12.json): 2,133/2,141 words and valid-signature mismatch |
| Sensitivity-corrected pristine SHA2-128f | [PASS](verification/slh-portable-corrected-128f-2026-10-12.json): 2,141 exact words; valid verification flag 0, one-bit signature-memory corruption rejected with flag 1 |
| Sensitivity-corrected candidate selected as SHA2-128f | [PASS](verification/slh-portable-corrected-candidate-128f-2026-10-12.json): the same 2,141 exact words and flags 0/1; forms a same-parameter functional pair with the corrected baseline |
| Syntax-only selected optimized SHA2-192f | [FAIL](verification/slh-portable-syntax-192f-2026-10-12.json): all 4,463 words match, but valid verification fails with flag 1; negative control is unqualified |
| Sensitivity-corrected selected optimized SHA2-192f | [PASS](verification/slh-portable-corrected-192f-2026-10-12.json): 4,463 exact words; valid verification flag 0, one-bit signature-memory corruption rejected with flag 1 |
| Sensitivity-corrected baseline selected as SHA2-192f | [PASS](verification/slh-portable-corrected-baseline-192f-2026-10-12.json): the same 4,463 exact words and flags 0/1; completes the same-parameter 192f functional pair |

The correction is opt-in `--fix-auth-sensitivity`, which includes `leaf_idx`
in an incomplete authentication-path sensitivity list. A corrected pass
qualifies the particular staged derivative and one deterministic 33-byte
message fixture. Both corrected arms passed at 128f and at 192f. The
[source exporter](HARDWARE_HANDOFF.md#slh-dsa-keep-mode-and-derivative-together)
binds each bundle to its exact passing record and same-mode partner. The
corrected source pairs differ only in the two candidate SHA cores; functional
pairing does not establish timing or area improvement. The other four SHA2
modes were not executed. These passes do not qualify unchanged pristine RTL, an unmodified
Vivado build, all six SHA2 modes, the unsupported SHAKE family, independent
FIPS 205 conformance or physical PPA. Streams include the padded message tail.
A negative control is unqualified if its ordinary positive baseline fails.
See [reproduction commands](REPRODUCE.md#slh-dsa) and the
[evidence index](verification/README.md) for complete logs.

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

- No Vivado synthesis, place-and-route, or new Vivado full-design HQC/ML-DSA/SLH simulation
- No licensed Genus or Design Compiler run; no ASIC physical/signoff run
- No paid model/API calls or hosted GitHub Actions
- No full four-state ML-DSA datapath qualification or unified Adam's Bridge ML-DSA-87 qualification
- No independent FIPS 205 validation or SHAKE-family SLH gate
- HQC gates check legacy shared-secret consistency, not independent standardized
  known-answer responses

Private workspaces and proposal guards support cooperating experiments. They
are not a hostile-code security sandbox. The recorded block and ML-KEM fault
checks do not establish the sensitivity of every other gate or prove
constant-time operation.
