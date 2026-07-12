# FINDINGS: synthesis reproducibility check + pristine-tree contamination incident

## Reproducibility (advisor request)
makehint synthesized 3 consecutive times, identical flow/constraints:
all three runs bit-identical (WNS -0.633, 2705 LUT, 752 FF, 177.5 MHz).
Conclusion: Vivado synthesis is deterministic on this flow, so the 7 ps
agent-vs-hand difference on the makehint re-derivation is a real (tiny)
netlist difference between the two edits, not tool variation.

## Pristine-tree contamination (found and fixed)
The pristine ML-DSA reference tree contained an OPTIMIZED coeff_decomposer.v
(the sign_select rewrite of the sub_val correction term), with the true
original left as coeff_decomposer.v.bak in the same directory: at some point
the edit was applied in the pristine tree instead of the tracked override dir.
Sweep confirmed this was the only contaminated file.

Impact assessment: no results invalidated. The edit compiled into every
full-KAT run was itself a KAT-verified accepted win, and no stream bisection
ever used coeff_decomposer as its pristine reference (only the butterfly
cluster). Fixed by restoring pristine from .bak; the optimized version lives
correctly in agent/mldsa/mldsa_src/. Post-restore full-KAT: PASS 25/25.

Rule added: NEVER edit the pristine tree; .bak files appearing under pristine
are a contamination signal. Periodic sweep: ls pristine/*.bak should be empty.
