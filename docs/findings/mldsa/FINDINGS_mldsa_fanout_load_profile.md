# ML-DSA Session: The Fanout Load-Profile Cue — gen_c's +2.0 ns Win and Its Boundary Conditions

Four committed wins this session — gen_c cstate fanout (+2.043 ns, the
largest single-edit timing gain of the entire project), rejection_y
ge-flags (+0.719), decoder ENCODE_LVL_r consumers (+0.183, on top of the
earlier +0.274), makehint num_hints fanout (+0.148) — plus two further
negatives that, together with the wins, pin down exactly when the
max_fanout lever pays. All kept results full-KAT 25/25 verified; all
negatives reverted. (The session's earlier wins/negatives through the
rejection_s skid buffer are in FINDINGS_mldsa_precompute_boundaries.md;
this doc covers the fanout arc that followed.)

---
## 1. gen_c cstate: +2.043 ns from one attribute
Post-sample_addr residual path: FSM `cstate` (4-bit) fanning into the
256-way C_POLY write-enable decode, 81.9% route, 7 levels, -3.307.
Edit: `(* max_fanout = 16 *)` on `cstate, nstate` — attribute only,
logic-identical, gate trivially PASS. Result: **WNS -3.307 -> -1.264**
(fmax 132 -> 159.6 MHz, +21%), resynth-verified bit-identical (stable,
not tool jitter). gen_c's full arc across all sessions:
-5.233 -> -1.264, +58% fmax cumulative, via three edits (max_fanout
dout_buffer, sample_addr precompute, max_fanout cstate).

## 2. makehint num_hints: -0.633 -> -0.485
Same profile: num_hints (8-bit) -> 80-way hint_addr CE decode. Vivado
was already auto-replicating (`_rep` cells in path reports) but an
explicit `max_fanout = 8` beat the auto result: -0.633 -> -0.485
(fmax 182.3). Swept 4: worse (-0.495) — 8 is the optimum; forcing
tighter adds replication overhead past the routing benefit. makehint is
now the closest block to timing-met on the board.

## 3. decoder ENCODE_LVL_r consumer extension: -4.482 -> -4.299
The remaining combinational `4*ENCODE_LVL` consumers (ready_i, the
di_shift amount, the sipo_in_len update) were swapped to the registered
`{ENCODE_LVL_r, 2'b00}` — same provably-equal value, three anchors,
-12 LUTs. Deeper len-flag precompute was evaluated and deliberately
skipped: decoder's len has three branch-dependent update sites, so the
flag registers would need replicated branch logic — complexity past the
expected gain on a secondary cone.

## 4. Negative: decoder SIPO_IN fanout (reverted)
`max_fanout = 16` on the 192-bit SIPO_IN register: -4.482 -> -4.617,
+325 LUTs. Each SIPO_IN bit feeds only a few transform slices — there
was no per-bit fanout to break; replication was pure overhead.

## 5. Negative: gen_c ctr fanout (reverted)
After the cstate win, gen_c's new #1 was ctr -> sample_addr_r (the byte
mux select). `max_fanout = 16` on `ctr, ctr_next`:
**-1.264 -> -3.769** — the worst regression of the project from an
attribute. ctr's loads are heterogeneous (mux select + FSM arithmetic +
comparison logic); constraining all of them destroyed the placement that
the cstate win depended on. gen_c restored to -1.264.

## 6. The load-profile rule (the transferable output)
Combining wins 1-2 with negatives 4-5 and every prior fanout datapoint
(rejection_a's +0.076 win, its composition inversion, two combinational-
reg regressions, decoder encode_mode's earlier +0.050):
- max_fanout PAYS on a **narrow register whose loads are homogeneous**
  — one wide, uniform structure (CE decode, write-enable bank). The
  narrower the reg and the wider/more uniform the load bank, the bigger
  the win (4-bit cstate -> 256 CEs: +2.0 ns; 8-bit num_hints -> 80 CEs:
  +0.15 ns).
- max_fanout LOSES on wide registers (per-bit loads are already few)
  and on registers with **heterogeneous loads** (mux selects mixed with
  arithmetic and control), where the blanket constraint disturbs
  placement that other paths depend on.
- Explicit attributes can beat Vivado's auto-replication (makehint),
  and the optimal N is empirical per-site (8 vs 16 both have wins;
  sweep one step once a direction is found).
Orchestrator classifier cue to encode: from the path report, dest=CE
across a numbered register array + a narrow source register => propose
max_fanout with high confidence; heterogeneous dest kinds across the
top paths from one source => do not.

## 7. Board after this session (WNS, Artix-7 OOC, 200 MHz)
makehint -0.485 | coeff_decomposer -1.196 | gen_c -1.264 |
rejection_s -2.486 (internal-merge-bound) | usehint -2.542 (ctr-loop) |
butterfly -2.793 (closed) | rejection_a -2.857 (family) |
rejection_y -3.511 (now internal-merge-bound like s/a) |
decoder -4.299 (residual: per-mode transform cone).
The narrow->homogeneous-CE profile has no remaining unclaimed instance
identifiable from current path boards; residuals are family-closed
merges, self-loops, near-floor blocks, or the decoder transform cone
(the one remaining rich target, but per-mode arithmetic — a different
lever class than anything validated so far).
