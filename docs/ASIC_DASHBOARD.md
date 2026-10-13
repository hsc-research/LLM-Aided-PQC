# Read-only ASIC dashboard observations

The current-run dashboard can ingest existing local records with
`agent.asic_dashboard.collect(root)`. This reader never executes EDA, an adapter,
an LLM, shell commands, or source paths from a manifest. It does not change RTL,
qualification records, admission gates, or run artifacts.

## Supported records

- `.pqc_runs/whole_design/<run>/manifest.json` and numbered `*-measure/`
  request/response/report sets written by the whole-design controller.
- `runs/asic/{genus,dc}-<run>/manifest.json`, `result.json`, and reports written by
  `agent.asic_synthesis` using its default output location.

Custom ASIC output roots and historical `logs/asic` directories are deliberately
not searched. Move neither historical reports nor test fixtures into these
locations to present them as current measurements. There are no real current
ASIC PPA records supplied by this change. The tests generate synthetic records
in temporary directories only; passing tests is not EDA/site qualification.

## Evidence and limits

Whole-design responses must bind their exact request SHA-256, source-hash
manifest, and full measurement configuration. Their timing and area report
hashes are checked inside the measurement invocation. Critical paths require
valid timing-report line references; values remain **adapter-recorded
observations**, not independent vendor-parser validation. Baseline/candidate
labels describe recorded source manifests, not acceptance.

Standalone ASIC metrics are reparsed from hash-checked reports using the existing
strict ASIC parser and must equal the recorded metrics. Explicit DC dynamic and
leakage power labels are displayed in watts, alongside total power. Genus total
power can be shown, but unlabelled subtotal component order is not guessed.
Explicit DC setup start/endpoints and slack are parsed; unsupported path formats
remain absent. Data-arrival time is never mislabeled as combinational path delay.

Missing metrics are `null` (rendered **Not measured**), including latency, hold,
unsupported path delay breakdowns, or unreported power. No Fmax is calculated
from requested period or slack. Unit, tool release, library corner, technology,
period, and stage are shown when recorded. Declared area units are preserved.

All summaries keep automatic acceptance/comparison blocked and timing signoff
false. Recorded qualification/admission fields are retained separately and never
promoted into verified site qualification. Hash matching establishes local record
consistency, not tool execution, complete source closure, cryptographic
correctness, mapped-memory semantics, or validated workload power. There are no
percentage gains without an independently qualified matching comparison.

The reader rejects outside/traversing paths, symlinked ancestors/files, oversized
records/reports (4 MiB), stale request/configuration bindings, malformed source
hashes, and changed reports. It reads only known JSON record filenames and
`.rpt` evidence; source paths are hashed as manifest data, never opened. Directory,
report, and path counts are bounded. Errors expose no arbitrary file contents.

## Interface

`collect(root)` returns `runs`, `errors`, and `read_only: true`. Each run has
`kind: asic_measurement`, `measurement_role: baseline|candidate|unspecified`,
`target: asic`, tool/configuration labels, provenance digests, `notes`,
`recorded_qualification`, and conservative verification/comparison status.

`observations.metrics` contains `area`/`cell_area_reported`, `area_unit`,
`cell_count`, setup/hold slack, `power_w`/`total_power_w`, `dynamic_power_w`,
`leakage_power_w`, and `latency_cycles`. `observations.critical_paths` contains
bounded source-report references and only supported endpoint/delay observations.
