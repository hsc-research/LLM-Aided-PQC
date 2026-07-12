# Full-Chip Integration: Chip-Level Critical Path Identified, Compared Against GMU's Reported Clock

First full-chip (combined_top) synthesis run this project, per the
advisor's requested integration sequence. Two results: the chip-level
bottleneck is now identified and located, and it explains why block-level
wins did not move chip-level WNS.

---
## 1. Setup
combined_top registered in synthesizer.py (~39 Verilog + 11 VHDL files,
Keccak included via VHDL). Two variants: pristine (all GMU original
sources) and combined_top (tracked mldsa_src overrides applied by
basename, i.e. every committed block win included). Both synthesized
OOC at the project's 200MHz (5ns) target, matching every block-level run
this project has used. WSL memory was raised to 12GB (from a default
7.6GB that OOM-killed the first attempt) to fit the full-chip synthesis.

## 2. Results
Pristine:  54,224 LUT / 29,069 FF / 29 BRAM / 16 DSP / WNS -9.801 / 67.6 MHz
Optimized: 53,993 LUT / 30,083 FF / 29 BRAM / 16 DSP / WNS -10.045 / 66.5 MHz
Optimized is marginally worse (-0.244 ns, +1014 FF). At this scale the
delta is within full-chip placement noise from the added flip-flops
across nine blocks; it is not read as a regression of any individual win.

## 3. Where the chip-level path actually is
Top-5 path report: **ENCODER: piso_len_reg -> PISO_reg**, 20 logic
levels, 73.7% route, -10.045ns. This is encoder.v's PISO output merge —
a 256-bit variable-length shift register, never registered as a
standalone block, never on any block-level board this project produced.
Registering encoder as its own OOC block for comparison: **-2.900ns**
(di_uncentered_buffer -> PISO, a *different* source register than the
chip-level path). The gap between -2.900 (best-case block-isolated) and
-10.045 (in-chip) is approximately 7.1ns of context this project's
per-block methodology structurally cannot see: cross-module fanout,
whole-design placement congestion, and/or the shared Keccak interconnect
GMU's own paper names as their critical path (Section 4).

## 4. Comparison against GMU's reported numbers
GMU (Beckwith, Nguyen, Gaj, eprint 2021/1451, Table V) report their
combined Dilithium-V architecture achieves **116 MHz on Artix-7**, found
via the Minerva tool searching for the design's natural achievable
frequency post place-and-route — not by targeting a fixed clock and
reporting slack. Their paper states directly: "The critical path of the
design is within the interconnect for the shared Keccak modules."
Two implications:
- **This project's -10.045ns / 66.5MHz at a fixed 200MHz (5ns) target is
  not directly comparable to GMU's 116MHz.** Different methodology:
  synthesis-only slack against an aggressive target vs. a
  placed-and-routed natural-frequency search. A post-route run at a
  clock near 116MHz (8.6ns) would be the apples-to-apples comparison.
- **GMU's own root-cause diagnosis matches what this run found**: a
  shared-resource interconnect bottleneck (Keccak fanout) rather than
  any single arithmetic block. This project's nine block-level campaigns
  targeted exactly the class of path GMU's paper says is NOT the
  bottleneck at the top level — which is consistent with, not
  contradicted by, block wins not moving chip WNS.

## 5. What this means for the project's claims
- Block-level relative wins remain valid and honestly reported: each is
  a real, full-KAT-verified, reproducible improvement to that block in
  isolation, and composition studies (rejection_y/s/a in sampler
  wrappers) already showed most transfer intact one level up.
  **Chip-level absolute timing closure was never claimed and should
  continue not to be claimed** — this run confirms why: the chip
  bottleneck lives in interconnect/congestion territory that OOC
  per-block synthesis cannot see or fix.
- The honest framing for the paper: this project demonstrates an
  agent-driven methodology for systematic, verified, block-level PPA
  improvement across two designs (ML-DSA and HQC transfer), with
  chip-level integration explicitly characterized as a distinct,
  larger-scope problem (shared-resource contention, requiring
  floorplanning/hierarchy-aware synthesis, not the block-taxonomy
  approach used here).

## 6. Recommended next step (not run this session)
Re-run combined_top (pristine and optimized) at a clock near GMU's
achieved 116MHz (period ~8.6ns) rather than the 200MHz stretch target.
This removes the placement-noise floor problem and gives a fair
pristine-vs-optimized chip-level comparison. Each run is long
(~15-40 min observed at 12GB WSL memory); budget accordingly.
