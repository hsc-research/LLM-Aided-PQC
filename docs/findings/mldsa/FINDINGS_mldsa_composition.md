# Findings: block-level wins under composition (sampler wrappers)

Method: synthesize each sampler wrapper (sampler_s, sampler_y_ext,
sampler_a_ext) with pristine vs optimized rejection core, identical flow
(Artix-7 OOC, 200 MHz). Measurement only; no new edits.

| Composite | pristine WNS/LUTs | optimized WNS/LUTs | delta |
|---|---|---|---|
| sampler_s | -4.013 / 1667 | -2.486 / 1529 | +1.527 ns, -138 LUTs |
| sampler_y | -4.470 / 1769 | -4.230 / 1483 | +0.240 ns, -286 LUTs |
| sampler_a | -2.891 / 932  | -3.337 / 1058 | **-0.446 ns, +126 LUTs** |

## Structural rewrites compose; fanout attributes may invert
rejection_s (constant-LUT collapse) and rejection_y (sign-select +
explicit shifter) transfer their full block-level gains into composition
— sampler_s reproduces the block delta exactly; sampler_y's LUT saving
grows (-251 block -> -286 composite).

rejection_a's optimization was (* max_fanout = 16 *) on SIPO_IN and
sipo_out_len: +0.076 ns at block level, INVERTED to -0.446 ns / +126 LUTs
in composition. Diff confirms the attributes are the only delta. Forced
replication is placement/context-sensitive; inside the wrapper, Vivado's
cross-boundary optimization interacts with the replicas destructively.
The attribute also sat on sipo_out_len_next, a combinational always@(*)
reg — violating the documented rule, unenforced at the time.

## Actions
- rejection_a reverted to pristine in tracked sources (composition is the
  deployment truth; the block-level +0.076 was not worth carrying).
- Policy demotion: max_fanout wins are context-conditional and must be
  re-validated at the composition level before being kept. Structural
  rewrites (flag-precompute, constant-LUT, sign-select) have no such
  caveat on current evidence (n=3 composites).
- Orchestrator v2 backlog: enforce the no-combinational-reg rule in code;
  add composite-level re-measurement as an accept criterion for
  attribute-only edits.
