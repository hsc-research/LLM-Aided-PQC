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
that a human has associated with the reported critical path. These are the only
**editable files**, selected with `--rtl`. Supply top-level interfaces,
instantiations and relevant cross-module logic separately with **read-only**
`--context-rtl`. Reading a file does not authorize editing it. There is no automatic
hierarchy-to-file proof in this preliminary route. Substitute actual file paths
and source line ranges:

```sh
python3 tools/prepare_fpga_proposal.py prepare \
  --preparation build/launch/mldsa-latch-corrected-fpga/preparation.json \
  --rtl build/profiles/mldsa-latch-corrected-fpga/REPLACE_WITH_PROFILE_SOURCE_PATH.v \
  --context-rtl build/profiles/mldsa-latch-corrected-fpga/REPLACE_WITH_TOP_SOURCE_PATH.v:START:END \
  --out .pqc_runs/fpga-proposals/mldsa-review-001
```

The selected file must be in the exact profile source list; inspect `profile.json`
for its path. The command finds reports at the frozen launch configuration's
output directory and requires `timing.rpt`, `utilization.rpt`, `check_timing.rpt`
and `drc.rpt`. It does not invent missing data or silently truncate reports.

`prompt.json` contains the selected editable RTL, read-only source context and
complete report text. Inspect it before sharing
with an API provider. `proposal-context.json` freezes source/configuration/report
hashes and labels imported results preliminary. Matching hashes establish which
bytes were imported, not that Vivado actually used them during an earlier run.
No source file, constraint, or baseline report is modified.

### Top-down context without widening edit permission

Repeat `--context-rtl PATH` for a full read-only file, or
`--context-rtl PATH:START:END` for an explicit one-based, inclusive line range.
For example, `top.v:50:90` selects lines 50 through 90 of a file that must be in
the frozen profile. Replace those example numbers with ranges reviewed against
**your exact exported source**, not upstream files or a different derivative.
Specify top-level context first, then the relevant downstream dependencies.

The prompt includes a source overview with the declared top, compile settings,
the exact ordered source list, and each source's text role. It directs analysis
from the top-level interfaces and instantiations toward the actual reported
whole-design critical paths before considering local edits. This is a **partial
source-context view**, not an elaborated hierarchy graph or proof of ownership
of synthesized cells. In particular, rebuilt synthesis hierarchy and similarly
named generated cells are not enough to identify an RTL edit location.

Each read-only entry records the full source's SHA-256, byte and line counts,
selected line range, exact span SHA-256/byte count, and omitted line counts.
Lines outside a span are explicitly unknown, not assumed irrelevant. Read-only
text preserves UTF-8 bytes and CRLF; line ranges split on LF boundaries. Editable
text uses universal newlines, matching the existing exact-anchor preview, while
its input hash still binds the original bytes. All profile sources, including
unselected files and omitted lines, remain frozen and are rechecked before a
request and during review. Reports are read and hashed from the same byte snapshot.

The following fail closed before creating a prompt:

- A read-only source outside the exact exported profile, a direct symlink target,
  or a colon-containing filename ambiguous with range syntax
- A source selected as both editable and read-only, duplicate/overlapping ranges,
  invalid/reversed/out-of-file line numbers, or duplicate canonical profile paths
- More than three editable files or 64 read-only selections
- More than 4 MiB in one scanned read-only source or 16 MiB across unique scanned
  read-only sources
- A combined system/user prompt exceeding **192 KiB**, including the complete
  reports, source text and metadata; nothing is silently truncated

Canonical parent-directory aliases still resolve through exact profile membership.
Selecting a small span from a large generated file is supported within the scan
limits. Reduce explicit spans when the total prompt is too large. No report is
dropped to make room, and no model request is made by `prepare`.

The source-context feature changes neither the three-file edit limit nor the
exact-anchor, size, interface/latency and verification requirements. A proposed
edit to any read-only file is rejected, even if all its text was provided. A fresh
prepared prompt is only an offline artifact; it does not authorize another paid
request or imply that a defensible optimization exists.

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

## Review a saved response without another API call

If Claude completed generation but the local response review failed, **do not run
another paid proposal or remove the request claim**. After updating this code,
review the retained response offline:

```sh
python3 tools/prepare_fpga_proposal.py review-existing \
  --context .pqc_runs/fpga-proposals/mldsa-review-002/proposal-context.json
```

This command needs no key, unlock, model, price or `PQC_ENABLE_LLM`. It requires a
finished `FAILED` record at `response_review`, one recorded generation attempt,
returned token usage, the original context/prompt, response and claim, and unchanged
source/configuration/report hashes. It creates **`review-offline.json`** once and
refuses to overwrite it. The original `proposal-run.json`, `proposal-response.json`,
`.proposal-request.lock`, prompt, context and RTL remain byte-for-byte unchanged.

The sidecar binds the original run, request claim, context, prompt, raw response
and decoded proposal with hashes. New paid runs record the raw response hash
before reviewing it. Older runs did not: their offline review is explicitly marked
`LEGACY_RESPONSE_NOT_BOUND_BY_PAID_RUN`. It binds the retained local bytes now;
it cannot prove retrospectively that those bytes are unchanged provider output.
No API request is made to establish that association.

The dashboard derives the displayed decision from a valid offline sidecar while
also showing the **original failed status, failure stage and paid usage**. It
checks the local evidence hashes before using the sidecar. Source hashes are
checked by the offline review command; the dashboard never follows recorded live
RTL paths and does not claim a live integrity check. Changed or missing local
response/run/claim evidence excludes the derived decision.

### Bounded response formatting

New prompts request exactly one plain JSON object. The defensive parser also
accepts exactly one `json` or unlabeled Markdown code fence, with an optional
trailing `Rationale:` or `**Rationale:**` section. That section is unverified model
commentary, not a source of decisions, commands, timing requirements or measured
hardware facts. It remains in the original raw response and is not promoted into
the dashboard's measurements. The JSON object alone determines `STOP` or
`PROPOSED`.

The parser does not hunt for the first object in arbitrary prose or repair broken
JSON. Multiple objects/values/fences, duplicate keys, non-finite numbers, non-object
roots and nesting beyond 64 levels are rejected. Raw responses are bounded to
192 KiB and trailing rationale to 32 KiB. Numeric RTL selectors attached to
identifiers, such as `signal[0]`, `bus[31:0]` and `genblk1[2].KECCAK`, are allowed
in rationale. Other braces/brackets, additional fences, unlabeled trailing text
and standalone JSON-valued rationale lines are rejected as ambiguous. Existing
frozen prompts and raw responses are never rewritten for normalization.

`STOP` means no edit was proposed. It does not validate the accompanying rationale.
For example, a model's suggested delay target is not a user requirement, and a
routing-delay estimate from a synthesis report is not evidence of a measured
placement problem or routed timing result.

A `PROPOSED` response still passes the same allowlist, exact-anchor, edit-size and
safe-preview gates. `EDIT_PREVIEW_VALID_NOT_APPLIED` is only a preview: the command
never applies RTL, runs KATs or synthesis, or accepts a candidate. After a separately
approved edit, exact-source functional verification and matched baseline/candidate
measurements are still required. The 210-operation exported ML-DSA adapter below
is not invoked automatically by proposal review.

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
