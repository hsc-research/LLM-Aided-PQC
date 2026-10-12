# Project status

[Project home](../README.md) · [Documentation](README.md) · [Run guide](REPRODUCE.md) · [Results](RESULTS.md)

Status of the portable software update, 2026-10-12. Historical measurements
remain tied to their original source versions and tool configurations.
A Python test pass, a prepared Tcl script, and a successful hardware run are
three different results.

The current goal is separate FPGA and ASIC baseline qualification followed by
target-specific optimization. FPGA memory inference prefers BRAM where compatible;
ASIC uses generic RTL storage intended for standard-cell FF/logic mapping without
a macro compiler. Neither intent is a measured mapping result. The
[hardware handoff](HARDWARE_HANDOFF.md) keeps source preparation, portable
functional evidence and user-run licensed qualification separate. **The four
algorithms are not all target-qualified; HQC SAC 2026 remains blocked.**

The [target-profile exporter](HARDWARE_HANDOFF.md#prepare-explicit-target-profiles-without-eda)
now prepares explicit ML-KEM, corrected ML-DSA and corrected SLH source bundles
for both targets. `SOURCE_EXPORTED_TARGET_UNQUALIFIED` and
`SOURCE_PREPARED_NOT_RUN` are preparation states. The profiles retain real
compatibility blockers, including mapped startup/memory behavior and clock-gate
mapping. New [ASIC startup source derivatives](ASIC_STARTUP.md) separately expose
ML-DSA/SLH boot interfaces, exact source-bound functional reruns and generic FF
structural evidence. They preserve all original FPGA selections and do not
qualify licensed standard-cell mapping or admit target-bound optimization.
ML-DSA tests include in-operation boot-abort recovery; SLH repeated boot is
qualified while inactive only. ML-KEM retains its existing shared generic-memory
baseline; HQC SAC 2026 remains blocked.

[Bounded memory-component checks](../verification/asic_memory/README.md) add
generic Yosys FF/logic mapping evidence for selected existing RAMs and a tested,
optional ML-DSA zetas constant-ROM derivative. The original portable export still does not substitute that ROM.
The new explicit ML-DSA startup source separately uses constant logic and has its
own full-core evidence. Component checks alone do not qualify whole-design
startup, standard-cell mapping, functional behavior or PPA.

## Design coverage

| Design | Baseline and current functional evidence | Current hardware-tool boundary |
|---|---|---|
| ML-KEM | Pinned Adam's Bridge v2.0.3 shared ML-KEM-1024 / ML-DSA-87 core, with memories. **80 official samples / 39,840 checks passed** for the ML-KEM API only. [Scope and commands](#ml-kem-entry-points) | Whole-wrapper Vivado and Genus/DC configurations exist; no new licensed synthesis/PPA result |
| ML-DSA | **210 cases passed per corrected variant:** guarded baseline and guarded candidate with an encoder repair. Original malformed-hint acceptance and candidate Sign stall are retained failures. [Entry points](#ml-dsa-entry-points) | Original portable and new explicit startup source pairs are separate; use the [startup guide](ASIC_STARTUP.md) for new ASIC work. Existing ASIC examples select older arms. Licensed mapping/PPA remain pending |
| SLH-DSA | Original SPHINCSLET trees preserved. **Corrected baseline/candidate pairs at 128f and 192f passed** one fixture plus live corruption rejection per run. Syntax-only variants failed; the other four SHA2 modes were not run. [Exact variants and evidence](#slh-dsa-baseline-boundary) | Original portable and explicit startup exports retain exact same-mode pairs. Startup/reboot scope is limited; licensed mapping/PPA remain pending. SHAKE unsupported |
| HQC | Preferred **SAC 2026 snapshot is source-only and unverified**. [New baseline](#hqc-preferred-source-baseline). Older SAC 2023 consistency coverage and rejection review are [separate](#hqc-legacy-verification-boundary) | No SAC 2026 executable adapter or qualified synthesis manifest. Historical SAC 2023 Genus records do not qualify it |

ML-KEM, ML-DSA, and SLH-DSA are the three initial final NIST PQC standards.
HQC was [selected for standardization in March 2025](https://www.nist.gov/news-events/news/2025/03/nist-selects-hqc-fifth-algorithm-post-quantum-encryption).
These descriptions concern the algorithms; they do not certify this RTL.

The legacy Vivado SLH-DSA gate stages a private workspace and requires the
Vivado simulator. Select the pristine tree for its tracked SHA2-128f mode;
the no-argument command selects the current SHA2-192f candidate and its own
pinned golden. The separately corrected Icarus results below do not qualify
an unchanged Vivado run.

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

## Still needed for dual-target results

1. Preserve the imported ML-KEM baseline’s recorded 80-case evidence and rerun
   the gate on every candidate. Retain the unified ML-KEM/ML-DSA area scope;
   shared-block changes need separate ML-DSA checks to preserve both functions.
2. Reviewed source lists, defines, parameters, ROM data, and memory treatment
   for each full design and configuration.
3. User-owned licensed Vivado or DC/Genus runs with the selected FPGA part or
   permitted ASIC target libraries, reviewed constraints and mapped-memory evidence.
4. Functional validation of the exact baseline/candidate sources being measured.
5. Separate matched FPGA and ASIC baseline/candidate reports and review of
   elaboration, timing constraints, units, and power assumptions.
6. Resolution of the HQC SAC 2026 execution restriction and independent
   qualification before it can enter either target's optimization loop. No new
   HQC execution or RTL repair is authorized by this handoff.

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

The [portable full-design guide](../verification/mldsa_osh/README.md) identifies
the exact variants, commands, toolchain and retained failures. The full runs
use GHDL-translated Keccak RTL with Verilator, not an independently substituted
software SHAKE model.

| Source variant | Recorded result |
|---|---|
| Pinned baseline with portability/testbench adaptations | All 165 upstream cases pass, but an added malformed-hint case is accepted; the stronger suite [fails](verification/mldsa-portable-2026-10-12/baseline_upstream_failure/result.json) |
| Original 14-file candidate | KeyGen and upstream Verify pass in their runs, but Sign stalls and malformed-hint rejection also fails; [signing failure](verification/mldsa-portable-2026-10-12/candidate_sign_failure/result.json), [rejection failure](verification/mldsa-portable-2026-10-12/candidate_verify_failure/result.json) |
| Baseline plus canonical-hint guard | [PASS: 210 cases](verification/mldsa-portable-2026-10-12/baseline_canonical_pass/result.json) |
| Candidate plus encoder fallthrough repair and canonical-hint guard | [PASS: 210 cases](verification/mldsa-portable-2026-10-12/candidate_corrected_pass/result.json) |

Each 210-case run completes 75 KeyGen, 45 Sign, 45 upstream Verify, 12 one-bit
tamper cases and 33 canonical-encoding controls/negatives. Upstream Verify has
**9 accepted and 36 rejected** cases; the RTL flag is 0 for accept, 1 for reject.
The 33 added checks contain 18 valid controls and 15 invalid cases and use
reset-based sequences. These are finite tests, not FIPS 204 certification,
full four-state qualification, formal equivalence or PPA measurements.

- [No-EDA source exporter](../tools/export_mldsa_verified.py): select
  `guarded-baseline` or `corrected-candidate`, then use its checked source
  manifest. [Hardware handoff](HARDWARE_HANDOFF.md#ml-dsa-export-the-passing-derivatives)
  gives exact commands and comparison requirements.
- [Pinned input provenance](../third_party/mldsa_osh/README.md) and
  `python3 tools/check_mldsa_sources.py`: source checks only.
- `python3 agent/mldsa/full_kat_gate.py`: the separate legacy Vivado KeyGen-only
  gate, requiring `xvhdl`, `xvlog`, `xelab`, `xsim`; `MLDSA_ROOT` overrides its
  reference tree. This does not silently select either corrected derivative.
- `configs/mldsa_osh_asic.example.json` still describes a historical ASIC arm,
  not the newly tested guarded derivatives. Replace its source selection with
  the exact export and review all site inputs before measuring.

The 106 pinned upstream files remain unchanged. The historical ASIC arm still
contains its earlier `combined_top.v` declaration and `ntt_fifo_piso.v`
[portability edits](findings/asic/2026-07-31_mldsa_genus_port.md). Neither those
older files nor the original candidate becomes qualified by a separate
corrected variant's pass. Whole-design controller adapters and legacy dispatch
remain subject to their explicitly declared verification coverage.

## HQC preferred source baseline

The selected newer HQC baseline is
[`dbroy-iitk/HQC_SAC`, SAC 2026](../third_party/hqc_sac2026/README.md), pinned to
`4be1fe99c677d6a3ff055d380a386f65184544f1`. The source-only snapshot retains
126 unchanged upstream files (1,459,138 bytes), with Git blob/SHA-256 inventory
and upstream licensing. **Imported and byte-checked does not mean functionally
qualified.** No upstream scripts, RTL simulation or synthesis were executed
for this import.

The existing `hqc` design key, tests and ASIC configurations are not redirected
to the new snapshot. It has no qualified runnable adapter yet. Before an
executable integration can be claimed, source order, defines, parameter/width
selection, inputs, independent expected outputs, rejection behavior and memory
treatment need review. The [import notes](../third_party/hqc_sac2026/README.md#static-findings-and-qualification-still-required)
record static issues in upstream recipes without repairing them. Historical
SAC 2023 functional/PPA evidence must not be transferred to this source release.

## HQC legacy verification boundary

The existing `hqc` / `hqc_baseline` flow and
`agent/hqc/joint_kat_gate.py` use the older SAC 2023-era experiment trees.
The legacy gate runs standalone KeyGen and encapsulation before checking the
joint decapsulation/re-encryption path. It does not test all joint API
operations, nor establish independent standardized known-answer coverage.

A static review of the tracked
[`build/joint_design/decap.v`](../build/joint_design/decap.v#L392-L429)
found that `u_neq`, `v_neq` and `d_neq` are assigned comparison results but
never read. [`decap_out` is assigned directly from `encap_dout`](../build/joint_design/decap.v#L457).
This is a static rejection-path defect in that specific legacy source tree;
it is not evidence about a different HQC source release.

The attempted dynamic rejection check is **inconclusive**. Changed input files
and equal output files did not establish that the DUT loaded the changed
ciphertext. A later instrumented attempt reported unknown loaded data and
failed its valid-decapsulation control. It establishes neither successful
rejection nor a confirmed live invalid-ciphertext acceptance. No repaired
variant is qualified; unfinished harness/repair additions are not published
as supported run paths. A legacy consistency-gate pass must not be presented
as resolving this issue. The [read-only rejection review](verification/hqc-readonly-review-2026-10-12.json)
records source hashes, exact static occurrences and the limits of the attempted probes.

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
`FSM.v` duplicate declarations (`WOTS_FSM_start`, `WOTS_s_in_0_wr_en`). The
original tracked RTL remains unchanged. Fresh Vivado simulation and
Vivado/DC/Genus implementation qualification remain pending. The [portable runner](../verification/slh_portable/README.md) stages
explicit, hash-recorded Icarus changes without editing the tracked reference,
candidate, input or frozen-output files.

| Portable variant | Result | Evidence and exact scope |
|---|---|---|
| Pristine 128f, syntax adaptations only | **FAIL** | [Record](verification/slh-portable-syntax-128f-2026-10-12.json): 2,133 rather than 2,141 words; RTL verifier mismatch |
| Pristine 128f plus explicit sensitivity correction | **PASS** | [Record](verification/slh-portable-corrected-128f-2026-10-12.json): all 2,141 words match, valid verification flag 0, one-bit captured-signature corruption rejected with flag 1 |
| Selected optimized 192f, syntax adaptations only | **FAIL** | [Record](verification/slh-portable-syntax-192f-2026-10-12.json): all 4,463 words match, but the untampered signature is rejected (flag 1); its negative control is unqualified |
| Selected optimized 192f plus explicit sensitivity correction | **PASS** | [Record](verification/slh-portable-corrected-192f-2026-10-12.json): all 4,463 words match, valid verification flag 0, one-bit captured-signature corruption rejected with flag 1 |
| Candidate selected as 128f plus explicit sensitivity correction | **PASS** | [Record](verification/slh-portable-corrected-candidate-128f-2026-10-12.json): all 2,141 words match and valid/corrupted signatures are distinguished; a same-mode functional pair with the corrected 128f baseline |
| Baseline selected as 192f plus explicit sensitivity correction | **PASS** | [Record](verification/slh-portable-corrected-baseline-192f-2026-10-12.json): all 4,463 words match and valid/corrupted signatures are distinguished; a same-mode functional pair with the corrected 192f candidate |

`--fix-auth-sensitivity` adds a missing `leaf_idx` dependency to a hash-pinned
RTL sensitivity list in the staged copy. It is an explicit corrected derivative,
not an unchanged-pristine or unmodified Vivado result. Each passing derivative
covers one deterministic fixture and its live bit-flip control. Baseline and
candidate have now both passed at each of 128f and 192f. The [hardware handoff](HARDWARE_HANDOFF.md#slh-dsa-keep-mode-and-derivative-together)
exports exact same-mode source pairs; their only source differences are the
two SHA-core changes. No new timing/area measurement is supplied. The other four
SHA2 modes were not executed; these results do not establish all-mode coverage
or independent FIPS 205 conformance. A negative control is unqualified
when the untampered positive control fails. Never regenerate expected output
or switch a candidate's parameter set merely to obtain a pass.

## Public-release boundary

The [release checklist](RELEASE_CHECKLIST.md) records unresolved review of
vendor tool databases/logs and third-party notices. Those files are retained
as historical evidence; retaining them does not establish permission to
redistribute them. No repository-history cleanup is implied by this update.
