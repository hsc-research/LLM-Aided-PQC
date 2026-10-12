# FPGA and ASIC measurement handoff

[Project home](../README.md) · [Run guide](REPRODUCE.md) · [Verification record](VERIFICATION.md) · [Results](RESULTS.md)

Functional verification and source preparation are recorded here; the next
stage is to run the FPGA/ASIC tools on the chosen machine. **No new commercial
synthesis, place-and-route or PPA result is supplied by this handoff.** Keep
baseline and candidate source versions separate and use identical constraints.

The intended sequence is **qualify one baseline for each target, then optimize
that target separately**. FPGA prefers inferred block RAM where the existing
interface permits it. ASIC selects generic RTL storage intended for standard-cell
FF/logic mapping; no SRAM macro compiler is assumed. These are implementation
policies to check in reports, not proof of the mapped result. Vivado and
DC/Genus qualification runs are performed by the user on their licensed machine.

## Choose the actual design being measured

| Design | Source/verification boundary | What must not be assumed |
|---|---|---|
| ML-KEM-1024 | Pinned Adam's Bridge whole-core wrapper, including memories; 80 ML-KEM API samples passed | It is a shared ML-KEM/ML-DSA accelerator, not ML-KEM-only area; ML-DSA-87 behavior remains unqualified |
| ML-DSA-44/65/87 | Guarded baseline and guarded, encoder-corrected candidate; 210 cases passed for each explicit derivative | Original baseline/candidate failures were not repaired in place; legacy source/config selections do not automatically use the passing derivatives |
| SLH-DSA | Explicit sensitivity-corrected baseline/candidate pairs at SHA2-128f and SHA2-192f, with frozen vendor-stream evidence | Match the same SHA2 parameter set across both arms; these functional source pairs do not provide new PPA measurements |
| HQC SAC 2026 | Pinned source-only import | **Blocked/unverified for this handoff:** no executable qualification or verified implementation configuration. Older SAC 2023 tests/PPA do not qualify it |

## Prepare explicit target profiles without EDA

Use [the target-profile exporter](../tools/export_target_profiles.py) to bind
an exact source bundle to either target. For example, prepare the same guarded
ML-DSA baseline twice:

```bash
python3 tools/export_target_profiles.py --design mldsa \
  --variant guarded-baseline --target fpga --out build/profiles/mldsa-baseline-fpga
python3 tools/export_target_profiles.py --design mldsa \
  --variant guarded-baseline --target asic --out build/profiles/mldsa-baseline-asic
python3 tools/export_target_profiles.py \
  --verify build/profiles/mldsa-baseline-asic/profile.json
```

Every output directory must be absent or empty. Supported selections are:

| `--design` | `--variant` | `--parameter-set` |
|---|---|---|
| `mlkem` | `baseline` | Optional `1024`; unified core boundary retained |
| `mldsa` | `guarded-baseline`, `corrected-candidate` | Optional `44-65-87`; runtime selection retained |
| `slh` | `corrected-baseline`, `corrected-candidate` | Required `128f` or `192f`; both arms must match |

Repeat with `--target fpga` or `--target asic` and a fresh destination for each
selected baseline/candidate. HQC is deliberately unsupported. ML-KEM has no
separately qualified optimized source export yet; create and requalify candidates
through the controlled optimization workflow.

The output contains `profile.json`, the unchanged qualified `source-bundle/`,
source/include lists, `sources.tcl`, a portable `verify_profile.py`, and
`site.<target>.example.json`. The profile records source/evidence hashes,
elaboration settings, memory intent, external boundaries and
`compatibility_blockers`. It does not rewrite RAMs or repair startup behavior.
In particular:

- ML-KEM selects upstream target-specific defines; equivalence of those target
  compile settings is not established by the previous generic-source test.
  Generic clock-gate mapping still needs review. Full-selected-design admission
  requires both ML-KEM and ML-DSA operations of the unified core; the existing
  ML-KEM-only record cannot satisfy that requirement.
- ML-DSA and SLH retain initialization-dependent memories/control state; ASIC
  reset/load/startup equivalence is unresolved. Hash-preserved sources alone
  do not make those designs ASIC-ready.
- SLH retains its external signature-memory boundary and limited sign/verify
  fixture coverage; it is not a complete independently qualified algorithm.

Export reports `SOURCE_EXPORTED_TARGET_UNQUALIFIED`; verification reports
`SOURCE_PROFILE_VERIFIED` while `target_tool_qualified` remains false. Neither
status proves simulation under the target defines, synthesis, BRAM/FF mapping,
or startup equivalence.

### Prepare a local launch configuration

Copy the chosen profile's `site.<target>.example.json` to `site.local.json` and
fill its actual tool/version, period, constraints and fresh output location.
FPGA also requires the exact part/speed grade. ASIC requires approved standard-cell
libraries, units, corner and site Tcl; DC needs genuine `.db` libraries.
Keep the profile fingerprint unchanged. Then, for the ASIC example above:

```bash
python3 tools/export_target_profiles.py --prepare \
  --profile build/profiles/mldsa-baseline-asic/profile.json \
  --site build/profiles/mldsa-baseline-asic/site.local.json \
  --out build/launch/mldsa-baseline-asic
python3 tools/export_target_profiles.py \
  --verify-preparation build/launch/mldsa-baseline-asic/preparation.json
python3 -m agent.run --target asic --synth-tool genus \
  --config build/launch/mldsa-baseline-asic/launch-config.json --dry-run
```

`site.local.json` is a user-created input, not generated by these commands.
Preparation rejects unresolved site values and writes `launch-config.json` and
`preparation.json`; its status is `SOURCE_PREPARED_NOT_RUN`. It never starts EDA.
ASIC preparation may omit an admission adapter, but a real strict run then
refuses to start. Supply and qualify the [site admission adapter](ASIC_ADMISSION.md)
before removing `--dry-run` on the licensed machine. Select `dc` consistently in
the site file and command when using Design Compiler.

For an FPGA profile, the same preparation command writes `launch_vivado.tcl`
and its reviewed launch command in `README.txt`. It prepares OOC synthesis,
not place-and-route or a qualified optimization adapter. Review the actual
clock in the XDC against the declared period and inspect the resulting hierarchy,
memory, timing and DRC reports. Source preparation cannot validate a Tcl/XDC's
meaning or prove hardware compatibility.

Preserve this prepared baseline; use the
[matched-run procedure](#record-a-fair-comparison) before starting the
[target-bound controller](WHOLE_DESIGN.md#bind-a-target-profile-before-optimizing).
Missing full-operation verification, startup fixes, structural/memory evidence
or a qualified adapter remains a blocker, even when the source profile verifies.
The target-bound optimizer requires a separate mapped-memory semantics report
and exact implementation netlist. The built-in ASIC runner's strict FF inventory
does not provide that startup/behavior proof.

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

For Genus/DC, prefer the explicit target-profile preparation above. For a manual
integration, copy the [existing configuration example](../configs/mldsa_osh_asic.example.json)
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

The target exporter supplies source-preparation configurations, not a qualified
SLH ASIC implementation. Review global
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
The prior security restriction remains in force: keep SAC 2026 blocked and
unqualified rather than substituting the legacy source or inventing evidence.

## Record a fair comparison

Use a fresh, separate baseline/candidate workspace for each target. Start both
arms from the same declared functional derivative and parameter set. First
qualify the target-specific baseline with its complete functional gate and
licensed-tool elaboration/mapping reports. Only then enable proposals against
that target's measured baseline. A corrected derivative is an explicit baseline
choice; it is not a claim that the unmodified upstream version passed.

An FPGA candidate and an ASIC candidate may diverge. Recheck a change from one
target on the other target before adopting it there, and retain separate
histories. A portable source export, a Python regression pass, and an open-source
simulation do not establish Vivado, DC or Genus qualification.

Before launching either arm, record and match:

- Algorithm, parameter set, operations, top module and complete source hashes
- FPGA part/speed grade or ASIC library/corner and exact tool version
- Clock period, IO delay/load/transition, clock uncertainty and timing exceptions
- Runtime/static mode settings, memories, macros, initialization and excluded logic
- Synthesis/implementation effort, placement/routing settings and analysis stage
- Functional coverage and per-operation cycle counts, including backpressure assumptions

### Preserve memory behavior

The target policy must not silently change the memory contract:

- Preserve read latency, output registers, clock/read enables, write strobes,
  depth/width, address bounds and reset/zeroization behavior. In particular,
  inserting a read register merely to infer BRAM changes cycle behavior.
- Check same-port read-during-write and cross-port same-address collisions.
  Do not assume one collision mode across all arrays. The retained SLH
  `mem_dual` forwards write data on its writing port; `mem_single` has a later
  unconditional nonblocking read assignment, so its output uses the old array
  value. Two writes to one address require a documented, tested assumption.
- Keep ROM/data-file hashes and working-directory requirements. Simulation
  `initial` blocks and `$readmemh`/`$readmemb` do not establish ASIC power-up
  contents. If startup depends on them, implement and verify the approved
  reset/load/constant-ROM behavior before calling the ASIC design usable.
- Keep the full memory boundary. ML-KEM includes its upstream memory wrapper.
  SLH signature storage is external to the exported design top; use equivalent
  storage and report its inclusion or exclusion identically in both arms.

FPGA BRAM preference does not mean every FIFO/register bank can or should
become BRAM. Inspect RAM primitive counts, warnings and any distributed/FF
fallback. ASIC FF policy does not mean a declaration proves FF mapping: inspect
the mapped cells and reject unmodeled memories/blackboxes. Compare resource
usage only within a matched target configuration.

The [memory-component checks](../verification/asic_memory/README.md) and
[recorded evidence](verification/asic-memory-components-2026-10-12.json) provide
bounded open-source progress: existing Adam's Bridge RAM components map to
generic Yosys FF/logic cells, and a separately tested
[ML-DSA constant zetas ROM](../asic/rtl/mldsa_zetas/README.md) avoids a
file-initialized table. The ROM replacement is optional and is not selected by
the qualified default export. Its component pass cannot inherit the whole-core
KAT. Representative SLH `INIT=0` mappings do not resolve the production
`INIT=1` hash memories or FIFO startup. These checks are not full-design
DC/Genus standard-cell mapping or a completed ASIC baseline port.

Inspect elaboration, unresolved/empty modules, inferred memories, warnings,
unconstrained paths and actual clock units before trusting a timing/area
number. ASIC pre-layout synthesis is not physical design or signoff. Block
area/timing does not establish a full-design result. Power needs explicit
activity, voltage, frequency, corner and workload assumptions.

Keep each run's command, source/config hashes, tool version, exit status,
original reports and functional evidence in a fresh directory. Use
[results rules](RESULTS.md#fair-comparisons) and the
[documentation standard](DOCUMENTATION_STANDARD.md) when reporting the pair.

## File map

| Location | Purpose |
|---|---|
| [Target-profile exporter](../tools/export_target_profiles.py) | Explicit source/target policy binding and no-EDA launch preparation |
| [ML-DSA exporter](../tools/export_mldsa_verified.py), [SLH exporter](../tools/export_slh_verified.py) | Exact-source portable evidence bundles |
| [Adam's Bridge integration](../third_party/adams_bridge/README.md) | Unified-core source boundary and inputs |
| [ASIC guide](../asic/README.md), [FPGA guide](FPGA.md) | Site-specific licensed measurement setup |
| [Whole-design controller](WHOLE_DESIGN.md) | Functional/latency gates, measured candidate admission and rollback |
| [Project status](PROJECT_STATUS.md) | Current scope, retained failures and blocked designs |
