# Candidate safety and ASIC selection update

[Project](../README.md) · [Agent](../agent/README.md) · [ASIC](../asic/README.md)

This page records the earlier candidate-safety/ASIC-selection update. Its test
counts and unrun stages are a historical snapshot. For the current checkout,
use [design status](PROJECT_STATUS.md), the [verification record](VERIFICATION.md)
and the [run guide](REPRODUCE.md).

## Changes

The FPGA top-level PPA-rejection branch previously printed a revert verdict without restoring the source. It now wraps candidate evaluation in a transaction covering the configured source directories and checkpoint. Failed tests, insufficient timing gain, exceptions, and timeouts restore the pre-run working state, including uncommitted files and paired edits. Accepted RTL remains uncommitted for review.

HQC joint testing previously staged pristine files and checked out tracked joint-design sources, potentially replacing a proposed edit before simulation. It now copies the effective synthesis manifest into a private workspace. Live candidate files are never staged over or reset to HEAD. The joint simulation sets SHARED and SHARED_ENCAP together rather than overwriting one define with the other. Top-level verification requests all three HQC levels. Source hashes are checked across testing and implementation.

The update also introduces unique run tags, timeout cleanup, a per-checkout top-level lock, strict process-status checks, rejection when no effective source changed, and no dispatch without a supported checker. Existing FPGA timing recipes and historical measurement records are not modified.

A common command entry point now selects FPGA/Vivado or ASIC/Genus/DC. ASIC runs use ordered manifests, per-tool libraries and commands, fresh output directories, provenance, and supported report parsing. They do not call the LLM, perform place-and-route, or automatically accept a new RTL baseline. Legacy ASIC scripts remain available for historical reproduction.

## Validation

The earlier candidate-safety/ASIC-selection update passed **44 tests** using temporary files, mock executables, and Tcl command stubs. Coverage includes multi-file rollback, dirty-file preservation, source mutation, private HQC staging, combined defines, failed KATs, PPA rejection, missing artifacts, invalid timing, explicit tool choice, input provenance, and timeouts. Python syntax compilation also passed.

That historical count is not the current test total. Run the complete suite
against the checkout being reviewed. No Vivado, Genus, DC, hardware simulation,
or model call was run during that software validation. Both generated ASIC flows and the changed HQC gate must be checked on the licensed server before merging as an EDA-validated release. Run the suite with `python3 -m unittest discover -s tests -v`.

## Remaining boundaries

- ML-DSA now defaults to the pinned bundled source/testbench/KAT/common tree;
  its current full-design simulation remains unrun and the gate covers KeyGen
  only. SLH-DSA stages private inputs and selects the frozen vendor stream for
  each of the six SHA2 sets, including the unchanged 192f candidate. Fresh RTL
  simulation is unrun; SHAKE and independent FIPS 205 validation are unsupported.
- The FPGA period search remains bounded and cannot prove global Fmax. The
  portable follow-on removes DRC warning downgrades and checks routing and
  timing reports more strictly; it does not revalidate historical measurements.
- Transactions and locks protect cooperating code, not hostile programs or concurrent manual edits. Direct legacy optimizer invocations are outside the top-level transaction.
- SIGKILL or power loss cannot execute rollback. Backups remain under `.pqc_runs/transactions/`; inspect the manifest and restore its scopes before restarting.
- Functional evidence remains design-specific. The new whole-design controller compares declared per-operation cycle profiles; this does not add untested operations or an all-input constant-time proof.
- ASIC report formats and library units need site review. Unknown fields stay null. The example SDC is not a reproduction of the historical ASAP7 experiment constraints.
- Legacy learned-rule records may refer to block-level successes; the top-level verdict determines the integrated result.

The earlier safety update did not alter hardware RTL, vectors or historical measurements.
The current follow-on additionally imports pinned upstream ML-KEM/ML-DSA inputs
and new local ML-KEM verification evidence, preserving original notices and
existing RTL snapshots. See [the current verification record](VERIFICATION.md).

## Portable setup and public documentation

The follow-on adds standard-library `doctor`, `list`, and `smoke` commands,
optional Python extras, explicit opt-in for model calls, and an offline-first
installation guide. Current setup, four-scheme coverage, result interpretation,
and dated research records now have separate entry points.

The Makefile cleanup target preserves tracked HQC source snapshots. Source
packaging excludes historical hardware evidence and binary tool artifacts.
Third-party notices now cover SLH-DSA imports, and Apache-2.0 text accompanies
the ML-DSA headers. The [release review](RELEASE_CHECKLIST.md) remains open;
package exclusions do not remove historical files from the repository.
