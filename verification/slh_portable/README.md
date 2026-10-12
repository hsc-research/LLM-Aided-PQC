# SPHINCSLET portable differential verification

This is a separately identified **Icarus portability variant**, not a claim
that the unmodified vendor tree compiled. It runs the actual SPHINCSLET
signing and verification RTL, compares the entire generated stream with a
frozen historical vendor answer, then repeats with one captured signature
bit corrupted before the RTL verifier reads it.

## Scope and algorithm version

- Original RTL: CASLAB SPHINCSLET, pinned upstream revision
  `a1adc2b324483d0f95ae42b3119997d3a61c77b6`.
- Expected streams and trusted fixtures: existing repository revision
  `25a9de8fb399644889f9d6f602b302f949a6e86f`; no run creates or replaces them.
- Algorithm/evidence label: historical SPHINCSLET vendor SHA2 fixture,
  `portable_vendor_rtl_differential`.
- **This is not independent FIPS 205 or ACVP validation.** The fixed answers
  came from the vendor RTL, not an independent current-standard oracle.
  Signature-plus-message framing and matching parameter names alone do not
  establish conformance to FIPS 205. No official certification is implied.
- The selected-mode gate supports SHA2-128f, 128s, 192f, 192s, 256f and 256s.
  SHAKE is rejected. Supporting a selection in the harness does not mean
  that selection has actually completed simulation.
- Current tracked configurations are pristine SHA2-128f and optimized
  SHA2-192f. They use their own reference, input keys and output filename.
  These are one deterministic 33-byte-message fixture per configuration,
  not all-message coverage or a security/side-channel claim.

## Explicit portability changes

[The runner](../../tools/check_slh_portable.py) copies the selected tree to a
fresh run directory. The original and staged source sets are hashed. Only
three hash-pinned vendor files are transformed, and every before/after hash
and unified diff is recorded:

1. `sphincslet/fsm/FSM.v`: remove two redundant internal `wire` declarations
   already present in the ANSI output port list (`WOTS_FSM_start` and
   `WOTS_s_in_0_wr_en`).
2. `sphincslet/hash_tile/hash_mem_interface_sha.v`: normalize one replication
   count from a concatenated unsized expression to the expression itself.
   The zero-padding count and width are unchanged.
3. `sphincslet/tb.v`: assign the 23 ignored `$fscanf` return values to an
   otherwise unused integer, observe the final RTL verification flag, and
   add a disabled-by-default negative-control hook before verification.
   File inputs, signing stimulus, generated-output capture, and the vendor
   verification sequence remain the same.

The hook flips bit 0 in signature memory word 0 only when the runner supplies
`+SLH_TAMPER`. The baseline and negative run use the **same compiled RTL
executable** in separate fresh directories. Both first sign the same trusted
message and must emit the complete unchanged known-answer stream. The
negative run then corrupts the in-memory signature, independently of the
saved stream, and must finish RTL verification with flag `1` and the vendor
mismatch marker. The baseline requires flag `0` and the match marker.
Unknown/high-impedance verification flags cannot pass.

The runner does not patch the checkout, its pristine tree, reference files,
or checksums. A changed portability input fails closed until reviewed; it
is not silently adapted. Other candidate RTL, including the optimized SHA
cores, is copied and simulated as selected. A `portability.patch` plus
source/input manifests and complete compile/simulation logs remain under
`.pqc_runs/slh-portable-*`.

## Explicit authentication-path sensitivity correction

An optional `--fix-auth-sensitivity` creates a **separate corrected variant**.
It changes the hash-pinned vendor `XMSS_FSM.v` block from
`always@(h_cnt2)` to `always@(h_cnt2, leaf_idx)`. This block reads both signals
when computing the authentication-path target and left/right selection;
without `leaf_idx` in the event list, simulation can retain values from a
previous FORS tree when the height does not change.

This is more than the syntax-only portability changes above. It is disabled
by default, identified by `auth_sensitivity_fix: true`, recorded in the patch
and source hashes, and never applied to the original checkout. A successful
corrected run qualifies this corrected portable variant. It does not relabel
the syntax-only variant as passing or prove vendor-tool equivalence.

## Reproduce

From the repository root, with Icarus Verilog compiler/runtime on `PATH`:

```sh
python3 tools/check_slh_portable.py \
  --rtl-dir agent/slh_dsa/pristine \
  --output .pqc_runs/slh-portable-pristine-128f.json

python3 tools/check_slh_portable.py \
  --rtl-dir agent/slh_dsa/slh_src \
  --output .pqc_runs/slh-portable-candidate-192f.json
```

To reproduce the separately labeled corrected SHA2-128f variant:

```sh
python3 tools/check_slh_portable.py \
  --rtl-dir agent/slh_dsa/pristine --fix-auth-sensitivity \
  --output .pqc_runs/slh-portable-fixed-128f.json

python3 tools/check_slh_portable.py \
  --rtl-dir agent/slh_dsa/slh_src --fix-auth-sensitivity \
  --output .pqc_runs/slh-portable-fixed-192f.json
```

A relocated installation can use `--iverilog`, `--vvp`, and `--ivl-base`.
The runner installs nothing and uses no network or paid services. Default
wall timeout is 3,600 seconds for compilation and each simulation. Two
isolated simulations run concurrently; `--jobs 1` runs them sequentially.
`PQC_RUN_DIR` chooses the run-directory parent. Missing tools exit 2 with
`UNAVAILABLE`; setup/timeouts exit 2; compilation, comparison or verification
failures exit nonzero; only completed baseline **and** negative-control
success exits 0. A negative control can only qualify after the unchanged
signature passes its positive baseline. Unknown/empty/partial/stale dumps
cannot pass.

Unit tests (mocked evidence contracts, not RTL passes):

```sh
python3 -m unittest discover -s tests -p 'test_slh*.py' -v
python3 -O -m unittest discover -s tests -p 'test_slh*.py' -v
```

## Results

The syntax-only SHA2-128f run has completed and **failed**. The separate
sensitivity-corrected SHA2-128f variant has completed and **passed** its
baseline and live corruption control. Syntax-only selected SHA2-192f has
failed verification despite its exact signing output; the separate corrected
SHA2-192f full run has **passed** its baseline and live corruption control.
Compilation or partial output is not counted as a completed RTL pass.

- [Syntax-only 128f record](../../docs/verification/slh-portable-syntax-128f-2026-10-12.json)
  and [complete simulation logs](../../docs/verification/slh-portable-syntax-128f-2026-10-12.txt):
  compiler and simulator exit 0, but the RTL verifier reports mismatch
  (`c_flag=1`). Output contains 2,133 words instead of 2,141. Four pairs of
  expected words are absent at zero-based golden offsets 174, 188, 216 and
  342. All remaining words match in order. First expected word is
  `1642eead17ca6ca7`; actual word 174 is `7cacc063f4449d96`.
  The negative run cannot qualify a baseline whose generated signature is
  already invalid. The overall runner exits 1, as required.
- [Sensitivity-corrected 128f record](../../docs/verification/slh-portable-corrected-128f-2026-10-12.json)
  and [complete simulation logs](../../docs/verification/slh-portable-corrected-128f-2026-10-12.txt):
  **PASS** with `auth_sensitivity_fix: true`. Baseline and negative-control
  runs each generate all 2,141 words, SHA-256
  `10f35fcc0cc98680d87cf7aaef1479ba359303a84ba2553d69a8b77771bdf2a8`.
  Baseline verifies with `c_flag=0`; after a real one-bit signature-memory
  corruption, the RTL verifier rejects with `c_flag=1`. Both simulations
  exit 0, and the overall qualification runner exits 0. The complete
  unchanged golden, including the padded message, is compared byte for byte.
- [Syntax-only 192f record](../../docs/verification/slh-portable-syntax-192f-2026-10-12.json)
  and [complete simulation logs](../../docs/verification/slh-portable-syntax-192f-2026-10-12.txt):
  **FAIL**. Both runs generate all 4,463 words exactly, SHA-256
  `22bfbe1c1130b0faf039268adf00504a0ffec308f8ac7a8692593c757371dfe3`,
  but the untampered signature is rejected with `c_flag=1`. Matching signing
  output alone is insufficient. The corrupted signature is also rejected,
  but this does not establish discrimination; it is explicitly
  `UNQUALIFIED` / `negative_control_qualified: false` because the positive
  baseline failed. The overall runner exits 1. The separately corrected run
  below is qualified independently.
- [Sensitivity-corrected 192f record](../../docs/verification/slh-portable-corrected-192f-2026-10-12.json)
  and [complete simulation logs](../../docs/verification/slh-portable-corrected-192f-2026-10-12.txt):
  **PASS** with `auth_sensitivity_fix: true`. Both runs generate all 4,463
  words matching SHA-256
  `22bfbe1c1130b0faf039268adf00504a0ffec308f8ac7a8692593c757371dfe3`.
  The baseline verifies with `c_flag=0`, and one-bit in-memory signature
  corruption is rejected with `c_flag=1`. Both simulator exits and the
  overall runner exit are 0. The selected candidate's existing optimized
  SHA-256/SHA-512 cores are included in this run.
- [192f verification-only diagnostic](../../docs/verification/slh-portable-verify-only-192f-2026-10-12.json)
  and [diagnostic logs](../../docs/verification/slh-portable-verify-only-192f-2026-10-12.txt):
  the same pinned golden signature supplied directly to the verifier is
  rejected by the syntax-only candidate (`c_flag=1`) and accepted after the
  explicit sensitivity correction (`c_flag=0`). This isolates the 192f
  verification issue. It supplies a signature as input and makes no fresh
  signing claim; the full corrected sign/verify/corruption result above is separate.
- [Capture diagnostic](../../docs/verification/slh-portable-capture-diagnostic-2026-10-12.json):
  sampling both rising and falling edges through FORS completion gives the
  same 456 words, versus 464 expected. The omission is visible at the DUT
  output before capture, rather than a rising-edge output-file sampling
  loss. This supports investigation of the incomplete RTL sensitivity list.
- No reference was edited, truncated, shifted, regenerated or filled to
  accommodate the failing output. The original source and staged binaries
  remained unchanged throughout the qualification run.

Only corrected SHA2-128f and corrected SHA2-192f have completed successful
full runs here. SHA2-128s, 192s, 256f and 256s remain unexecuted by this
portable qualification; SHAKE is unsupported. The measured full corrected
runs took approximately 9.4 minutes for 128f and 18.5 minutes for 192f on
this environment. These wall-clock durations are simulator runtime, not
hardware latency or throughput measurements.

The original [Vivado gate](../../agent/slh_dsa/slh_kat_gate.py) remains
unchanged and still requires Vivado. Portable simulation does not establish
Vivado/DC/Genus synthesis, implementation, timing, area, power or PPA results.

## Source-only FPGA / ASIC handoff

[The source exporter](../../tools/export_slh_verified.py) runs **no EDA tool**,
installs nothing and produces no PPA measurements. It materializes the exact
corrected RTL bytes bound to a completed functional record. It refuses stale
sources, missing or wrong-parameter evidence, failed positive/negative
controls, and nonempty destinations. Both original tracked RTL trees remain
unchanged.

```sh
python3 tools/export_slh_verified.py --variant corrected-baseline \
  --parameter-set 128f --out build/slh-handoff/corrected-baseline-128f
python3 tools/export_slh_verified.py --variant corrected-candidate \
  --parameter-set 128f --out build/slh-handoff/corrected-candidate-128f

python3 tools/export_slh_verified.py --variant corrected-baseline \
  --parameter-set 192f --out build/slh-handoff/corrected-baseline-192f
python3 tools/export_slh_verified.py --variant corrected-candidate \
  --parameter-set 192f --out build/slh-handoff/corrected-candidate-192f
```

Each bundle contains:

- `manifest.json`: design top `top`, simulation top `tb`, parameter-selection
  source/macro, exact original and corrected source hashes, ordered source
  entries, include directories, qualification record/hash, fixture hashes,
  memory semantics and explicit limitations.
- `sources.f`: synthesis/design sources only. `simulation_sources.f` also
  includes the instrumented testbench. Preserve file order and the three
  include directories in `include_dirs.f`; files setting `default_nettype`
  remain last as in the qualified simulation.
- `sources.tcl`: source-only variables (`slh_top`, `slh_include_dirs`,
  `slh_sources`). Sourcing it does not launch an EDA command.
- `rtl/`, `changes.patch`, preserved source notices, repository license and
  notice files, and copied qualification/reference evidence.
- Four public deterministic test fixtures in the vendor-relative simulation
  layout. They are test keys/data, never production secrets. The expected
  golden is kept separately under `evidence/`; no produced-signature file
  is pre-populated in the simulation data directory.
- `SHA256SUMS`, covering the manifest and every exported content file.
  Verify it from the bundle root with `sha256sum -c SHA256SUMS`.

The compile-time parameter is already selected in `rtl/sphincslet/setting.v`.
Do not override only the top-level `parameter_set` parameter: configuration
macros also choose widths and hash cores. The exporter therefore supplies
empty external `defines` and `parameter_overrides` lists and records the
selected source configuration explicitly.

The top exposes an external signature-memory interface. `SIG_MEM` in `tb.v`
is **testbench-only**, and is not in the synthesis source list. Budget and
supply equivalent external signature storage in both arms. Internal RAMs
and FIFOs remain the generic vendor models: no ASIC SRAM macros or FPGA
memory primitive wrappers are supplied. In particular, the unchanged
`mem_dual` array is declared `[0:DEPTH]` (DEPTH+1 entries). Initialization and
inference behavior need target-specific review. No timing/placement or clock
constraints are supplied; the testbench's 10 ns simulated clock is not a
measured operating frequency or proposed implementation constraint.

### Matched functional source pairs

The earlier pristine-derived **128f** and candidate-derived **192f** passes
are different parameter sets, **not a matched baseline/candidate PPA pair**.
For a comparison, export baseline and candidate at the **same** parameter,
with the same correction, wrapper, clocks, constraints, memory mapping and
implementation settings.

The exporter verifies that same-parameter corrected trees differ only in
`sha256_core.v` and `sha512_core.v`, the candidate carry-save-adder changes.
It reports a separate `source_relationship.partner_qualified` flag after
validating the other arm's same-parameter completed functional record. A
qualified individual bundle with a missing partner is not a qualified pair.

The additional [corrected candidate128f run](../../docs/verification/slh-portable-corrected-candidate-128f-2026-10-12.json)
([complete logs](../../docs/verification/slh-portable-corrected-candidate-128f-2026-10-12.txt))
has passed the same 2,141-word positive fixture and live corruption rejection.
Together with the earlier corrected baseline128f record, this establishes a
same-parameter **128f functional source pair**. Both exported 128f manifests
report `partner_qualified: true`, with only the two SHA-core files differing.
This establishes functional evidence for the pair, not a PPA result.

The additional [corrected baseline192f run](../../docs/verification/slh-portable-corrected-baseline-192f-2026-10-12.json)
([complete logs](../../docs/verification/slh-portable-corrected-baseline-192f-2026-10-12.txt))
also passed, including all 4,463 golden words and the positive/negative
verification controls. Together with the earlier corrected candidate192f
record, the **192f functional source pair** is now qualified too.

The [source-handoff audit](../../docs/verification/slh-source-handoff-2026-10-12.json)
records all four exported manifests, exact source hashes and qualification
record hashes. Every bundle passed its complete checksum verification and
byte-identical repeat export. Within each pair, top, parameter configuration
and design-source ordering match; only `sha256_core.v` and `sha512_core.v`
differ. All four manifests report `partner_qualified: true`.

Explicit `--parameter-set` selection alters only disposable staged copies
and is recorded in source hashes and patches. Reproduce the additional
checks with:

```sh
python3 tools/check_slh_portable.py --rtl-dir agent/slh_dsa/slh_src \
  --parameter-set 128f --fix-auth-sensitivity \
  --output .pqc_runs/slh-portable-candidate-128f.json
python3 tools/check_slh_portable.py --rtl-dir agent/slh_dsa/pristine \
  --parameter-set 192f --fix-auth-sensitivity \
  --output .pqc_runs/slh-portable-pristine-192f.json
```

These functional checks still provide historical vendor-differential
coverage for one fixed message per parameter, not independent FIPS 205
validation, formal equivalence or FPGA/ASIC implementation results.
