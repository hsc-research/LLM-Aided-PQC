# ASIC synthesis: choose Genus or Design Compiler

[Project](../README.md) · [Documentation](../docs/README.md) · [Agent](../agent/README.md)

<img src="../docs/assets/backend-selection.svg" alt="User-selected Genus or Design Compiler" width="100%">

## Implemented scope

`agent/asic_synthesis.py` generates and executes a **fixed-period, pre-layout logical-synthesis** flow for the selected tool. It reads an ordered HDL manifest, include paths, defines, parameters, libraries, and SDC; records provenance; checks completion and required outputs; and parses supported timing, area, and power fields. This is measurement infrastructure, not an autonomous ASIC optimizer.

Both generated vendor flows require qualification on a licensed installation before publishing measurements. Mock execution and Tcl-stub tests do not validate the EDA commands. Historical Genus/ASAP7 scripts remain unchanged; the new example is not asserted to reproduce their PPA.

## Configuration

Start with [the example JSON](../configs/butterfly_asic.example.json).

| Field | Meaning |
|---|---|
| `synthesis_tool` | `genus` or `dc`; command-line choice takes precedence |
| `root` | Relative-path base, resolved relative to the configuration file |
| `top`, `scope` | Exact elaborated module and reported hierarchy scope |
| `files` | Ordered `{path, language}` entries: Verilog, SystemVerilog, or VHDL |
| `include_dirs`, `defines`, `parameters` | Explicit compilation configuration |
| `period_ns` | Requested period in nanoseconds, not a measured maximum frequency |
| `sdc` | User-reviewed timing constraints |
| `memory_model` | `flops` or `macros`; no unmodeled-blackbox mode |
| `data_files` | Extra memory data staged by unique basename and hashed |
| `tools.*.time_unit` | Native library/report units: `ps`, `ns`, or `us` |
| `tools.*.target_libraries` | Genus `.lib` files; DC compiled `.db` files |
| `tools.*.link_libraries` | Additional modeled macro libraries |
| `tools.*.setup_tcl` | Optional trusted site initialization |
| `tools.genus.effort` | Separate `generic`, `map`, and `opt` efforts |
| `tools.dc.compile` | Explicit `compile` or `compile_ultra`; no license-driven fallback |

Paths support environment variables. A dry run checks declared files without launching a tool. Supply DC's compiled libraries yourself; the runner does not rename or convert Liberty files.

Generated Tcl defines `PQC_PERIOD_NS`, `PERIOD_PS`, and native-unit `PQC_PERIOD`. The [example SDC](../configs/butterfly_asic.sdc) uses the latter and does not automatically false-path reset or mode inputs. Review constraints and native units before execution. A site SDC containing a hard-coded period must agree with the run configuration.

```bash
python3 scripts/run_asic_tool.py --tool genus --config configs/butterfly_asic.example.json --dry-run
python3 scripts/run_asic_tool.py --tool dc --config configs/butterfly_asic.example.json --dry-run
# Remove --dry-run to launch the selected licensed tool.
```

## Outputs and interpretation

Each run creates `runs/asic/<tool>-<uuid>/` with generated Tcl, a manifest, tool log, reports, netlist, exported constraints, checkpoint, and `result.json`. Configuration, source/header, library, setup-script, and SDC hashes are recorded and rechecked. Failed runs retain their log and error result.

`worst_setup_slack_ns` is normalized from supported timing syntax. Missing metrics remain `null`, not zero. Cell area stays in declared library units; do not assume ASAP7-scaled values are physical square micrometers. Power is normalized only for recognized labeled fields. TNS and Fmax are not inferred. `timing_met_reported` applies to reported setup paths, not signoff or an unconstrained-path audit.

There is no automatic RTL acceptance here. Compare baseline and candidate within the same tool, hierarchy, constraints, libraries, and memory model, and verify functionality separately. Genus and DC are separate experimental configurations.

## Site qualification

Check the installed version, library units, elaborated hierarchy and parameters, unresolved modules, modeled memories, clocks/IO coverage, and parsed values against native reports. Run a known baseline, a controlled candidate, and deliberately invalid RTL. ASIC place-and-route and automated ASIC editing remain future work.
