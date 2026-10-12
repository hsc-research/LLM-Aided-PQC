# SLH ASIC startup / control derivative

This is a separately identified derivative of the corrected portable SHA2-128f
and SHA2-192f source pairs. The FPGA source trees under `agent/slh_dsa/pristine`
and `agent/slh_dsa/slh_src` are never edited. No HQC is executed, and no SRAM
compiler, licensed EDA, technology library, remote CI or PPA measurement is used.

## Explicit implementation contract

The top keeps its original interface and adds `i_boot_reset` and `o_boot_ready`.
`i_boot_reset` is active-high synchronous: assert it across at least one rising
clock edge after power-up, deassert it, then wait for `o_boot_ready` before
loading seeds/data or issuing start. There is no implicit FPGA power-up state.

All hash-tile memories previously inherited `INIT=1`. They are scrubbed in
parallel, one word per rising edge per memory, with their actual inclusive
`mem[0:DEPTH]` declaration preserved. Ready asserts after 81 clocks in 128f and
172 in 192f. A repeated boot reset during scrub restarts the complete sweep.
Normal active-low `rstn` holds the same control reset semantics as before and
does not repeat scrub or reset FIFO pointers. Startup pointer reset is separate
from ordinary operation reset. Signature-valid, completion, start acceptance,
seed loading and top-memory writes are blocked until ready.

Data outputs are not valid merely because boot has completed: their original
registered-read/streaming protocol still applies. Host keys, optrand, public key
and message enter via the existing byte seed and H_MSG memory load interfaces.
No production data file or secret is compiled into RTL. Nonempty memory FILE
parameters fail elaboration, rather than silently substituting zeros.

The focused tests cover cold boot, interrupted scrub, inactive reboot, and
ordinary reset preserving memory and FIFO state. Active-operation abort and
successful restart/reload are **not** qualified by those tests.

## State and overwrite-before-use audit

- SMALL_MEM/BIG_MEM: startup zeros are explicitly preserved for every declared
  word, including the vendor extra word. No overwrite-before-use assumption is
  used to remove them. There are two banks at 128f and four at 192f.
- H_MSG_MEM and MEM_64BIT_1: each declares 513x64 words with a 9-bit runtime address;
  the final declared word is inaccessible at the interface. `INIT=0` is retained.
  The host loads H_MSG runtime data before start. Working nodes and roots are
  produced by the original controller before their later operations.
- INDICES_MEM: 65 words with a 6-bit runtime address, width 12/14. The last word is
  inaccessible. `message_to_indices` produces indices before their consumption.
- W_MEM: 37/53x4 words. `chain_lengths` writes chain lengths before WOTS uses them.
  Read outputs update even in inactive cycles; those reads are not all consumed.
- FIFO arrays: eight 64-bit words per FIFO, with only pointers initialized at boot.
  Empty/full checks ensure a successful read follows a successful write. Normal
  reset preserves the original FIFO contents/pointers.
- `hash_mem_interface_sha.h_state`, its unused SHAKE counterpart, and
  `hash_tile.m_s_state`: declaration initializers are removed because the
  pre-existing reset branches assign them. Control reset stays asserted through
  boot. Other uninitialized pipeline/data registers remain under their existing
  load/valid protocols; this is not an all-state zeroization claim.

This audit and finite functional tests are not a formal overwrite-before-use
proof for every possible message, reset interruption or hostile input sequence.

## Separate control and width transformations

`tools/slh_asic_control.py` is distinct from startup initialization:

1. `hash_tile` assigns output_enable and s_h_ADDR_update defaults for illegal
   FSM states. Reset selects state 0 and every legal transition stays in 0..7;
   all those legal states already assign the outputs. No fault-injection or
   arbitrary illegal-state equivalence is claimed.
2. The SHA2 XMSS signature-read decoder intentionally retains history at cnt 4/5
   while XMSS_start is low. That behavior is implemented by a previous-value FF
   plus a combinational bypass, with history reset to 0. This preserves settled
   clock-cycle behavior because cnt/ch_cnt/XMSS_start/LR_flag2 originate in
   posedge registers. It is not an arbitrary asynchronous-input equivalence
   claim. Tests extract the actual original and transformed decoder blocks and
   run 12,294 comparisons for each CH_len 2 and 4, including hold 0/1 entry/exit,
   all binary input tuples and asynchronous reset of the real input contract.

`tools/slh_asic_widths.py` makes original truncation/constant semantics explicit:
XMSS layer_addr uses bits 7:0, HT_mode uses bit 0, one-bit constant ports use sized
literals, unused zero memory data uses its exact width, and the 128f 15-bit index
producer feeds an explicitly truncated 12-bit consumer. The already driven
one-bit LR_flag2_pre net gains a declaration. No out-of-range value is replaced
with zero. Deferred Yosys elaboration selects the actual parameter hierarchy
before processing default module variants; this avoids mixing a default 128s
parameter with the 128f global configuration macro.

## Memory timing, invalid addresses and synthesis

After ready, the two original independent mem_dual clocked write processes are
retained: local writes are write-first, an opposite-port read sees old data, and
same-address simultaneous dual writes remain outside the portable contract.
`mem_single` preserves the vendor read-first result. No clock is gated or added.

Non-power-of-two memories expose representable addresses beyond DEPTH. The
read-only view explicitly wires real words and marks nonexistent words X.
It adds no storage or boot work and never initializes uninitialized valid words.
Simulation X represents the same undefined input domain; synthesis treats it as
a don't-care, not a physical X generator. The component scoreboard compares
valid final words, invalid tails, X addresses and defined collisions to the
original RTL. Production dimension mapping checks exact FF counts.

The first raw indexed-memory FF mapping failed strict checks with 6232/10840
undriven Yosys read-mux leaves. That failure is preserved in the prior-map
record. The read view addresses those holes without global setundef or zero
filling. A direct unoptimized mapping of the full read view also exhausted the Wasm
tool runtime while building temporary muxes. The ordinary semantics-preserving
`memory -nomap` optimization before `memory_map` resolves that expansion. Exact
source-bound mapping scripts and the failed attempt remain recorded. Structural
results are separate from functional PASS claims.

## Consumed-read diagnostics

The instrumented testbench has no synthesis role. It tracks the previous-cycle
address corresponding to each registered RAM output, rejects invalid writes,
unknown consumption controls and undefined simultaneous dual writes, and checks:

- Hash shifter consumption only in memory mode and when its ternary data path
  actually includes RAM data, preserving partial-mask priority
- The hash-tile address-update consumers condition_s and condition_b
- W_MEM port 0 conservatively throughout active mode 0 WOTS
- W_MEM port 1 only under its actual clocked flag2 decoder enable:
  i_wots_chain_flag and either opcode 1 with chain_cnt!=CC, or opcode 4/6

The initial deliberately broad port 1 monitor fired at 128f t3158930000:
address1=37, cnt 17, state 3, opcode 0, chain_cnt 37, CC 35, flags 1/2=0. The decoder
cannot read in_w_cnt2 in opcode 0. That captured failure and corrected guard
rationale are retained; no DUT behavior was changed to accommodate it.

Each completed functional case records exact monitor names and counters.
Unconsumed invalid reads are reported separately. This is fixed-trace evidence,
not a universal proof that externally supplied illegal addresses are safe.

## Reproduce

Use the approved local tool wrappers or equivalent installed open-source tools:

```
python tools/check_slh_asic_components.py --tool-dir TOOL_DIR \
  --work-dir .pqc_runs/slh-asic-components --report component-report.json
python tools/check_slh_asic_control.py --tool-dir TOOL_DIR \
  --work-dir .pqc_runs/slh-asic-control --report control-report.json
python tools/check_slh_portable.py --rtl-dir agent/slh_dsa/pristine \
  --parameter-set 128f --fix-auth-sensitivity --asic-startup \
  --iverilog TOOL_DIR/iverilog --vvp TOOL_DIR/vvp --output functional-report.json
python tools/check_slh_asic_structure.py --variant corrected-baseline \
  --parameter-set 128f --work-dir .pqc_runs/slh-asic-structure \
  --yosys TOOL_DIR/yosys --report structure-report.json
python -m unittest discover -s tests -p 'test_slh*.py' -v
```

Run both corrected-baseline/pristine and corrected-candidate/slh_src at each
parameter. `--parameter-set` selects 128f/192f. Full functional
checks require byte-identical golden signing output, accepted positive verify,
and rejected live signature-memory bitflip using the same executable. Their
scope remains historical SPHINCSLET vendor differential, not independent
FIPS 205/ACVP or certification. Source/fixture/transform hashes bind each record.

The separate exporter accepts asic-boot-baseline and asic-boot-candidate only
when both same-parameter reports pass against exact regenerated derivative bytes.
It does not transfer qualification from the FPGA predecessor. The testbench and
its external SIG_MEM are excluded from design source lists. Supply equivalent
external signature storage in both arms. No timing/clock constraint is implied
by the testbench clock, and generic FF lowering is not standard-cell PPA.

## Portable evidence and final admission

The standalone exporter is `tools/export_slh_asic_verified.py` with variants
`asic-boot-baseline` / `asic-boot-candidate`. The target-profile adapter names
these `asic-startup-baseline` / `asic-startup-candidate` and permits ASIC only.
The top remains `top`. Source lists are Verilog-2005 and retain their qualified
source-selected defaults and explicit selected parameter.

Admission requires both same-parameter functional records, their independently
rechecked raw logs and complete output dumps, all exact focused test records,
the selected pair's whole-top FF records and exact-netlist post-audits. Missing
cases, stale hashes, failed inner records or incomplete monitors fail closed.
The combined handoff covers all four arms. Each bundle carries selected and
partner logs separately, exact original Yosys mapping scripts/logs, the limited
generic FF recipe, source hashes, report hashes and exporter/monitor provenance.
Original mapping scripts retain their historical absolute staged paths; the
manifest pass list describes the recipe for a relocated staged source list.

`audit_slh_asic_functional.py` rechecks full dumps, verification flags, the unique
boot marker and the exact consumed-address report set from saved simulator logs.
`audit_slh_asic_netlist.py` checks the exact mapped netlist hash and rejects
blackbox/whitebox modules, tri-state cells, remaining memories, latches and
power-up initialization attributes, then retains the bound mapping artifacts.
These audits do not repeat synthesis or turn generic FF counts into ASIC PPA.

## Final result, 2026-10-12

All four baseline/candidate and 128f/192f combinations pass full golden signing,
positive verification and live signature-memory corruption rejection. The
128f output has 2,141 words; 192f has 4,463. All eight completed simulations
report zero consumed-invalid reads, unknown consume controls and undefined
same-address dual writes, with nonzero live consumption at every required
watcher. Unconsumed invalid reads remain visible in the bound logs.

Both 128f arms lower to 85,243 generic FF bits; both 192f arms to 129,594. All
four selected hierarchies have zero remaining memories, latches, power-up init
attributes, unresolved drivers, black/white boxes and tri-state cells. These
are generic structural counts, not standard-cell area or timing results.

The focused suite passes all four boot cases, both 2,000-cycle memory/FIFO
scoreboards, both unsupported-FILE rejection cases, all seven component FF
mappings and both 12,294-case control equivalence tests. The 39 Python tests
pass normally and with `python -O`. All four exported bundles verify every
checksum and reproduce byte-identically in a second export. Both original
FPGA trees remain unchanged across all 124 files.

See `docs/verification/slh-asic-release-2026-10-12.json` for the exact final
report inventory and bundle hashes. Earlier failed mapping attempts and the
overconservative monitor failure are preserved separately and never admitted
as final qualification.
