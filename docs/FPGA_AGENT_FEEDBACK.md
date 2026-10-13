# FPGA agent feedback and proposal review

[Project home](../README.md) · [Whole-design controller](WHOLE_DESIGN.md) · [FPGA latch correction](fpga/MLDSA_LATCH_CORRECTION.md)

## What can run now

The exact exported ML-DSA sources can be checked with the new 210-case RTL
verification adapter. Vivado OOC synthesis can collect fresh feedback from those
same sources. A bounded Claude request can propose one edit for review. **This is
not yet automatic implementation-qualified optimization:** mapped-memory behavior,
structural-warning qualification and timing-path ownership still require site
checks. The strict controller retains these requirements and rejects the
preliminary measurement response. A proposal alone never edits RTL or proves a
PPA improvement.

Use the explicitly named latch-corrected FPGA baseline for a new experiment.
Preserve the old baseline and its reports; the new derivative has a different
source fingerprint. Compare baseline and candidate at the same tool version,
part, clock period, constraints and measurement stage.

## Prepare feedback without an API key or charge

After the prepared Vivado run finishes, select one to three exported RTL files
that a human has associated with the reported critical path. There is no automatic
hierarchy-to-file proof in this preliminary route. Substitute actual file paths:

```sh
python3 tools/prepare_fpga_proposal.py prepare \
  --preparation build/launch/mldsa-latch-corrected-fpga/preparation.json \
  --rtl build/profiles/mldsa-latch-corrected-fpga/REPLACE_WITH_PROFILE_SOURCE_PATH.v \
  --out .pqc_runs/fpga-proposals/mldsa-review-001
```

The selected file must be in the exact profile source list; inspect `profile.json`
for its path. The command finds reports at the frozen launch configuration's
output directory and requires `timing.rpt`, `utilization.rpt`, `check_timing.rpt`
and `drc.rpt`. It does not invent missing data or silently truncate reports.

`prompt.json` contains the selected RTL and report text. Inspect it before sharing
with an API provider. `proposal-context.json` freezes source/configuration/report
hashes and labels imported results preliminary. Matching hashes establish which
bytes were imported, not that Vivado actually used them during an earlier run.
No source file, constraint, or baseline report is modified.

## Optional single Claude request

Only run after approving the chosen model, data sent and expected API spending.
[Set up the local encrypted Claude vault](CLAUDE_CREDENTIALS.md) first. The
foreground command prompts for its passphrase; the key and workspace ID never
need to be retyped for each run. Install the project's optional `llm` dependencies.
Supply current prices
for the exact model and your budget; the following values are placeholders:

```sh
PQC_ENABLE_LLM=1 python3 tools/run_fpga_proposal.py \
  --context .pqc_runs/fpga-proposals/mldsa-review-001/proposal-context.json \
  --model YOUR_APPROVED_MODEL \
  --input-usd-per-million CURRENT_INPUT_PRICE \
  --output-usd-per-million CURRENT_OUTPUT_PRICE \
  --budget-usd YOUR_APPROVED_BUDGET --max-tokens 4096
```

One token-count request precedes at most one generation request. SDK retries are
disabled. The estimate reserves 10% extra input tokens plus 1024 tokens and the
full output limit. This is an **estimated cost check, not a guaranteed billing
cap**: the provider's count estimate and supplied pricing may differ from billing.
Use account-side spending controls for a hard limit. A timed-out generation has
unknown cost and is never automatically retried. Do not start another request
until checking provider usage. Reusing the same request directory is refused.

`proposal-run.json` records state, model, estimated cost and returned token usage;
it never records the key or SDK exception text. Bounded failure-stage/category
fields distinguish local unlock, token-count, generation and review failures.
For a confirmed zero-generation preflight failure, use the explicit
[offline recovery command](CLAUDE_CREDENTIALS.md#recover-a-confirmed-preflight-failure-without-erasing-history)
to prepare a new context while preserving the original claim and record. `review.json` states whether the
typed edit can be previewed against the original source. `EDIT_PREVIEW_VALID_NOT_APPLIED`
means only the edit anchors and allowed paths passed validation. Correctness,
latency and PPA remain unverified. There are no new power measurements here.

## Exact-source verification adapter

```sh
python3 -m agent.mldsa.exported_kat_adapter --describe
```

Use the returned complete check list, all 210 latency keys and immutable fixture
inputs when configuring the whole-design controller. The invocation is:

```sh
python3 -m agent.mldsa.exported_kat_adapter \
  --request REQUEST.json --response RESPONSE.json --jobs 8 --timeout 1800
```

Requests use the existing controller's frozen source/configuration format. This
adapter compiles the selected exported Verilog files directly, including the
exported Keccak netlist; it does not regenerate, replace or patch RTL. It runs
75 KeyGen, 45 Sign, 45 Verify, 12 modified-input and 33 canonical-hint cases across
levels II/III/V, and records each case's latency. Verilator simulation remains a
finite two-state check. It is not formal equivalence, complete standard
certification or mapped-memory verification. The fixture's documented testbench
repairs are retained. Tool installation is an explicit site prerequisite.

## Fresh Vivado feedback adapter

```sh
python3 -m agent.fpga_feedback --request REQUEST.json --response RESPONSE.json
```

This writes a reviewed launch script without executing Vivado. Add `--execute`
only on the licensed server. Use an absolute, frozen XDC path in the controller
configuration. The adapter records actual Vivado version, full source hashes,
OOC utilization/setup reports, timing checks, DRC, five paths, functional netlist
and checkpoint. It returns `BLOCKED` with `PRELIMINARY_POST_SYNTH_NOT_ADMITTED`
feedback even if synthesis succeeds. The missing implementation checks are
listed in the response; no boolean is forged to pass controller admission.
Post-synthesis slack is not routed timing closure. No power estimate is produced.

## Validation scope

Tests use clearly labeled synthetic API/simulator responses to exercise failure,
source-drift, budget, unknown-cost, coverage and no-edit handling. Such tests do
not qualify Vivado or prove that an optimization works. Real site feedback and
hardware results must be recorded separately from fixture results.
