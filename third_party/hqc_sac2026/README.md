# HQC SAC 2026: pinned, source-only baseline

This is the newer HQC source baseline selected for this project. Its status is **imported,
not functionally qualified**. The import does not run upstream software or RTL,
repair upstream files, or establish a simulation, synthesis, equivalence,
conformance, or PPA result.

Existing HQC runners and their historical results still concern the separate
SAC 2023-derived sources. They do not select this directory automatically.
No existing runner, CLI design entry, ASIC configuration, or acceptance gate
has been redirected to this snapshot.

## Provenance

- Repository: [dbroy-iitk/HQC_SAC](https://github.com/dbroy-iitk/HQC_SAC)
- Pinned commit: [`4be1fe99c677d6a3ff055d380a386f65184544f1`](https://github.com/dbroy-iitk/HQC_SAC/tree/4be1fe99c677d6a3ff055d380a386f65184544f1)
- Upstream tree: `a20e5140a5b4ce9e50c2e6a812f3a2c84f209920`
- Paper: [Performance Analysis of Parameterizable HQC Hardware Architecture,
  ePrint 2026/592](https://eprint.iacr.org/2026/592), by Nishant Pandey,
  Sanjay Deshpande, Dixit Dutt Bohra, Debapriya Basu Roy, Dip Sankar Banerjee,
  and Jakub Szefer, SAC 2026.
- Contribution 6 on page 3 of the [official SAC paper](https://sacworkshop.org/SAC26/preproceedings/SAC2026_1-final51.pdf#page=3)
  links this repository. [Sanjay's publications page](https://sanjaydeshpande.phd/publication/)
  links the same code, and the preserved [upstream README](upstream/readme.md)
  links back to ePrint 2026/592.

The [source manifest](SOURCE_MANIFEST.json) is locally authored and separate
from the unchanged `upstream/` tree. It records every included upstream path,
Git blob SHA-1, SHA-256, byte length, file mode, and category. It also records
every exclusion, so the file inventory accounts for the entire pinned tree.

## What is included

All 126 non-Finder-metadata upstream files are retained, totaling **1,459,138
bytes**. Only three `.DS_Store` files are excluded. There are no upstream Git
metadata, generated binaries, imported simulation logs, or synthesis outputs.

- 88 design Verilog files, including alternative implementations present in
  the upstream tree. This count is an inventory, not a validated compile list.
- 14 Verilog testbench/test-vector files, including operation, joint-design,
  common-component, and SHAKE tests.
- 12 memory/stimulus files: three Barrett tables and nine `u`, `v`, and `y`
  inputs for the three parameter sets.
- Seven build/input scripts: the Makefile, four Tcl scripts, and two Python
  seed-alignment scripts. They are preserved as source bytes and were not run.
- The upstream license, three upstream documentation files, and the empty
  `build/.gitkeep` marker.

Useful source entry points:

- [Key generation](upstream/hardware/keygen/keygen.v)
- [Encapsulation](upstream/hardware/encap/encap.v)
- [Decapsulation](upstream/hardware/decap/decap.v)
- [Shared joint design](upstream/hardware/joint_design/hqc_kem_joint_design.v)
- [Shared modules](upstream/hardware/common/)
- [Upstream build recipes](upstream/Makefile)

The top-level sources expose `hqc128`, `hqc192`, and `hqc256` parameter sets,
corresponding to the paper's HQC-1, HQC-3, and HQC-5 terminology. The paper
describes all three KEM operations and a unified architecture, with a
configurable datapath. These describe upstream design scope; importing the
files does not establish that every operation, width, or security level works.

The published memory-input README specifies fixed zero seeds and sample
messages. Those public stimulus files are not production keys, fresh entropy,
or an independent official known-answer response suite. No missing generated
outputs have been fabricated or borrowed from the SAC 2023 baseline.

## License and attribution

The unchanged [upstream LICENSE](upstream/LICENSE) contains GNU GPL version 3.
Sampled HQC and SHAKE source headers grant GPL version 3 or later and retain
their original author/copyright notices, including Sanjay Deshpande and Jakub
Szefer and the SHAKE implementation's attribution to Bernhard Jungk's earlier
work. There is no separate upstream `NOTICE` file at this pin.

All original source headers and documentation are retained byte-for-byte.
Some alternative source files have no individual license header. The upstream
repository license is retained; this import is not a complete source-by-source
redistribution clearance or legal opinion. Preserve and review applicable
component notices before redistribution. Local provenance/documentation does
not replace upstream terms.

## Static findings and qualification still required

Source-copy integrity was checked by comparing decoded file bytes with the
pinned Git blob IDs and by reading back each copied file's SHA-256. All 126
files matched. This is a byte-integrity result only.

Static inspection found reasons not to treat the upstream recipes as an
already-qualified all-level flow:

- [The encapsulation Tcl](upstream/hardware/encap/tcl/encap.tcl) comments out
  the HQC-192 selection and run, although the upstream README describes all
  parameter sets.
- [The joint-design Tcl](upstream/hardware/joint_design/tcl/joint_design.tcl)
  assigns `verilog_define` separately for `SHARED` and `SHARED_ENCAP`, rather
  than supplying both definitions together. Its simulation launches are
  commented out. These lines were preserved without repair.
- The tree contains multiple implementations and testbenches. It is not one
  validated source manifest for compiling every `.v` file together.

Before a future executable integration is qualified, it needs a reviewed
ordered compile list, explicit configuration/width/level selection, input and
expected-output provenance, an independent correctness oracle including
invalid-ciphertext behavior, and functional coverage of every claimed mode.
Claims of correspondence to the paper's updated specification and compressed
keys also require validation of the actual imported implementation.

ASIC qualification additionally requires a reviewed memory/initialization
strategy, target libraries and timing constraints, clean elaboration, and
matched baseline/candidate measurements. Existing SAC 2023 functional or
Genus-elaboration evidence does not qualify this SAC 2026 snapshot.

No executable adapter, script repair, simulation, or synthesis is supplied or
claimed by this source-only import.
