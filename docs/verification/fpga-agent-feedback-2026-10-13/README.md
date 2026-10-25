# FPGA agent feedback verification, 2026-10-13

This package separates real finite RTL simulation from offline software fixtures.
No licensed Vivado run, API generation request or HQC execution was performed.

## Exact exported ML-DSA RTL simulation

`exact-export-kat/functional.json` records all 210 checks passing for the
`fpga-latch-corrected-baseline` export, fingerprint
`59d15144b824edba333d34a4a6ba924a0f10735ce3b165e3d29d8e38ae6e8918`.
The new verifier compiles the actual 35 exported Verilog sources directly without
RTL transformations. Counts: 75 KeyGen, 45 Sign, 45 Verify, 12 modified-input,
33 canonical-hint cases. Individual cycle counts, source/test input hashes and
actual Verilator version are recorded. Raw compile and simulation logs are kept.

The saved request uses historical absolute local paths for provenance; it is not
a portable launch configuration. Re-export and prepare a fresh source-bound
request to reproduce. Generated executables/build trees are intentionally omitted.
This two-state finite-vector test is not formal equivalence or mapped-memory
behavior proof. It does not establish a PPA improvement.

`exact-export-candidate-kat/` separately records all 210 cases passing for the
existing `fpga-latch-corrected-candidate` export under the same final adapter.
This is the previously corrected candidate, not newly generated optimization RTL.
Both runs retain all individual operation cycle counts. In this comparison the
existing corrected candidate is slower in all 210 cases by 115 to 3565 cycles;
see `latency-comparison.json`. A no-latency-regression acceptance rule would reject
this candidate against this baseline. Passing KATs does not establish a speedup.

## Software and UI checks

The permitted aggregate suite and its exact HQC exclusions are recorded in
`unittest-O0.json` and `unittest-O1.json`. Both final runs completed 453 tests with no
failures, errors or skips, using the installed Flask dashboard test dependencies. The new API tests
use synthetic responses only. No real API pricing, model or account was queried
by these tests. The recorded source-specific RTL check above is separate from
those fixtures. The read-only JavaScript UI check also passed.

## Remaining gates

Automatic optimization acceptance remains blocked: no site-qualified
mapped-memory verification, structural warning qualification or timing-path
ownership proof has been supplied. Imported post-synthesis reports remain
preliminary; synthesis timing is not routed timing closure, and power is unknown.
