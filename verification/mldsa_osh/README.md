# Portable ML-DSA RTL verification

The runner is [`agent/mldsa/portable_kat_gate.py`](../../agent/mldsa/portable_kat_gate.py).
It stages the pinned KULeuven-COSIC ML-DSA-OSH design, synthesizes its VHDL Keccak
hierarchy to Verilog using GHDL, and runs the resulting netlist together with the
actual Verilog design and upstream testbenches. It does not substitute a software
SHAKE implementation or a behavioral cryptographic oracle for the RTL.

## Current qualification

**Pending execution:** the runner and its fail-closed control tests have been
implemented, but an end-to-end GHDL-plus-simulator run has not yet been completed.
Do not treat the Python unit tests, source-integrity check, historical logs, or
Verilog syntax checks as new ML-DSA functional results.

## Prerequisites and commands

Use Python 3.10+, GHDL with synthesis and Verilog output support, and either
Icarus Verilog (`iverilog` and `vvp`) or Verilator with a C++ compiler and make.
Put the selected tools on `PATH`. See [GHDL synthesis documentation](https://ghdl.github.io/ghdl/using/Synthesis.html).

From the repository root:

```sh
# Four-state simulation; all 165 upstream cases plus 12 deliberate negatives.
python3 agent/mldsa/portable_kat_gate.py --verify-mutations

# Faster two-state simulation of the same actual design.
python3 agent/mldsa/portable_kat_gate.py --simulator verilator --verify-mutations

# Separately qualify the 14 committed candidate overrides.
python3 agent/mldsa/portable_kat_gate.py --simulator verilator \
  --override agent/mldsa/mldsa_src --verify-mutations

# Explicit reduced-coverage smoke test: 1 vector per level and operation.
python3 agent/mldsa/portable_kat_gate.py --vectors 1

# Harness/source checks only, not simulation evidence.
python3 -m unittest tests.test_mldsa_portable_gate tests.test_mldsa_source_integration
python3 tools/check_mldsa_sources.py
```

`--operations keygen sign verify` selects operations (all by default).
`--vectors N` limits the number **per security level** and must be labeled reduced
coverage. `--timeout` bounds each external process; `--cycle-limit` adds an explicit
hardware-simulation watchdog. A fresh run directory under `.pqc_runs/` contains
commands, versions, original and actual staged input hashes, logs, and `result.json`.
`PQC_RUN_DIR` can select a different output directory. No packages are installed
by the runner.

## Coverage and acceptance

The bundled upstream corpus supplies:

| Operation | ML-DSA-44 | ML-DSA-65 | ML-DSA-87 | Total |
|---|---:|---:|---:|---:|
| KeyGen, byte-exact public and secret keys | 25 | 25 | 25 | 75 |
| Deterministic Sign, byte-exact signatures | 15 | 15 | 15 | 45 |
| Verify, known valid inputs | 12 | 12 | 12 | 36 |
| Verify, known invalid inputs | 3 | 3 | 3 | 9 |
| Optional one-bit Verify mutations | 4 | 4 | 4 | 12 |

The optional mutations change one bit of each of the signature, message, context,
and public key, using an upstream valid vector with nonempty message/context as
the control. Each mutated case must be rejected. The corresponding unchanged
positive control must first pass the ordinary Verify test. These are added
negative tests; they are not new official ACVP vectors.

Acceptance requires the exact expected set of unique operation/level/vector
completions, positive cycle counts, the final testbench marker, successful process
exit, and no mismatch/error/watchdog output. The original testbenches compare
results with four-state `!==`. The runner validates staged copies before changing
them, records each intentional transformation, and rechecks both original inputs
and exact simulator inputs after execution. Missing tools, missing data, changed
inputs, a timeout, a truncated log, and duplicate completion markers cannot pass.

## Transformations and evidence boundary

- `third_party/mldsa_osh/upstream/` is never edited. Its manifest is verified first.
- Forward-referenced declarations in the staged `combined_top.v` are hoisted,
  matching the existing vendor runner's declaration-only portability treatment.
- The original VHDL hierarchy is synthesized by GHDL. This verifies the combined
  Verilog/GHDL-netlist variant, not a formal equivalence result between the VHDL
  source and its synthesized representation.
- Testbench capacities may be explicitly reduced, and watchdogs are appended.
- `--fifo-nonblocking` explicitly opts into eight blocking-to-nonblocking changes
  in the staged `ntt_fifo_piso.v`. This changes simulation semantics and is a
  separately named variant, never a silent repair of the pinned source. It is
  not enabled by default.
- Verilator is two-state. Passing there does not establish absence of X/Z
  initialization bugs; a four-state simulation provides complementary evidence.
- The oracles are the pinned **upstream KAT files**. The upstream repository
  identifies NIST/ACVP inputs, but this runner does not independently retrieve or
  authenticate the corresponding official ACVP corpus. Passing is not FIPS 204
  certification, a proof of cryptographic correctness, side-channel qualification,
  ASIC timing closure, licensed synthesis, or measured PPA.

The existing Vivado-only KeyGen runner remains available separately at
[`agent/mldsa/full_kat_gate.py`](../../agent/mldsa/full_kat_gate.py).
