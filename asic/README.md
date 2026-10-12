# ASIC synthesis: choose Genus or Design Compiler

[Project](../README.md) · [Documentation](../docs/README.md) · [Agent](../agent/README.md)

<img src="../docs/assets/backend-selection.svg" alt="User-selected Genus or Design Compiler" width="100%">

## What is implemented and verified

`agent/asic_synthesis.py` prepares **fixed-period, single-clock, pre-layout logical synthesis** for an explicitly selected Genus or Synopsys Design Compiler installation. It reads an ordered HDL manifest, includes, defines, parameters, libraries, data files, and SDC. It isolates runs, records input hashes, checks process completion and report evidence, and parses supported timing/area/power syntax.

Offline tests cover execution failures, malformed reports, units, clock-period mismatches, input changes, and Tcl control flow with stubs. **Neither commercial tool has been run to qualify this revision.** Tcl stubs cannot validate vendor commands, RTL synthesis, cryptographic correctness, power accuracy, or place-and-route. `MEASURED` means the configured process produced supported reports; it does not mean publication-ready, equivalent, or signoff-clean.

The dual-target ASIC arm selects **generic RTL memories intended for FF/logic mapping,
without a macro compiler**. Use `memory_model: "flops"` and the strict admission
contract below. The older `macros` setting remains a separate legacy runner
option; it is not the selected dual-target policy. Merely setting `flops` does
not establish mapped storage. Actual DC/Genus runs remain user-owned work on the
licensed machine.

## Four-scheme readiness

| Scheme | Tracked source evidence | ASIC readiness |
|---|---|---|
| ML-KEM | Pinned Adam's Bridge v2.0.3 unified ML-KEM-1024 / ML-DSA-87 source and generic memories; baseline passed 80 official ACVP cases under Verilator | [Whole-wrapper example](../configs/mlkem_adams_bridge_asic.example.json) covers the unified design, not ML-KEM-only area. Licensed synthesis, site constraints and library/memory qualification remain open |
| ML-DSA | Pinned mixed-Verilog/VHDL ML-DSA-OSH inputs under `third_party/mldsa_osh/upstream`, including `common/zetas.txt`; existing ASIC arms and butterfly arms retained | [Full-design example](../configs/mldsa_osh_asic.example.json) supplies ordered source/data inputs. The historical baseline retains two portability edits. Separate guarded baseline/corrected candidate variants now pass 210 portable functional cases each. [Export those exact sources](../docs/HARDWARE_HANDOFF.md#ml-dsa-export-the-passing-derivatives) before replacing this older arm's configuration; no new licensed elaboration/synthesis or PPA result |
| HQC | [Preferred SAC 2026 source-only snapshot](../third_party/hqc_sac2026/README.md); older baseline/optimized arms remain in `asic/arms/hqc_*` | No SAC 2026 executable integration or synthesis qualification. Older archived Genus reports apply only to their SAC 2023-derived sources; reviewed manifests, memory treatment, correctness and licensed runs remain required |
| SLH-DSA | All 62 pristine files match pinned SPHINCSLET upstream; corrected baseline/candidate pairs have portable 128f/192f functional evidence | Exact-source target profiles are available, but ASIC startup, external signature storage, compilation-unit semantics and licensed mapping remain unqualified. The legacy selected-mode gate supports six SHA2 sets; only the four named corrected 128f/192f portable combinations have the recorded passes. SHAKE is unsupported |

These are source/flow facts, not four verified ASIC implementations. The shared butterfly block is not a complete ML-DSA accelerator, nor an ML-KEM implementation. Do not substitute it for a scheme-level result. Do not invent missing twiddle/ROM data or silently blackbox absent modules.

Preserve third-party source headers. HQC includes GPL notices; ML-DSA includes Apache/MIT notices; SLH's Secworks SHA files include BSD-style notices, while some SPHINCSLET files lack per-file provenance. Resolve the upstream distribution/permission record before asserting a complete third-party license inventory. Licensed PDK/library files must stay outside the public repository.

## Configure the licensed machine

Start from [the example JSON](../configs/butterfly_asic.example.json), [site shell template](../configs/asic_site.example.sh), and [site Tcl template](../configs/asic_site.example.tcl). Copy configuration locally and fill it with actual approved paths, installed version, corner, and interface assumptions. No EDA software or proprietary PDK is downloaded by this flow.

For new dual-target work, start with the
[profile preparation commands](../docs/HARDWARE_HANDOFF.md#prepare-explicit-target-profiles-without-eda)
and the generated ASIC launch configuration. It retains source/startup blockers
and requires strict site admission before execution. For historical manual
scheme-level configurations, select the
[ML-DSA full-design example](../configs/mldsa_osh_asic.example.json) or the
[ML-KEM/ML-DSA unified example](../configs/mlkem_adams_bridge_asic.example.json)
rather than the butterfly block config. The
[ML-DSA bundle notes](../third_party/mldsa_osh/README.md) identify the pristine
source pin and its relationship to existing ASIC arms. Of 50 compared
source/common files, 48 match the historical ML-DSA baseline byte-for-byte;
`combined_top.v` declaration placement and `ntt_fifo_piso.v` assignment
semantics differ because of the retained
[portability edits](../docs/findings/asic/2026-07-31_mldsa_genus_port.md).
Do not describe those edited arms as pristine upstream RTL or infer equivalence
from matching source basenames. The newly available `zetas.txt` removes the
missing-ROM-input blocker; it does not establish that a selected synthesis
tool inferred or mapped that ROM correctly.

| Field | Meaning |
|---|---|
| `synthesis_tool` | `genus` or `dc`; command-line selection takes precedence |
| `root` | Relative-path base, resolved from the configuration file |
| `top`, `scope` | Exact elaborated module and reported hierarchy scope |
| `files` | Explicit ordered `{path, language}` entries, including VHDL packages before their users |
| `include_dirs`, `defines`, `parameters` | Compilation configuration; no inferred dependency glob |
| `compilation_unit` | Explicit profile semantics identifier, matched by the strict site's qualification record |
| `language_standard` | Profile HDL standard, also matched by the strict site's qualification record |
| `period_ns` | Requested period, not measured Fmax |
| `sdc` | Reviewed single-clock timing constraints |
| `memory_model` | `flops` or `macros`; declaration alone does not validate inferred memory implementation |
| `admission` | Opt-in `strict-rtl-flops-v1` policy and exact reviewed diagnostic waivers; required by the dual-target ASIC profile |
| `data_files` | Required ROM/memory data, staged by unique basename and hashed |
| `tools.*.time_unit` | Native library unit: `ps`, `ns`, or `us` |
| `tools.*.target_libraries` | Genus `.lib`/`.lib.gz`; DC compiled `.db` |
| `tools.*.link_libraries` | Additional modeled macro libraries |
| `tools.*.setup_tcl` | Trusted site initialization; dependencies/data must be declared for hashing |
| `tools.*.admission_adapter` | Hash-pinned site Tcl, qualification record and dependencies for the exact installed tool release |
| `tools.*.version`, `corner` | Record actual installed tool release and loaded PVT |
| `tools.*.power_activity` | Explicit description such as `vectorless`; no validated workload-power flow is provided |
| `tools.genus.effort` | `generic`, `map`, and `opt` settings |
| `tools.dc.compile` | `compile` or `compile_ultra`; no automatic license-driven fallback |

Paths support environment variables. DC needs genuine compiled `.db` libraries; renaming `.lib` is invalid. Genus library `time_unit` headers must match the declaration. DC's actual `report_units` output is checked after execution. Genus records library metadata verification separately from runtime unit verification; site Tcl must not override time units. Unknown report/unit dialects fail closed and require a reviewed parser update.

The example SDC requires positive, site-reviewed input transition, clock uncertainty, and output load from the site Tcl. The environment variables are `PQC_ASIC_INPUT_TRANSITION_NS`, `PQC_ASIC_CLOCK_UNCERTAINTY_NS`, and `PQC_ASIC_OUTPUT_LOAD` (native capacitance units). Input/output delays are explicitly separated into max and min constraints. No reset or mode false paths are silently added.

```bash
# After configuring approved local libraries and reviewing the site files:
python3 scripts/run_asic_tool.py --tool dc --config configs/butterfly_asic.example.json --dry-run
python3 scripts/run_asic_tool.py --tool genus --config configs/butterfly_asic.example.json --dry-run
# Remove --dry-run only on the licensed machine to execute the selected tool.
```

Dry-run validates declared input existence/hashes and renders Tcl; it **does not execute SDC/site Tcl or elaborate RTL**. The unconfigured example correctly fails when library environment variables/files are missing. Do not create dummy libraries to claim a successful hardware preflight.

License-free regression checks:

```bash
python3 -m unittest discover -s tests -v
```

## Strict RTL and FF-memory admission

The ASIC configuration selects the policy explicitly:

```json
{
  "memory_model": "flops",
  "admission": {"policy": "strict-rtl-flops-v1", "waivers": []}
}
```

This fragment is not a complete run configuration. Under the selected
`tools.genus` or `tools.dc`, provide `admission_adapter` with `tcl`,
`qualification` and `inputs` paths. The site adapter must be qualified against
the exact installed release and preserve native full-hierarchy reports. No
bundled adapter is claimed DC/Genus-qualified. A dry-run with no adapter reports
`admission_qualification: "site_qualification_required"`; execution refuses to
launch a tool until the reviewed adapter is supplied.

The adapter procedure `pqc_admission_snapshot` is called after elaboration/link
and again after mapping. It returns the documented interchange counts in
`agent/asic_synthesis.py`, backed by nonempty native reports. Admission requires:

- Zero missing/empty modules, port-width or connection errors, multiple drivers,
  latches, implicit/undriven nets, combinational loops and unreviewed diagnostics.
- A complete memory inventory with zero macro cells or memory blackboxes.
- After mapping, zero unmapped memory bits and equal mapped-memory and FF-memory
  bit counts. Review optimized-away and constant storage in the native evidence;
  a generic RAM declaration or an FF count without memory ownership is insufficient.
- Matching tool/version/top/phase, adapter hashes and qualification controls.
  The qualification record must demonstrate a known-good pass and rejection of
  each supported structural fault and a memory-macro control.

The [site admission reference](../docs/ASIC_ADMISSION.md) lists the concrete
procedure/count/qualification schema and a deliberately fail-closed template.
Qualification records are reviewed site assertions; hashes bind their bytes
but cannot independently prove the licensed tests or their interpretation.

Structural/fatal findings cannot be waived. Reviewed non-structural diagnostics
may have exact waivers recording `diagnostic_id`, `line_sha256`, `reason` and
`approved_by`. Ordinary warnings are not all automatically fatal; the qualified
site policy must classify them rather than hide them. Unknown/missing evidence
fails closed. Python/Tcl fixtures exercise this contract, not vendor diagnostics.

Only a completed strict run can set `admission_passed`,
`structural_checks_verified` and `memory_implementation_verified` to true and
`memory_implementation` to `flops`. `DRY_RUN` leaves them false. A legacy
`MEASURED` result without this evidence cannot qualify the target-bound optimizer.
Even a strict admission pass is not functional correctness, physical timing
signoff, or proof that simulation initialization is implementable. Review the
[memory behavior checklist](../docs/HARDWARE_HANDOFF.md#preserve-memory-behavior).
The runner therefore leaves `memory_semantics_verified` false. The target-bound
optimizer additionally needs separately qualified mapped-implementation startup,
read/write and collision evidence; the built-in measurement bridge by itself
remains blocked for that purpose.

## Outputs and interpretation

Runs use `runs/asic/<tool>-<uuid>/`, with generated Tcl, manifest, log, reports, netlist, exported SDC, checkpoint, and `result.json`. Inputs are hashed before and after execution. Generated Tcl and reports are hashed. The three allowlisted site-constraint environment values are recorded and checked for changes; license credentials and the general environment are not collected. A failed run retains its error and logs; stale reports from another run cannot be reused.

- Every reported setup path must have supported syntax. A malformed later path cannot be silently dropped. Rounded `VIOLATED -0` stays violated.
- The actual single-clock period is queried and compared with the configured native-unit period. DC unit verification permits a normalized `actual_period_ns`; Genus leaves it unknown pending runtime unit qualification.
- Genus must explicitly report zero unresolved references **and** zero empty modules. Known blackbox warnings cause failure even if the process exits zero.
- Missing area/power fields remain `null`. Recognized malformed, negative, non-finite, duplicated, or contradictory fields cause failure.
- Cell area stays in declared library units. Scaled ASAP7 area is not automatically physical square micrometers.
- Power is normalized only from supported labeled fields or a consistent Genus subtotal. Its activity assumptions are recorded; `workload_power_validated` remains false. Vectorless estimates are not measured workload power.
- `timing_met_reported` covers reported setup paths only. DC hold/check-timing reports are retained for review; no automatic timing signoff claim is made. TNS and Fmax remain unknown.

Compare baseline and candidate at identical periods, tool versions, libraries/corners, constraints, hierarchy, memory models, and activity assumptions. Run the applicable correctness gate separately. Do not compare DC and Genus numbers as interchangeable configurations.

## Retired experiments

The three historical Python binary-search launchers and `agent/backends/genus.py` now fail before running tools or SSH. The old remote port-fix/sweep entry points are also disabled: shared logs, broad process termination, and skipped correctness checks were unsafe.

Historical Tcl, RTL, and measured logs are preserved as evidence. They are not current validated launch interfaces. In particular, synthesis response was demonstrably non-monotonic; binary search cannot establish a minimum closing period. The documented [ASIC closure retractions](../docs/findings/asic/2026-08-12_bf2x2_asap7_complete.md) remain in force. Use independent fixed-period comparisons, and do not relabel archived retracted Fmax values as new results.

## Before a paper result

Qualify the installed tool with a small known baseline, a controlled candidate, deliberately invalid RTL, and a missing-module test. Check hierarchy/parameters, ROM contents, macro models, clocks, units, IO coverage, unconstrained paths, hold, synthesis warnings, and native report values. Record the correctness-gate evidence and exact source/config/tool/library fingerprints. For power, add a separately validated workload/activity flow. For physical PPA, run and label place-and-route separately.

## File map

| Location | Purpose |
|---|---|
| [ASIC runner](../agent/asic_synthesis.py) | Fixed-period synthesis and strict admission interchange |
| [Site shell](../configs/asic_site.example.sh), [site Tcl](../configs/asic_site.example.tcl) | Local tool and constraint settings |
| [Hardware handoff](../docs/HARDWARE_HANDOFF.md) | Source profiles, matched target runs and memory caveats |
| [Whole-design controller](../docs/WHOLE_DESIGN.md) | Separate functional, implementation and candidate-acceptance gates |
| `runs/asic/<tool>-<uuid>/` | Local run artifacts; licensed libraries remain site-owned inputs |
