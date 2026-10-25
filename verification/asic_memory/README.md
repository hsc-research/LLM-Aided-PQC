# Bounded ASIC memory-component checks

These checks provide an actual constant-ROM derivative and evidence that selected
existing generic memory RTL maps to flip-flops. They do **not** qualify an entire
ML-KEM, ML-DSA, or SLH-DSA ASIC baseline, perform standard-cell mapping, or claim
area, timing, power, or certification. No HQC RTL is executed or modified.

## Run

```sh
python tools/check_asic_memory_components.py \
  --tool-dir /workspace/shared/spectral-memory-reduction/tools/bin \
  --work-dir .pqc_runs/asic-memory-components \
  --report docs/verification/asic-memory-components-2026-10-12.json
python -m unittest discover -s tests -p test_asic_memory_components.py -v
```

Omit `--tool-dir` to use installed `iverilog`, `vvp`, and `yosys` from PATH. No
software is downloaded. The runner writes logs/netlists only under its work
folder and hashes every design/test input before and after execution. It rejects
stale ROM constants, unsupported file configurations, residual memories/latches,
power-up initialization attributes, and unexpected FF counts. The report binds
exact source bytes, tool versions, parameters, and focused results.

### Actual RTL derivative

`asic/rtl/mldsa_zetas/dual_port_rom.v` is an optional replacement for the qualified
ML-DSA `dual_port_rom.v`. It retains the upstream license/attribution and module
interface. All 256 24-bit zeta words are expressed as combinational constants;
only the enabled read outputs are registers. `INIT_FILE=""` still means an
all-zero ROM. Nonempty configurations other than exactly `WIDTH=24`,
`LENGTH=256`, `INIT_FILE="zetas.txt"` fail elaboration instead of silently reading
the wrong data. The default ROM and every selected zeta address are compared
against the original RTL, including disabled reads, out-of-range zero-ROM reads,
and unknown addresses.

Do not compile this file together with the original module. It is not selected
by the default qualified export. Substitution changes the source identity and
requires a new target manifest and full functional qualification. Passing the
ROM component test does not transfer the original whole-core KAT result.

### Existing memory behavior preserved

| Component | Read timing and enable | Write/collision behavior | Initialization/reset |
|---|---|---|---|
| Adams Bridge `abr_1r1w_ram`, `abr_1r1w_512x4_ram` | One rising-edge registered read; `re_i=0` holds output | `we_i` writes independently; simultaneous same-address read returns old word | No memory/output initialization or reset |
| Adams Bridge `abr_1r1w_be_ram` | Same registered read/hold | `we_i` and per-lane strobe preserve inactive bytes; same-edge read sees old word | No initialization/reset |
| Adams Bridge `abr_ram_regout` | Enabled registered reads plus continuous full-array output | Highest-numbered enabled write port wins an address collision; reads still see pre-edge word | Existing synchronous `zeroize_i` clears storage, overrides writes; it does not reset the registered read outputs, which may capture pre-clear data |
| ML-DSA original `dual_port_ram` | Each clock/enable separately updates its output; disabled output holds | Read-first on local or simultaneous opposite-port writes; simultaneous same-address dual write has no defined portable priority | `initial` loads file or zeros every word; no reset/boot port |
| ML-DSA original/derived `dual_port_rom` | One rising-edge registered read on both addresses; `en=0` holds | No write ports | Original loads static table; derivative represents table as constants; outputs remain uninitialized until a read |
| SLH `mem_dual` | Both outputs update every rising edge; no read-enable | Write-first on the writing port; other port reads old data; simultaneous same-address dual write is outside the defined portable contract | `INIT=1` zeros all words after any FILE read; no reset port; array has `DEPTH+1` words |
| SLH `mem_single` | One rising-edge registered output; no enable | Read-first, because the final `q <= mem[address]` overrides the earlier write assignment | Optional binary FILE read, then zero-fill if INIT; no reset port |
| SLH FIFO | Asynchronous head-data output | Existing full/empty guards determine accepted operations | Only read/write pointers have `initial` values; memory has none; no reset port |

The ABR scoreboard executes both original non-FPGA and `RV_FPGA_OPTIMIZE`
branches, without rewriting either. It covers 1,200 cycles per branch, byte
masks, read hold, read/write collision, all 512 nibble addresses, register-output
zeroization, and deterministic multiwrite priority. The SLH scoreboard uses a
non-power-of-two DEPTH of 5 to exercise its real extra sixth word; it excludes
undefined dual-write collisions. File initialization and out-of-range behavior
are not silently replaced by zeros.

### Generic FF mapping evidence

Yosys runs `proc; opt; memory_map; opt; techmap; opt; check -assert`, then records
the generic-cell netlist. No FPGA memory primitive or technology library is
used. All selected mappings have no remaining memory cells, latches, or power-up
init attributes:

- ABR `abr_1r1w_ram`: default 64x32 storage + 32-bit output = 2,080 FF bits
- ABR `abr_1r1w_be_ram`: default 64x32 storage + 32-bit output = 2,080 FF bits
- ABR `abr_1r1w_512x4_ram`: 512x4 storage + 4-bit output = 2,052 FF bits
- ABR `abr_ram_regout`: default 64x32 storage + 32-bit output = 2,080 FF bits; storage FFs implement its pre-existing synchronous zeroize
- Derived ML-DSA zetas ROM: 46 output FF bits; the two constant-zero top bits are optimized out
- SLH `mem_dual`, WIDTH=8, DEPTH=7, INIT=0: 8 actual words + two outputs = 80 FF bits
- SLH `mem_single`, WIDTH=8, DEPTH=8, INIT=0: 8 words + one output = 72 FF bits

The SLH synthesis examples use fully populated address spaces. A separate
non-power-of-two trial produced Yosys undriven-read warnings for out-of-range
addresses, which were not hidden by assigning replacement values. Non-power-of-two
semantics are exercised by simulation instead. Neither example qualifies every
production dimension or SLH's power-up initialized hash-tile memories.

## Remaining whole-design ASIC blockers

ML-KEM's original non-FPGA memory branches already support generic FF mapping;
a source rewrite is not required merely to remove FPGA RAM inference. These
component checks are still not full-design ASIC elaboration or PPA.

ML-DSA instantiates seven `dual_port_ram` blocks, all with both ports connected to
the same clock: one 4096x96 and six 1024x96. Their unconditional power-up zeros
must be implemented explicitly or proven unnecessary. A faithful approach is a
boot-only serial scrub (up to 4,096 cycles in parallel across the banks), a
boot-ready handshake, and a core held inactive until ready. Ordinary operation
reset must not accidentally become a new full-memory clear. Numerous additional
control/pipeline register initializers require their own reset/validity audit.
The constant-ROM replacement resolves only static zeta representation.

SLH's hash-tile small/big memories inherit `INIT=1`; top-level memories explicitly
use `INIT=0`. FIFO pointers also depend on power-up initialization. A complete
port must distinguish boot initialization from normal operation reset, propagate
readiness through `hash_tile`, `two_hash_tile`, and `top`, initialize only the
required state, and rerun the same corrected functional cases at each parameter
set. Any runtime data or key initialization requires an actual load interface,
not a hardwired simulation file. No unintegrated startup wrapper is selected by
this change.
