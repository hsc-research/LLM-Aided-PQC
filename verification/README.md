# RTL verification harnesses

[Project home](../README.md) · [Run guide](../docs/REPRODUCE.md#4-run-functional-rtl-tests) · [Recorded results](../docs/VERIFICATION.md)

This directory contains checker-side source and instructions. The hardware
inputs remain in their design source trees. **Recorded test evidence** belongs
in [`docs/verification/`](../docs/verification/README.md); generated compilation
and simulation products belong in private run directories.

For later FPGA/ASIC measurements, use the [hardware handoff](../docs/HARDWARE_HANDOFF.md)
to export the exact passing derivatives and preserve their design boundaries.

| Design | Start here | Important boundary |
|---|---|---|
| ML-KEM | [Adam's Bridge ACVP harness](mlkem_adams_bridge/README.md) | Exercises ML-KEM-1024 on the shared ML-KEM/ML-DSA core; it does not qualify the ML-DSA function |
| ML-DSA | [Portable full-design runner](mldsa_osh/README.md) and [current coverage](../docs/REPRODUCE.md#ml-dsa) | Distinguish full-design operations from the separate arithmetic-block smoke test |
| HQC | [SAC 2026 source-only status](../docs/PROJECT_STATUS.md#hqc-preferred-source-baseline), [legacy commands](../docs/REPRODUCE.md#hqc) | No new-baseline runner; legacy shared-secret consistency alone does not establish independent correctness or rejection behavior |
| SLH-DSA | [Selected-mode checker](../agent/slh_dsa/README.md) and [portable variant](slh_portable/README.md) | Frozen vendor-output differential checks are not independent FIPS 205 validation |

Keep the testbench, reference answers and input data fixed when evaluating an
RTL edit. Record source hashes and actual completed cases. A compile failure,
timeout, skipped operation or missing output is not a functional pass.
