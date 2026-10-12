# Whole-design-first optimization controller

## Status and scope

`agent/whole_design.py` is an opt-in, offline-tested controller for future FPGA
and ASIC runs. **No new EDA optimization result is established by this change.**
Its subprocess fixtures contain synthetic numbers solely to test control flow.
Built-in command adapters cover typed LLM proposals, existing ASIC measurement,
and the exact existing ML-DSA KeyGen gate. Vendor path extraction still requires
site qualification; there is no complete new cryptographic verification suite. Missing sources, tests, commands, report
fields, latency evidence, or critical-path ownership mappings block execution.

The existing `agent.run` / `chip_orchestrator` FPGA workflow and
`agent.asic_synthesis` fixed-period measurement entry point remain separate.
This controller is the conservative generic route for explicitly configured
whole-design experiments. It does not silently fall back to block-level PPA.

## The loop

1. Freeze the ordered complete source manifest and all declared immutable inputs.
2. Run the configured **full-design** functional gate, including every declared
   operation/parameter check and per-operation cycle count.
3. Measure the entire design under the frozen configuration.
4. Inspect several worst setup paths, including original report line ranges.
   Map tool-reported instance paths to reviewed editable RTL ownership. Mapping
   uses exact hierarchy components and longest prefix; no substring guessing.
5. Give the proposer those paths, a small allowlisted file set, source text,
   current measurement, and recent failure feedback.
6. Apply only typed `edit_ops` operations, bounded by file and changed-byte budgets.
7. Rerun the full-design functional gate on the edited source bytes.
8. Remeasure the entire design with identical declared configuration and compare
   actual measured metrics. Reject missing evidence, functional or latency
   regressions, area regressions beyond the declared allowance, timing-floor
   violations, or gains below the configured threshold.
9. Retain accepted RTL, use the **new** full-design critical paths for the next
   proposal, and repeat until the candidate budget or proposer stop is reached.

Block checks can be additional fast filters inside a trusted adapter. They never
replace the full-design gate or full-design measurement used for admission.

## Plan first

Copy [the deliberately blocked template](../configs/whole_design.example.json)
to `configs/whole_design.local.json`, then supply the actual source closure,
immutable inputs, mapping, complete checks, and reviewed adapter commands.
The template wires the built-in adapters for the supported ML-DSA KeyGen-only
profile; change the verification adapter for a different design.
The example period and improvement threshold are illustrative configuration,
not measured PPA or a qualified noise margin.

```sh
python3 -m agent.whole_design --config configs/whole_design.local.json
```

This only validates and prints a plan. `BLOCKED` means a prerequisite is missing.
`CONFIGURED_NOT_RUN` means static configuration is present; it does **not** mean
that the adapters, tools, design, functional coverage, or PPA have been validated.

Only after reviewing the plan and command costs:

```sh
python3 -m agent.whole_design --config configs/whole_design.local.json --execute
```

Execution may consume licensed-tool or explicitly configured LLM/API budget.
The core controller does not call an LLM itself, execute model-provided commands,
install software, push Git changes, or launch CI. Proposals are JSON data.
Only trusted commands from the local configuration can execute.

### Configuration requirements

- `target` / `backend`: `fpga` / `vivado`, or `asic` / `genus` or `dc`.
- `scope`: exactly `full_design`. `top` is the whole accelerator top.
- `sources`: complete ordered synthesis source closure, rooted at `root`.
- `immutable_inputs`: constraints, testbenches, independent references, vectors,
  ROM contents, include headers, adapter scripts/dependencies, site configuration,
  libraries, and any other input capable of changing the comparison. The
  whole-design configuration itself is automatically included. Absolute immutable
  library paths outside the checkout are allowed and only read/hashed.
- `editable_files`: a small reviewed RTL subset of `sources`; tests and checker
  inputs must be in `immutable_inputs`, never this allowlist.
- `instance_to_file`: qualified hierarchical instance prefixes mapped to editable
  files. Every sampled worst path needs a supported mapping. A path becoming
  unmappable after an edit rejects the candidate.
- `required_checks` and `operations`: explicit functional and latency coverage.
  `verification_profile: "mldsa_keygen_75"` expands the exact built-in ML-DSA
  check/latency keys; conflicting custom lists are refused.
  Existing ML-DSA, SLH-DSA and HQC gates have limited coverage; wrapping one does
  not expand that coverage. See [design status](PROJECT_STATUS.md).
- `measurement`: stage, fixed period, exact tool release, technology, corner,
  effort/directives, seed policy, memory model, constraints, and a qualification
  record identifier. Add all site-relevant defines, parameters, implementation
  settings, environment settings, and library interpretation to this object.
  ASIC is currently restricted to logical `post_synth`; FPGA allows `post_synth`
  or `post_route`, which must never be compared to each other.
- `commands`: argument arrays for `verify`, `measure`, and `propose`. Every command
  consumes `{request}` and `{response}`. Commands run from the design root without
  shell expansion. Include their scripts and dependency/config files in immutable
  inputs. Executables and tool installations must be controlled by the site.

The controller can enforce the declared manifest, not discover missing hidden
inputs or prove a trusted adapter actually ran all tests. Review and qualify
adapters against known failures, complete source manifests, and real tool output.
A reported `PASS` remains the configured test scope, never a formal-equivalence,
cryptographic conformance, side-channel, or timing-signoff claim.

## Built-in adapters, without hand-written glue

The template already supplies real `python3 -m agent.whole_design_adapters`
entry points. Inspect their commands with `--help` before execution.

### Typed LLM proposer

`propose-llm --model MODEL --max-tokens 4096 --request PATH --response PATH`
uses the existing `agent.llm_client` and refuses to create a client unless
`PQC_ENABLE_LLM=1`. Install the existing `[llm]` extra separately if needed.
The template uses the model name already used by this repository; confirm model
availability and pricing with your provider before enabling it.

The proposer sends the selected RTL text, critical paths, measurement settings,
metrics, and recent failure feedback to that configured model. Review permission
to send proprietary RTL and these details before opting in. It makes one model
request per attempted proposal and records the actual request/response locally.
The candidate budget bounds these calls; it is not a currency spending limit.
Only strict JSON with allowlisted `replace_exact` edits or `STOP` is accepted.
Truncated/tool-directed replies, command operations, and unallowlisted files are
refused. The adapter previews edits; the controller owns all RTL writes.

### ASIC measurement CLI

First prepare the exact effective measurement configuration without EDA:

```sh
python3 -m agent.whole_design_adapters describe-asic --site-config configs/site_asic.local.json
```

Copy `asic_effective_config` from this output into `measurement` and add every
`required_frozen_inputs` entry to the source/immutable manifests as appropriate.
The controller also requires matching outer period, memory model, exact library
corner/version/effort, and declared SDC. Use `seed: "not_applicable"`; this ASIC
adapter cannot configure random seeds. `technology` is a declared human label;
the effective plan and library hashes identify the actual libraries used.

`measure-asic --site-config ... --extractor-config ... --request ... --response ...`
then runs the existing fixed-period ASIC flow in a fresh invocation-local
directory and calls a separately configured, qualified timing-path extractor.
Its JSON command file has this shape:

```json
{
  "argv": ["python3", "site/extract_paths.py", "{timing_report}", "{paths_json}"],
  "inputs": ["site/extract_paths.py"]
}
```

Freeze this JSON and every extractor input in `immutable_inputs`. The extractor
must write the path-array contract below. No vendor parser is guessed or shipped
as qualified merely to make an example executable. Absent extraction support
blocks search, while plain ASIC measurement remains available independently.

### Existing ML-DSA KeyGen gate

`verify-mldsa-keygen --source-dir ... --reference-root ... --request ... --response ...`
runs the existing full-top KeyGen gate for exactly 25 vectors at each of II/III/V.
It checks that every measured candidate source was actually consumed and freezes
all reference, vector, and testbench inputs. It records each of the 75 individual
cycle counts, so an individual vector slowdown cannot hide behind a lower mean.
The measured source manifest must use the explicit single override directory.

Use `verification_profile: "mldsa_keygen_75"` with `top: "combined_top"` rather than
hand-entering 75 operation keys. `describe-mldsa-keygen` prints the exact expanded
profile without invoking a simulator. Signing, signature verification, extra
handshake claims, and other parameter coverage are rejected by this adapter.
Other designs still need an exact qualified functional/latency adapter. These
wrappers have offline fixture coverage; licensed-tool runs remain site work.

## Adapter protocol

Each invocation receives a new directory with `request.json`. It must create
`response.json` at the supplied path and return exit code zero. Responses contain:

```json
{
  "schema_version": 1,
  "request_sha256": "SHA256 of the exact request.json bytes"
}
```

The request includes `phase`, `run_id`, the current source SHA-256 map, and the
frozen `configuration`. A proposer also receives selected critical paths,
`allowed_files`, `rtl`, current `measurement`, and recent `feedback`.

Verification and measurement responses require nonempty, invocation-local
report files with hashes. Absolute paths are acceptable only when they resolve
inside the invocation directory; symlinked reports and path escapes are refused.

```json
{
  "reports": {
    "functional": {"path": "functional.rpt", "sha256": "SHA256 of report bytes"}
  }
}
```

### Verification response

Add `status: "PASS"`, `scope: "full_design"`, `checks` mapping every configured
check to `"PASS"`, and `latency_cycles` mapping exactly the configured operation
keys to positive integer cycle counts. Supply the `functional` evidence report.
Any failure, inconclusive result, missing check, or missing cycle count rejects
verification. The wrapper must check the underlying process exit code and real
self-checking verdict, and must consume the request's edited source files.

For example, a site wrapper around `agent/mldsa/full_kat_gate.py` must preserve
that gate's actual key-generation-only limitation and extract its actual cycle
evidence. It cannot label an untested signing or verification operation `PASS`.

### Measurement response

Add these fields:

- `status: "MEASURED"`, `scope: "full_design"`, and the exact `configuration`
  received in the request
- `metrics.worst_setup_slack_ns` and the configured area metric
- `area_unit`, unchanged across comparisons
- `reports.timing` and `reports.area`, plus useful original additional reports
- `critical_paths`: at least `critical_path_count` distinct records, each with
  `id`, `startpoint`, `endpoint`, `slack_ns`, `instances`, `report`, `line_start`,
  and `line_end`

`instances` must come from qualified tool hierarchy evidence, not the LLM.
`report` names a report key. Line ranges are one-based and inclusive. The worst
path slack must match the summary slack. Paths must reference `reports.timing`
and have distinct endpoint pairs and line ranges. Same-endpoint alternate routes
are intentionally not counted as separate critical paths in this version. Preserve real path values, endpoint
identities, and evidence locations; do not duplicate a path to satisfy the count.

For FPGA, the primary area metric can be `lut`, `ff`, `dsp`, or `bram`; ASIC uses
`cell_area_reported` and its declared unit. The area guard protects that selected
metric only. Review other resource budgets in the site adapter and record them
in reports; the controller is not an automatic multi-resource Pareto optimizer.

### Concrete bridge to existing ASIC measurement

`asic_measurement_response` translates the existing
`agent.asic_synthesis.run()` result schema. It checks the actual source/order
and immutable manifest hashes, backend/top/stage/scope, period, memory mode,
the entire effective ASIC plan (including defines, parameters, compile mode,
libraries and environment), version/corner/effort declarations, unit evidence,
audited clock period, and
report hashes. The original `result.json` must match the supplied object.
The ASIC run directory must be newly created inside this invocation's directory.

A reviewed **site measurement adapter** can use this pattern:

```python
from pathlib import Path
from agent import asic_synthesis
from agent.whole_design import asic_measurement_response

# request_path and response_path come from the configured argv, not the model.
plan = asic_synthesis.load_config("configs/site_asic.local.json")
plan["output_root"] = str(Path(response_path).resolve().parent)
result = asic_synthesis.run(plan)
# Site-specific, qualified extraction must preserve real report line ranges
# and tool-reported hierarchical instances. This function is NOT bundled.
paths = extract_qualified_site_paths(Path(result["run_dir"]) / "timing.rpt")
asic_measurement_response(result, request_path, response_path, paths)
```

The CLI above removes the need to write this wrapper by hand. The ASIC site config must itself declare `scope: "full_design"`, use the exact
ordered source manifest, and list libraries/configs that are frozen in the
whole-design manifest. The bridge performs no speculative vendor-text parsing,
infers no Fmax from fixed-period slack, and does not turn vectorless power into
validated workload power. Raw `asic_synthesis` output alone is insufficient for
search because it does not yet provide qualified path-to-RTL and full-design
functional/latency adapters.

For Vivado, a site adapter must regenerate the full-design netlist/checkpoint
from the current request's sources and extract several real paths and resource
counts at the configured stage/period. The existing closure runner is not a
fixed-period adapter merely because it emits an Fmax number. Do not translate
Fmax to this controller's slack objective or reuse a stale checkpoint.

### Proposal response

Add `status: "PROPOSED"`, a short `strategy`, `source_model`, and `experiment`
using the existing [typed edit format](../agent/edit_ops.py):

```json
{
  "experiment": {
    "name": "small-reviewed-change",
    "files": [{
      "path": "rtl/responsible_block.v",
      "ops": [{"op": "replace_exact", "old": "exact old RTL", "new": "exact new RTL", "expect": 1}]
    }]
  }
}
```

The file must be in the current request's exact allowlist. A proposer can instead
return `status: "STOP"` to finish without another edit. Repeated edit attempts on
the same source state are rejected before verification/EDA even if renamed;
repeated resulting source states are also filtered during the run.

## Acceptance, rollback, and records

The objective is either larger fixed-period `worst_setup_slack_ns` or smaller
selected area. `min_improvement` is an absolute positive threshold in the metric's
units. Set it above the qualified flow's variation/measurement precision; the
controller does not infer statistical significance from one run.

Default guards require nonnegative setup slack, no selected-area growth, and no
per-operation cycle regression. Area optimization additionally requires no setup
slack regression. A configured area-growth fraction is measured against the
current incumbent, so avoid nonzero allowances when a fixed global budget is
required. Power optimization and mixed backend/stage comparisons are refused.

`edit_ops` validates all edits before writing, atomically replaces each file, and
restores candidates rejected or interrupted during checking. There is no global
multi-file filesystem transaction and no guarantee against power loss or SIGKILL.
The checkout lock serializes cooperating top-level runs. Declared local source
and immutable files are snapshotted around adapter calls; unexpected mutations
are detected and restored. External immutable libraries are never modified by
the controller; a detected change blocks the run and requires site investigation.
Adapters are trusted processes, **not** a security sandbox: undeclared file writes
or background processes remain outside the declared transaction contract.

Every run creates `.pqc_runs/whole_design/<run-id>/` containing:

- `manifest.json`: frozen configuration and baseline sources
- fresh per-invocation request/response, exact command and stdout/stderr log
- hashed functional/timing/area evidence and original ASIC artifacts when used
- `outcomes.jsonl`: bounded candidate attempts, failure feedback, rejections and
  final accepted source fingerprints
- `result.json`: completed or blocked result, last retained source state, and
  explicit `timing_signoff: false` / `workload_power_validated: false`
- retained candidate backups for manual recovery if rollback or the process fails

Outcome rows use the `experiment_history` final-acceptance contract:
`history_schema: 1`, `history_state: "finally_accepted"`,
`evidence_stage: "full_design"`, `correctness_status: "PASS"`, `verdict: "ACCEPT"`,
`candidate_sources`, and structured `proposal`. Rejected attempts are
`history_state: "chip_rejected"`. No learned rule is automatically distilled.
These per-run journals can be passed explicitly to history readers; existing
chip journals are not overwritten. A final acceptance is valid only while the
recorded source and immutable-input hashes match the currently applied files.
The older chip-driver prompt path does not automatically ingest these separate
per-run journals.

Normal bounded completion can contain zero accepted proposals. `BLOCKED` is not
an optimization result. A baseline or configuration failure prevents proposal
work; ordinary candidate rejection permits another bounded attempt. Check both
`result.json` and the outcomes before describing a run as successful.

## Offline verification and file map

```sh
python3 -m unittest discover -s tests -p test_whole_design.py -v
```

The tests cover baseline failure, missing latency, candidate failure, rollback
on timeout/interruption/input mutation, metric/configuration regressions, duplicate
proposals, critical-path retargeting, stale/missing reports, both target choices,
proposal budgets, the existing ASIC result-schema bridge, strict proposer output,
full effective-plan mismatches, and exact ML-DSA KeyGen-only coverage. They invoke only
small local Python fixtures and provide no hardware PPA or cryptographic result.

| File | Purpose |
|---|---|
| [agent/whole_design_adapters.py](../agent/whole_design_adapters.py) | Built-in opt-in LLM, ASIC and exact ML-DSA KeyGen adapters |
| [tests/test_whole_design_adapters.py](../tests/test_whole_design_adapters.py) | Offline adapter tests with all paid/EDA/simulator calls mocked |
| [agent/whole_design.py](../agent/whole_design.py) | Controller, strict adapter contract, ASIC result bridge |
| [configs/whole_design.example.json](../configs/whole_design.example.json) | Deliberately incomplete site configuration template |
| [tests/test_whole_design.py](../tests/test_whole_design.py) | Offline synthetic subprocess regressions |
| [agent/edit_ops.py](../agent/edit_ops.py) | Existing typed edit and atomic per-file write/restore helpers |
| [agent/run_safety.py](../agent/run_safety.py) | Existing input hashing, checkout locking and command/transaction helpers |
| [agent/asic_synthesis.py](../agent/asic_synthesis.py) | Existing fixed-period Genus/DC synthesis and report provenance |
