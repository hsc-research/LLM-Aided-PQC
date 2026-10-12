# Local experiment dashboard

The dashboard reads recorded proposal logs, selected simulation output, and
local process status. It is a convenience view, not an independent checker.
A historical `ACCEPTED` label does not mean the current checkout was rerun.

## Run locally

From the repository root, in the Python environment from
[installation](REPRODUCE.md):

```bash
python3 -m pip install -e '.[dashboard]'
python3 agent/dashboard.py
```

Open http://127.0.0.1:8080 in your browser. The server binds to loopback by
default. Stop it with Ctrl+C. Do not expose this unauthenticated research
viewer on a public interface or use a broad process-kill command to restart it.

The dashboard does not need an LLM key. Installing Flask is separate from
running a paid proposal experiment.

## Interpret the display

- Proposal outcomes and costs come from the retained JSONL logs.
- Simulation text may be from an earlier run. Inspect the timestamp, source
  version, vector coverage, and final process status before treating it as
  evidence for a candidate.
- Process detection and aggregate summaries are hints. Inspect the specific
  report or run record when diagnosing a failure or citing a result.
- Timing and resource numbers may describe different scopes or tool stages.
  Follow [RESULTS.md](RESULTS.md) before comparing them.

The underlying files remain available through the
[repository layout guide](REPOSITORY_LAYOUT.md) and
[findings index](findings/INDEX.md).
