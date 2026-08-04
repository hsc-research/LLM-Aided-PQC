# Findings Index

One-line map of every findings document. W = accepted win, N = documented
negative, I = infrastructure/process. Full details in each file.

## ML-DSA (docs/findings/mldsa/)

| Doc | Tag | Summary |
|---|---|---|
| fullkat_gate | I | Full-design 75-vector NIST KAT outer gate via xsim; corruption-validated; per-vector logging; 600s timeout handling |
| pipelining_coeff_decomposer | N/I | Block pipeline cut regressed (-1.247→-1.688); latency-tolerant block gate validated (reusable); redirected to sub_val lead |
| coeff_decomposer_decomp_map1 | N | Placement-coupled restructurings failed 5 ways; block closed for restructuring |
| cd_width_narrowing | W | 56b→28b reg narrowing: WNS -1.247→-1.196, LUT -21%; refined narrowing policy rule (logic-bound + written bound proof) |
| butterfly_dsp_pipeline | W | Round-1 mult_p PREG stage: -3.802→-3.280; first latency-changing win; MULT drain root cause |
| butterfly_round2_areg | W | Round-2 INTT sub_r AREG: -3.280→-2.793 (+12.9% cumulative fmax); chained-stage ×2 retap rule |
| latency_orchestrator_v0 | I/N | Autonomous latency tier: divergence-guided repair steers tap derivation but not insertion-point choice; Sonnet 12 calls no win vs Opus 1 call correct refusal ($0.245); butterfly closed |
| gen_c_autonomous | W | Autonomous max_fanout win on gen_c (orchestrator-discovered) |
| gen_c_sample_addr | W | sample_addr precompute 1 cycle ahead: -5.029→-3.307 (+20.8% fmax) |
| fanout_load_profile | W/N | gen_c FSM fanout -3.307→-1.264 (project record +2.043ns) + makehint N=8; load-profile rule: narrow reg + homogeneous CE bank pays, wide/heterogeneous loses |
| precompute_boundaries | W/N | decoder ENCODE_LVL_r + rejection_y ge-flag wins; 4 negatives incl. loop-endpoint rule (usehint ctr) |
| gate_catch_rate | I/W | 59 LLM calls -> 33 applied -> 14 functionally incorrect; 4/23 latency-preserving vs 10/10 latency-changing; the measured case for correctness gating |
| policy_v2_insertion_point | I/N | POLICY v2 rendezvous rubric: insertion-point selection 0/12 to 4/4 post-rule (log-verified); all 4 edits still failed downstream (3 anchor, 1 gate) |
| decoder_usehint_autonomous | W | Autonomous decoder win; usehint characterization |
| decoder_s_lut_negative | N | S-mode constant-LUT regressed; binding mode is T0/Z; constant_lut excluded for domain width |
| decoder_signselect_negative | N | T0/Z sign-select regressed at 13-20b; strategy excluded on explicit-compare ternaries at ALL widths; board closed under taxonomy |
| composition | W/N | Structural rewrites compose intact (+1.53ns transfers exactly); fanout attribute inverted in composition and was reverted |
| rejection_makehint_session | W | rejection_s/y + makehint latency-preserving wins |
| board_closure | I | Latency-preserving tier closure rationale per block |
| repro_and_pristine_integrity | I | Synthesis determinism (3× bit-identical, 7ps delta real); pristine-tree contamination found/fixed, no results invalidated |
| fullchip_integration | I | First combined_top synthesis (39 V + 11 VHDL); chip critical path = encoder PISO merge, invisible to block OOC; GMU 116MHz methodology comparison |
| postroute_acceptance | I | Measurement law: post-synth chip compares mislead (sign errors); post-route is the only chip judge; optimized beats pristine at every corner post-route |
| postroute_ppa | I/W | Post-route chip PPA flow (impl_runner power/util); iso-frequency power at 15.31ns, both MET: 1.198W vs 1.213W (+1.3%) at ~66 MHz. NOTE: the 5.0ns and 8.6ns Fmax figures in this doc are 1/(period-WNS) PROJECTIONS from violated runs and are invalid per FINDINGS_crossdesign_closure; use the closure ledger below |
| flow_directive_sweep | W/I | Tier-3 flow-space search: directive sweep infra; agent autonomously found new-best (101.5) at $0.016 |
| encoder_campaign | W/N | 4-angle encoder RTL campaign: mode/lvl precompute kept (-2.900→-2.837); piso_len fanout regressed; insert-delay gate-caught occupancy-unsafe; skid excluded by capacity measurement |
| encoder_insert_delay | N | stripped_r insert delay: occupancy-unsafe under backpressure (unbounded AXI stall); occupancy-probe method established |
| DESIGN_encoder_banked_piso | I | Vector 2 design doc: banked word-aligned ACC+FIFO replacing 256b variable-shift PISO; 200MHz verdict (not reachable on -1; ~140-165 ceiling on -3); advisor sign-off doc |
| precompute_boundaries | W/N | (see above) |

## HQC (docs/findings/hqc/)

| Doc | Tag | Summary |
|---|---|---|
| fixed_weight_pipeline | W | Showpiece: fixed_weight -2.064→+0.122 (141→205 MHz) |
| barrett_dsp | W/N | Barrett reduction DSP findings |
| poly_mult_ramwidth | W | Memory-retarget family win |
| decap_encap_crossmodule | I | Cross-module characterization |
| decap_topN_recon | I | Decap path recon; decap closed (placement-bound) |
| hqc_transfer_v0 | I/N | Transfer orchestrator v0: ML-DSA POLICY verbatim on HQC; correct rule application, honest marginal reverts, gate-caught false positive |
| transfer_v1_and_policy_v2 | W/I | First autonomous cross-design win (decap flag_precompute +0.726ns, $0.037); POLICY v2 rendezvous rubric closed insertion-point gap; CE-pin prior refinement |
| joint_propagation | I/W | a1a7ad2 silently reverted the joint composition to pristine for 3 days (untracked build tree + stage() regeneration); restored, 114.8 -> 116.0 MHz true closure; HQC now binds on shared Keccak state RAM, 4 of 5 worst paths |
| keccak_transfer | I | Keccak symmetric-primitive transfer experiments (Malik datapoint) |

## Cross-design (docs/findings/)

| Doc | Tag | Summary |
|---|---|---|
| crossdesign_closure | I/W | True-closure A/B: HQC joint win vs ML-DSA block-first null; thesis: top-down target selection composes, block-first doesn't. NUMBERS SUPERSEDED, see HQC chip ledger below (+5.8%) |

## Current WNS ledger (Artix-7 OOC, 200 MHz) — measured 2026-07-11, all deterministic (3×-verified flow)

| Block | Base | Final | Status |
|---|---|---|---|
| makehint | -3.511 | -0.485 | precompute (-0.640) then fanout N=8 |
| coeff_decomposer | -1.247* | -1.196 | routing-bound residual |
| gen_c | -5.233 | -1.264 | +58% fmax cumulative |
| rejection_s | -4.013 | -2.486 | internal-merge-bound |
| usehint | -2.542 | -2.542 | self-loop, closed |
| butterfly | -3.802 | -2.793 | DSP floor, closed (2 DSP) |
| rejection_a | -2.933 | -2.933 | fanout win deliberately reverted (composition inversion), closed |
| rejection_y | -4.470 | -3.511 | internal-merge-bound |
| decoder | -4.806 | -4.299 | architectural residual |
| encoder (banked) | -2.900 | -2.288 | Vector 2 architectural rework; best encoder OOC |

*coeff_decomposer base shown post sign_select win (true pristine base predates
current ledger; the earlier failed pipeline attempt measured -1.688).

## ML-DSA chip-level ledger (post-route closure, Artix-7 xc7a200tfbg676-1 grade -1)

Recipe fixed in `fmax_search.py`: ExtraTimingOpt / Explore / Explore.
Closure is binary search to minimum MET period. Never projected.

### CANONICAL: out-of-context flow

Measured 2026-08-03. Both arms: `-mode out_of_context`, regen period 8.600 ns,
bracket 12.0-16.0 ns, same commit. Fmax and utilization from the same run.

| ID | Arm | Closing period | Fmax | Slice LUT | LUT as Mem | Slice Reg | Slice | BRAM | DSP | WNS | Log |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | baseline (`combined_top_pristine`) | 14.25 ns | 70.2 MHz | 53127 | 1319 | 29079 | 16111 | 29 | 16 | +0.027 | `logs/closure/mldsa_ooc_20260803/fsrch_chipv2_mldsa_baseline_1244_14.25.rpt` |
| M2 | optimized (`combined_top`, banked encoder) | 12.43 ns | 80.5 MHz | 53543 | 1363 | 30078 | 16205 | 29 | 16 | +0.029 | `logs/closure/mldsa_ooc_20260803/fsrch_chipv2_mldsa_5372_12.43.rpt` |

**M2 vs M1: +14.7% Fmax, +0.8% LUT, +3.4% FF, BRAM and DSP unchanged.**

Power is HELD for both arms. `fmax_search.py` emits `report_utilization` only,
and vectorless power in OOC excludes I/O and assumes default switching
activity. Energy-per-operation claims remain gated on the SAIF/VCD flow
(see PPA_mldsa_fullchip).

Binding path moves between arms, which is the mechanism:

| Arm | Worst path at closure |
|---|---|
| M1 | `DECODER/encode_mode_reg[1]/C` -> `ENCODER/PISO_reg[117]/D` |
| M2 | `ctr0_reg[1]/C` -> `CHALLENGE_SAMPLER/C_SIPO_reg[426]/R` |

The baseline binds in the encoder cone. After the banked encoder rewrite the
design binds on the challenge sampler instead.

### RETIRED: pinned flow

Not for citation. Retained to document flow-mode sensitivity.

| Arm | Closing period | Fmax | Slice LUT | Slice Reg | Power |
|---|---|---|---|---|---|
| pristine | 14.25 ns | ~~70.2 MHz~~ | 52987 | 29081 | 1.286 W |
| optimized, pre-banked | — | ~~73.4 MHz~~ | — | — | — |
| optimized, banked encoder (12.09 ns) | | ~~82.7 MHz~~ | 53597 | 30123 | 1.480 W |

~~Banked vs pristine: +17.8% fmax.~~

These ran before commit `23c5672` put `regen_ckpt` into out-of-context mode,
so the checkpoint was built in Vivado's default pinned mode: every top-level
port assigned a package pin, I/O buffers inserted, placement constrained
toward the die periphery.

### Why the OOC numbers are canonical

The pinned optimized figure is higher (82.7 vs 80.5), so this is a retraction
to a smaller result. The reasons:

1. **Both ML-DSA arms share one configuration only in OOC.** The pinned
   baseline and pinned optimized closures were not run under a single verified
   flow, and the pinned optimized run reported a different binding cone
   (`FSM_sequential_cstate2_reg[0]_rep__0_replica/C` -> `start_op_reg[0]/D`,
   verdict NO_TARGET, out-of-scope cone) than either OOC arm.
2. **HQC is measured in OOC and cannot be measured otherwise.** The HQC joint
   top has 1611 I/O, which overflows package pinning. Reporting ML-DSA pinned
   and HQC OOC would mean the two designs in the same paper use different
   flows.
3. **Area is flow-mode-insensitive; only timing moved.** Pinned and OOC
   utilization agree within 0.3% (53127 vs 52987 LUT, 29079 vs 29081 FF). The
   ~3% Fmax gap is the flow mode, not a different design.
4. **OOC is the correct mode for the claim being made.** These are accelerator
   cores intended for integration, not standalone parts on this package.

Minerva TP_Opt reports 83.33 MHz optimized and 70.42 MHz pristine in its own
separate flow (LUT ~57.4k, materially different from both tables above). Both
snapshots carry `is_complete="0"`. Minerva is a third measurement
configuration and is not a Result of Record.

## HQC chip-level ledger (post-route closure, joint KEM, Artix-7 -1, OOC)

**Canonical. Measured 2026-08-03 at commit 6351cac. Reproduce with:**
Recipe is fixed in `fmax_search.py`: ExtraTimingOpt / Explore / Explore,
regen period 8.600 ns, bracket 6.0-10.0 ns, accept only WNS >= 0.

| Build | Closing fmax | WNS | LUT | LUT-mem | FF | BRAM | DSP |
|---|---|---|---|---|---|---|---|
| `hqc_joint_pristine` (9.12 ns) | 109.6 MHz | +0.072 | 13045 | 1019 | 6765 | 21 | 4 |
| `hqc_joint_opt` (8.62 ns) | **116.0 MHz** | +0.006 | 13331 | 1075 | 6887 | 19.5 | 4 |

Optimized vs baseline: **+5.8% fmax**, +2.2% LUT, +1.8% FF, -7.1% BRAM.
The BRAM reduction is the memory-retarget wins (MSG_MEM, FFT FIFO to
distributed RAM), which is also why LUT-as-memory rises.

**Binding path moves between arms**, which is the mechanism, not a side note:

| Build | Worst path at closure |
|---|---|
| baseline | `DECAP/DECRYPT/V_MINUS_UY/uv_addr_0_mul_reg[1]/C` -> `POLY_MULT/dshift_reg[35]/D` |
| optimized | `SHAKE256/control_path/counter_reg[5]/C` -> `SHAKE256/data_path/state_ram/.../SP/I` |

The agent's one accepted HQC edit (flag_precompute on `v_minus_uy`, commit
`12d930d`, $0.037, one API call) sits on the baseline's binding path. After
the edit the design binds on the shared Keccak state RAM instead, which the
rule set does not address.

**FPGA-neutrality control.** The baseline was re-closed on pre-port-fix RTL
(commit `cd92639`, before the five cross-tool portability fixes) and
reproduced 9.12 ns / 109.6 MHz / WNS +0.072 exactly. The declaration
reorderings are therefore FPGA-neutral, and the normalized RTL is the common
source artifact for both backends.

### Superseded HQC numbers, do not quote

| Number | What it actually was | Why superseded |
|---|---|---|
| 117.1 / 119.3 MHz | pre-`a1a7ad2` pair | Different regen period, configuration not recorded, not comparable |
| 114.8 MHz | **the optimized arm while its composition was silently reverted** by `a1a7ad2`, not a baseline | Measured a design that was pristine in everything but name |
| 116.0 MHz (as "vs 114.8") | correct value, wrong comparator | 114.8 is not the baseline; the baseline is 109.6 |

Before 2026-08-03 no properly measured HQC pristine baseline existed. That is
the root cause of every prior discrepancy in these numbers.

### Open question, recorded rather than resolved

The pre-`a1a7ad2` pristine measurement read 117.1 MHz; today's reads 109.6 MHz.
Both are genuine pristine closures. The difference is 7.5 MHz and **we cannot
currently explain it.** The regen period differed and was not recorded for the
earlier run, so the two started from different synthesized netlists, but that
is a hypothesis and not a verified cause.

What is established: today's pair was measured under one recorded command at
one commit, and both arms reproduced exactly on re-run (baseline twice at
9.12 ns, optimized matching a prior 8.62 ns measurement). That is why it is
the canonical pair.

What is not established: whether 117.1 was optimistic, whether the current
regen is pessimistic for the baseline, or whether the two measure meaningfully
different netlists. Reproducing the earlier configuration would settle it and
has not been done.

## ASIC (docs/findings/asic/)

| Doc | Tag | Summary |
|---|---|---|
| 2026-07-30_genus_asic_port | I | **SUPERSEDED (GPDK045).** Genus bring-up, F1 use-before-declaration, F2 memory blackboxing (later reversed), F3 effort sensitivity 10.9% |
| 2026-07-31_defect_survey | I | 13 of 59 HQC files carry cross-tool RTL portability defects, confirmed by Genus and an independent static checker; 102 instances |
| 2026-07-31_vmu_arm_comparison | N | **SUPERSEDED (GPDK045).** F6 the one accepted HQC edit does not transfer at ASIC block level; arms invert with constraint tightness |
| 2026-07-31_mldsa_genus_port | I | F8 same defect class in ML-DSA (different codebase), F9 mixed blocking/non-blocking, F10 mixed-language design, VHDL package read order is load-bearing |
| 2026-08-02_asap7_transition | I | **CURRENT.** A1-A4 retracted (library change to ASAP7 7nm); F11 memories now flip-flop arrays; F12 a search must prove its lower bound violates; F13 unconstrained static inputs capture the critical path; F14 reference flow validated |
