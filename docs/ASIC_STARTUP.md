# Explicit ASIC startup source derivatives

[Project home](../README.md) · [Hardware handoff](HARDWARE_HANDOFF.md) · [ASIC admission](ASIC_ADMISSION.md)

The ASIC startup variants are separately tested derivatives of the corrected
ML-DSA and SLH source arms. They replace power-up initialization assumptions
with explicit boot control and synthesizable constants. Original FPGA exports
remain available under their original names.

**These are source-level functional results, not DC/Genus qualification, a
standard-cell implementation, mapped-netlist equivalence, PPA or certification.**
A successful export does not admit either arm into target-bound optimization.
The exact licensed implementation still needs its own startup, memory and
structural evidence, reviewed constraints and qualified site adapters.

## Where each source arm lives

| Design | FPGA original / qualified portable source | ASIC startup baseline | ASIC startup candidate |
|---|---|---|---|
| ML-KEM | [Pinned unified core](../third_party/adams_bridge/README.md); target variant `baseline` | Existing generic-memory unified core via `baseline`; no new startup derivative is substituted | No separately qualified candidate |
| ML-DSA | Pinned inputs in `third_party/mldsa_osh/upstream`; [portable exporter](../tools/export_mldsa_verified.py) selects the guarded/corrected variants | `asic/rtl/mldsa_startup/guarded-baseline`, selected as `asic-startup-baseline` | `asic/rtl/mldsa_startup/corrected-candidate`, selected as `asic-startup-candidate` |
| SLH | `agent/slh_dsa/pristine` and `agent/slh_dsa/slh_src`; [portable exporter](../tools/export_slh_verified.py) applies the recorded corrections and exact mode | [ASIC exporter](../tools/export_slh_asic_verified.py) generates the exact same-mode baseline, selected as `asic-startup-baseline` | The same exporter generates the candidate, selected as `asic-startup-candidate` |
| HQC SAC 2026 | [Source-only import](../third_party/hqc_sac2026/README.md); no qualified export | Blocked/unqualified | Blocked/unqualified |

SLH uses shared templates in `asic/rtl/slh_startup` plus the checked startup,
control and width transforms. The templates alone are not a full design.
Each complete selected-mode design is generated into its own exported
`source-bundle/rtl`; never edit the preserved FPGA trees to select the ASIC arm.
ML-DSA's complete frozen startup trees are already separated by source arm.

`asic/arms/` and `configs/mldsa_osh_asic.example.json` preserve historical source
selections and experiments. They do not default to these new startup sources.
Use the target exporter and its generated launch configuration for new runs.
No historical directories are moved or replaced.

## Select a source arm explicitly

Only `--target asic` accepts `asic-startup-baseline` and
`asic-startup-candidate`. The names are common across both designs; their
predecessors are ML-DSA `guarded-baseline` / `corrected-candidate` and SLH
`corrected-baseline` / `corrected-candidate`.

```bash
# Existing unified ML-KEM baseline; its target qualification remains pending.
python3 tools/export_target_profiles.py --design mlkem --variant baseline \
  --target asic --out build/profiles/mlkem-unified-asic

# Explicit new ML-DSA startup pair.
python3 tools/export_target_profiles.py --design mldsa \
  --variant asic-startup-baseline --target asic --out build/profiles/mldsa-boot-base
python3 tools/export_target_profiles.py --design mldsa \
  --variant asic-startup-candidate --target asic --out build/profiles/mldsa-boot-candidate

python3 tools/export_target_profiles.py --design slh --parameter-set 128f \
  --variant asic-startup-baseline --target asic --out build/profiles/slh-128f-boot-base
python3 tools/export_target_profiles.py --design slh --parameter-set 128f \
  --variant asic-startup-candidate --target asic --out build/profiles/slh-128f-boot-candidate
```

For FPGA, keep the original qualified selections: ML-KEM `baseline`, ML-DSA
`guarded-baseline` / `corrected-candidate`, and SLH `corrected-baseline` /
`corrected-candidate` with an exact mode. For example:

```bash
python3 tools/export_target_profiles.py --design mldsa --variant guarded-baseline \
  --target fpga --out build/profiles/mldsa-guarded-fpga
```

Repeat the SLH pair with `--parameter-set 192f` and fresh output directories
for SHA2-192f. Never compare different parameter sets. ML-DSA retains runtime
44/65/87 selection. No extra defines or top-parameter overrides are supplied.
Use Verilog-2005, the exported file order and the exported include directories.
SLH's `setting.v` controls mode-dependent widths and SHA cores; overriding only
`parameter_set` is unsupported.

Verify `profile.json` with the copied `verify_profile.py`. Then use the
[local launch preparation procedure](HARDWARE_HANDOFF.md#prepare-a-local-launch-configuration).
The profile binds the exact derivative sources and fresh functional evidence,
including startup contracts, constants and memory boundaries. Target preparation
makes no further RTL edits. Legacy reports describe the predecessor only and
cannot qualify changed startup sources.

## Boot and ordinary operation reset are different

| Design | Selected top | Boot input | Ready output | Scrub clocks after boot deassertion |
|---|---|---|---|---|
| ML-DSA | `combined_top_asic` | `boot_rst`, synchronous active high | `boot_ready` | 4096 |
| SLH SHA2-128f | `top` | `i_boot_reset`, synchronous active high | `o_boot_ready` | 81 |
| SLH SHA2-192f | `top` | `i_boot_reset`, synchronous active high | `o_boot_ready` | 172 |

Assert boot across at least one rising clock edge after power-up. Deassert it,
wait for ready, and then use the original operation reset/start/input protocol.
Do not load inputs or issue starts before ready. ML-DSA's tested boot-abort
sequences discard in-flight work and stored context; restart the host transaction
and reload required inputs after boot completes. SLH qualifies repeated boot
while inactive only. Its active-operation boot abort/recovery remains unqualified.

ML-DSA's ordinary active-high `rst` and SLH's ordinary active-low `rstn` do not
repeat the boot scrub. Neither is a general erase operation. Finite reset and
reboot tests do not prove arbitrary asynchronous input changes or every possible
abort/restart sequence. Follow the contract in the selected profile.

Boot is a functional initialization protocol. Secure zeroization or secret
erasure has not been qualified. ML-DSA initializes its selected RAM banks and
startup control; SLH clears only INIT=1 banks and FIFO pointers, preserves
INIT=0/data storage, and requires runtime inputs to be reloaded as specified.

## Storage and constant boundaries

ML-DSA has one 4096×96 bank and six 1024×96 banks. Boot scrubs them in parallel;
the largest bank determines ready latency. The same-clock FF-targeted RAM
retains the selected post-boot read/write behavior. Concurrent writes to the
same address remain outside the qualified contract. Zetas and generated
Keccak constant tables are logic inputs rather than runtime file loads. Do not
also compile the original VHDL Keccak modules.

SLH preserves the vendor `mem_dual` array's inclusive `[0:DEPTH]` declaration.
INIT=1 hash memories scrub all DEPTH+1 words. INIT=0 memories and FIFO data
arrays are not zeroed; valid operation must overwrite them before use. Boot
resets FIFO pointers; ordinary `rstn` does not. Registered read/write behavior,
read-first single-port behavior and undefined simultaneous same-address dual
writes retain their documented boundaries. A clocked-history/bypass control
rewrite is checked under the original synchronous, settled-cycle contract;
arbitrary asynchronous equivalence is not claimed.

The external SLH signature store remains outside the selected design top.
Supply and account for the same store in both arms. Testbench `SIG_MEM` and
public deterministic input fixtures are not production memory contents.
There is no memory compiler or SRAM/ROM macro substitution. Generic FF/logic
lowering evidence cannot establish actual standard-cell mapping or timing.
The recorded SLH Yosys recipe uses `read_verilog -defer`, then `hierarchy`,
`proc`, `opt`, `memory -nomap`, `memory_map`, `opt`, `techmap`, `opt` and
`check -assert`. Normal memory optimization before FF lowering coalesces static
read views. The complete recipe is preserved in `generic_ff_lowering`; this is
a generic structural check, not a DC/Genus implementation recipe.

## Recorded source-level evidence

| Source selection | Fresh functional records | Scope |
|---|---|---|
| ML-DSA startup baseline and candidate | [Aggregate and source bindings](verification/mldsa-asic-startup-2026-10-12/result.json), [detailed source/test guide](../asic/rtl/mldsa_startup/README.md) | Full finite KeyGen/Sign/Verify suite, negative controls and tested in-operation boot-abort recovery; two-state full-core simulation plus separate four-state components |
| SLH startup SHA2-128f | [Baseline](verification/slh-asic-boot-baseline-128f-2026-10-12.json), [candidate](verification/slh-asic-boot-candidate-128f-2026-10-12.json) | Historical full-signature stream, positive verify and live corruption rejection; idle boot/reboot scope |
| SLH startup SHA2-192f | [Baseline](verification/slh-asic-boot-baseline-192f-2026-10-12.json), [candidate](verification/slh-asic-boot-candidate-192f-2026-10-12.json) | Same limited vendor-differential and boot scope at the selected mode |

Export rejects missing, stale or mismatched derivative evidence. Each profile
also binds a separate generic FF structural record. Raw logs, exact source
hashes and scope limitations travel with the export; they are not substituted
for licensed implementation reports.

## Compare only matched implementations

Use identical boot logic, storage treatment, top boundary, source parameters,
clocks, constraints, libraries and tool settings for a same-mode pair. Startup
latency is an integration cost, separate from per-operation cycle counts. Record
both; do not silently subtract startup overhead or compare a boot-enabled arm
against an initialization-dependent predecessor.

ML-DSA's fresh finite tests cover KeyGen, Sign and Verify with recorded negative
controls. SLH's fresh sign/verify streams and live corruption controls remain
historical vendor differentials, not independent complete FIPS 205 validation.
Neither original whole-core evidence nor component-only checks are inherited as
proof for a changed derivative. `whole_algorithm_qualified`,
`target_tool_qualified` and `technology_mapping_verified` remain false in these
new target profiles.

The [target-bound optimizer](WHOLE_DESIGN.md#bind-a-target-profile-before-optimizing)
still requires a qualified full-selected-design verifier, exact implementation
netlist, mapped startup/memory-semantics report and licensed structural/memory
admission. No licensed tool, paid API, HQC execution or HQC repair is part of
this startup handoff.

## File map

| Path | Contents |
|---|---|
| [Target exporter](../tools/export_target_profiles.py) | Explicit source selection, exact hashes, boot boundary and offline preparation |
| [Target exporter tests](../tests/test_target_source_export.py) | Existing profile preservation and new derivative integrity/fail-closed tests |
| `asic/rtl/mldsa_startup/` | Frozen ML-DSA baseline and candidate startup source trees |
| `tools/export_slh_asic_verified.py` | Separate SLH startup exporter and fresh-report validation |
| `docs/verification/` | Source-bound startup functional and structural records |
| [ASIC site admission](ASIC_ADMISSION.md) | Remaining licensed mapping and implementation requirements |
