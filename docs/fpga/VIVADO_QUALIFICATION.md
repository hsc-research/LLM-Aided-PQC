# Vivado feedback evidence and remaining qualification

[FPGA feedback](../FPGA_AGENT_FEEDBACK.md)

`agent.fpga_feedback` now runs a fixed repository-owned report producer after
Vivado OOC synthesis. `agent.vivado_qualification` computes each observable gate
from its raw reports. It does not accept a user or model `verified: true` field.
The producer is designed for the declared Vivado 2022.2,
`xc7a200tfbg676-1`, 15 ns ML-DSA `combined_top` flow. It has **not been run against
a licensed Vivado installation in this change**. Synthetic tests exercise the
protocol, parser and failure boundaries; they are not FPGA qualification.

## Execution and binding

The existing command is unchanged:

```sh
python3 -m agent.fpga_feedback --request REQUEST.json --response RESPONSE.json
# Only on the licensed host, after reviewing the frozen inputs:
python3 -m agent.fpga_feedback --request REQUEST.json --response RESPONSE.json --execute
```

Preparation alone never executes Vivado. The autonomous controller constructs
these request files. A manual caller must use the same whole-design request
contract and freeze the producer files returned by
`agent.vivado_qualification.dependencies()`, the XDC, all data and include files,
and the existing adapter dependencies. Use a fresh response directory per run.
The three producer files are Python, Tcl, and the feedback adapter itself.

The launch script reads the exact ordered exported sources; it does not
regenerate RTL, introduce false paths, supply I/O delay numbers, or accept model
commands. The only supported synthesis settings are default effort,
`out_of_context`, gated-clock conversion off and no implementation seed.

The launch calls the documented `synth_design` command directly. It does not
use the `redirect` command from other EDA Tcl shells. Once the child exits,
Python copies the complete captured `console.log` byte-for-byte to
`synthesis.log`, before building qualification. Despite the historical filename,
this now contains the **whole invocation transcript**, including elaboration and
report generation. The warning gate conservatively reviews warnings/errors
from all these stages; no warning is filtered out to obtain a pass. Native
`vivado.log` remains available alongside the capture.

`tool-version.txt` is written before the version comparison, so an observed
mismatch is preserved even when synthesis never begins. A nonzero process exit
blocks measurement and points to `vivado/console.log`. A collection or parser
exception points to `vivado/qualification-error.txt`; missing qualified metadata
is not presented as proof that the installed Vivado version differs. For an old
failed run, inspect `tool_returncode`, `qualification_error_type`, `blockers`, and
`actual_tool_version` in its bound `response.json`, plus those logs. Preserve the
old run and create a fresh run so the updated adapter dependencies are frozen.
Recreate preparation only if its bound inputs (such as site/XDC settings or
Python executable) changed.

License-free tests execute the generated launch with real Tcl and an explicit
stubbed command surface that rejects unknown commands, including the formerly
used `redirect`. They test warning retention, tool failure, actual version
mismatch, and parser failure; they do not validate real Vivado synthesis or the
post-synthesis query semantics. A licensed-host replay is still required.

`vivado/input-manifest.json` binds the invocation request, source read order,
full configuration, source hashes, frozen dependency hashes and producer hashes.
`vivado/qualification.json` binds all raw artifacts, including the generated
launch Tcl, synthesis log, exact functional netlist and synthesized DCP, and
records derived observations. Full Vivado version/build text is retained.
These hashes protect association and detect local byte changes; they are not
vendor signatures or protection against a malicious EDA installation.

`validate_feedback(response, request, response_directory)` reopens the fixed
report locations, rechecks hashes, checks live source/dependency bytes and
recomputes observations. It returns the observed qualification or raises.
It allows observed failures for explicit exploratory work.
`validate_admission` performs the same checks and additionally requires every
qualification gate to pass. The current mapped-memory behavioral gap means
strict overall admission remains blocked.

## Collector progress and bounded property queries

The primitive inventory is emitted in batches of at most 256 cells. Mandatory
property columns use bulk `get_property` calls with checked result cardinality.
The single-object API returns a scalar; it is explicitly wrapped as one value
so empty, whitespace-containing, or list-like values are never split.
Property availability is still inspected on **every individual cell** exactly
once; there is no type-level availability cache. Optional columns are queried
only on the cells advertising each property, with missing values kept empty.
Every matching memory INIT, mode, width, register, reset and collision property
is retained. Rows keep the previous inventory order and encoding. The separate
latch/blackbox queries and all downstream qualification gates are unchanged.

`PQC_COLLECTOR` progress lines record the phase and completed/total primitive
counts. The object stream and stdout are flushed at batch boundaries. A quiet
native Vivado command log alone does not establish a hang: inspect those progress
lines and the object-file growth. Earlier collectors had no such progress and
made repeated property-list queries inside a silent full-netlist loop. The new
query structure reduces API call counts in synthetic tests; actual Vivado
runtime improvement must be measured on the licensed host.

The parser retains its existing limits: `objects.tsv` and `qualification.json`
are limited to 128 MiB, while ordinary text reports default to 32 MiB. A partial
inventory, incorrect property cardinality, failed query, missing completion
marker or missing required report cannot qualify a design. Do not change the
collector under an active run or overwrite its evidence. A separate checkpoint
inspection can be diagnostic, but cannot become accepted evidence from the old
run by bypassing its frozen producer hashes.

## Observable checks

- Primitive latch inventory uses the primitive subgroup and `LD*` reference
  family and retains `REF_TYPE`, `PRIMITIVE_TYPE` and `REF_NAME`. A zero
  `latch_loops` count is never treated as zero latches.
- Blackboxes are queried explicitly. Structural DRCs `MDRV-1`, `LUTLP-1` and
  `INBB-3` must all be present and enabled, and run with waivers ignored.
- Every required `check_timing` category must be present. Conflicting duplicate
  counts fail. No-clock, unconstrained internal endpoints, partial delays,
  combinational loops and all other observed positive counts block coverage.
- Both global setup and hold metrics and positive constrained-endpoint counts
  are required. Detailed path objects must agree with their report endpoints,
  delay types and rounded slack; global worst slacks must agree too.
- Min and max analysis must be enabled for both Fast and Slow corners, and I/O
  paths must not be ignored. Exactly one non-generated clock must match the
  declared period and the profile's declared clock port.
- Each non-clock I/O port receives separate min/max path queries. Missing paths,
  infinite slack, inout ports and unexplained ignored paths are uncovered.
  OOC mode does not waive the external timing contract.
- Each critical path contains actual datapath cell objects queried from its Vivado timing-path object. Source
  attribution uses only an absolute `FILE_NAME` plus a valid `LINE_NUMBER`
  within the exact frozen source manifest. Missing properties are `unknown`.
  Similar cell names, module names and matching file basenames are not proof.
  The response's `source_ownership` contains path cells only; the complete
  primitive inventory is preserved in `objects.tsv`.
- RAM/LUTRAM/ROM/SRL primitives, modes, widths, output-register settings and
  initialization properties are collected. The compact response hashes the
  full per-cell property set; exact values remain in the bound raw report.
- Synthesis warnings need review and keep the structural gate blocked, even
  when explicit latch and DRC counts are zero. The implementation does not
  silently whitelist warnings about removed or changed logic.

Strict timing gates additionally require setup at the frozen nonnegative floor
and hold at or above zero, with no failing endpoints. Negative slacks remain
recorded for exploration and are not promoted by a clean structural check.

Individual structural, constraint, source-attribution and mapped-inventory
checks can pass or fail from measured data. Resource and slack results remain
post-synthesis estimates. A negative slack is useful feedback, not timing
closure. No power, routed Fmax, silicon result or training claim is made.

The archived old baseline's 198 no-clock pins and 66 unconstrained internal
endpoints remain failures even though its `latch_loops` count is zero. The
latch-corrected source derivative needs a new source-bound run; old reports are
not transferred to it.

## Explicit I/O exceptions

The preferred input is a complete user-approved XDC timing contract. Do not add
invented delays merely to make the report green. For deliberate asynchronous
I/O exceptions, the frozen measurement configuration may contain:

```json
{
  "qualification": {
    "io_exceptions": [
      {
        "port": "reset",
        "direction": "IN",
        "reason": "User-reviewed asynchronous reset interface contract",
        "xdc": "/absolute/path/to/frozen-user-constraints.xdc",
        "line": 12
      }
    ]
  }
}
```

This example is a schema illustration, not a recommendation to false-path this
design's reset. That exact line must already be a user-supplied command such as
`set_false_path -from [get_ports {reset}]`. Output exceptions use `-to` and `OUT`.
Only an exact single-port all-path exception is recognized. Its XDC must already
be frozen, its reason must be present, the port direction must match the tool
inventory, both min and max ignored-path queries must observe it, and the
serialized effective constraints must not contain unsupported timing-hiding
commands. The parser never subtracts a waiver count from positive missing-delay
counts. Wildcards, internal-pin exceptions, multicycle paths, clock groups,
case analysis and alternative serialized exception forms are not automatically
qualified. They may be legitimate engineering constraints, but need a separately
reviewed producer/parser extension. Missing evidence remains blocked.

## Remaining mapped-memory behavioral work

Observing `RAMB36E1` or `RAMB18E1` is not verification of startup, reset, latency
or collision behavior. The existing exported 210-case gate compiles RTL under
Verilator and cannot stand in for simulation of `implementation.v`.

A future exact-netlist XSim/UNISIM gate can reuse these existing assets without
replacing the design under test:

1. `exported_kat_adapter.CASES` and `coverage_contract()` provide the exact 75
   KeyGen, 45 Sign, 45 Verify, 12 modified-input and 33 canonical-hint cases.
2. `portable_kat_gate.prepare_testbench` stages the existing byte-comparison
   benches with their documented bounded partial-word fixes and watchdog.
   `stage_verify_mutations` and `stage_canonical_cases` stage the negative data.
3. Compile only the bound Vivado functional netlist as the DUT, plus each staged
   bench, its headers and the matching vendor `glbl`/UNISIM models. Do not also
   compile the exported RTL as another implementation of the same top.
4. Preserve the fresh compile, elaboration and simulation commands/logs, actual
   simulator/model versions and input hashes; bind them to the exact DCP,
   netlist, source/configuration manifest and fixture closure. Check exact
   completion counts, terminal marker, byte comparisons, four-state failures
   and per-case latency against the corresponding RTL result.
5. Separately add and test directed startup/reset, read/write-enable,
   first/last-address, output-register latency, and same-address collision cases
   for the **actual inferred memory configurations and reachable protocols**.
   Exercise the configured read-first/write-first/no-change modes and document
   unsupported/undefined cross-port collision cases. A generic RAM bench that
   instantiates a new primitive does not test the design's mapped memories.
6. Make those coverage requirements machine-checked and frozen before allowing
   the overall mapped-memory semantics gate to pass.

Steps 3–6 are not implemented or claimed as completed here. The current adapter
accepts neither an arbitrary external harness command nor a supplied pass
boolean to bypass them. This is the remaining strict-admission limitation; an
explicit exploratory run may still use fresh, integrity-checked estimates and
save provisional candidates without accepting them.

## Primary command references

- [Vivado 2022.2 get_property scalar/list semantics](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/get_property?contentId=LelYUw3FZOlqpGXaBpu12Q)
- [Vivado 2022.2 get_property ordering and batching](https://docs.amd.com/r/2022.2-English/ug894-vivado-tcl-scripting/get_property-and-Sorted-Lists?contentId=VizwBFZx0uBQMTGlyThZ~w)

- [Vivado 2022.2 synth_design](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/synth_design)

- [Vivado 2022.2 check_timing](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/check_timing)
- [Vivado 2022.2 get_timing_paths](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/get_timing_paths)
- [Vivado 2022.2 report_timing](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/report_timing)
- [Vivado 2022.2 timing summary](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/report_timing_summary)
- [Vivado 2022.2 blackbox query](https://docs.amd.com/r/2022.2-English/ug893-vivado-ide/Tcl-Command-for-Finding-Black-Box-Cells)
- [DRC enable/disable property](https://docs.amd.com/r/2024.1-English/ug912-vivado-properties/IS_ENABLED)


### Vivado 2022.2 object-contract correction

Critical-path cell membership is queried with `get_cells -of_objects $path`.
Vivado timing paths do not expose the previously assumed `POINTS` property.
This query identifies datapath members; it does not establish clock-network
ownership or infer source ownership from endpoint names. Exact source properties
and the existing frozen-source checks remain required. Path reports use only
`report_timing -of_objects $path -return_string`: display switches that Vivado
ignores with `-of_objects` are omitted.

Before structural reporting, every returned rule must have class `drc_check`,
be enabled, and collectively have exactly the three required names. The validated
plain names are passed to `report_drc`, avoiding opaque collection display text.
The observed licensed-host report selected the correct three rules even though
its command header displayed `valid_o`; that header alone is not evidence of
incorrect rule execution.

Only optional per-port clock association uses `get_clocks -quiet`, after checking
the object class is `port`. Absence of a clock on a data port is expected. Returned
clock names must occur in the global clock inventory. An empty result leads to
mandatory separate min/max port timing coverage, never a clock-port exemption.
The global clock query, clock properties, configured clock-port agreement,
`check_timing` no-clock and unconstrained checks, synthesis, DRC, timing-path
queries and property queries remain unsuppressed and fail closed. The transcript
warning gate still examines every warning that Vivado emits.

An executed process with a nonzero exit now reports `EXECUTED_TOOL_FAILED`,
with blocked status and null measurements, rather than `PREPARED_NOT_EXECUTED`.

Primary API references:
- [2022.2 timing path objects and datapath relationships](https://docs.amd.com/r/2022.2-English/ug894-vivado-tcl-scripting/Timing-Path-Object)
- [2022.2 path-cell query example](https://docs.amd.com/r/2022.2-English/ug894-vivado-tcl-scripting/Defining-Tcl-Procedures)
- [2022.2 report_timing](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/report_timing)
- [2022.2 DRC properties and class](https://docs.amd.com/r/2022.2-English/ug894-vivado-tcl-scripting/Manipulating-DRCs)
- [2022.2 get_clocks and quiet behavior](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/get_clocks)
