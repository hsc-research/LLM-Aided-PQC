# Paper update checklist (reference when writing)

## ICCAD SRC abstract (Overleaf .tex) — DUE JUL 31
- [ ] Chip headline: +11.2% post-route fmax at 200MHz stretch target (65.3 -> 72.6 MHz, -1 grade)
- [ ] Post-synth/post-route inversion: deterministic post-synth regression (-0.217ns, N=3 bit-identical) INVERTS to a win post-route -> post-route is the only valid chip judge
- [ ] Third tier: flow-directive optimization (+5.3% at GMU corner, zero RTL change; constraint-target sweep = checked null)
- [ ] PPA: +11.2% fmax for -0.3% LUT / +4.2% FF / +2.8% power; iso-frequency power within 1.4% (~1% per-op energy)
- [ ] Keccak transfer: correct refusal after full-menu exploration on shared primitive; new RAM-macro policy rule derived
- [ ] Keep: three-tier model attribution, controlled-case-study framing, priors-as-artifact
- [ ] Current numbers: gen_c -1.264, makehint -0.485, rejection_y -3.511, decoder -4.299, butterfly -2.793

## IEEE D&T draft v0.2 -> v0.3 content pass — DUE AUG 15
- [ ] Results section: replace all pre-integration numbers with post-route four-corner table (-1 5.0ns, -1 8.6ns, -3 8.62ns + directive-searched 101.5)
- [ ] New section/subsection: post-route acceptance rule (the inversion story, variability N=3)
- [ ] New subsection: flow-space tier (directive sweep both corners, constraint-dependent optimum, constraint-target null)
- [ ] PPA table incl. iso-frequency power + the two honest power framings
- [ ] GMU comparison: full decomposition (grade -> directives -> device family ZCU102 vs Artix-7 — VERIFY their exact device from ePrint 2021/1451 before citing)
- [ ] Encoder campaign: 4-angle closure (occupancy-unsafe insert, fanout regression, kept mode-precompute, capacity-excluded skid) as the boundary exemplar
- [ ] Keccak transfer section (Malik's shared-primitive question answered; rho-folded architecture analysis)
- [ ] Butterfly full metric table (delay/fmax/latency/regs — advisor format)
- [ ] Terminology sweep: latency-preserving / agent-assisted / controlled case study / cross-design transfer evidence
- [ ] Falcon related-work: cite arXiv 2602.09410 (LLM generates FALCON HW) and differentiate (we optimize existing verified RTL, model-untrusted, gated)
