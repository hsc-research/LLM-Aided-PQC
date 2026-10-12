# FPGA and ASIC measurement handoff

[Project home](../README.md) · [Run guide](REPRODUCE.md) · [Verification record](VERIFICATION.md) · [Results](RESULTS.md)

Functional verification and source preparation are recorded here; the next
stage is to run the FPGA/ASIC tools on the chosen machine. **No new commercial
synthesis, place-and-route or PPA result is supplied by this handoff.** Keep
baseline and candidate source versions separate and use identical constraints.

## Choose the actual design being measured

| Design | Source/verification boundary | What must not be assumed |
|---|---|---|
| ML-KEM-1024 | Pinned Adam's Bridge whole-core wrapper, including memories; 80 ML-KEM API samples passed | It is a shared ML-KEM/ML-DSA accelerator, not ML-KEM-only area; ML-DSA-87 behavior remains unqualified |
| ML-DSA-44/65/87 | Guarded baseline and guarded, encoder-corrected candidate; 210 cases passed for each explicit derivative | Original baseline/candidate failures were not repaired in place; legacy source/config selections do not automatically use the passing derivatives |
| SLH-DSA | Explicit sensitivity-corrected baseline/candidate pairs at SHA2-128f and SHA2-192f, with frozen vendor-stream evidence | Match the same SHA2 parameter set across both arms; these functional source pairs do not provide new PPA measurements |
| HQC SAC 2026 | Pinned source-only import | **Blocked/unverified for this handoff:** no executable qualification or verified implementation configuration. Older SAC 2023 tests/PPA do not qualify it |

## ML-DSA: export the passing derivatives

From the repository root, use the [no-EDA exporter](../tools/export_mldsa_verified.py):

```bash
python3 tools/export_mldsa_verified.py --variant guarded-baseline \
  --out build/mldsa-handoff/guarded-baseline

python3 tools/export_mldsa_verified.py --variant corrected-candidate \
  --out build/mldsa-handoff/corrected-candidate
```

Each output directory must be empty or absent. The exporter verifies the pinned
upstream snapshot, applies the declared source selection/corrections, and
compares source hashes with that variant's complete passing report. It does
not download tools or launch simulation/synthesis.

The default output contains **35 ordered Verilog files**, including the exact
GHDL-generated Keccak netlist bytes used by the passing simulation. Both arms
include the canonical-hint guard. The candidate also includes the encoder
fallthrough repair and its other recorded candidate overrides.

| Exported item | How to use it |
|---|---|
| `manifest.json` | Read the variant, source hashes/order, top, runtime controls, data and linked qualification record |
| `sources.f` | Compile exactly this ordered source list; paths are relative to the export root |
| `sources.tcl` | Source-list data only: `mldsa_sources`, `mldsa_top`, `mldsa_zetas`; loading it does not launch EDA |
| `zetas.txt` | Required ROM data; run the tool from the export root or stage this exact file into its working directory |
| `rtl/combined_top.v` | Top module `combined_top`; do not substitute the unstaged original |
| `LICENSES/`, `NOTICE`, `UPSTREAM_NOTICE` | Retained source/component notices |

Runtime `mode` is 0 = KeyGen, 1 = Verify, 2 = Sign; `sec_lvl` is
2 = ML-DSA-44, 3 = ML-DSA-65, 5 = ML-DSA-87. The export declares no extra
preprocessor defines or top-parameter overrides. Record whether the measured
core retains runtime selection or deliberately specializes any inputs; a
specialized boundary is a different result and needs its own checks.

`--format mixed` instead exports 50 ordered files: original VHDL sources plus
corrected Verilog. This is provided for a later native mixed-language flow;
**direct mixed-language equivalence was not established by the passing
GHDL-netlist simulation**. Never compile both the original VHDL `keccak_top`
and generated Verilog `keccak_top` together. Use the default exact-byte export
when tying a first measurement to the recorded portable result.

### Connect an export to the hardware tools

For Vivado, create a separate site project using that export's complete source
list, top and ROM data. Supply the exact FPGA part and reviewed XDC. The legacy
`python3 -m agent.run --target fpga --design mldsa` path still selects its
historical source tree and KeyGen-only gate; it is not a launcher for these
new exports.

For Genus/DC, copy the [existing configuration example](../configs/mldsa_osh_asic.example.json)
to two local configurations. That example selects an older ASIC arm, so it
must be changed before measuring the new derivatives:

1. Set `files` to the exact exported `manifest.json` source order. Translate
   the paths relative to the configured `root`; the default export entries
   are all `verilog`. Do not keep the old `asic/arms/mldsa_baseline` list.
2. Select top `combined_top`, full-design scope and the correct exported
   `zetas.txt` through `data_files`. Do not omit the guard, corrected encoder,
   generated Keccak netlist or memory logic.
3. Supply the actual tool/version, approved target/link libraries, corner,
   library time units, reviewed SDC/site Tcl and memory implementation.
4. Keep all settings identical between the two arms except the declared source
   version/output directory. Run from a fresh output workspace.

For example, after creating and reviewing those local configurations:

```bash
python3 -m agent.run --target asic --synth-tool genus \
  --config configs/mldsa_guarded_baseline.local.json --dry-run
python3 -m agent.run --target asic --synth-tool genus \
  --config configs/mldsa_corrected_candidate.local.json --dry-run
```

Use `dc` to select Design Compiler. The local configs are site inputs to be
created; the commands do not generate them. Remove `--dry-run` only when
ready to launch the selected licensed tool. Dry-run still requires readable
real source/library files and does not establish elaboration or mapped PPA.
See the [ASIC guide](../asic/README.md) for fields, units and report checks.

## ML-KEM: preserve the unified-core boundary

Use the [Adam's Bridge launch guide](../third_party/adams_bridge/README.md#launch-preparation)
and `third_party/adams_bridge/integration/vivado_synth.tcl` for baseline OOC
synthesis. It requires an explicit FPGA part, target period and fresh output
directory. The [ASIC example](../configs/mlkem_adams_bridge_asic.example.json)
selects the complete wrapper and generic memories, with user-supplied libraries
and constraints.

Record area as the **unified ML-KEM-1024 / ML-DSA-87 engine including memories**.
Do not synthesize only `abr_top` and exclude its memory wrapper. Shared-block
edits need separate ML-DSA behavior checks in addition to the ML-KEM samples.

## SLH-DSA: keep mode and derivative together

The passing portable results concern explicitly staged sensitivity corrections;
tracked pristine/candidate RTL remains unchanged. Select the corrected source
version and preserve its `setting.v` SHA2 mode and corresponding pinned inputs.
The [portable guide](../verification/slh_portable/README.md) lists the exact
transformations and completed parameter/source combinations.

Both arms have completed the positive and live corruption tests at each mode:

| SHA2 mode | Corrected baseline | Corrected candidate | Complete frozen words per run |
|---|---|---|---|
| 128f | [PASS](verification/slh-portable-corrected-128f-2026-10-12.json) | [PASS](verification/slh-portable-corrected-candidate-128f-2026-10-12.json) | 2,141 |
| 192f | [PASS](verification/slh-portable-corrected-baseline-192f-2026-10-12.json) | [PASS](verification/slh-portable-corrected-192f-2026-10-12.json) | 4,463 |

Use the [no-EDA exporter](../tools/export_slh_verified.py) for the chosen mode:

```bash
python3 tools/export_slh_verified.py --variant corrected-baseline \
  --parameter-set 128f --out build/slh-handoff/corrected-baseline-128f
python3 tools/export_slh_verified.py --variant corrected-candidate \
  --parameter-set 128f --out build/slh-handoff/corrected-candidate-128f

python3 tools/export_slh_verified.py --variant corrected-baseline \
  --parameter-set 192f --out build/slh-handoff/corrected-baseline-192f
python3 tools/export_slh_verified.py --variant corrected-candidate \
  --parameter-set 192f --out build/slh-handoff/corrected-candidate-192f
```

Each destination must be empty or absent. The exporter requires complete
passing positive/negative evidence for the exact selected sources and mode;
it refuses missing or stale records. Read `source_relationship.partner_qualified`
in `manifest.json` before treating two exports as a functional source pair.
The [four-bundle audit](verification/slh-source-handoff-2026-10-12.json) records
deterministic repeated exports, complete checksum verification and the
same-mode source relationship.
A SHA2-128f baseline and SHA2-192f candidate are **not** a matched pair.
Supporting a mode in a runner does not qualify it. Frozen vendor-output
evidence is not independent FIPS 205 validation; SHAKE remains unsupported.

Each bundle contains 29 design source files. Use top `top`, the ordered
design-only `sources.f` and all three directories
in `include_dirs.f`; `sources.tcl` supplies the same source-list data without
launching a tool. `simulation_sources.f` adds the instrumented testbench and
must not be used as the synthesis source list. Validate the complete bundle
from its root with `sha256sum -c SHA256SUMS`.

The selected `rtl/sphincslet/setting.v` controls widths and hash-core selection.
Do not change only the top-level `parameter_set` parameter or combine files
from different modes. The bundle records no external defines or parameter
overrides. Both corrected arms have the same control correction; the same-mode
candidate differs in its two SHA carry-save-adder cores.

No qualified generic SLH ASIC configuration is supplied. Review global
`setting.v`/`clog2.v` handling, source order, memory inference and the external
signature-memory boundary. The top exposes signature-memory ports; `SIG_MEM`
inside `tb.v` is testbench-only and excluded from the design list. Supply and
account for equivalent signature storage in both arms. Generic RAM/FIFO models
are retained without technology macros; the vendor `mem_dual` declaration
`[0:DEPTH]` has DEPTH+1 entries. Review inference and initialization on the
target tool. No implementation clock is prescribed: the testbench's 10 ns
clock is stimulus, not a measured frequency or a synthesis constraint.

## HQC: keep the unresolved boundary visible

The [SAC 2026 snapshot](../third_party/hqc_sac2026/README.md) is imported and
byte-checked only. It has no qualified functional gate or hardware adapter.
Do not route the older `hqc` commands to it, borrow their expected outputs,
or interpret source completeness as verification.

The [read-only rejection review](verification/hqc-readonly-review-2026-10-12.json)
concerns only an older tracked SAC 2023-derived joint-design file. Its static
finding and inconclusive dynamic probes do not establish a repaired baseline
or a result for SAC 2026. New HQC execution/repair is not part of this handoff.

## Record a fair comparison

Before launching either arm, record and match:

- Algorithm, parameter set, operations, top module and complete source hashes
- FPGA part/speed grade or ASIC library/corner and exact tool version
- Clock period, IO delay/load/transition, clock uncertainty and timing exceptions
- Runtime/static mode settings, memories, macros, initialization and excluded logic
- Synthesis/implementation effort, placement/routing settings and analysis stage
- Functional coverage and per-operation cycle counts, including backpressure assumptions

Inspect elaboration, unresolved/empty modules, inferred memories, warnings,
unconstrained paths and actual clock units before trusting a timing/area
number. ASIC pre-layout synthesis is not physical design or signoff. Block
area/timing does not establish a full-design result. Power needs explicit
activity, voltage, frequency, corner and workload assumptions.

Keep each run's command, source/config hashes, tool version, exit status,
original reports and functional evidence in a fresh directory. Use
[results rules](RESULTS.md#fair-comparisons) and the
[documentation standard](DOCUMENTATION_STANDARD.md) when reporting the pair.
