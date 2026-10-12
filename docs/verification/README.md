# Recorded verification evidence

[Project home](../../README.md) · [Verification record](../VERIFICATION.md) · [Results](../RESULTS.md) · [Run guide](../REPRODUCE.md)

These are dated results from actual local checks. The explanatory
[verification record](../VERIFICATION.md) states scope and limitations; the
JSON/text files preserve the reported counts, tool versions, input fingerprints
and verdicts. They do not automatically describe later source changes.

## Baselines and fault checks

| Record | Meaning |
|---|---|
| [ML-KEM baseline JSON](mlkem-adams-bridge-acvp-2026-10-12.json) and [simulator output](mlkem-adams-bridge-acvp-2026-10-12.txt) | 80 official ACVP samples / 39,840 checks on the ML-KEM API of the unified core |
| [ML-KEM RTL-fault JSON](mlkem-adams-bridge-rtl-fault-2026-10-12.json) and [output](mlkem-adams-bridge-rtl-fault-2026-10-12.txt) | A compiled one-bit key-output fault was rejected by a comparison mismatch |
| [Expected-word bit flip](mlkem-adams-bridge-expected_word_bitflip-2026-10-12.txt) | Diagnostic command-stream control using the real DUT |
| [Input-seed bit flip](mlkem-adams-bridge-seed_input_bitflip-2026-10-12.txt) | Diagnostic command-stream control using the real DUT |
| [SLH-DSA corrected 128f JSON](slh-portable-corrected-128f-2026-10-12.json) and [output](slh-portable-corrected-128f-2026-10-12.txt) | Explicit sensitivity-corrected portable variant: 2,141 frozen words match; actual one-bit captured-signature mutation rejected. Not unchanged pristine RTL or FIPS 205 qualification |
| [SLH-DSA corrected 192f JSON](slh-portable-corrected-192f-2026-10-12.json) and [output](slh-portable-corrected-192f-2026-10-12.txt) | Explicit sensitivity-corrected optimized derivative: 4,463 frozen words match and live signature-bitflip rejection passes. One fixed fixture; not unchanged candidate or FIPS 205 qualification |
| [ML-DSA arithmetic-block smoke JSON](hdl-smoke-2026-10-12.json) | 400 baseline vectors and two rejected arithmetic faults; not full-design ML-DSA coverage |

## Read-only diagnostic reviews

- [HQC rejection review](hqc-readonly-review-2026-10-12.json): the exact tracked
  legacy `build/joint_design/decap.v` has unused mismatch flags. Existing dynamic
  probes are inconclusive because mutation loading was not established and
  an instrumented valid control failed. This is not a full functional pass,
  a confirmed live rejection failure, or evidence about the separate SAC 2026
  import. No runnable incomplete repair/harness is included.

## Recorded failures

- [SLH-DSA syntax-only Icarus SHA2-128f record](slh-portable-syntax-128f-2026-10-12.json)
  and [simulation output](slh-portable-syntax-128f-2026-10-12.txt): 2,133 words
  instead of 2,141, with RTL verification mismatch. Its negative run cannot
  qualify a baseline that already produces an invalid signature. This is a
  failing staged derivative, not a test of unmodified Vivado RTL. See the
  [portable variant guide](../../verification/slh_portable/README.md).

- [SLH-DSA syntax-only Icarus SHA2-192f record](slh-portable-syntax-192f-2026-10-12.json)
  and [simulation output](slh-portable-syntax-192f-2026-10-12.txt): all 4,463
  words match, but the RTL rejects the untampered signature. Its negative
  control is unqualified; rejection of a corrupted signature is not sufficient
  when the normal signature is also rejected. The corrected variant is recorded separately above.

## Supporting SLH diagnostics

- [128f capture diagnostic](slh-portable-capture-diagnostic-2026-10-12.json):
  the missing output is observed on both clock edges before file capture;
  this diagnostic is not a complete qualification run.
- [192f verifier-only diagnostic](slh-portable-verify-only-192f-2026-10-12.json)
  and [output](slh-portable-verify-only-192f-2026-10-12.txt): a supplied frozen
  signature isolates the verification issue. The fresh signing/verification
  and corruption results are in the separate full-run records above.

Fault detection applies to the particular injected fault and tested inputs.
It does not establish exhaustive verification or physical fault resistance.

For checker implementation and reproduction, use the
[harness index](../../verification/README.md) and [staged run guide](../REPRODUCE.md).
Do not overwrite an earlier record when running a different source revision.
