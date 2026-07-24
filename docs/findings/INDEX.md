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
| crossdesign_closure | I/W | True-closure A/B: HQC joint +1.9% win vs ML-DSA block-first null; thesis: top-down target selection composes, block-first doesn't |

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

## Chip-level ledger (post-route closure, grade -1, ExtraTimingOpt/Explore/Explore recipe)

| Build | Closing fmax | LUT | FF | Power @ closure |
|---|---|---|---|---|
| combined_top pristine (14.25ns) | 70.2 MHz | 52987 | 29081 | 1.286 W |
| combined_top optimized, pre-banked | 73.4 MHz | — | — | — |
| combined_top banked encoder (12.09ns) | **82.7 MHz** | 53597 | 30123 | 1.480 W* |

Banked vs pristine: +17.8% fmax, +1.2% LUT, +3.6% FF.
*Power for the banked build is still the 12.73 ns figure and needs a re-pull
at 12.09 ns. Energy-per-operation claims remain HELD pending the SAIF/VCD
flow (see PPA_mldsa_fullchip).
HQC ledger in the ICCAD abstract Table I.
