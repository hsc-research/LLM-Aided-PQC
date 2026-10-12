# Adam's Bridge unified reference baseline

This package vendors the **unified ML-KEM-1024 / ML-DSA-87 accelerator**, including
its generic memories. It is a full key-generation, encapsulation, and
decapsulation reference, not an NTT-only block. It is **not a standalone ML-KEM
area baseline**: the hardware also implements ML-DSA-87.

## Provenance and license

- Upstream: https://github.com/chipsalliance/adams-bridge
- Release: [v2.0.3](https://github.com/chipsalliance/adams-bridge/releases/tag/v2.0.3)
- Commit: `b77e3d899e828d626cfc2a0d26a6b5704cc121e0` (2026-03-12)
- License: [Apache-2.0](upstream/LICENSE). Original notices remain intact.
- `upstream/` contains 220 selected, unmodified text files. It is a source subset,
  not a complete upstream checkout. The complete design file-list closure is
  present, together with all RTL include files, reference KAT sequences, and
  selected documentation. No binaries, PDKs, generated bitstreams, or upstream
  executable test generators are included.
- [Upstream hash manifest](upstream/SOURCE_MANIFEST.json) records Git blob SHA-1,
  byte length, and SHA-256 for every selected file. All were checked against
  the pinned repository contents.
- `integration/` is a locally authored addition dated 2026-10-12. Upstream RTL
  was not edited. Derived vector files are identified in `test_vectors/`.

The upstream release reports completed verification plans, clean CDC/lint/RDC/
synthesis, and continued regressions. Public UVM sequences include known-answer
checks for complete keys, ciphertexts and shared secrets; formal property
artifacts are also public. These are **upstream evidence**, not a claim that this
local wrapper or these synthesis flows have passed them. The public formal
README says reproduction load scripts must be requested from LUBIS EDA.

## Local qualification status

The pinned baseline's ML-KEM-1024 API passed all 80 bundled official ACVP cases
under Verilator 5.032 on 2026-10-12: 39,840 exact word/status checks, including
five implicit rejection secrets and 20 key-input checks. Compile and simulation
both exited zero; original source bytes stayed unchanged. See the
[recorded evidence](../../docs/verification/mlkem-adams-bridge-acvp-2026-10-12.json).

This is sampled, two-state RTL simulation, not NIST certification, formal proof,
ML-DSA-87 verification, four-state X checks, side-channel evaluation, or vendor
synthesis/PPA. Upstream assertion macros are disabled under Verilator; the
independent testbench checks remain active. The integration manifest's original
qualification label records import-time status and is superseded by the dated
evidence. It remains unchanged to preserve the qualified input fingerprint.

Run the local, standard-library-only integrity check from any directory:

```sh
python3 third_party/adams_bridge/integration/verify_sources.py
```

This command neither imports nor executes upstream software and does not invoke
an EDA tool. Failure must stop baseline admission.

## Synthesis and simulation inputs

- Top: `abr_unified_top`, defined in
  [the local wrapper](integration/abr_unified_top.sv).
- The wrapper instantiates unmodified `abr_top`, `abr_mem_if`, and `abr_mem_top`.
  All ten upstream external memory instances are therefore included. Synthesizing
  `abr_top` alone would leave those memories outside the measured boundary.
- Fixed interface: 32-bit AHB address, 64-bit AHB data, 32-bit internal register
  accesses, `clk`, active-low `rst_b`, debug/scan zeroization input, and status/
  interrupt outputs. Respect AHB address/data phase timing and byte lanes.
- [sources.f](integration/sources.f): 25 include directories and 175 ordered
  source/header entries, including the wrapper. Paths are relative to this
  package directory. Do not compile all `.sv` files in alphabetical order.
- [manifest.json](integration/manifest.json): equivalent structured metadata.
- [sources.tcl](integration/sources.tcl): data-only Tcl adapter yielding absolute
  `abr_sources`, `abr_include_dirs`, and `abr_top`. It launches no EDA process.

For Vivado synthesis, the proposed define set is `SYNTHESIS RV_FPGA_OPTIMIZE`.
`RV_FPGA_OPTIMIZE` selects upstream FPGA memory inference code and a ROM
attribute. For DC/Genus, use `SYNTHESIS` and the generic memory code. These
settings require tool-version qualification; their availability is not evidence
that Vivado/DC/Genus has successfully compiled the imported sources.

Do not define `CALIPTRA`: that enables external key-vault types and interfaces.
Do not define `ABR_SIMULATION` or `RV_FPGA_SCA` for the synthesis wrapper.
The pinned upstream config defines `MLDSA_MASKING`; leave that unchanged for the
initial baseline. The current upstream main branch is a different architecture
with different parameters and memory dimensions; do not mix its files or docs
into this pinned release.

The default RAM models infer generic state rather than an ASIC SRAM macro. A
logic-only DC/Genus run may therefore have substantial flop-mapped memory area.
Declare `memory_model=flops` and count all memory logic, or supply an explicit,
verified SRAM mapping with macro area/timing. Do not silently black-box memory.
The generic clock-gating model must be qualified for the target FPGA/ASIC flow.
Foundry-specific security-cell mapping and preservation constraints are a
separate requirement for side-channel claims.

## Launch preparation

From the repository root, check the source package and run the full vector gate:

```sh
python3 third_party/adams_bridge/integration/verify_sources.py
python3 tools/run_mlkem_adams_bridge_kat.py --simulator verilator
```

The gate requires a compatible installed Verilator with timing support. It
returns zero only after all 80 official cases have actually passed RTL
simulation. Missing tools, compile errors, timeouts and `--prepare-only` return
nonzero. The available Icarus fallback currently rejects upstream SystemVerilog;
its presence does not qualify this core. See `--help` for explicit tool paths,
timeouts, output directory and report options. No tool is installed automatically.

For a baseline-only Vivado OOC synthesis run:

```sh
export FPGA_PART=your_exact_device_part
vivado -mode batch \
  -source third_party/adams_bridge/integration/vivado_synth.tcl \
  -tclargs "$FPGA_PART" 10 runs/mlkem-adams-baseline-synth
```

Choose a real part before running. The 10 ns period is an example target, not a
measured or recommended Fmax. The output path must not already exist. The script
checks source identity, reads the full wrapper and memories, uses the upstream
FPGA define, and writes hierarchical utilization, timing, DRC and clock checks.
It does not place/route or interpret a synthesis report as a functional pass.
Default clock-gate conversion is explicitly off; changes require a qualified
and matched baseline/candidate configuration. Review the example 10% I/O-delay
assumption against the actual interface contract.

For Genus/DC, prepare a local copy of the actual runner configuration:

```sh
cp configs/mlkem_adams_bridge_asic.example.json configs/mlkem_adams_bridge_asic.local.json
export PQC_GENUS_TARGET_LIB=/absolute/path/to/your/target.lib
export PQC_DC_TARGET_DB=/absolute/path/to/your/target.db
# Also set reviewed values for these variables as described in
# configs/asic_site.example.tcl:
# PQC_ASIC_INPUT_TRANSITION_NS, PQC_ASIC_CLOCK_UNCERTAINTY_NS, PQC_ASIC_OUTPUT_LOAD
python3 -m agent.run --target asic --synth-tool genus \
  --config configs/mlkem_adams_bridge_asic.local.json --dry-run
python3 -m agent.run --target asic --synth-tool genus \
  --config configs/mlkem_adams_bridge_asic.local.json
python3 -m agent.run --target asic --synth-tool dc \
  --config configs/mlkem_adams_bridge_asic.local.json
```

Edit the copied config's target period, library time unit, corner, tool version,
library list, and setup/SDC as required by your site. The example declares ns;
the loaded library must match, or change the declaration appropriately. DC
requires compiled `.db` files. Only the selected tool's library variable is
needed for a run. Dry-run still requires real readable input/library files.
The default `flops` model measures all generic memory logic; no ASIC SRAM PDK
or licensed library bytes are bundled. These generated flows still require
licensed target-tool qualification and do not claim standalone ML-KEM PPA.

There is no supported `MLKEM_ONLY` parameter in this release. A workload using
only ML-KEM does not make the ML-DSA datapath unreachable during synthesis.
Pruning it would create a new derived architecture requiring fresh verification.
Pair baseline and optimized results using the same wrapper, memory model,
algorithm subset, tool version, constraints, library, and implementation stage.

## Test-vector provenance

- `upstream_kats.json` extracts the three hardcoded upstream UVM KAT cases
  without changing their bytes. Their source provenance is the upstream
  repository; no claim is made that these literals are official NIST ACVP data.
- `nist_acvp_mlkem1024.json` contains 80 official published FIPS203 ACVP sample
  cases: 25 KeyGen, 25 Encaps, 10 Decaps, 10 encapsulation-key checks, and 10
  decapsulation-key checks. The file preserves inputs, expected results, group
  attributes, `tgId`, and `tcId`; no cryptographic outputs were generated locally.
- NIST source: [ACVP-Server](https://github.com/usnistgov/ACVP-Server/tree/975de31eb83d87039ec88934fdc47d8c312b892d/gen-val/json-files),
  commit `975de31eb83d87039ec88934fdc47d8c312b892d` (2026-08-12).
  Raw source hashes are in `test_vectors/NIST_SOURCE_MANIFEST.json`.
  The derived subset was created 2026-10-12 by selecting ML-KEM-1024 groups and
  joining prompt/expected-results records on `tgId` and `tcId`.
- NIST's complete license notice is preserved in
  `test_vectors/NIST_ACVP_README.upstream.md`, under its License section.
  NIST is acknowledged as the source of the official test-vector data.

Algorithm byte strings map to little-endian 32-bit register words; preserve the
order of words. Output lengths are `ek=1568`, `dk=3168`, `c=1568`, `k=32` bytes.
The harness must compare every output byte, include invalid-ciphertext implicit
rejection and invalid-key checks, fail on timeout or bus error, and return
nonzero for any mismatch, missing case, or unrun simulation. Passing published
sample vectors is not NIST validation/certification or side-channel assurance.

The release's randomized UVM sequence invokes `ml-kem/random_test_ml_kem.py`,
which is absent from the pinned release tree; a stock randomized-UVM run is not
self-contained. Use an independently authored ACVP-driven testbench or an
explicitly qualified reference-model dependency. Do not run downloaded `.exe`
files or silently add a moving-branch software oracle.
