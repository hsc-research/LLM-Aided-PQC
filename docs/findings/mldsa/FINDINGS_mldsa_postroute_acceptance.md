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
