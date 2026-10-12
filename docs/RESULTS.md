# Reading and reproducing results

The repository includes historical experiments, later corrections, and
portable software improvements. Keep each result attached to its actual
source revision, configuration, and report. The current test suite does not
rerun historical FPGA or ASIC measurements.

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
