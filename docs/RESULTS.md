# Results: what was measured and what was tested

[Project home](../README.md) · [Documentation](README.md) · [Learn](LEARN.md) · [Run](REPRODUCE.md)

The repository includes historical experiments, later corrections, and
portable software improvements. Keep each result attached to its actual
source revision, configuration, and report. The current test suite does not
rerun historical FPGA or ASIC measurements.

## Current local verification

These checks were recorded on 2026-10-12. They establish functional or software
behavior within the listed scope; they do not establish new PPA improvements.
The [verification record](VERIFICATION.md) holds the detailed commands, versions,
source hashes and negative controls. [Design status](PROJECT_STATUS.md) is the
entry point for current full-design coverage across the four schemes.

| Check | Recorded result | Scope and evidence |
|---|---|---|
| ML-KEM-1024 on Adam's Bridge | 80 official ACVP sample cases; 39,840 exact word/status checks passed | [Machine-readable result](verification/mlkem-adams-bridge-acvp-2026-10-12.json); shared ML-KEM/ML-DSA core, ML-KEM API only, two-state Verilator simulation |
| Faulty ML-KEM candidate | Compiled, then rejected on its first mismatched key output | [RTL-fault record](verification/mlkem-adams-bridge-rtl-fault-2026-10-12.json); proves detection of this particular injected fault |
| ML-DSA guarded baseline | 210 cases passed: upstream operations plus tamper/canonical checks | [Result and exact derivative](verification/mldsa-portable-2026-10-12/baseline_canonical_pass/result.json); GHDL/Verilator two-state full-design simulation |
| ML-DSA guarded, encoder-corrected candidate | Same 210 cases passed | [Result](verification/mldsa-portable-2026-10-12/candidate_corrected_pass/result.json); explicit semantic corrections, not an unchanged candidate or PPA gain |
| Original ML-DSA failures | Baseline accepts an added malformed hint; original candidate also stalls Sign | [Baseline rejection failure](verification/mldsa-portable-2026-10-12/baseline_upstream_failure/result.json), [candidate Sign failure](verification/mldsa-portable-2026-10-12/candidate_sign_failure/result.json), [candidate rejection failure](verification/mldsa-portable-2026-10-12/candidate_verify_failure/result.json) |
| ML-DSA `coeff_decomposer` block | 400 vectors passed; two arithmetic faults rejected | [HDL smoke record](verification/hdl-smoke-2026-10-12.json); a block test, not full ML-DSA verification |
| SLH-DSA syntax-only Icarus 128f variant | Failed: 2,133 words instead of 2,141, with RTL verification mismatch | [Recorded failure](verification/slh-portable-syntax-128f-2026-10-12.json); a staged portable derivative, not an unmodified Vivado result. Failure is retained independently of the corrected variant below |
| SLH-DSA syntax-only Icarus 192f variant | Failed despite all 4,463 frozen words matching: RTL rejects the untampered signature | [Recorded failure](verification/slh-portable-syntax-192f-2026-10-12.json); its negative control cannot qualify a failed positive baseline |
| SLH-DSA sensitivity-corrected Icarus 128f variant | Passed: all 2,141 frozen words; valid signature accepted and one-bit captured-signature corruption rejected | [Corrected-variant record](verification/slh-portable-corrected-128f-2026-10-12.json); one deterministic fixture, not unchanged pristine RTL or independent FIPS 205 validation. |
| SLH-DSA corrected candidate selected as 128f | Passed the same 2,141-word fixture and live rejection control | [Candidate record](verification/slh-portable-corrected-candidate-128f-2026-10-12.json); qualifies a same-parameter functional source pair with the corrected 128f baseline, without new PPA measurements |
| SLH-DSA sensitivity-corrected Icarus 192f variant | Passed: all 4,463 frozen words; valid signature accepted and one-bit captured-signature corruption rejected | [Corrected-variant record](verification/slh-portable-corrected-192f-2026-10-12.json); the selected optimized derivative, one deterministic fixture. Other four SHA2 modes unexecuted; no independent FIPS 205 validation |
| SLH-DSA corrected baseline selected as 192f | Passed the same 4,463-word fixture and live rejection control | [Baseline record](verification/slh-portable-corrected-baseline-192f-2026-10-12.json); completes the same-parameter 192f functional source pair, without new PPA measurements |
| Python flows and whole-design controller | Software checks recorded; includes temporary files, mock tools and synthetic measurements | [Software record](VERIFICATION.md#portable-software-checks); not vendor EDA qualification |

The preferred [HQC SAC 2026 baseline](../third_party/hqc_sac2026/README.md) is a
new, source-only import with no functional or PPA result. A
[read-only rejection review](verification/hqc-readonly-review-2026-10-12.json)
concerns only the earlier tracked joint-design source: unused mismatch flags
are a static finding; the attempted dynamic probe is inconclusive. No repaired
HQC variant is qualified. Do not attach either the older FPGA numbers or that
legacy-source finding to the newer SAC 2026 snapshot.

The ML-DSA 210-case total is 75 KeyGen + 45 Sign + 45 upstream Verify + 12
one-bit tamper cases + 33 canonical-hint controls/negatives. Upstream Verify
contains 9 valid and 36 invalid cases; the added canonical set has 18 valid
controls and 15 invalid cases. These counts do not imply exhaustive or
independent full-standard validation. [Read the complete scope](VERIFICATION.md#real-ml-dsa-portable-variants)
and use the [exact-source hardware handoff](HARDWARE_HANDOFF.md) before measuring.

A source-integrity check, an RTL simulation pass and a synthesis result answer
different questions. None is a substitute for the others. No new Genus/DC
optimization, ASIC place-and-route, signoff or measured power result is claimed.

## Historical FPGA results

The following are selected **previously recorded** full-core measurements,
not reruns of the current checkout. Each baseline/candidate pair uses the
recorded Artix-7 `xc7a200tfbg676-1`, out-of-context, post-route flow. Do not
compare different schemes' frequencies as equivalent workloads or security
levels. Frequency is the reciprocal of an observed passing period in a
bounded search, not proof of a global maximum.

| Design and record | Recorded baseline → candidate | What changed and what to learn |
|---|---|---|
| ML-DSA, M1/M2, 2026-08-03 | 14.25 ns / 70.2 MHz → 12.43 ns / 80.5 MHz; reported +14.7% frequency, +0.8% LUT, +3.4% FF | A human-authored banked encoder removed the top-level bottleneck; the worst path moved to the challenge sampler. [Corrected ledger](findings/INDEX.md#canonical-out-of-context-flow), [baseline report](../logs/closure/mldsa_ooc_20260803/fsrch_chipv2_mldsa_baseline_1244_14.25.rpt), [candidate report](../logs/closure/mldsa_ooc_20260803/fsrch_chipv2_mldsa_5372_12.43.rpt) |
| HQC joint KEM, 2026-08-03 | 9.12 ns / 109.6 MHz → 8.62 ns / 116.0 MHz; reported +5.8% frequency, +2.2% LUT, −7.1% BRAM | The accepted flag edit lies on the original binding path; the optimized design binds on shared Keccak memory. The combined result includes earlier edits. [Corrected HQC ledger](findings/INDEX.md#hqc-chip-level-ledger-post-route-closure-joint-kem-artix-7--1-ooc) |
| SLH-DSA SHA2, S12–S17, 2026-08-29 | Six parameter sets; reported frequency gains from +4.4% (128s) to +20.4% (256f) | Carry-save changes to SHA-256/SHA-512 adders; finite five-iteration searches, differential correctness evidence, and external signature memory excluded. [Six-set report, source commit and logs](findings/slh-dsa/2026-08-29_slh_dsa_level_sweep.md) |

The reports also record rejected changes and limitations. In particular:

- **ML-DSA:** the earlier pinned-IO timing figures were retired. Cite the
  corrected OOC M1/M2 pair. Power/energy claims are not established by that pair.
- **HQC:** the superseded 114.8 MHz was a silently reverted optimized tree, not the canonical
  baseline. The superseded 117.1 MHz pristine run has an unresolved configuration
  difference; use the matched 109.6/116.0 MHz pair with its recorded limits.
- **SLH-DSA:** standalone and sweep 128f baselines differ under different search
  brackets. The six-set report retains that unresolved limitation; it does not
  claim exhaustive timing search or independent FIPS 205 validation.
- **ASIC:** earlier blackboxed butterfly results and ASIC binary-search
  “closure” claims were retracted. The [complete butterfly study](findings/asic/2026-08-12_bf2x2_asap7_complete.md)
  records matched fixed-period measurements and non-monotonic synthesis behavior.
  FPGA improvements do not automatically transfer to ASIC.

For every numerical claim, follow the dated report and its correction history.
Do not promote an older favorable number over a later corrected comparison.

## Where to find a result

| Subject | Start here |
|---|---|
| ML-DSA and HQC top-level timing | [Findings index and ledgers](findings/INDEX.md) |
| ML-DSA integration and cycle counts | [ML-DSA findings](findings/mldsa/) |
| HQC joint KEM and transferred changes | [HQC findings](findings/hqc/) |
| SLH-DSA six-configuration SHA-2 sweep | [2026-08-29 sweep](findings/slh-dsa/2026-08-29_slh_dsa_level_sweep.md) |
| Historical ASIC studies and corrections | [ASIC findings](findings/asic/) |
| Proposal outcomes and rejected edits | [Agent logs](../agent/), including each scheme's subdirectory |

The older [results summary](01_results.md), [roadmap](ROADMAP.md), and
[archived README](archive/README_RESEARCH_LOG_2026-08-30.md) are retained for
context. Where summaries disagree, inspect the dated correction and the raw
report. If a cited report is absent or cannot be tied to a source revision,
mark the claim unverified rather than choosing the more favorable number.

## Fair comparisons

A baseline/candidate comparison must match:

- Design, hierarchy boundary, operation, parameter set, and source inputs
- Tool and version, device or library corner, and implementation stage
- Clocks, IO constraints, false paths, and synthesis/implementation settings
- Memory inference, macro models, blackboxing, and excluded logic
- Functional-check coverage and any added cycles

FPGA post-route timing is not comparable to ASIC pre-layout timing. A block
improvement does not establish a top-level improvement. Genus and Design
Compiler measurements are separate comparisons even with similar settings.

## Frequency, area, power, and throughput

- The historical bounded FPGA search reports an observed passing period.
  Non-monotonic placement/routing and finite search steps mean it is not a
  proof of a global maximum frequency.
- Do not use `1 / (period - WNS)` from a failing, over-constrained run as measured
  closing frequency. The project retracted that interpretation.
- A fixed-period ASIC run reports timing at the chosen constraint. It is not
  an Fmax search, place-and-route result, or signoff result.
- Keep cell area in the reported library units until the scaling is verified.
  ASAP7-scaled area must not be silently relabeled as physical square micrometers.
- Report power only with its corner, voltage, frequency, activity assumptions,
  and analysis stage. Missing power remains missing.
- Throughput depends on both frequency and cycles for the stated operation.
  If an edit changes latency, compare the tested cycle counts as well.

## Functional and authorship limits

Record which vectors and operations ran. A checker may detect a deliberate
fault and still miss another defect. The historical corruption tests are
useful evidence of checker coverage, not an absolute guarantee.

Distinguish automatically proposed edits from manually authored changes and
human-approved rules. The ML-DSA banked encoder rewrite was human-authored
after bottleneck localization. A favorable result from that rewrite is not
evidence of autonomous architectural design.

For new measurements, use a fresh output directory and follow the
[documentation standard](DOCUMENTATION_STANDARD.md). For current commands and
missing dependencies, use [installation](REPRODUCE.md) and
[project status](PROJECT_STATUS.md).
