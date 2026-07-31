# Genus / ASIC Port: Bring-Up Findings

Date: 2026-07-30
Branch: `asic-genus-port`
Commits: `950bfc1` (RTL fix), `11c472d` (scripts)

## 1. Environment

| Item | Value |
|---|---|
| Host | `engr-r940s01.engr.uidaho.edu` (RHEL 9.8, 80 CPU, 1 TB RAM) |
| Synthesis | Genus 25.12-s067_1 (`/tools/cadence/installs/DDI251/bin/genus`) |
| License | `5280@ece-cadence-lic.ece.uidaho.edu` |
| Simulation | Xcelium 25.03 (`xrun`) available; not yet used |
| Library | GPDK045, `gsclib045_svt_v4.8`, 537 cells |
| Corner of record | `slow_vdd1v0_basicCells.lib` = PVT 0.9 V, 125 C |
| Vivado on server | Not installed. FPGA flow remains on WSL. |

Note: the Liberty filenames are misleading. `slow_vdd1v0` reports
`nom_voltage : 0.9`, not 1.0. Corner labels must be taken from the file
header, not the filename.

## 2. RTL portability defect: use-before-declaration

Genus rejected `poly_mult.v` at `read_hdl` with `VLOGPT-20`
(reference to undeclared variable). Three declarations appeared below
their first use:

- `reg [ADDR_WIDTH-1:0] addr_0_intermediate;` (was line 240, used at 203)
- `reg [3:0] state = 0;` (was line 244, used at 216)
- `parameter S_*` state encoding block (was line 247, used at 216)

Verilog-2001 requires declaration before use. Vivado accepts the
violation silently; Genus does not.

**Fix:** hoisted all three above first use. Pure reordering, verified by
byte-level comparison of sorted file contents (`LC_ALL=C sort`, one
blank line delta).

**Verification:** `agent/hqc/kat_gate.py` PASS at HQC-128, HQC-192, and
HQC-256 after the edit. The edit is semantically inert, which is the
required outcome; a behavioral change would have indicated the
reordering broke something.

**Implication for the paper.** "Verified RTL" is relative to the
verifying tool. Vivado's permissiveness masked a latent standards
violation that a second toolchain caught immediately. Cross-target
porting is itself a verification method.

### Diagnostic hazard encountered

Initial bisection blamed macro-scope loss for `` `CLOG2 `` in
`mem_dual.v`. This was wrong. Genus aborts mid-parse on the first error
cluster, so downstream files report spurious macro failures. Two
diagnostic cycles were lost to this, compounded by Genus rotating its
log file per invocation (`genus.log`, `genus.log1`, ...), which caused
stale logs to be read as current results.

**Rule:** always read the newest log via `ls -t | head -n 1`, and
resolve the *first* error cluster before interpreting any later one.

## 3. Memory handling

`mem_dual` / `mem_single` are behavioral arrays
(`reg [WIDTH-1:0] mem [0:DEPTH-1]`). Vivado infers BRAM primitives.
Genus has no BRAM, discards the `ram_style = "block"` attribute
(`VLOGPT-506`), and synthesizes flops plus mux trees.

GPDK045 contains no SRAM macro. All 585 entries in
`gsclib045_macro.lef` are standard cells; no memory compiler ships with
the PDK.

**Runtime evidence:**

| Configuration | Result |
|---|---|
| Flat (memory as flops), `medium` effort | Did not complete in 30 min |
| Memory blackboxed, `medium` effort | Completed in ~5 min |

`poly_mult` instantiates exactly one memory (`INTERLEAVED_RED_MEM`,
line 244), confirmed boxed via `CDFG-428`.

**Decision: blackbox memories.** Justification is scope, not
convenience. The agent edits control and datapath logic; it has never
modified a memory. On FPGA the memories are hard BRAM primitives outside
the agent's reach. Reporting logic-only ASIC PPA measures the same thing
the FPGA arc measures. Flat flop-array synthesis would not be a
pessimistic estimate of a real chip, it would be a different design.

## 4. First Fmax measurement (pristine `poly_mult`, HQC-128)

Binary search, `high` effort on generic/map/opt, accepting only MET:

| Period (ns) | Result | Slack (ps) | Runtime (s) |
|---|---|---|---|
| 5.000 | MET | 2524 | 375 |
| 3.000 | MET | 549 | 334 |
| 2.000 | MET | 7 | 343 |
| 1.500 | MET | 0 | 427 |
| 1.250 | VIOLATED | -18 | 931 |
| 1.375 | MET | 0 | 458 |
| 1.312 | MET | 0 | 642 |
| 1.281 | MET | 0 | 882 |

**Result: 1.281 ns minimum period, 780.49 MHz.**

Critical path is flop-to-flop (`count_chunks_reg[4]/CK` ->
`loc_addr_reg[15]/D`), not a memory boundary, so the path is real.
Area 6754.842 um^2, 2706 cells, memory excluded.

## 5. Measurement caveats (must appear in any write-up)

These are stated up front because each is a likely reviewer objection.

1. **Not comparable to the FPGA number.** FPGA HQC closes at 114.8 MHz.
   The prior FPGA finding is that HQC binds on SHAKE256 state RAM
   write-data addressing. Blackboxing removes that memory, so the ASIC
   measurement may have deleted the binding path rather than sped it up.
   The 6.8x ratio is not a technology-scaling result.

2. **Zero wire load.** `Wireload mode: enclosed`, `Net-Area 0.000`. No
   interconnect delay is modeled. At a 1.281 ns period, wire delay would
   be a large fraction of the real period. These are synthesis-level
   estimates, not closed timing. The ASIC analogue of the project's
   "post-route closure is the judge" rule is Innovus place-and-route,
   which is not set up.

3. **Slack pins to 0 ps.** Four consecutive MET points returned exactly
   0 ps. Genus optimizes until the constraint is met and then stops, so
   the search converges on where the tool stops trying, which is
   effort-dependent. Untested: whether Fmax moves under a different
   effort setting. Until that is checked, the number is partly a tool
   property, not purely a circuit property.

4. **Educational PDK.** The GPDK045 Liberty README states the timing is
   characterized on 2x2 constraint tables for demonstration, with 7x7
   recommended for accuracy. Absolute numbers are not silicon-grade.
   Only relative pristine-versus-optimized deltas are defensible.

## 6. Status and next steps

Done: flow works end to end. RTL reads, elaborates, synthesizes, and a
binary search closes on a real flop-to-flop path.

Not done: no optimized-versus-pristine delta exists yet. Only pristine
has been measured, on one module.

Next, in priority order:

1. Effort-sensitivity check at 1.281 ns (tests caveat 3 cheaply).
2. Pristine baseline across remaining HQC blocks.
3. Run the agent's existing optimized RTL through the same search to
   obtain the first ASIC delta.
4. Backend abstraction in `agent/` so `fmax_search.py` is
   backend-parameterized rather than Vivado-specific.

Deferred: Innovus place-and-route; ML-DSA ASIC retarget.

## 7. Open question for advisor

Whether the ASIC arc belongs in the ICCAD abstract at all, or is
D&T-only. As of this session it is a flow-bring-up result, not a results
table. The defensible claim is cross-target generality ("the same agent,
with only a synthesis backend swapped, improves timing on a 45 nm
standard-cell target"), supported by relative deltas. A claim of the
form "HQC achieves X MHz in 45 nm" is not supported by this data.
