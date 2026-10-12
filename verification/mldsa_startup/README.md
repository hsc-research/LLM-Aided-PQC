# ML-DSA ASIC startup checks

No upstream or previously qualified source file is edited by these checks.
No paid tools, cloud EDA, external APIs, downloads or HQC work is involved.

## Rebuild the frozen derivative from its qualified reference

From the integrated repository root, export each exact reference into a fresh
working directory using `tools/export_mldsa_verified.py`. Then:

```sh
python tools/build_mldsa_startup_derivative.py \
  --reference .pqc_runs/reference/guarded-baseline \
  --components asic/rtl/mldsa_startup \
  --out .pqc_runs/rebuilt/guarded-baseline
python -m unittest discover -s tests -p test_mldsa_asic_startup.py -v
```

The builder requires one of the two exact pinned reference manifest hashes,
checks every source hash, and rejects unsupported initializer/driver or RAM-bank
shapes. It is a bounded transformation for these sources, not a general HDL
parser. The test rebuilds both arms and compares every byte with the frozen tree.

## Full functional checks

```sh
python tools/check_mldsa_startup_kats.py --repo . \
  --design asic/rtl/mldsa_startup/guarded-baseline \
  --out .pqc_runs/mldsa-asic-startup-baseline \
  --tool-dir /path/to/installed/tools --jobs 2 \
  --seeds 0 11 29 --boot-restarts
```

Repeat for `corrected-candidate` into another fresh work directory. Seed 0 means
the ordinary default initialization setting; seeds 11/29 use Verilator
`+verilator+rand+reset+2`. RTL power-up initializers are absent in all cases.
`--vectors` is reduced coverage and cannot qualify the complete source target.
The frozen source hash and full 210-case requirement must both match when
consuming a report.

Every process performs an initial boot, starts an operation, cold-boots after
250 active cycles, starts again, cold-boots after 2,000 active cycles, resets its
host transaction state, and then completes the selected unmodified KAT cases.
The first complete operation must still pass and every later expected result
must appear exactly once. Original bytewise partial-signature testbench
portability repairs are retained. Input/source/executable/testbench hashes,
compile commands, simulator statuses and finite result coverage are recorded.

## Four-state component tests

- `tb_sameclock_ff_ram.sv`: real 4096x96 and 1024x96 dimensions; original and
  derivative enabled-read/hold/read-before-write comparison, randomized dual
  port traffic, exhaustive post-scrub readback, blocked core traffic during boot,
  and a destructive second boot. Undefined dual-write collisions are excluded.
- `tb_boot_shell.sv`: real startup shell with an explicitly identified interface
  observation stub; exact 4,096-cycle readiness, held core inputs and zeroed
  external outputs, ordinary-reset retention, active reboot, interrupted scrub,
  and repeated boot. This test is not presented as full-core simulation.
- `tb_makehint_read_view.sv`: four arbitrary storage patterns, every 8-bit `ctr`,
  both states/rejection conditions and all supported levels, 12,288 cases. It
  compares every observable output to the original and rejects unknown outputs.
  Only this combinational test writes internal fixture state directly.

## Whole-core generic FF mapping

Run the exact ordered source list through installed Yosys:

```text
read_verilog -sv <sources>
hierarchy -check -top combined_top_asic
proc; opt
check -assert -noinit -nolatches
memory_map; opt
check -assert -noinit -nolatches
stat
write_json <output>
```

The release was also elaborated by Icarus in Verilog-2005 mode. The SystemVerilog
flag above is accepted by the existing Yosys flow; it does not imply that source
files require SystemVerilog.

The saved report binds the resulting JSON hash and checks every reachable module
for residual memory/latch/tri-state cells, state init attributes and black boxes.
FF bit counts account for hierarchy multiplicity, including all seven banks.
This is generic memory mapping only; no standard-cell library or mapped-netlist
simulation/equivalence is supplied.
