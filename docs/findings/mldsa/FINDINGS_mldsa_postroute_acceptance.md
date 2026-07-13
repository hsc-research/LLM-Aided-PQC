# FINDINGS: post-route acceptance — block wins DO compose at chip level

Post-synthesis chip comparisons showed the optimized design marginally worse
than pristine (noise), which earlier read as "block wins don't move the chip."
Post-route with phys_opt reverses this: the optimized design wins at every
measured corner.

| Config | Pristine WNS / fmax | Optimized WNS / fmax | delta fmax |
|---|---|---|---|
| -1 grade, 8.60ns | -5.995 / 68.5 MHz | -5.017 / 73.4 MHz | +7.2% |
| -3 grade, 8.62ns | -1.974 / 94.4 MHz | -1.779 / 96.2 MHz | +1.9% |

Corrected acceptance rule: post-synthesis OOC estimates are valid for
block-level filtering, but chip-level accept/reject requires post-route
timing — synthesis-stage chip estimates buried a real +7.2% fmax win in
placement noise.

## GMU comparison resolved
GMU reports 116 MHz (Minerva-searched, post-P&R). Our gap decomposes:
speed grade -1 vs -3 accounts for 68.5 -> 94.1 MHz; constraint targeting
(8.62ns at -3) reaches 96.2 MHz optimized. Residual ~17% is
directive/frequency-search class (Minerva iterates targets; we ran one).
Fair-comparison methodology for the paper: always state part grade, flow
stage, and constraint target.

## Critical path after all edits
Both variants still bind on the DECODER->ENCODER cone. The optimized
variant's path now STARTS at ENCODE_LVL_r_rep (our precompute register,
fanout-replicated) — the RTL-reachable portion of the cone is consumed;
the residual is the cross-module handshake + 256-bit variable shift + PISO
fanout, architectural per FINDINGS_mldsa_encoder_campaign.md.

## GMU comparison alignment checklist (advisor req — verify before citing)
Source: Beckwith et al., ePrint 2021/1451 — cite the exact Artix-7 timing
table/passage and their "critical path is within the interconnect for the
shared Keccak modules" statement with page/table number (VERIFY in PDF).
Alignment to state explicitly in the report:
- Device: theirs Artix-7 (CONFIRM exact part+grade from paper) vs ours
  xc7a200tfbg676-1 (and -3 for the grade study)
- Tool: their Vivado version (CONFIRM) vs ours 2025.2
- Flow: theirs Minerva frequency search, post-P&R vs ours single-target
  post-route (synth default, opt/place/phys_opt/route)
- Clock: theirs searched natural frequency vs ours fixed 8.60/8.62 ns targets
- Hierarchy: same combined_top RTL lineage (ours = their open-source release
  + our committed optimizations)
Unresolved residual after grade+target alignment: 96.2 vs 116 MHz (~17%),
attributed to directive/frequency-search class — quantify via Vector-1
flow sweep before making comparative claims in the paper.
