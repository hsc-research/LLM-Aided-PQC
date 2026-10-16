# Vivado primitive collector batching, 2026-10-15

## Scope and diagnosis

A licensed-host run completed synthesis, saved its checkpoint, and then spent a
long time in post-synthesis object collection. Its object file continued to grow,
so the quiet native command log did not establish a hang at `llength`. The old
collector had no progress markers and performed four `list_property` scans per
primitive, repeated scalar property reads, and additional per-memory-property
reads. This patch reduces that avoidable query overhead and makes progress
visible. **No actual Vivado speedup is measured or claimed here.**

Test base tree: `424009275a5e93a86413b9225de113820cc7df7c` (the previous launch
fix). Publication must preserve the later documentation-only main changes; only
the collector, its tests, qualification documentation and these evidence files
are part of this delta.

## Preserved evidence and API behavior

- All primitives are visited, in the same order, in batches of at most 256.
- Each cell's available properties are inspected once individually, including
  cells with equal types but different properties. No type-based property cache
  or sampling is used.
- Property reads are grouped only across cells advertising the property.
  Missing optional values remain empty. Every matching memory INIT, INITP, mode,
  width, register, reset and collision property remains in the output.
- Vivado's singleton API returns a scalar, including an empty string. The helper
  explicitly wraps it as one value. Multi-object results require exact list
  cardinality. This preserves whitespace, backslashes and list-like values.
- Object and stdout streams are flushed at batch boundaries. Progress identifies
  query, primitive inventory, structural/timing and path-collection phases.
- Independent latch/blackbox inventories, parser limits, timing/path checks,
  source ownership, completion markers and admission rules are unchanged.
- Existing run directories and frozen producer hashes are not modified. A
  checkpoint-only inspection in another directory would be diagnostic; it must
  not be represented as accepted evidence from the original run.

## License-free verification

See `verification.json` for exact source hashes and final results, and
`unittest-O0.json` / `unittest-O1.json` for all dependency skips and the full
pre-existing 19-test exclusion list. The checked-in runner uses the same
permitted non-HQC selection policy as previous verification.

Eight collector regressions execute real Tcl with a synthetic object API that
models scalar singleton and list-valued multiple-object returns. Tests compare
the complete emitted inventory byte-for-byte with the prior row semantics,
including heterogeneous properties, generated/Unicode names, empty and
space/backslash/list-like values, 257-cell singleton tails, and all 128 INIT plus
16 INITP fields in a synthetic BRAM fixture. Query failures and cardinality
mismatches remain errors. Empty inventory cannot pass the parser. Another reader
sees exactly 256/512 flushed cell rows at the corresponding progress messages.

For 600 synthetic primitives, the fixture records 600 `list_property` calls and
18 `get_property` calls with at most 256 objects per query. This establishes API
call counts under the fixture, not elapsed-time improvement in licensed Vivado.

No licensed EDA, model API, HQC experiment, checkpoint replay or GitHub Actions
run was launched for these checks. A licensed-host test remains necessary.

```sh
python3 -m unittest tests.test_vivado_collector tests.test_vivado_launch tests.test_vivado_qualification tests.test_autonomous_fpga tests.test_autonomous_fpga_adversarial tests.test_fpga_proposal -v
python3 docs/verification/vivado-collector-batching-2026-10-15/run_permitted_subset.py
python3 -O docs/verification/vivado-collector-batching-2026-10-15/run_permitted_subset.py
python3 -m compileall -q agent tools tests
python3 tools/check_docs.py
```

## Primary references

- [Vivado 2022.2 get_property scalar and multiple-object semantics, UG835](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/get_property?contentId=LelYUw3FZOlqpGXaBpu12Q)
- [Vivado 2022.2 get_property ordering and bulk-query guidance, UG894](https://docs.amd.com/r/2022.2-English/ug894-vivado-tcl-scripting/get_property-and-Sorted-Lists?contentId=VizwBFZx0uBQMTGlyThZ~w)
- [Qualification and progress documentation](../../fpga/VIVADO_QUALIFICATION.md)
