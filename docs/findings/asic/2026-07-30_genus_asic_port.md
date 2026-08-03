> **SUPERSEDED 2026-08-02.** This document describes GPDK045 45 nm work.
> The ASIC target is now **ASAP7 7 nm** and every number here is retracted as
> not comparable. Mechanisms and methodology findings still hold; the numbers
> do not. See `docs/findings/asic/2026-08-02_asap7_transition.md`.

# Genus / ASIC Port: Bring-Up Findings

**Status:** flow bring-up complete. No optimized-vs-baseline delta exists yet.
**Dates:** 2026-07-30 (bring-up), 2026-07-31 (effort sensitivity)
**Branch:** `asic-genus-port`
**Commits:** `950bfc1` RTL fix, `cd92639` build propagation, `11c472d` scripts, `0264a3a` this doc, `1e3b64e` Fmax driver

---

## 0. RESULTS OF RECORD

Every ASIC number produced so far. Nothing outside this table is a result.
If a number is quoted anywhere (abstract, paper, slides) it must appear here
first, with its log path.

| # | Design | Config | Effort | Min period | Fmax | Area (um^2) | Cells | Log | Date |
|---|---|---|---|---|---|---|---|---|---|
| A1 | `poly_mult` HQC-128 | baseline, memories blackboxed | **high** | 1.281 ns | **780.49 MHz** | 6754.842 | 2706 | `asic/results/fmax_poly_mult.log` | 2026-07-30 |
| A2 | `poly_mult` HQC-128 | baseline, memories blackboxed | **medium** | 1.438 ns | **695.65 MHz** | not captured | not captured | `asic/results/fmax_poly_mult_medium.log` | 2026-07-31 |

**Corner for A1 and A2:** GPDK045 SVT, `slow_vdd1v0_basicCells.lib`,
PVT 0.9 V / 125 C, pre-layout, zero wire load.

**A1 vs A2 is NOT a result.** It is a control experiment measuring tool
effort sensitivity. See Section 5.

**What does not exist yet:** any optimized-vs-baseline ASIC delta, any module
other than `poly_mult`, any HQC-192 or HQC-256 ASIC number, any post-layout
number.

### Terminology (fixed, do not vary)

| Term | Means |
|---|---|
| **baseline** | Unmodified RTL, the control arm of an optimization comparison |
| **optimized** | RTL after agent edits, the treatment arm |
| **initial characterization** | The May 2026 Vivado PPA survey in the master doc |
| **closure** | Binary search to minimum MET period. Not projected, not extrapolated |

"Pristine" is retired. Use "baseline".

---

## 1. Environment

| Item | Value |
|---|---|
| Host | `engr-r940s01.engr.uidaho.edu` (RHEL 9.8, 80 CPU, 1 TB RAM) |
| Synthesis | Genus 25.12-s067_1 (`/tools/cadence/installs/DDI251/bin/genus`) |
| License | `5280@ece-cadence-lic.ece.uidaho.edu` (shared; another user holds a long-running job) |
| Simulation | Xcelium 25.03 (`xrun`) present, not yet used |
| Library | GPDK045, `gsclib045_svt_v4.8`, 537 cells |
| Corner of record | `slow_vdd1v0_basicCells.lib` = PVT 0.9 V, 125 C |
| Vivado on server | Not installed. All FPGA work stays on WSL. |
| Server repo path | `~/pqc/hqc` |
| Transport | rsync over ssh. Deploy key requested from advisor; not yet granted. |

Liberty filenames are misleading: `slow_vdd1v0` reports `nom_voltage : 0.9`.
Take corner labels from the file header, never the filename.

---

## 2. Finding F1: RTL portability defect, use-before-declaration

Genus rejected `poly_mult.v` at `read_hdl` with `VLOGPT-20`. Three
declarations sat below their first use:

| Declaration | Was at line | First used at |
|---|---|---|
| `reg [ADDR_WIDTH-1:0] addr_0_intermediate;` | 240 | 203 |
| `reg [3:0] state = 0;` | 244 | 216 |
| `parameter S_*` state encoding block | 247 | 216 |

Verilog-2001 requires declaration before use. Vivado accepts the violation
silently; Genus does not.

**Fix:** hoisted all three above first use. Verified pure reordering by
`LC_ALL=C sort` comparison of pre- and post-edit files (one blank-line delta,
no other difference).

**Verification:** `agent/hqc/kat_gate.py` PASS at HQC-128, HQC-192, HQC-256.
Semantic inertness is the required outcome; a behavioral change would have
meant the reorder broke something.

**Commit:** `950bfc1`. Build-dir propagation: `cd92639`.

**Vacuity check performed:** `build/encap`, `build/decap`, and
`build/joint_design` all held stale copies of `poly_mult.v` before the KAT
run. Had the gate run first, it would have passed on unmodified RTL. All four
build dirs were synced and re-verified before the gate.

**Implication.** "Verified RTL" is relative to the verifying tool. A second
toolchain caught a latent standards violation the FPGA flow never surfaced.
Cross-target porting is itself a verification method.

### Diagnostic hazards (cost two cycles)

- Genus aborts mid-parse on the first error cluster. Downstream files then
  report spurious macro-scope failures. **Resolve the first cluster before
  interpreting any later one.**
- Genus rotates its log per invocation (`genus.log`, `genus.log1`, ...).
  Stale logs were read as current twice. **Always
  `ls -t genus.log* | head -n 1`.**
- Genus stays resident after a `read_hdl` failure and holds a license. Use
  `exit -force` and wrap runs in `timeout`.

---

## 3. Finding F2: memory handling, blackboxed

`mem_dual` / `mem_single` are behavioral arrays. Vivado infers BRAM. Genus has
no BRAM, discards `ram_style = "block"` (`VLOGPT-506`), and builds flops plus
mux trees.

GPDK045 has **no SRAM macro**. All 585 entries in `gsclib045_macro.lef` are
standard cells. No memory compiler ships with the PDK.

**Runtime evidence:**

| Configuration | Effort | Result |
|---|---|---|
| Flat, memory as flops | medium | Did not complete in 30 min (timed out) |
| Memory blackboxed | medium | Completed in ~5 min |

`poly_mult` instantiates exactly one memory (`INTERLEAVED_RED_MEM`, line 244),
confirmed boxed via `CDFG-428`. Blackbox count verified as 1, matching the
instantiation count.

**Decision: blackbox memories.** Justification is scope, not convenience. The
agent edits control and datapath logic and has never modified a memory. On
FPGA the memories are hard BRAM primitives outside the agent's reach. Flat
flop-array synthesis is not a pessimistic estimate of a real chip; it is a
different design.

**Unresolved:** blackboxes currently carry no timing arcs, so paths through
them are unconstrained. Acceptable only because the measured critical path is
flop-to-flop (verified for A1). Must be re-checked for every new module.

---

## 4. Measurement method (canonical, ASIC)

Mirrors the Vivado `fmax_search.py` ruling.

1. Binary search on clock period, tolerance 0.05 ns.
2. Accept **only** `Path 1: MET`. Never project from a violated run.
3. Effort **pinned and reported**. See Section 5; this is not optional.
4. Memories blackboxed.
5. Corner recorded in every report header.
6. Confirm the reported critical path is flop-to-flop, not a blackbox pin.

**Never** compute Fmax as `1/(period - WNS)`. Retracted on the FPGA side; the
same prohibition applies here.

Scripts: `asic/scripts/genus_fmax.tcl`, `asic/scripts/genus_fmax.py`.

---

## 5. Finding F3: effort setting materially changes Fmax

**This is the most important result of the port so far.**

| Effort | Min period | Fmax | Delta vs high |
|---|---|---|---|
| high (`syn_generic`/`syn_map`/`syn_opt` = high) | 1.281 ns | 780.49 MHz | reference |
| medium | 1.438 ns | 695.65 MHz | **-10.9% Fmax** |

Search traces:

| Period (ns) | high | medium |
|---|---|---|
| 5.000 | MET +2524 ps | MET +2331 ps |
| 3.000 | MET +549 ps | MET +418 ps |
| 2.000 | MET +7 ps | MET 0 ps |
| 1.500 | MET 0 ps | MET +2 ps |
| 1.438 | not probed | MET 0 ps (result) |
| 1.406 | not probed | VIOLATED -6 ps |
| 1.375 | MET 0 ps | VIOLATED -11 ps |
| 1.312 | MET 0 ps | not probed |
| 1.281 | MET 0 ps (result) | not probed |
| 1.250 | VIOLATED -18 ps | VIOLATED -110 ps |

**Consequences, all binding:**

1. Effort must be identical between baseline and optimized arms, and stated in
   every reported number. Treat it exactly like the OOC-mode ruling on Vivado.
2. **The effort gap (10.9%) is larger than the FPGA results being replicated**
   (ML-DSA +17.8%, HQC +5.8%). Any ASIC delta below roughly 11% cannot be
   distinguished from a tooling artifact without holding effort fixed and
   publishing the search traces.
3. Slack pins to exactly 0 ps across many MET points. Genus optimizes until
   the constraint is met, then stops. The search therefore finds where the
   tool gives up, which is effort-dependent, not purely physical.
4. Runtime is not a reason to prefer medium (medium 376-465 s/point, high
   334-931 s/point). **Use high for all reported numbers.**

---

## 6. Standing caveats for any write-up

State these before a reviewer finds them.

1. **Not comparable to the FPGA number.** FPGA HQC closes at 114.8 MHz; A1 is
   780 MHz. The FPGA binding path is SHAKE256 state-RAM write-data addressing.
   Blackboxing removes that memory, so the ASIC measurement may have deleted
   the binding path rather than sped it up. The ratio is not a
   technology-scaling result.
2. **Zero wire load.** `Wireload mode: enclosed`, `Net-Area 0.000`. No
   interconnect delay modeled. At 1.281 ns, wire delay would be a large
   fraction of the real period. These are synthesis-level estimates, not
   closed timing. The ASIC analogue of "post-route closure is the judge" is
   Innovus place-and-route, which is not set up.
3. **Effort sensitivity.** See Section 5.
4. **Educational PDK.** GPDK045 Liberty README states 2x2 constraint tables
   for demonstration, 7x7 recommended for accuracy. Absolute numbers are not
   silicon-grade. Only relative deltas are defensible.

**Supportable claim:** "the same agent, with only a synthesis backend swapped,
improves timing on a 45 nm standard-cell target," evidenced by relative deltas
at fixed effort.

**Not supportable:** "HQC achieves X MHz in 45 nm."

---

## 7. Next steps

1. Identify which HQC blocks the agent actually edited, from
   `agent/flight_log.jsonl`. `poly_mult` has only two commits (initial import,
   `950bfc1`) and **has never been optimized**, so no delta can come from it.
   This gates everything else.
2. Run baseline and optimized arms of whichever module the agent did edit,
   both at high effort.
3. Per-effort output directories in the driver, so two runs cannot overwrite
   each other's reports. Near-miss on 2026-07-30: a duplicate run was launched
   into the same `OUTDIR` and would have silently corrupted both results.
4. Backend abstraction in `agent/` so `fmax_search.py` is
   backend-parameterized rather than Vivado-specific.

**Deferred:** Innovus place-and-route, ML-DSA ASIC retarget, Xcelium-based
ASIC KAT gate.

**Open for advisor:** whether the ASIC arc belongs in the ICCAD abstract at
all, or is D&T-only. As of now it is flow bring-up, not a results table.

---

## 8. File map

| What | Where |
|---|---|
| Genus Fmax driver | `asic/scripts/genus_fmax.py` |
| Genus Fmax TCL | `asic/scripts/genus_fmax.tcl` |
| Medium-effort variants | `asic/scripts/genus_fmax_med.{py,tcl}` (server only, not yet committed) |
| Parse bisection probes | `asic/probe/probe*.tcl`, `asic/probe/probe.v` |
| Result logs | `asic/results/` |
| Raw Genus reports | server `~/pqc/hqc/asic/out/` (gitignored) |
| This doc | `docs/findings/asic/2026-07-30_genus_asic_port.md` |
