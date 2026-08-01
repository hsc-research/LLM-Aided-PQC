# ML-DSA Genus Port: elaboration achieved

Date: 2026-07-31
Branch: `main`
Status: elaborates and synthesizes in Genus. **No ASIC Fmax number yet.**

---

## RESULTS OF RECORD (additions)

None. No ML-DSA ASIC measurement exists yet. A single-point synthesis at
10.0 ns was in flight when this document was written.

---

## Summary

ML-DSA `combined_top` now elaborates in Cadence Genus after three fixes and
one build-configuration correction. Full NIST KAT passes 25/25 vectors after
the fixes, in 70.8 s.

The design is **mixed-language**: 33 Verilog files plus 16 VHDL files, with
the Keccak core written in VHDL. This was not apparent from the FPGA flow and
caused the first two failed attempts.

---

## Finding F8: ML-DSA carries the same use-before-declaration defect

`combined_top.v` used three symbols before declaring them:

| Symbol | Used | Declared |
|---|---|---|
| `a_generated` | L1902 | L2285 |
| `a_generated_during` | L1907 | L2286 |
| `op_done_ntty` | L1907 | L2287 |

Same class as F1 (`poly_mult`) and F4 (`v_minus_uy`), but a **different
codebase by different authors** (GMU/Beckwith vs Yale/Deshpande). This
strengthens the claim from "one codebase has this problem" to "this is what
single-toolchain validation produces."

**Incidence differs sharply and must be reported as two numbers, not averaged:**

| Codebase | Files | Files affected | Rate |
|---|---|---|---|
| HQC (Yale/Deshpande) | 59 | 13 | 22% |
| ML-DSA (GMU/Beckwith) | 33 | 1 | 3% |

Both Genus and the independent static checker
(`asic/scripts/declcheck.py`) agree exactly on the ML-DSA result: 3 symbols,
1 file.

**Fix:** hoisted the three declarations to module scope, adjacent to the
existing declaration block at L129. Verified pure reordering by
`LC_ALL=C sort` diff.

### Sub-finding: the hoist must respect scope

The first attempt inserted the declarations immediately above first use, which
placed them **inside a procedural block**. `reg` declarations are illegal
there, and Genus rejected with `VLOGPT-1`, followed by a large cascade of
`VLOGPT-203` "unresolved subprogram reference" errors that were entirely
artifacts of the parse failure. Reverted from `.bak` and redone at module
scope.

**Implication for automating this fix:** a hoist is not a pure text move. The
destination must be module scope, not merely "above first use." Any agent
implementation needs this constraint encoded, and the `LC_ALL=C sort` check
will **not** catch the error, since the bad version is also a pure reordering.
Only the tool catches it.

---

## Finding F9: illegal mix of blocking and non-blocking assignments

`ntt_fifo_piso.v` assigned to the same variable `fifo` with both `<=` (line
56, inside a `for` loop) and `=` (lines 59 to 67) in one `always` block.
Genus rejects with `CDFG-238`. Vivado accepts silently.

This is a more serious class than F1/F4/F8. Mixed assignment semantics on one
variable have tool-dependent ordering, so simulation and synthesis can
legitimately disagree.

**Fix:** converted the eight blocking assignments to non-blocking.

**Equivalence argument.** The blocking assignments run in descending index
order, so each reads a value not yet modified in that pass. Non-blocking gives
the same behavior by definition, because all right-hand sides are sampled
before any update. Line 56's `fifo[i] <= fifo[i-1]` already sampled the old
values. For the `DEPTH=4` instantiation the loop never executes
(`for i = DEPTH-1; i > 3`), so nothing changes there.

**This is reasoning, not proof.** Unlike a hoist, this edit changes assignment
semantics and **cannot** be verified by a sorted diff.

**Verification:** `agent/mldsa/full_kat_gate.py` PASS, 25/25 vectors, 70.8 s,
`"override": "pristine"` confirming it exercised the patched reference tree.

Instantiations affected: `ntt_fifo.v` instantiates `ntt_fifo_piso` at DEPTH 4,
6, 5, and 7. The three with DEPTH > 4 exercise both the loop and the blocking
block.

**Worth reporting upstream.** Related warning in the same file: `CDFG-485`,
the `for` loop condition is always false when `DEPTH <= 4`, so the loop body
is never synthesized for `PISO_A`. That may be intentional or may be a latent
bug; it is the authors' call.

---

## Finding F10: mixed-language design, VHDL read order is load-bearing

Two build-configuration errors, neither a defect in the RTL.

**1. Keccak was silently blackboxed.** The first synthesis attempt read only
`*.v` and produced `CDFG-428`, a blackbox for instance `KECCAK`. Keccak is
VHDL (`keccak_top.vhd` and 15 other `.vhd` files). Because ML-DSA's
chip-level binding path runs through Keccak
(`genblk1[0].KECCAK/control_gen/sel_final_reg/C -> .../output_reg[803]/D`, per
`agent/chip_orchestrator_log.jsonl`), that run would have measured a design
with its critical path hollowed out.

**This is the same hazard as the HQC blackboxing problem (F2), arriving by a
different route.** A blackbox created by a missing file looks identical in the
netlist to a blackbox created deliberately. The
`GenusBackend` guard added in `agent/backends/genus.py` rejects any result
whose reported critical path terminates at a blackboxed pin, but a blackbox
that removes the path entirely will not trip that guard. **Always check the
blackbox count against the expected memory count.**

**2. VHDL alphabetical read order fails.** `glob *.vhd` sorts
`keccak_top.vhd` before `keccak_pkg.vhd` and `sha3_pkg.vhd`, and VHDL requires
packages analysed before their users. Result: `VHDLPT-703` "no such primary
unit in library," cascading into `VHDLPT-766` undeclared identifiers for every
constant the packages define.

**Fix:** read `sha3_pkg.vhd` and `keccak_pkg.vhd` first, then the remainder.
See `asic/scripts/mldsa_fmax.tcl`.

Also copied `common/mldsa_params.v` into both arms; it lives outside
`ref_combined/src` and was missing from the initial arm construction.

After these corrections: **zero blackboxes**, no errors, elaboration succeeds.

---

## Arms

| Arm | Source | Files |
|---|---|---|
| baseline | `minerva_ws/mldsa_pristine/src_rtl` | 33 `.v` + 16 `.vhd` + params |
| optimized | `minerva_ws/mldsa_combined/src_rtl` | same |

Ten files differ. The headline edit is `encoder.v`: the 256-bit
variable-shift PISO replaced by a 256-bit accumulator plus a 4-deep word FIFO
(commit `dca29bc`). FPGA result was chip post-route closure 73.4 -> 78.6 MHz,
**+12.0% over baseline 70.2 MHz** at grade -1.

All portability fixes above were applied **identically to both arms**, so the
only difference between them remains the agent's optimizations.

`combined_top.v` and `ntt_fifo_piso.v` are byte-identical across arms, so a
single fix served both.

## Why this experiment matters

F6 showed the one accepted HQC edit sits off the ASIC critical path, so no
delta was expected or observed. ML-DSA is the opposite case: the chip
orchestrator dispatched to `ENCODER` and the binding path terminates at
`ENCODER/PISO_reg[69]/D`. **The edit is on the path.** If cross-target
transfer works anywhere in this project, it works here.

## Caveats carried forward

1. Elaboration used default parameters (`CDFG-818`), so the security level is
   whatever `combined_top` defaults to. Record which, and confirm it matches
   the level the FPGA result was measured at.
2. Zero wire load, no place-and-route. Not comparable to the FPGA post-route
   numbers.
3. Effort must be identical across arms (F3: effort alone moves Fmax 10.9%).
4. Runtime: one synthesis point at 10.0 ns exceeded 10 minutes and was still
   running. A 7-point binary search is likely 3 to 5 hours per arm, so the
   comparison is an overnight job.

## Next steps

1. Complete the single-point synthesis; record runtime and confirm the
   critical path is flop-to-flop and inside a real module.
2. Binary search both arms at high effort, sequentially, overnight.
3. Compare. Flag any delta below ~11% as indistinguishable from tooling
   sensitivity.
4. Report F9 and the `CDFG-485` always-false loop upstream to the ML-DSA
   authors.

## File map

| What | Where |
|---|---|
| Genus mixed-language script | `asic/scripts/mldsa_fmax.tcl` (server) |
| Elaboration probe | `asic/scripts/mldsa_probe.tcl` (server) |
| Arms | `asic/arms/mldsa_baseline/`, `asic/arms/mldsa_optimized/` |
| Reference tree (KAT reads this) | `/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src` |
| KAT gate | `agent/mldsa/full_kat_gate.py` |
| Raw Genus logs | server `~/pqc/hqc/asic/scripts/genus.log*` |
