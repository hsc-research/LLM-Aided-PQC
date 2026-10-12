# Project status

Status of the portable software update, 2026-10-12. Historical measurements
remain tied to their original source versions and tool configurations.
A Python test pass, a prepared Tcl script, and a successful hardware run are
three different results.

## Design coverage

| Design | Sources in this checkout | Functional evidence and current limits | ASIC status |
|---|---|---|---|
| ML-KEM | No ML-KEM RTL | No functional checker or measured baseline | No implementation or qualified configuration; no hardware result |
| ML-DSA | Modified FPGA RTL and ASIC source snapshots | Existing full-design driver checks key generation. The matching upstream Verilog/VHDL, testbench, KAT and common-data tree is required. Signing and verification are not established by a key-generation pass | Butterfly block inputs are available. Full-design `operation_module.v` refers to `zetas.txt`, which is absent; licensed synthesis remains open |
| SLH-DSA | Baseline and modified SPHINCSLET RTL, SHA-2/SHAKE inputs, and golden signatures | Historical parameter sweeps exist. The standalone gate checks SHA2-128f against a frozen signature. The checked-in candidate selects 192f, so it is deliberately blocked by that gate. It is not an independent official KAT | No validated complete ASIC run; FPGA RTL requires ASIC-specific input and memory review |
| HQC | Reference RTL, testbenches, and tracked operation/joint-design source snapshots | Shared-secret consistency across keygen, encapsulation and decapsulation. Top-level candidate checks request all three levels; direct joint-gate calls default to HQC-128 unless `--all` is supplied | ASIC source snapshots and historical zero-unresolved Genus reports exist; no qualified full-design DC configuration |

ML-KEM, ML-DSA, and SLH-DSA are the three initial final NIST PQC standards.
HQC was [selected for standardization in March 2025](https://www.nist.gov/news-events/news/2025/03/nist-selects-hqc-fifth-algorithm-post-quantum-encryption).
These descriptions concern the algorithms; they do not certify this RTL.

The standalone SLH-DSA check now stages a private workspace and uses tracked
data by default. It does not require the former external shell-script staging
layout. Its limited configuration coverage still applies.

Run `python3 -m agent doctor --json` and `python3 -m agent list --json` to inspect
inputs and entry points in your checkout. See [FPGA setup](FPGA.md), the
[agent guide](../agent/README.md), and [ASIC setup](../asic/README.md) for the
relevant commands.

## What the checks establish

- Offline tests exercise edit validation, rollback, source selection, generated
  commands, and report handling with temporary files and tool substitutes.
- RTL simulation checks only the operations, inputs, modes, and conditions in
  the selected testbench.
- An HQC shared-secret match is an end-to-end consistency check; both sides can
  share a bug. It is not a comparison to an independent official answer file.
- An SLH-DSA signature match against baseline RTL establishes agreement for
  that test, not independent conformance to the standard.
- A successful synthesis requires complete elaboration and modeled memories.
  A prepared script, a missing metric, or a blackboxed path is not a PPA result.
- None of these checks proves resistance to timing, power, or EM leakage.

## Still needed for four-scheme ASIC results

1. A complete, licensed-to-use ML-KEM implementation and self-checking tests.
2. Reviewed source lists, defines, parameters, ROM data, and memory treatment
   for each full design and configuration.
3. Access to the selected licensed tool and permitted target libraries.
4. Functional validation of the exact baseline/candidate sources being measured.
5. Matched baseline/candidate synthesis reports and independent review of
   elaboration, timing constraints, units, and power assumptions.

There is no automatic ASIC-edit acceptance loop in the new runner, and no ASIC
place-and-route or signoff result is claimed. Historical Genus records are
available under [ASIC findings](findings/asic/); they do not substitute for new
Design Compiler measurements.

## Public-release boundary

The [release checklist](RELEASE_CHECKLIST.md) records unresolved review of
vendor tool databases/logs and third-party notices. Those files are retained
as historical evidence; retaining them does not establish permission to
redistribute them. No repository-history cleanup is implied by this update.
