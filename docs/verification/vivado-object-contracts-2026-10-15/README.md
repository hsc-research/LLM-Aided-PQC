# Vivado 2022.2 object-contract corrections, 2026-10-15

## Observed failure and scope

The user's licensed-host run004 completed synthesis and structural DRC, then
failed with Common 17-54 because a Vivado timing_path has no POINTS property.
Its exit code was 1, not a demonstrated timeout. The report_timing command also
warned that display options were incompatible with -of_objects. The DRC report
itself selected INBB-3, LUTLP-1 and MDRV-1 despite a misleading command header
showing valid_o; no incorrect rule execution was established.

This combined delta includes the separately tested primitive batching changes,
plus the following corrections:

- Direct documented get_cells -of_objects timing_path membership; no assumed
  timing-point properties, endpoint-name inference, or clock-network ownership.
- Path reports use only -of_objects and -return_string.
- Exact required DRC name set, object class and enabled-state checks before
  report generation; validated plain names passed to the report command.
- Only per-port optional clock association uses -quiet after validating class.
  Empty results require min/max data-port coverage. Returned clocks must belong
  to the global inventory. All global clock, configured clock-port, no-clock,
  unconstrained, structural and memory verification remains in force.
- Executed nonzero processes are labelled EXECUTED_TOOL_FAILED, retaining null
  metrics and blocked status.

Every emitted warning remains in the transcript and existing warning gate.
The expected named-report/non-GUI and zero-DRC-violation warnings are deliberately
not whitelisted in this patch. Strict admission can remain blocked by these
or synthesis warnings; this patch does not certify the user's baseline.

## Verification limits

The tests execute Tcl 8.6 against synthetic API contracts, not licensed Vivado.
The full-helper fixture rejects unknown properties and incompatible options,
checks exact setup/hold cell memberships with generated names, and covers wrong,
duplicate, missing, disabled or wrong-class DRC checks, invalid port objects,
foreign clocks and errors from property, path-cell and DRC operations. Those
failures cannot produce the complete marker or pass parse_objects. A nonempty MDRV violation is also emitted, parsed and passed into the full
qualification evaluator, where it blocks the structural gate.

Batch regressions retain all primitive and memory INIT/INITP evidence, singleton
scalar semantics, heterogeneous optional properties, cardinality checks and
flush/progress behavior. Existing qualification and launch regressions remain.
No hardware speedup, licensed EDA qualification, RTL algorithm requalification,
model API or HQC experiment is claimed. No hosted Actions run was started.

`verification.json` binds the final sources and counts. `unittest-O0.json` and
`unittest-O1.json` list every dependency skip and all 19 excluded tests, with
reasons. The earlier collector-batching directory describes its own historical
source snapshot; this directory binds the combined final sources.

Test baseline is staged PR15 tree 424009275a5e93a86413b9225de113820cc7df7c.
Publication must select only this delta and preserve later main documentation.
Existing frozen run004 artifacts must not be changed or relabelled. A licensed
host rerun under a new run ID is required to validate native object behavior.

## Primary references

- [2022.2 timing path object relationships](https://docs.amd.com/r/2022.2-English/ug894-vivado-tcl-scripting/Timing-Path-Object)
- [2022.2 get_cells on timing_path example](https://docs.amd.com/r/2022.2-English/ug894-vivado-tcl-scripting/Defining-Tcl-Procedures)
- [2022.2 report_timing](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/report_timing)
- [2022.2 DRC CLASS and enabled properties](https://docs.amd.com/r/2022.2-English/ug894-vivado-tcl-scripting/Manipulating-DRCs)
- [2022.2 get_clocks](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/get_clocks)
- [2022.2 scalar and multi-object property returns](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/get_property)
