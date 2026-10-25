# Vivado measurement launch correction, 2026-10-15

## Problem and correction

The reported licensed-host run used Vivado **2022.2**, then failed before
`synth_design` with `invalid command name "redirect"`. The controller reported
“Vivado actual version mismatch” because qualified version metadata was absent.
That message did not establish an installed-version mismatch.

This change:

- Calls documented `synth_design` directly under the existing Tcl error handler.
- Copies the complete captured `console.log` byte-for-byte to `synthesis.log`
  after process exit, before qualification. This historical filename now covers
  the whole invocation, including constraint and reporting warnings. Warning
  review is conservatively broader; no warning is discarded or gate relaxed.
- Records `tool-version.txt` before comparison and preserves observed version
  diagnostics even for a nonzero return code.
- Distinguishes failed processes and evidence/parser failures from missing or
  conflicting version metadata. Errors point to the corresponding bound logs.

## Verification scope

The base is current-main commit `f003116e3fb6ba7f80bc6becc48507f3605222e0`,
tree `80e7500128e485d4625e81841b158fe511f7c7bd`. The isolated test checkout was
constructed from that exact tree; the patch changes only the files listed in
`verification.json` and these new evidence files.

- Focused launch, qualification, autonomous-controller, adversarial, and proposal
  suites: **103 tests, no failures/errors or skips**.
- Final broader permitted subset: see `unittest-O0.json` and `unittest-O1.json`
  for exact counts, dependency skips, and the complete 19-test exclusion list.
  The same pre-existing non-HQC selection policy is retained.
- Real `tclsh` executes the generated launcher with a small explicit stubbed
  command surface. Unknown commands fail; recreating `redirect` produces the
  reported Tcl error. Fixtures cover successful launch, warnings from three
  phases, synthesis failure, true version mismatch, missing executable, malformed
  reports, and missing actual-version metadata. These are synthetic tests.
- Independent review checked the changed code and documented Vivado 2022.2
  helper switches; its final focused launch/qualification run passed 36 tests.
- Python compilation and local Markdown-link checks pass as recorded in the
  machine-readable summary.

**No licensed Vivado replay was performed for this patch.** No hardware timing,
resource, mapped-memory, or source-ownership qualification is claimed. No model
API, paid EDA, HQC experiment, or GitHub Actions run was launched. The broader
subset is not a full-suite pass; explicit skips are not passes.

The next licensed-host check must use a **new run directory**, preserving the
failed run. The controller freezes updated adapter dependencies at setup.
Unchanged preparation can be reused; regenerate it only if its own frozen
site/XDC/Python/profile-verifier inputs changed. This fix does not bypass the
remaining post-synthesis evidence or mapped-memory admission requirements.

## Reproduce the license-free checks

```sh
python3 -m unittest tests.test_vivado_launch tests.test_vivado_qualification tests.test_autonomous_fpga tests.test_autonomous_fpga_adversarial tests.test_fpga_proposal -v
python3 docs/verification/vivado-launch-fix-2026-10-15/run_permitted_subset.py
python3 -O docs/verification/vivado-launch-fix-2026-10-15/run_permitted_subset.py
python3 -m compileall -q agent tools tests
python3 tools/check_docs.py
```

The checked-in subset runner is copied unchanged from the prior compatibility
verification and writes results only beside itself. It deliberately retains the
prior HQC exclusions and reports optional dependency skips.

## Primary references

- [Vivado 2022.2 synth_design, UG835](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/synth_design)
- [Vivado 2022.2 running synthesis with Tcl, UG901](https://docs.amd.com/r/2022.2-English/ug901-vivado-synthesis/Running-Synthesis-with-Tcl)
- [Qualification contract and additional command references](../../fpga/VIVADO_QUALIFICATION.md)
