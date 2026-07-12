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
| decoder_usehint_autonomous | W | Autonomous decoder win; usehint characterization |
| decoder_slut_negative | N | S-mode constant-LUT regressed; binding mode is T0/Z; constant_lut excluded for domain width |
| decoder_signselect_negative | N | T0/Z sign-select regressed at 13-20b; strategy excluded on explicit-compare ternaries at ALL widths; board closed under taxonomy |
| composition | W/N | Structural rewrites compose intact (+1.53ns transfers exactly); fanout attribute inverted in composition and was reverted |
| rejection_makehint_session | W | rejection_s/y + makehint latency-preserving wins |
| board_closure | I | Latency-preserving tier closure rationale per block |
| repro_and_pristine_integrity | I | Synthesis determinism (3× bit-identical, 7ps delta real); pristine-tree contamination found/fixed, no results invalidated |

## HQC (docs/findings/hqc/)

| Doc | Tag | Summary |
|---|---|---|
| fixed_weight_pipeline | W | Showpiece: fixed_weight -2.064→+0.122 (141→205 MHz) |
| barrett_dsp | W/N | Barrett reduction DSP findings |
| poly_mult_ramwidth | W | Memory-retarget family win |
| decap_encap_crossmodule | I | Cross-module characterization |
| decap_topN_recon | I | Decap path recon; decap closed (placement-bound) |

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

*coeff_decomposer base shown post sign_select win (true pristine base predates
current ledger; the earlier failed pipeline attempt measured -1.688).
HQC ledger in the ICCAD abstract Table I.
