# Release and third-party review

Status: **review incomplete**, 2026-10-12. The portable software checks do not
clear the historical files for public redistribution. No files or Git history
were removed as part of this documentation update.

## Known review items

| Material | Observed in this checkout | Required before release |
|---|---|---|
| Cadence binary design snapshots | Three `*_generic.db`, `*_mapped.db`, and `*_final.db` files under `logs/asic/asap7_bf2x2_optvariant_20260810/` | Owner/vendor review of the applicable tool terms and contents; these are design databases, not identified target-cell libraries |
| Vendor diagnostics | Historical ASIC logs include `Cadence Confidential` notices | Review the notices and redistribution terms; do not infer clearance or proprietary foundry content from a filename alone |
| ML-DSA imports | GMU/CERG Apache-2.0 and KU Leuven/COSIC MIT headers | Preserve the applicable notices, verify upstream revisions and any required upstream NOTICE files |
| HQC imports | Yale/Deshpande headers, including GPL v3-or-later terms | Confirm the complete upstream source/notice set |
| SLH-DSA/SPHINCSLET imports | Project RTL plus Secworks SHA-2 and MIT-licensed Keccak components | Confirm the top-level project's terms and all imported components; a license on a submodule does not cover every file |
| Public test data | Checked-in testbench fixtures include secret-key-named files | Keep them test-only; confirm their documented origin before packaging and never replace them with live keys |

This is an inventory of observed notices and pending work, not a legal opinion
or a statement that every component's terms have been satisfied.

## Notices retained

- [Root GPL v3 license text](../LICENSE)
- [Third-party summary](../NOTICE)
- [Apache License 2.0 text](../LICENSES/Apache-2.0.txt), accompanying headers in
  [ML-DSA overrides](../agent/mldsa/mldsa_src/)
- Secworks two-clause redistribution text in
  [SHA-256](../agent/slh_dsa/pristine/sphincslet/sha/sha256_core.v) and
  [SHA-512](../agent/slh_dsa/pristine/sphincslet/sha/sha512_core.v)
- MIT text in [Josh Moles' Keccak round](../agent/slh_dsa/pristine/sphincslet/shake256/keccak_round.v)
  and [Ma'muri's Keccak top](../agent/slh_dsa/pristine/sphincslet/shake256/keccak_top.v)

Keep the corresponding notices in both baseline and modified copies. The
source headers are more specific than a repository-wide license label.

## Packaging policy

A reviewed source release should use an explicit file list. Exclude API keys,
license-server configuration, PDKs, target libraries, binary tool databases,
and unreviewed vendor logs. Retain source notices and the license texts needed
for the included files.

Python package builds are for the tooling, not a full hardware experiment
archive. Historical reports, binary snapshots, RTL snapshots, external design
inputs, and vendor libraries must not be silently bundled as Python package
data. Inspect the built wheel and source archive before publishing either.

Excluding a file from a new package does not remove it from Git history or an
existing public checkout. A separate repository/history decision and explicit
authorization would be needed for that. Preserve the original evidence in a
permitted location and document any omission from a distributable archive.

## Verification before publishing

- [ ] Resolve the vendor database/log review above
- [ ] Complete upstream license and notice review for all distributed source files
- [ ] Check the actual release file list, including generated archives
- [ ] Run the [offline tests](REPRODUCE.md) in a fresh environment
- [ ] Mark hardware flows as executed, preparation-only, or blocked
- [ ] Attach complete source/tool/configuration evidence to any PPA claim
- [ ] Verify that every local documentation link works in the chosen package
- [ ] Record a release commit; do not invent a release date, DOI, or hardware result
