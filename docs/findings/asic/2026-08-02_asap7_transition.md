# ASAP7 Transition: retraction and measurement methodology

Date: 2026-08-02
Supersedes the GPDK045 approach in
`docs/findings/asic/2026-07-30_genus_asic_port.md` and
`docs/findings/asic/2026-07-31_vmu_arm_comparison.md`.

---

## 0. RESULTS OF RECORD

**All prior ASIC results are retracted.** The library changed from GPDK045
45 nm to ASAP7 7 nm on advisor instruction. Numbers measured on a different
library are not comparable and may not be quoted anywhere.

| # | Design | Config | Value | Status |
|---|---|---|---|---|
| ~~A1~~ | ~~`poly_mult` HQC-128~~ | ~~GPDK045, baseline, high effort~~ | ~~1.281 ns / 780.49 MHz~~ | **RETRACTED: wrong library** |
| ~~A2~~ | ~~`poly_mult` HQC-128~~ | ~~GPDK045, baseline, medium effort~~ | ~~1.438 ns / 695.65 MHz~~ | **RETRACTED: wrong library** |
| ~~A3~~ | ~~`v_minus_uy` HQC-128~~ | ~~GPDK045, baseline, high effort~~ | ~~0.711 ns / 1406.59 MHz~~ | **RETRACTED: wrong library** |
| ~~A4~~ | ~~`v_minus_uy` HQC-128~~ | ~~GPDK045, optimized, high effort~~ | ~~0.746 ns / 1340.31 MHz~~ | **RETRACTED: wrong library** |

The A1/A2 pair retains value as the source observation for F3 (effort
sensitivity), and A3/A4 for F6 (block-level transfer null). The mechanisms
those findings describe are not library-specific even though the numbers are.

**No ASAP7 result exists yet.** A single `combined_top` profiling run is in
flight at the time of writing and is a runtime measurement, not a result.

### Corner of record (new)

ASAP7 7 nm, `asap7sc7p5t`, LVT and SLVT cells, **TT corner only** (no fast or
slow libraries ship with the tutorial distribution). `4x` scaled LEF with the
matching `4x` tech LEF. **Liberty time unit is picoseconds**, not nanoseconds.

---

## 1. Terminology corrections

Applied on advisor instruction, from both Dr. Abideen and Dr. Deshpande
independently.

| Was | Now | Reason |
|---|---|---|
| "Verilog-2001 violations" | **"cross-tool RTL portability defects"** | The standard interpretation has not been confirmed by an independent parser. Claim softened until a linter agrees. |
| F3 as a "noise floor" | **"tool-configuration sensitivity"** | Not a threshold below which deltas are meaningless. It is a variable under our control. Pin every setting identically across arms and a delta of any size is valid. |
| Genus numbers unqualified | **"pre-layout"** | Must be reported separately from Innovus post-route. |

The F3 correction matters more than it sounds. The earlier framing implied any
delta under 10.9% was unreportable, which would have ruled out the HQC +1.9%
result entirely. The correct statement is that effort, clock period and
uncertainty, library and corner, hierarchy, flattening, and retiming must be
identical across arms and recorded with the number.

---

## 2. Finding F11: memories are now flip-flop arrays, reversing F2

F2 blackboxed memories on runtime grounds. **That decision is reversed.**

Instruction: map inferred memories to flip-flop arrays for the initial
experiments. This is neither area- nor power-efficient, but it validates the
complete RTL-to-GDS flow without introducing SRAM integration problems at the
outset. SRAM macros come after the flow closes, via the ASAP7-compatible
memory flow.

**Why the original reasoning was wrong.** F2 optimized for iteration speed,
which is the wrong objective when the flow itself is unvalidated. Blackboxing
also defers memory integration problems rather than solving them, and on PQC
designs the critical path is expected to run through the memories, so those
problems are the point rather than a distraction.

Consequence: runtime will be worse than the F2 measurements suggested, and
that is accepted.

---

## 3. Finding F12: a binary search must prove its lower bound

**Observed.** An encoder search over the bracket [2.0, 5.0] ns returned
**exactly 2.047 ns for both the baseline and the optimized arm.** Every probed
point met:

| Period (ns) | Result |
|---|---|
| 5.000 | MET, 368 ps |
| 3.500 | MET, 0 ps |
| 2.750 | MET, 12 ps |
| 2.375 | MET, 12 ps |
| 2.188 | MET, 0 ps |
| 2.094 | MET, 0 ps |
| 2.047 | MET, 0 ps |

No point ever violated. The search converged on `LO + tolerance`, so what was
measured is the **bracket floor**, not the design limit. Both arms agreeing was
not a null result; it was both arms hitting the same artificial wall.

**Verification.** Re-run over [0.3, 2.1] ns on the same design and library:

| Period (ns) | Result |
|---|---|
| 2.100 | MET, 0 ps |
| 1.200 | VIOLATED, -156 ps |
| 1.650 | MET, 0 ps |
| 1.425 | MET, 0 ps |
| 1.312 | VIOLATED, -32 ps |
| 1.369 | MET, 0 ps |

Closes at **1.369 ns**, not 2.047 ns. The first search was wrong by 50%.

**Fix.** The driver now runs the lower bound first and **exits with an error if
it MEETS**, since any result from such a search is the bracket rather than a
measurement. It also aborts on an unparsable point rather than continuing (the
re-run produced a `NO REPORT` at 1.341 ns that the old driver would have
silently skipped).

**Rule.** A search result is only valid if both bounds were probed and the
lower bound violated. State the bracket alongside every reported Fmax.

**Note the slack pattern.** MET points return exactly 0 ps repeatedly. Genus
optimizes until the constraint is met and then stops, so slack at a met point
carries no information about headroom. Only the violated points locate the
floor.

---

## 4. Finding F13: unconstrained static inputs capture the critical path

**Observed.** The first ASAP7 encoder run used the tutorial's constraint set:

```tcl
set_input_delay  -clock clk 1   [all_inputs]
set_output_delay -clock clk 300 [all_outputs]
```

The reported critical path was:

```
Startpoint: (R) sec_lvl[0]          <- an input PORT, not a register
Endpoint:   (R) di_uncentered_buffer_reg[22]/D
```

`sec_lvl` selects the security level. It is static configuration, set once and
held for the duration of an operation. It is not a timed path in any
meaningful sense, but `[all_inputs]` constrained it anyway, and the resulting
path dominated the report.

**Why this is dangerous rather than merely wrong.** The number produced is
real, reproducible, and completely valid as an answer to the wrong question. It
measures the input constraint, not the design. Two arms compared under this
setup would differ mainly in how synthesis happened to buffer a configuration
signal.

**Fix.** A per-design SDC that classifies ports:

```tcl
create_clock -name clk -period $PERIOD_PS [get_ports clk]
set_clock_uncertainty [expr $PERIOD_PS * 0.05] [get_clocks clk]

# static configuration and async control are not timed paths
set_false_path -from [get_ports sec_lvl*]
set_false_path -from [get_ports mode*]
set_false_path -from [get_ports rst]
set_false_path -from [get_ports start]

# data and handshake interface, 10% of period each side
set IO_DELAY [expr $PERIOD_PS * 0.10]
set_input_delay  -clock clk $IO_DELAY [get_ports {data_i* valid_i ready_o}]
set_output_delay -clock clk $IO_DELAY [get_ports {data_o* valid_o ready_i}]
```

**Verification.** Same design, same period, with the SDC:

```
Startpoint: (R) di_buffer_reg[55]/CLK        <- register
Endpoint:   (F) di_uncentered_buffer_reg[68]/D
```

Flop to flop. The artifact is gone.

**Rule, generalizing F6's check.** Before trusting any timing number, read the
reported path endpoints. A path that starts at an input port, ends at an output
port, or terminates at a blackbox pin is not measuring the design's internal
logic. This must be checked for every module, since the port classification
differs per design and cannot be inherited.

Clock uncertainty of 5% was also added, which the earlier GPDK045 runs lacked
entirely. Zero uncertainty is unrealistic and it is one of the settings that
must match across arms.

---

## 5. Finding F14: the reference flow is validated

The tutorial at `hsc-research/tutorial_innovus` is self-contained and ships
ASAP7 (Liberty, LEF, tech LEF, QRC). No separate PDK download was needed.

SHA256 through the unmodified tutorial Genus script: **zero errors, netlist
written, roughly 13 minutes.** The flow is known-good on this machine.

Adapted to `asic/asap7/scripts/genus_asap7.tcl`, parameterized by top module,
source directory, SDC, period, and output directory. Two carried-over
requirements:

- **Periods are in picoseconds.** The tutorial's `create_clock -period 600`
  is 600 ps. Carrying the nanosecond assumption over from GPDK045 would
  corrupt every number by three orders of magnitude.
- **Mixed-language read order** (F10) is preserved: `sha3_pkg.vhd` and
  `keccak_pkg.vhd` first, then the remaining VHDL, then Verilog. A
  Verilog-only glob silently blackboxes the Keccak core.

Harmless warnings observed: `DECAP*` filler cells absent from the scaled LEF,
and `Pad` dropped for excessive width. Neither affects synthesis.

---

## 6. Machine baseline (for the runtime question)

Recorded to answer whether the earlier two-hour full-chip runtime was
abnormal.

| Item | Value |
|---|---|
| Host | `engr-r940s01`, 80 cores, 1006 GB RAM |
| Memory in use at run start | 13 GB, no swap |
| GPDK045 full-chip peak (earlier) | 16.8 GB, 12 partitions |
| ASAP7 `combined_top` at 2 min | 5.6 GB resident, 111% CPU |

**Memory is not the constraint.** Peak usage was under 2% of available RAM.

**Preliminary observation, not yet a finding.** CPU sits near 100 to 120%
during elaboration on an 80-core machine, so Genus is barely parallelizing at
that stage. If this persists into `syn_map`, the runtime may be single-thread
bound rather than design-size bound, which would make super-threading settings
the relevant lever rather than design scope. To be confirmed once the profiling
run reaches mapping.

**Standing rule.** Concurrent wall-clock is not a runtime measurement. The
earlier GPDK045 figures were taken with two or three jobs sharing the machine
and must not be quoted as runtime.

---

## 7. What this changes about the plan

- Full-chip baseline versus optimized on ASAP7 remains the **primary** goal.
- The encoder-block comparison is **supporting evidence** and is explicitly
  not equivalent to a full-chip result. If full-chip proves impractical, the
  result must be reported as a block-level cross-backend transfer study with
  full-chip ASIC improvement stated as unverified.
- Genus pre-layout and Innovus post-route are separate numbers, always
  labelled.
- The normalized RTL should become the single source artifact read by both
  Vivado and Genus, which also resolves F7.

## 8. File map

| What | Where |
|---|---|
| Tutorial and ASAP7 libraries | server `~/pqc/tutorial_innovus/` |
| ASAP7 Genus script | `asic/asap7/scripts/genus_asap7.tcl` |
| Fmax driver (bracket-asserting) | `asic/asap7/scripts/asap7_fmax.py` |
| SDC files | `asic/asap7/sdc/` |
| Reports | `asic/asap7/out/<arm>/` |
| Retracted GPDK045 material | `asic/results/`, `asic/scripts/` |
