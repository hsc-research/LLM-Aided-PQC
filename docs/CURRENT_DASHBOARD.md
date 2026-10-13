# Current FPGA proposal dashboard

The dashboard is read-only and binds to `127.0.0.1:8080`. It cannot launch the
agent, apply RTL, call an API, or accept a candidate. It reads current proposal
records under `.pqc_runs/fpga-proposals/<run>/`. The initial page does not mix
historical baseline values with your current Artix-7 results.

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
  run finished. Refreshes occur every five seconds, with a manual Refresh button.
- Preliminary imported report observations: setup slack, LUTs, FFs, RAM blocks,
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
```

Install the dashboard extra to include Flask endpoint tests. No API or FPGA/ASIC
tool is called by these checks.
