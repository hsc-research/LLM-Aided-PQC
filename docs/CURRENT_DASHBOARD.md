# Current FPGA proposal dashboard

The dashboard is read-only and binds to `127.0.0.1:8080`. It cannot launch the
agent, apply RTL, call an API, or accept a candidate. It reads current proposal
records under `.pqc_runs/fpga-proposals/<run>/` and the bounded current ASIC
layouts described in [ASIC dashboard observations](ASIC_DASHBOARD.md). The shared HSC Research Lab dashboard opens on current runs. The Historical
experiments navigation item preserves older displays in the same branded shell,
with explicit historical labels. Historical values are never mixed with your
current Artix-7 baseline.

From the repository root, install the optional UI dependency and start it:

```sh
python3 -m pip install -e '.[dashboard]'
python3 -m agent.dashboard
```

On your laptop, open an SSH tunnel to the server (replace `SERVER` with its
reachable hostname):

```sh
ssh -N -L 8080:127.0.0.1:8080 zabideen@SERVER
```

Then open `http://127.0.0.1:8080` on your laptop. Keep both processes running.
Do not expose the dashboard on `0.0.0.0` or a public port. It has no login.

## What is shown

- Exact profile fingerprint, FPGA part, declared Vivado version, clock period,
  and the post-synthesis measurement stage.
- Current prompt/API/review status. Missing or partially written records are
  reported; a stale refresh leaves an explicit message rather than claiming a
  run finished. Refreshes occur every five seconds, with manual Refresh and pause controls.
  Unchanged records do not redraw the current results. Updates are deferred while
  keyboard focus is in a result or the run selector.
- A side-by-side baseline/candidate table, with unmeasured candidate values
  explicitly marked Not run. Baseline latency, power, and inferred-latch count
  remain unknown when the imported reports do not establish them.
- Preliminary imported report observations: setup and hold slack, LUTs, FFs, RAM blocks,
  DSPs, no-clock and unconstrained-path counts. Missing values stay unknown.
  Positive slack does not establish complete timing coverage. `latch_loops`
  counts do not establish the number of inferred latches.
- API attempt count, recorded usage/cost, and declared-price cost estimates.
  Unknown usage or cost stays unknown; an estimate is not a provider billing cap.
- Functional verification, candidate PPA measurement, and automatic acceptance
  remain unqualified for this proposal-only workflow. No percentage improvement
  is computed without verified, matching baseline/candidate measurements.

The dashboard verifies the frozen prompt hash and each review/API record's
context hash before displaying it. It does not re-read arbitrary paths listed
inside records, inspect environment variables, expose source text, or validate
that imported reports came from the declared execution. It is a monitoring
view, not a substitute for verification gates. Stop/restart may leave a last
record marked RUNNING: this is recorded status, not proof of a live process.

The `/legacy` page retains older experiment displays with an explicit historical
banner. Those records do not qualify the current source export. No older RTL,
logs, or results are changed by opening either page.

## Offline checks

```sh
python3 -m unittest discover -s tests -p 'test_current_dashboard.py' -v
node tests/test_current_dashboard_ui.js
node tests/test_legacy_dashboard_ui.js
```

Install the dashboard extra to include Flask endpoint tests. No API or FPGA/ASIC
tool is called by these checks.

## Presentation and accessibility checks

The shared shell uses the lab's original logo and the University of Idaho mark
from the lab website, with the University's Pride Gold, black and white palette.
Sources and usage notes are retained in `agent/dashboard_static/brand/README.md`.
Assets are local; the dashboard does not load external fonts, images or trackers.

The current view includes a skip link, semantic headings, table captions and row/
column headers, visible keyboard focus, text status labels, responsive layouts,
pause controls, and empty/loading/error states. Unknown values and pending
candidate results are explicit. Historical detail controls support Enter/Space,
with Escape, focus containment and return in the details dialog. Historical auto-
refresh also pauses while controls have keyboard focus or a dialog is open.

Automated checks cover backend responses and DOM behavior, not formal Title II
or WCAG certification. A full browser/assistive-technology review remains a
separate check; do not label these tests as a complete accessibility audit.

### Critical paths and resource drill-down

The current FPGA view extracts setup and hold paths from the frozen timing text:
startpoint, endpoint, path group, slack, data-path delay, logic and net-delay
components, and logic levels. Missing path fields remain unknown. Post-synthesis
routing components are estimates, not post-route measurements.

When the frozen utilization report includes hierarchical rows, the view lists
up to twelve resource-heavy instances ranked by LUT count. Hierarchical rows can
overlap; their resource counts must not be added. A flat utilization report does
not establish block ownership, so the view explicitly reports missing hierarchy.
The source-details section identifies the frozen report text using SHA-256 hashes;
it does not expose an arbitrary-file browser or follow paths embedded in records.


### FPGA and ASIC remain separate

The overview counts FPGA proposal records and ASIC measurement records. Select a
run to inspect its target-specific values. FPGA tables show LUTs, FFs, BRAMs and
DSPs; ASIC tables preserve the recorded cell-area units, library/corner, and
reported dynamic/leakage/total power. A candidate ASIC record is labeled Candidate,
not silently promoted to a baseline. No matched comparison is fabricated.

ASIC source-manifest/configuration digests and path evidence type are shown in
the details. Adapter-reported path observations are distinct from values parsed
from a DC report. This dashboard does not independently qualify an adapter,
validate mapped-memory behavior, prove functional correctness, or establish
workload power. There are no actual new ASIC results bundled with the dashboard.

## Offline review of a retained response

A completed paid response can be reviewed again with the
[offline response-review command](FPGA_AGENT_FEEDBACK.md#review-a-saved-response-without-another-api-call).
The dashboard checks the fixed `review-offline.json` sidecar against the original
context, prompt, run, raw response and request claim. A valid sidecar can display
`STOP` or a valid edit preview while preserving and showing the original failed
run and its token usage/cost. No model call or RTL change is implied.

Legacy responses that were not originally hashed into their paid-run records
remain labeled as an unverified provider association. Source checks are historical
checks made by the offline reviewer; this read-only dashboard does not read live
RTL paths. Model rationale stays unverified commentary and is not displayed as
measured timing, placement evidence or a user requirement.
