# Independent ML-KEM-1024 AHB verification gate

## Current qualification status

**PASS on 2026-10-12:** the authentic unchanged RTL compiled and completed all
80 official ML-KEM-1024 ACVP cases with 39,840 exact word/status checks and clean
simulator exit 0 under Debian Verilator 5.032. All 159,040 output bytes, five
implicit-rejection secrets, and twenty key-input checks passed. Two real-DUT
negative controls (one expected-output bit flip and one seed-input bit flip)
produced genuine output-mismatch failures.

See [compact qualification evidence](../../docs/verification/mlkem-adams-bridge-acvp-2026-10-12.json)
and [complete success transcript](../../docs/verification/mlkem-adams-bridge-acvp-2026-10-12.txt).
Icarus Verilog 12.0 still cannot parse the unchanged upstream unpacked parameter
array at `upstream/src/abr_libs/rtl/abr_piso_multi.sv:23`; that tool failure is not
an RTL failure or a passed KAT. The runner never ignores nonzero simulator exits.

The actual hardware under test is `abr_unified_top`: the pinned **unified
ML-KEM-1024 / ML-DSA-87** accelerator plus its external SRAM models. This gate
exercises its ML-KEM public AHB API only. It does not qualify ML-DSA or give an
ML-KEM-only area measurement.

## Reproduce

From the repository root, with an already installed simulator:

```sh
python tools/run_mlkem_adams_bridge_kat.py --simulator verilator
# Equivalent explicit tool selection:
python tools/run_mlkem_adams_bridge_kat.py --simulator verilator --verilator /path/to/verilator
# Reproduce the Icarus limitation:
python tools/run_mlkem_adams_bridge_kat.py --simulator iverilog --iverilog /path/to/iverilog --vvp /path/to/vvp
# Inspect all transactions without making any simulation claim (exit 2):
python tools/run_mlkem_adams_bridge_kat.py --prepare-only
# Gate unit tests; optional Icarus tests exercise a mock AHB slave only:
python -m unittest discover -s tests -p test_mlkem_adams_bridge_gate.py -v
```

Verilator needs a suitable C++ compiler and `make`. The runner uses
`--binary --timing --assert`, preserves warnings, and does not run upstream UVM
sequences, C++ reference models, installation scripts, DPI, network commands,
or paid tools. `-Wno-fatal` makes warnings advisory, not assertion failures.
The `--assert` flag does not activate all vendor checks: the pinned
`abr_prim_assert.sv` selects dummy macros under VERILATOR, and `abr_sva.svh`
requires `ABR_ASSERT_ON`, which is not defined. The independent harness uses
explicit `$fatal` checks, which remain active. No upstream-assertion-coverage
claim is made.
No `SYNTHESIS`, `CALIPTRA`, `ABR_SIMULATION`, or FPGA-specific define is inserted.
The pinned configuration's default masking remains in place.

Options include `--work-dir`, `--report`, `--compile-timeout`, `--sim-timeout`,
`--max-cycles`, and `--jobs`. Defaults allow 900 seconds for each tool stage,
200,000 simulated cycles per case, and two compilation jobs. The work directory
contains `commands.hex`, `case_manifest.json`, `sources.f`, `compile.log`,
`simulation.log` when actually simulated, and `report.json` with commands, tool
version, input SHA256 hashes, return codes, and stage durations. A rerun first
invalidates an old report to RUNNING/false; interrupted runs cannot leave a stale
PASS at that report path. Stage timeouts terminate the owned tool process group.

Exit statuses are deliberately strict:

- **0 / PASS:** compilation succeeded and all 80 real RTL cases and 39,840 exact
  checks completed, with successful simulator exit and unchanged inputs
- **1 / FAIL:** a simulation mismatch, protocol failure, or incomplete/invalid
  simulator transcript
- **2:** unavailable tools, compilation failure, tool timeout, invalid inputs,
  or preparation without simulation; these can never qualify the baseline


## Qualify an isolated optimization candidate

The pinned reference tree is never edited. `--candidate-root` points to a
complete independent copy of `third_party/adams_bridge/upstream`, with the same
relative `src/...` layout. For example:

```sh
mkdir -p build/mlkem_adams_bridge
cp -a third_party/adams_bridge/upstream build/mlkem_adams_bridge/candidate_upstream
# Apply proposed RTL changes only in build/mlkem_adams_bridge/candidate_upstream.
python tools/run_mlkem_adams_bridge_kat.py --simulator verilator \
  --candidate-root build/mlkem_adams_bridge/candidate_upstream \
  --work-dir build/mlkem_adams_bridge/candidate
```

The ordered compile closure comes from the pinned original integration manifest.
Only upstream RTL/header paths are redirected; the wrapper, independent harness,
and all expected vectors remain the originals. Candidate reports record every
candidate hash, changed-file old/new hashes, target identity, original-source
integrity, and both trees' before/after stability. A modified candidate is never
labeled byte-exact verified upstream. Each candidate needs all 80 cases and the
same 39,840 checks with clean exit 0; the baseline PASS cannot be inherited.

Admission is intentionally conservative: no extra/missing files, symlinks,
changed includes, altered source manifests, non-RTL edits, masking-config edits,
assertion-header edits, DPI, host/file I/O, simulator-control calls, or harness
result-marker strings. A rejected candidate needs explicit review rather than a
weaker oracle or silently expanded closure. These checks are not an adversarial
sandbox or a proof against deliberately test-specialized hardware. The command's
default candidate work directory is separate from the default reference report.

The [recorded real-RTL fault control](../../docs/verification/mlkem-adams-bridge-rtl-fault-2026-10-12.json)
compiled an isolated one-bit mutation in `abr_ctrl.sv`'s EK output path, then
correctly failed for the first output word mismatch with unchanged reference
hashes. This is a genuine simulated RTL failure, not a compilation failure or
synthetic transcript. The final gate regression suite passed 35 tests.

**Coverage boundary:** a candidate PASS establishes only this ML-KEM API vector
coverage. Shared-module optimizations may break ML-DSA-87 while passing ML-KEM.
Preserving full unified-accelerator behavior requires separate ML-DSA-87
qualification, plus any required security/countermeasure checks. No whole-unified
correctness or preserved side-channel protection follows from this gate.

## Independent evidence and coverage

RTL pin: `chipsalliance/adams-bridge` tag `v2.0.3`, commit
`b77e3d899e828d626cfc2a0d26a6b5704cc121e0`.

Expected vectors: NIST ACVP-Server `FIPS203`, commit
`975de31eb83d87039ec88934fdc47d8c312b892d`, normalized fixture
`third_party/adams_bridge/test_vectors/nist_acvp_mlkem1024.json`.
The runner requires its exact SHA256, source-manifest SHA256, every pinned
upstream file hash, integration-manifest SHA256, and wrapper SHA256. Changing a
pin requires explicit review of this gate; it is not silently treated as the
same qualified reference.

All 80 ML-KEM-1024 cases are mandatory:

- 25 key generation cases: compare all 1,568 EK bytes and 3,168 DK bytes
- 25 encapsulation cases: compare all 1,568 ciphertext bytes and 32 secret bytes
- 10 decapsulation cases: compare all 32 secret bytes
- 10 decapsulation-key checks and 10 encapsulation-key checks: check the official
  expected acceptance/error result; invalid-key cases also require all 32
  shared-secret output bytes to remain hidden as zero

Decapsulation case IDs 96, 98, 101, 104, and 105 are implicit-rejection cases.
Their official expected secret is independently recognized as
`SHAKE256(z || ciphertext, 32)`, using Python's standard `hashlib`. Those cases
must produce the exact rejection secret with normal valid completion. An error
flag, a zero secret, or merely a different secret is insufficient.
The other five cases cover valid decapsulation. Key-check inputs do not supply a
message/ciphertext; those irrelevant inputs are explicitly zero-filled and only
key validity is claimed for these tests.

In total the gate compares 159,040 output bytes and 80 completion statuses. It
never computes expected key generation, encapsulation, or valid decapsulation
results from the DUT or the upstream reference implementation.

## Interface and fail-closed behavior

`tb_mlkem_acvp.sv` drives 32-bit non-pipelined AHB-Lite transactions on the real
64-bit interface. Byte 0 maps to bits 7:0 of word 0; address bit 2 selects the
correct AHB64 lane. Every test resets the DUT, waits for a clean ready status,
loads deterministic masking entropy and official inputs, and starts one command.
The register map is checked against pinned `abr_reg_uvm.sv` and the upstream
ML-KEM hardware specification. Completion requires VALID=1 and ERROR=0.
READY is required before loading inputs, but not after completion: the pinned
`abr_ctrl.sv` asserts READY only in ABR_RESET and holds completed operations
with VALID=1/READY=0 until reset or zeroize. Outputs are read only through the public AHB.
No hierarchical force, internal memory preload, or behavioral KEM substitution
is used in the real gate. Reported case cycles include reset settling, public
input/output transactions, and status polling; they are not standalone kernel
latency. The arbitrary testbench clock period provides no Fmax or timing-closure
evidence.

The harness aborts on AHB errors, unknown reads in four-state simulation,
wait-state timeout, case timeout, incorrect completion, any 32-bit output
mismatch, malformed commands, missing terminators, or incomplete accounting.
The Python gate separately requires exactly one ordered result per case and one
final completion record, a zero simulator exit, and unchanged input hashes.
Verilator is a two-state simulator; it cannot substantiate four-state/X claims.

The unit-test-only AHB mock validates lane selection, stalled data phases,
comparison failure, and malformed/incomplete command handling. Its success is
**not cryptographic RTL evidence**. Parser tests similarly use synthetic logs
only to prove fail-closed behavior. Neither can mark the authentic gate PASS. A Verilator mock regression also
requires clean simulator shutdown, preventing a result marker followed by a
nonzero process exit from being mistaken for success.

Passing this finite published vector set would be functional evidence, not NIST
certification, a side-channel/fault-resistance assessment, an exhaustive proof,
or FPGA/ASIC PPA evidence. Modified candidates need their own complete gate result; the successful pinned
reference run cannot qualify an edited implementation or establish a PPA gain.
