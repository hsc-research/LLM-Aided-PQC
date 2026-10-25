# ASIC site admission contract

[ASIC guide](../asic/README.md) · [Hardware handoff](HARDWARE_HANDOFF.md) · [Controller](WHOLE_DESIGN.md)

This is an interface for a reviewed site implementation of
`strict-rtl-flops-v1`, not a qualified DC/Genus report parser. The repository's
tests use synthetic fixtures. The user must qualify the adapter on the licensed
machine before using it for target-bound optimization. A qualification JSON
record or matching hash does not independently prove that a licensed test was
run or that the adapter interpreted the tool correctly.

## Configure the selected tool

Add these fields to the complete ASIC configuration. Put `admission_adapter`
under whichever of `tools.dc` or `tools.genus` is selected:

```json
{
  "memory_model": "flops",
  "compilation_unit": "REPLACE_WITH_PROFILE_COMPILATION_UNIT",
  "language_standard": "REPLACE_WITH_PROFILE_LANGUAGE_STANDARD",
  "admission": {"policy": "strict-rtl-flops-v1", "waivers": []},
  "tools": {
    "dc": {
      "admission_adapter": {
        "tcl": "site/admission.tcl",
        "qualification": "site/admission-qualification.json",
        "inputs": []
      }
    }
  }
}
```

These paths resolve against the ASIC configuration's `root`. Declare every
adapter dependency in `inputs`, including any diagnostic-rule file it reads.
Copy `compilation_unit` from the selected profile and qualify those exact
semantics. Copy and qualify `language_standard` too: current exports use
`verilog2005` for ML-DSA/SLH and `systemverilog2017` for ML-KEM. The site adapter
must select documented tool flags/defaults for those semantics. All ordinary
source, library, constraint and version fields remain
required. Omitting the adapter permits a source/configuration dry-run only;
strict execution refuses before launching the tool. The generated Tcl also
refuses to run without it.

## Implement the site procedure

Start with this deliberately nonfunctional template:

```tcl
proc pqc_admission_snapshot {phase native_report_path} {
    error "Site admission adapter is not implemented or vendor-qualified"
}
```

Replace it only after reviewing the installed tool's documented queries and
qualifying the implementation. Do not replace it with constant zero counts.
The adapter is sourced before HDL loading so it can configure its qualified
compilation-unit semantics. The procedure is called with `pre_synth` after
elaboration/link, then `post_synth` after mapping. Each call must write nonempty
raw full-hierarchy evidence to `native_report_path` and return a Tcl dictionary:

| Key | Required value |
|---|---|
| `tool_version` | Queried live; exactly matches the configured and qualified release |
| `checks` | Dictionary with every structural count listed below |
| `memory` | Dictionary with every memory count listed below |

All counts must be nonnegative integers. Every structural count must be zero:

```text
missing_modules
empty_modules
port_width_mismatches
port_connection_errors
multiple_drivers
latches
implicit_nets
undriven_nets
combinational_loops
unreviewed_diagnostics
```

Memory fields are:

| Field | Required interpretation |
|---|---|
| `memory_inventory_complete` | Exactly `1`; the adapter has classified the complete selected hierarchy |
| `memory_macro_cells` | `0`; no memory macro implementation |
| `memory_blackboxes` | `0`; no unmodeled storage |
| `unmapped_memory_bits` | Nonnegative before synthesis; `0` after mapping |
| `mapped_memory_bits` | All mapped storage bits belonging to memories |
| `flip_flop_memory_bits` | The subset implemented by FF cells; equals `mapped_memory_bits` after mapping |

The site review must explain constant/optimized-away storage, generated banks,
and memory-to-cell ownership. Equal counts without a complete inventory do not
establish the policy. Review read/write behavior and initialization separately;
this structural contract is not a functional memory test.

The runner provides `PQC_ADMISSION_POLICY`, `PQC_ADMISSION_COMPILATION_UNIT`,
`PQC_ADMISSION_LANGUAGE_STANDARD`, `PQC_ADMISSION_QUALIFICATION` and
`PQC_ADMISSION_WAIVERS_JSON` Tcl globals before HDL loading.
Use the same reviewed diagnostic policy and exact waivers when computing
`unreviewed_diagnostics`.

## Record qualification and negative controls

The qualification JSON requires:

- `schema_version: 1`, `policy: "strict-rtl-flops-v1"`, `tool: "dc"` or
  `"genus"`, exact `tool_version` and matching `compilation_unit` and
  `language_standard`.
- Nonempty `reviewed_by`, `reviewed_at` and `diagnostic_policy_review` fields.
- `adapter_hashes`: the exact SHA-256 map for the adapter Tcl and every declared
  dependency. Paths in this map resolve relative to the qualification JSON.
- `controls`: exactly `known_good`, `known_good_flop_memory`,
  `compilation_unit`, `language_standard`, all ten structural-count names above,
  and `memory_macro`. Each record has `observed`, `evidence` and `sha256`.
  The first four controls
  require `observed: "PASS"`; every fault requires `"REJECT"`. Evidence files
  resolve relative to the qualification JSON and are hash-checked.
- `diagnostics`: reviewed records with exactly `id`, `pattern`, `category`,
  `disposition` and `reason`. Patterns are Python regular expressions.
  Categories are the structural-count names above, `memory_macro`, or `other`.
  Dispositions are `fatal`, `review` or `benign`; every category except `other`
  must be `fatal`.

Use real controls that demonstrate each fault is detected in the selected
tool release. Retain commands, exact inputs, original reports and review
context. A report file containing only a claimed verdict is not meaningful
qualification, even if its checksum passes.

Each optional `admission.waivers` entry has exactly `diagnostic_id`,
`line_sha256`, `reason` and `approved_by`. The ID must name a `review`
diagnostic. `line_sha256` hashes the exact diagnostic line without its line
terminator. Structural/fatal checks cannot be waived. Update and re-review
qualification when the adapter, dependencies, tool release or diagnostic
interpretation changes.

## Inspect each run

Both phases produce `admission_<phase>.rpt` interchange records and
`admission_<phase>_native.rpt` native evidence. Python independently validates
the interchange fields and report hashes. Missing, duplicate, unknown,
contradictory or nonzero-fault fields reject admission.

A completed strict run records `admission_passed: true`,
`structural_checks_verified: true`, `memory_implementation_verified: true` and
`memory_implementation: "flops"`. A dry-run records false flags and no mapped
implementation. `qualification_evidence_origin` identifies site-supplied records
that were not independently reproduced. `memory_semantics_verified` and
`automatic_acceptance` remain false: functional tests, memory behavior,
candidate admission, timing review and physical signoff are separate steps.

## File map

| Location | Purpose |
|---|---|
| [agent/asic_synthesis.py](../agent/asic_synthesis.py) | Authoritative constants, qualification loader, generated Tcl and report checks |
| [ASIC setup](../asic/README.md) | Complete run configuration and result limits |
| Site-owned `admission.tcl` and qualification/control files | Tool-release-specific adapter and evidence; not supplied as qualified by this repository |
| `runs/asic/<tool>-<uuid>/` | Per-run reports, logs and `result.json` |
