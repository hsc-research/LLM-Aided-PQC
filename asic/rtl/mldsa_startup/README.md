# ML-DSA explicit ASIC startup derivatives

These are actual Verilog-2005 RTL derivatives of the qualified guarded baseline
and corrected candidate. The original upstream files, FPGA exports and old
qualified source bundles remain unchanged. Compile one complete derivative tree;
do not combine its duplicate module definitions with an original bundle.

The target exporter uses the distinct ASIC-only selections
`asic-startup-baseline` and `asic-startup-candidate`. Each source directory keeps
an immutable `manifest.json`, an ordered `sources.f`, and the complete RTL.
`deployment.json` links that immutable source identity to the new evidence.
A reproducible builder is `tools/build_mldsa_startup_derivative.py`.

## Interface and required startup sequence

Top: `combined_top_asic`. Existing `BUS_W`, `SAMPLE_W`, `W` parameters and all
original transaction ports are retained; tested production values remain
`4`, `23`, and `64`. Runtime modes are KeyGen=0, Verify=1, Sign=2. Supported
security selectors are 2, 3, and 5, corresponding to ML-DSA-44/-65/-87.

Additional ports:

- `boot_rst`: synchronous, active-high, destructive cold-start reset
- `boot_ready`: asserted after boot state and RAM initialization are complete

1. Assert `boot_rst` across at least one rising `clk` edge. Do not rely on
   power-up values of any register, including `boot_ready`.
2. Deassert it. Seven RAM banks clear in parallel, one word per bank per clock.
   `boot_ready` asserts after exactly 4,096 scrub edges. The smaller banks stop
   writing after their first 1,024 edges.
3. Wait for `boot_ready`, then follow the original per-operation `rst` and
   `start` sequence. `boot_ready` does not authorize skipping operation reset.
   Some original pipeline state is initialized by that subsequent reset/drain.
4. Keep the mode, level, data and ready/valid protocol required by the original
   design. Requests presented only before readiness are discarded, not queued.

The clock is never gated. Before readiness, the shell holds the core in reset,
blocks its input handshakes and start, disables ordinary RAM accesses, and drives
external ready/valid/data to zero. Ordinary `rst` neither starts a scrub nor drops
`boot_ready`; it retains the original behavior. Reasserting `boot_rst` aborts an
operation and destroys RAM contents. The host must restart its transaction and
reload its inputs after readiness and operation reset.

The original top's reset assigns `cstate1` twice and does not reset `cstate2`.
This derivative deliberately does not silently redesign ordinary reset semantics:
`cstate2` receives its original `FSM2_STALL` value on explicit boot. Arbitrary
mid-operation ordinary-reset recovery is not claimed.

## Exact memory/state changes

- One 4096x96 and six 1024x96 RAM banks remain, all on the same clock and with
  exactly the original production storage capacity (983,040 bits total).
- RAM reads retain one enabled rising-edge latency, output hold while disabled,
  and read-before-write behavior, including opposite-port read/write collisions.
  Same-address simultaneous writes from both ports remain outside the portable
  contract; the full-core tests assert they do not occur in tested operations.
- Boot scrub has exclusive access. It does not reset read-output registers,
  matching the original undefined output until the first enabled read.
- Sequential declaration/initial-block values move into explicit boot-reset
  branches in their existing clocked processes. Original ordinary-reset and
  post-boot datapath bodies retain their ordering, including the original mixed
  blocking/nonblocking FIFO assignments.
- Forty combinational initializers per arm are removed; they are not hardware
  state. Two read-only initialized signals become constant wires, one unused
  initializer is removed, and GHDL constant arrays become constant nets. The
  static zeta ROM uses the separately verified constant-table implementation.
- Only unsupported `sec_lvl` values receive new zero defaults in `gen_c` for
  `C_SIPO_START` and `ch`, removing two otherwise inferred latches. Values 2/3/5
  already assign both on every path and are unchanged.
- `makehint` still stores exactly 80 bytes. A 128-word combinational read view
  wires words 0..79 to that storage and ties words 80..127 to zero. The five
  dynamic reads use this view; writes are unchanged. Existing guards bound every
  observable read to 0..79 / 0..54 / 0..74 for levels 2/3/5. The extra constants
  remove undriven inactive branches from generic binary read-mux mapping and add
  no storage.

Both arms use byte-identical shell, RAM and zeta-ROM files and the same startup
protocol. Their different internal state still reflects their respective
baseline/candidate implementations; no historical PPA transfers to these files.

## Evidence and limitations

See `docs/verification/mldsa-asic-startup-2026-10-12/result.json` and the per-arm
full reports for the final status and exact source/tool/log hashes.

The suite checks all original 210 cases in each arm, plus two cold-boot aborts
before each test process completes those cases, at default and randomized initial
state settings. It compares every completed operation's reported cycle count
with its qualified reference. Four-state component checks cover real-size RAM
semantics, the startup shell, and exhaustive supported `makehint` read controls.
Whole-source Yosys checks reject residual state initialization and latches; a
separate full generic memory-to-FF pass checks that all inferred memories map.

This is RTL functionality and generic FF logic, not standard-cell library mapping,
physical implementation, timing closure, area, power, FIPS certification,
side-channel qualification, arbitrary backpressure proof or formal equivalence.
Full-core Icarus remains unqualified after a bounded timeout; full KATs use
Verilator's two-state simulation, with randomized initial storage as additional
finite checks. Four-state component tests are not a substitute for a successful
whole-core four-state run.

Yosys initially hit the installed YoWASP runtime's default 2 MiB recursion-stack
limit. `tools/run_yosys_large_stack.py` uses the unchanged installed tool with a
16 MiB Wasm stack, 32 MiB async-stack limit, and 32 MiB worker-thread stack, only
inside that process. No package, system configuration or synthesis semantics is
changed. Earlier failures are retained, including the two residual invalid-level
latches and the uncompleted 80-word read-mux branches before the narrow fixes.

The generated GHDL source warns about a high-impedance constant on an unused
`keccak_control.sel_cin` output. Its parent connection is open, and the final
reachable netlist contains no tri-state cells. This is a documented dead-output
warning, not a blanket waiver of synthesis warnings.
