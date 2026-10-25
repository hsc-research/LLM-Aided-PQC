# ML-DSA verified derivatives and hardware handoff

## Results of this verification

The original sources are preserved. The newly passing results belong to explicit
functional derivatives, **not** the unmodified upstream design or the old
fourteen-file optimization candidate.

| Source selection | Upstream KeyGen | Upstream Sign | Upstream Verify | Added tests | Overall |
|---|---:|---:|---:|---|---|
| Pinned baseline, portable testbenches | 75 pass | 45 pass | 45 pass | 11/12 one-bit negatives rejected | **FAIL**: accepts one noncanonical hint |
| Existing 14-file candidate | 75 pass | 0 complete, cycle watchdog | 45 pass in a separate run | Same noncanonical hint accepted | **FAIL** |
| Baseline + canonical hint guard | 75 pass | 45 pass | 45 pass | 12 mutation + 33 canonical/control cases pass | **210/210 PASS** |
| Candidate + encoder fallthrough + canonical guard | 75 pass | 45 pass | 45 pass | 12 mutation + 33 canonical/control cases pass | **210/210 PASS** |

All three security levels are covered. Upstream Verify contains **9 valid and
36 invalid** cases: the hardware returns an active-high failure flag, where
`0` means valid and `1` means invalid. The 33 additional cases alternate a valid
control with count overflow, decreasing counts, duplicate indices, descending
indices, and nonzero padding, across all three levels. They cover reset-based
recovery; the upstream testbench resets before each operation.

Permanent reports and raw simulation logs:

- [Guarded baseline](../../docs/verification/mldsa-portable-2026-10-12/baseline_canonical_pass/result.json)
- [Corrected candidate](../../docs/verification/mldsa-portable-2026-10-12/candidate_corrected_pass/result.json)
- [Retained baseline failure](../../docs/verification/mldsa-portable-2026-10-12/baseline_upstream_failure/result.json)
- [Retained original candidate Sign failure](../../docs/verification/mldsa-portable-2026-10-12/candidate_sign_failure/result.json)
- [Retained original candidate Verify/negative failure](../../docs/verification/mldsa-portable-2026-10-12/candidate_verify_failure/result.json)
- [Toolchain/package provenance](../../docs/verification/mldsa-portable-2026-10-12/toolchain.json)

These are actual Verilog RTL plus GHDL-synthesized VHDL-netlist simulations under
the preserved Verilator build (launcher `vUNKNOWN-built20260516-4e853d8`, runtime
5.49). They are two-state simulations. Full-design Icarus four-state simulation
**did not pass**: a reduced KeyGen run timed out while the event scheduler remained
at 106 time steps. Its [failure record](../../docs/verification/mldsa-portable-2026-10-12/icarus_full_datapath_timeout/result.json)
and scheduler diagnostic are retained.

Complementary four-state Icarus checks passed for the added guard and repaired
encoder, with their narrower scopes stated below.

## What was fixed

### Canonical hint validation

The original `usehint.v` expands indices into a bitmap without enforcing all
canonical encoding requirements. In ML-DSA-87 positive control index 4, changing
the last hint-count byte from `0x32` to `0x33` adds a duplicate index zero after
`0xb3` in the final polynomial. The bitmap is unchanged, so the original design
accepts the modified signature. This byte is inside the signature, not transport
padding.

[FIPS 204, Algorithm 21, HintBitUnpack](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.204.pdf)
requires bounded, nondecreasing cumulative counts, strictly increasing indices
within each polynomial, and zero unused index bytes. Empty polynomials and index
zero remain valid.

The separate [`mldsa_hint_guard.v`](mldsa_hint_guard.v) checks all those conditions.
The staged `usehint.v` latches an invalid-encoding flag until reset or a new start;
the staged top ORs it into the final active-high Verify failure result. This is a
semantic hardening variant, selected by `--canonical-hints`, and never edits the
pinned source or original candidate.

The standalone four-state checker passes 1,350 encodings (198 valid, 1,152 invalid).
An [independent four-state review](../../docs/verification/mldsa-portable-2026-10-12/independent-hint-guard-review.json)
passes a separate 9,371 encodings, including empty groups, the omega boundary,
all padding positions, ordering reset between polynomials, and index 255.

### Encoder output timing

The old banked encoder adds a FIFO output cycle while the surrounding controller
uses fixed drain deadlines. In the first failing Sign case, the controller resets
the encoder with two words still queued and loses the final challenge-input word.
A one-cycle change to only one controller deadline is insufficient and remains a
failed diagnostic experiment.

[`encoder_fallthrough.v`](encoder_fallthrough.v) preserves banked storage but
exposes an accumulator word directly when the output FIFO is empty. This restores
the reference output timing. The correction is selected by `--encoder-fallthrough`
with an explicit candidate override directory. The original fourteen files remain
unchanged.

[Encoder diagnosis, exact patch, controls and evidence](../../docs/verification/mldsa-portable-2026-10-12/encoder-fallthrough.md)
include 11,659 checked cycles and 2,278 accepted words over 18 configurations and
two mode-switch sequences. The repaired and pinned encoders pass; the old banked
encoder fails. Explicit both-valid-X and both-data-X injections fail the knownness
checks. This is finite cycle/stream testing with the documented buffer envelope,
not unconstrained formal equivalence.

## Export the exact sources for FPGA/ASIC work

The exporter runs **no EDA tools**. Both comparison arms include the canonical
guard and use the same interface and memory boundary:

```sh
python3 tools/export_mldsa_verified.py --variant guarded-baseline \
  --out build/mldsa-handoff/guarded-baseline
python3 tools/export_mldsa_verified.py --variant corrected-candidate \
  --out build/mldsa-handoff/corrected-candidate
```

Each output directory must be absent or empty. The default export contains 35
Verilog source files, including the exact GHDL-generated Keccak netlist bytes from
the passing run. Export checks every reconstructed source against that run's
recorded hashes before producing a manifest.

Each directory contains:

- `manifest.json`: ordered source languages/hashes, top, runtime controls,
  parameter overrides, defines, memory input, and the qualifying report/hash
- `sources.f`: relative source paths, with `combined_top` last
- `sources.tcl`: source-list variables only; it invokes no EDA commands
- `zetas.txt`: ROM data; run tools from the export directory so `$readmemh` resolves
- `common/mldsa_params.v`: reference testbench parameter definitions
- License and notice files

Top: `combined_top`; no top-level parameter overrides or extra preprocessor defines.
Mode is runtime-selected: 0 KeyGen, 1 Verify, 2 Sign. Security level is 2, 3, or 5
for ML-DSA-44, -65, or -87. Memories are generic RTL/inferred structures; technology
mapping, memory treatment, clocks, constraints and implementation settings remain
the hardware flow's responsibility.

For a tool that will compile the original VHDL instead of the captured netlist:

```sh
python3 tools/export_mldsa_verified.py --variant corrected-candidate --format mixed \
  --out build/mldsa-handoff/corrected-candidate-mixed
```

The mixed export has 16 dependency-ordered VHDL files and 34 Verilog files. These
VHDL bytes are the inputs to the passing GHDL conversion. Direct mixed-language
simulation/source-to-netlist equivalence has **not** been established. Do not
compile both the VHDL and generated Verilog `keccak_top` definitions together.
Do not use an old unguarded baseline/old-candidate ASIC example as a qualified
comparison arm by mistake.

No FPGA/ASIC synthesis or PPA is supplied by this handoff. Both the canonical guard
and encoder fallthrough mux change logic and timing paths. Historical PPA cannot
be attributed to these sources; measure both exported arms under the same flow.

## Reproduce functional verification

Requirements: Python 3.10+, GHDL with synthesis/Verilog output and its Synopsys
compatibility packages, Verilator plus a C++ compiler/make, and Icarus for the
standalone four-state checks. The verified local Linux x86-64 GHDL setup is:

```sh
python3 tools/bootstrap_mldsa_ghdl.py --prefix /tmp/pqc-ghdl
export PATH=/tmp/pqc-ghdl/bin:$PATH
```

The explicit setup helper downloads SHA-256-pinned official Debian packages,
extracts them locally, and builds the two legacy compatibility units locally.
It does not run apt, require root, or modify system settings. GHDL 6 packages omit
those legacy sources, so exact source bytes are taken from the pinned GHDL 5
common package. The initial GHDL 5 emitter failure is retained in the toolchain
record. No GHDL 5 executable/libgnat runtime is needed by the successful setup.

Run the passing arms:

```sh
python3 agent/mldsa/portable_kat_gate.py --simulator verilator \
  --canonical-hints --verify-mutations
python3 agent/mldsa/portable_kat_gate.py --simulator verilator \
  --override agent/mldsa/mldsa_src --encoder-fallthrough \
  --canonical-hints --verify-mutations
```

The preserved Verilator wheel in the recorded environment needed
`MAKEFLAGS='CFG_CXXFLAGS_PCH_I=-include'` to correct its missing GCC precompiled-header
include switch. This is a compiler configuration repair, not an RTL change. Exact
commands, wrappers, executable/package hashes and versions are in the toolchain
and bootstrap records.

For block/control checks:

```sh
python3 tools/check_mldsa_hint_guard.py
python3 tools/check_mldsa_encoder_fallthrough.py
python3 -m unittest tests.test_mldsa_portable_gate tests.test_mldsa_source_integration tests.test_mldsa_export
python3 tools/check_mldsa_sources.py
```

Original-source failures remain reproducible by omitting the semantic fix flags.
`--vectors N` is reduced coverage. It cannot be combined with `--verify-mutations`,
because the chosen unchanged positive controls must be covered first. The full
runner stages private inputs under `.pqc_runs/` (or `PQC_RUN_DIR`), records exact
coverage/return codes/input and executable hashes, applies cycle and wall-time
watchdogs, and fails on missing/duplicate results, errors or changed files.

## Testbench portability and remaining boundaries

The original benches read/write 64-bit slices that extend beyond the final
3–5 signature hint bytes. This Verilator build zeros the whole out-of-range dynamic
slice. The runner packs/captures those words bytewise while retaining every
original signature-byte comparison. An [independent minimal simulator diagnostic](../../docs/verification/mldsa-portable-oob-diagnostic-2026-10-12.json)
confirms the behavior. `--raw-sign-capture` and `--raw-verify-hint-read` retain the
original behavior for diagnosis. Upstream Verify's original failure-message
argument labels are reversed; compare its actual failure bit with the expected
fixture bit, rather than trusting the printed “Expected/received” labels.

The runner also hoists forward declarations in the staged top, adds testbench
watchdogs, and selects leading fixture records for reduced runs. The optional
`--fifo-nonblocking` semantic variant was not needed for the passing results.
All 106 pinned upstream files remain unchanged.

Oracles are the pinned **upstream KAT files**. Their reported NIST/ACVP origin is
not independently authenticated by this runner. These results do not establish
FIPS certification, universal cryptographic correctness, formal VHDL/netlist or
RTL equivalence, side-channel resistance, arbitrary backpressure correctness,
physical timing closure, or measured PPA.
