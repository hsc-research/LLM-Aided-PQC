# Project status

Status of the portable software update, 2026-10-12. Historical measurements
remain tied to their original source versions and tool configurations.
A Python test pass, a prepared Tcl script, and a successful hardware run are
three different results.

## Design coverage

| Design | Sources in this checkout | Functional evidence and current limits | ASIC status |
|---|---|---|---|
| ML-KEM | Pinned Apache-2.0 Adam's Bridge v2.0.3; full ML-KEM-1024 operations in a unified ML-KEM/ML-DSA-87 engine, with memories | Upstream KAT/formal evidence; 80 independent official FIPS203 ACVP cases and a fail-closed local simulation gate. Pinned baseline passed all 80 cases / 39,840 checks under Verilator 5.032, including five implicit rejections. Two-state simulation; not NIST certification or ML-DSA verification. Icarus rejects upstream SystemVerilog | Whole-unified-design example configuration for Genus/DC and baseline Vivado synthesis Tcl; no licensed synthesis or PPA result |
| ML-DSA | Pinned ML-DSA-OSH Verilog/VHDL, testbenches, KAT and common data, including `zetas.txt`; modified FPGA and ASIC snapshots remain separate | Full-design gate defaults to 25 KeyGen vectors at each of II/III/V (75 total). The bundled baseline has not been simulated in this update. Signing, verification and independent FIPS 204 conformance are not established by a KeyGen pass | Full-design example now declares ordered sources and stages the pinned `zetas.txt`. The historical ASIC baseline retains two portability edits; licensed elaboration, memory review and synthesis remain open |
| SLH-DSA | 62 pristine SPHINCSLET files match a pinned upstream commit; modified candidate, SHA-2/SHAKE inputs and historical golden streams are retained | The standalone gate selects the matching pinned vendor-output stream for all six SHA2 sets, including the unchanged 192f candidate and pristine 128f baseline. Testbench and inputs are pinned; SHAKE is unsupported. Vivado simulation is unrun; Icarus/Verilator reject vendor duplicate declarations. No independent FIPS 205 oracle or new RTL pass is claimed | No validated complete ASIC run; FPGA RTL requires ASIC-specific input and memory review |
| HQC | Reference RTL, testbenches, and tracked operation/joint-design source snapshots | Shared-secret consistency across keygen, encapsulation and decapsulation. Top-level candidate checks request all three levels; direct joint-gate calls default to HQC-128 unless `--all` is supplied | ASIC source snapshots and historical zero-unresolved Genus reports exist; no qualified full-design DC configuration |

ML-KEM, ML-DSA, and SLH-DSA are the three initial final NIST PQC standards.
HQC was [selected for standardization in March 2025](https://www.nist.gov/news-events/news/2025/03/nist-selects-hqc-fifth-algorithm-post-quantum-encryption).
These descriptions concern the algorithms; they do not certify this RTL.

The standalone SLH-DSA check stages a private workspace. For the unchanged
SHA2-128f baseline, select the pristine RTL with the command below; its data
are selected automatically. The no-argument command preserves the current
192f candidate and selects its own pinned golden. Both now reach simulator
setup and report missing `xvlog` in this environment, without a false pass.

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

1. Preserve the imported ML-KEM baseline’s recorded 80-case evidence and rerun
   the gate on every candidate. Retain the unified ML-KEM/ML-DSA area scope;
   shared-block changes need separate ML-DSA checks to preserve both functions.
2. Reviewed source lists, defines, parameters, ROM data, and memory treatment
   for each full design and configuration.
3. Access to the selected licensed tool and permitted target libraries.
4. Functional validation of the exact baseline/candidate sources being measured.
5. Matched baseline/candidate synthesis reports and independent review of
   elaboration, timing constraints, units, and power assumptions.

The standalone ASIC runner performs measurements. A separate [whole-design
controller](WHOLE_DESIGN.md) now implements an offline-tested proposal/admission
loop around explicit adapters. Actual source/test coverage, timing-path mapping
and licensed tools still need site qualification. No ASIC place-and-route or
signoff result is claimed. Historical Genus records are
available under [ASIC findings](findings/asic/); they do not substitute for new
Design Compiler measurements.

## ML-KEM entry points

- [Pinned source, license, scope and launch instructions](../third_party/adams_bridge/README.md)
- `python3 third_party/adams_bridge/integration/verify_sources.py`: provenance only
- `python3 tools/run_mlkem_adams_bridge_kat.py --simulator verilator`: complete
  80-case official-vector RTL gate; missing/unsupported tools fail closed
- [Whole-wrapper Vivado synthesis Tcl](../third_party/adams_bridge/integration/vivado_synth.tcl):
  explicit FPGA part, chosen period and fresh output directory; OOC synthesis only
- [Full unified ASIC example](../configs/mlkem_adams_bridge_asic.example.json):
  Genus/DC runner input, with user-supplied libraries and site constraints

The whole-wrapper boundary includes ten upstream memory instances. No
ML-KEM-only synthesis configuration is supplied by this pinned upstream
release. A stripped standalone derivative would need independent verification;
simply exercising only ML-KEM does not remove ML-DSA hardware from area.

## ML-DSA entry points

- [Pinned ML-DSA-OSH inputs, provenance and coverage](../third_party/mldsa_osh/README.md)
- `python3 tools/check_mldsa_sources.py`: source-integrity and compatibility
  check only; no simulation or synthesis
- `python3 agent/mldsa/full_kat_gate.py`: bundled baseline KeyGen check with
  Vivado's `xvhdl`, `xvlog`, `xelab` and `xsim`; `MLDSA_ROOT` overrides the
  default source tree
- `python3 agent/mldsa/full_kat_gate.py agent/mldsa/mldsa_src`: the same gate
  with the 14 matching-basename candidate overrides
- [Full-design ASIC example](../configs/mldsa_osh_asic.example.json): ordered
  mixed-language sources and staged ROM input; requires approved local
  libraries, site constraints and licensed-tool qualification

The source bundle is pinned to KULeuven-COSIC/ML-DSA-OSH commit
`751009199ac081091a9059805e6921453bde0154`. Of 50 source/common files compared
with the historical ASIC baseline, 48 are byte-identical. The existing
`combined_top.v` declaration reorder and `ntt_fifo_piso.v` assignment changes
are documented in the [portability findings](findings/asic/2026-07-31_mldsa_genus_port.md)
and are not replaced by this import. Source correspondence does not prove
functional equivalence; a KeyGen-only gate does not qualify Sign/Verify.

## SLH-DSA baseline boundary

From the repository root, with Vivado simulator tools loaded:

```bash
# Unchanged pristine SHA2-128f baseline
python3 agent/slh_dsa/slh_kat_gate.py agent/slh_dsa/pristine
# Unchanged selected SHA2-192f candidate
python3 agent/slh_dsa/slh_kat_gate.py
```

All 62 pristine files are byte-identical to
[`caslab-code/pqc-hw-sphincslet` at `a1adc2b324483d0f95ae42b3119997d3a61c77b6`](https://github.com/caslab-code/pqc-hw-sphincslet/tree/a1adc2b324483d0f95ae42b3119997d3a61c77b6),
and all 30 entries in `agent/slh_dsa/pristine_rtl.sha256` match. These checks
establish provenance, not a new hardware result or complete license clearance.
The six parameter-set golden streams were already committed at
`25a9de8fb399644889f9d6f602b302f949a6e86f`. The gate now binds the actual
SHA2 selection to that set's immutable hash, expected complete length and
vendor output filename; neither references nor RTL were changed.

The SHA-256 of both 128f golden files is
`10f35fcc0cc98680d87cf7aaef1479ba359303a84ba2553d69a8b77771bdf2a8`;
the retained 192f stream is
`22bfbe1c1130b0faf039268adf00504a0ffec308f8ac7a8692593c757371dfe3`.
The last 40 bytes of the observed 128f/192f streams contain a 33-byte message
and seven zero-padding bytes, so these are vendor output streams including a
padded message tail, not independently validated bare FIPS 205 signatures.
The [selected-mode gate](../agent/slh_dsa/README.md) compares all bytes,
including this tail, and its positive/negative harness tests reject mismatched
parameters, truncated output, changed inputs and stale evidence. These mocked
tests are not RTL simulation. Existing Icarus 12 and Verilator both reject
`FSM.v` duplicate declarations (`WOTS_FSM_start`, `WOTS_s_in_0_wr_en`); no
portability edits were made. Fresh Vivado simulation and Vivado/DC/Genus
implementation qualification remain pending. Never regenerate an expected
stream from the candidate or switch its parameter set merely to obtain a pass.

## Public-release boundary

The [release checklist](RELEASE_CHECKLIST.md) records unresolved review of
vendor tool databases/logs and third-party notices. Those files are retained
as historical evidence; retaining them does not establish permission to
redistribute them. No repository-history cleanup is implied by this update.
