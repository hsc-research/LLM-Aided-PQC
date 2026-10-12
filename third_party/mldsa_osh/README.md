# Pinned ML-DSA-OSH reference inputs

This bundle supplies the source, testbench, vector and common-data inputs needed
by the existing full-design ML-DSA KeyGen gate. It also supplies the previously
missing `zetas.txt` for the historical ASIC source arms. Importing these files
does not establish a new simulation, synthesis or FIPS 204 conformance result.

## Provenance and license

- Upstream: [KULeuven-COSIC/ML-DSA-OSH](https://github.com/KULeuven-COSIC/ML-DSA-OSH)
- Pinned commit: [`751009199ac081091a9059805e6921453bde0154`](https://github.com/KULeuven-COSIC/ML-DSA-OSH/tree/751009199ac081091a9059805e6921453bde0154)
- [Upstream LICENSE](upstream/LICENSE): MIT, copyright 2025 KU Leuven - COSIC.
  Apache-2.0 portions are identified in the preserved
  [upstream NOTICE](upstream/NOTICE) and original source headers. The repository
  also retains the [Apache-2.0 license text](../../LICENSES/Apache-2.0.txt).
- [SOURCE_MANIFEST.json](upstream/SOURCE_MANIFEST.json) records each selected
  upstream path, pinned Git blob SHA-1, byte length and SHA-256. Original source
  bytes and notices are unchanged, including non-UTF-8 source-header bytes.
- `upstream/` is a pinned source snapshot, without upstream Git metadata.
  There are 106 original files totaling 3,300,503 bytes: 49 design RTL files,
  three testbenches, 48 KAT files, two common files, and `LICENSE`, `NOTICE`,
  `README.md` and `CITATION`. The local provenance manifest is additional.
  Upstream `CITATION` is an empty file at the pin and remains unchanged.

The bundled [upstream README](upstream/README.md) describes runtime support for
KeyGen, SigGen and SigVer across all three levels. That is upstream design
scope, not the coverage of the local acceptance gate.

## Check the imported bytes

From the repository root:

```bash
python3 tools/check_mldsa_sources.py
```

This is an offline source-integrity and input-shape check. It must not be
reported as an RTL simulation, proof of equivalence or licensed synthesis pass.
Do not repair an integrity failure by changing expected hashes to match an
unreviewed source or silently substituting a different upstream revision.

## Run the existing KeyGen gate

With Vivado's `xvhdl`, `xvlog`, `xelab` and `xsim` on `PATH`, run:

```bash
# Bundled baseline, 25 vectors per level (75 total).
python3 agent/mldsa/full_kat_gate.py

# The same baseline and tests, with the current 14 candidate RTL overrides.
python3 agent/mldsa/full_kat_gate.py agent/mldsa/mldsa_src
```

The default source selection prefers this bundled tree. `MLDSA_ROOT` remains
an explicit environment override, and the gate's `--root` selects a source
root for that invocation. Record any override with the run. `VIVADO_BIN` can
add the installed simulator binary directory to the tool path.

The gate requires all 25 KeyGen vectors at each of levels II, III and V by
default. `--vectors N` intentionally reduces the per-level count; label such
runs as reduced coverage. The imported SigGen/SigVer testbenches and vectors
are retained but are not invoked by this gate. Even a 75-case KeyGen pass
does not establish signing, verification, independent FIPS 204 conformance,
side-channel resistance or hardware PPA.

Each run stages a private workspace under `PQC_RUN_DIR` (default `.pqc_runs`).
The gate applies its existing declaration-hoisting shim to a staged copy of
`combined_top.v`; the imported upstream file is not rewritten. Simulator
inputs therefore include the gate's existing portability treatment and must
be identified with their run artifacts. No Vivado simulation or commercial
synthesis was run as part of this import.

## Relationship to the existing ASIC arms

All 14 candidate override basenames have counterparts in the pin. Of 50 files
compared between the pristine design/common inputs and
`asic/arms/mldsa_baseline`, 48 are byte-identical. The remaining two are the
existing, documented portability edits:

- `combined_top.v`: forward-referenced declarations moved to module scope
- `ntt_fifo_piso.v`: blocking assignments changed to non-blocking assignments

The assignment edit changes semantics and requires functional validation; a
source comparison alone does not prove equivalence. These edits remain
untouched. See the
[historical portability findings](../../docs/findings/asic/2026-07-31_mldsa_genus_port.md).

The [full-design ASIC example](../../configs/mldsa_osh_asic.example.json) uses
the existing `asic/arms/mldsa_baseline` files with top `combined_top`, orders
VHDL packages before their users, and stages
[`common/zetas.txt`](upstream/common/zetas.txt) through `data_files`.
It does not replace those arms with unmodified upstream RTL. The gate command
with `agent/mldsa/mldsa_src` selects the FPGA candidate; it is not evidence for
the separate ASIC-arm source set.

Supply approved local libraries and site constraints, then qualify the chosen
Genus/DC installation, elaboration, ROM/memory treatment and exact measured
sources. Dry-run preparation and source completeness are not ASIC PPA results.
See the [ASIC guide](../../asic/README.md) for the measurement boundary and
remaining qualification requirements.
