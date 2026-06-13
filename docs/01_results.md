# Results

All optimizations below are KAT-verified at HQC-128, 192, and 256, and are
cycle-schedule neutral: none changes the number of clock cycles for any
operation, and none introduces a data-dependent timing path that was not
already present in the baseline.

## Verified optimizations

The optimizations cluster into three mechanisms, described in detail in
[02_optimization_taxonomy.md](02_optimization_taxonomy.md). In brief:

- **Precompute-by-increment (flag):** a combinational comparison on a counter
  (for example `count < LIMIT`) is replaced by a registered flag updated in
  lockstep with the counter at each of its assignment sites. The comparison
  leaves the critical path; the flag is read directly from a flip-flop.
- **Strength reduction (incremental function):** the generalization of the
  above to any value that is a pure incremental function of a counter. The
  canonical case is replacing a combinational divide-by-constant with a
  maintained quotient/remainder pair.
- **Memory retargeting:** moving a small or feedback-bound memory off a
  block-RAM primitive into distributed (LUT) RAM, removing a block-RAM
  access from the critical path.

| # | Name | Mechanism | Cluster cleared |
|---|------|-----------|-----------------|
| 4 | `rd_at_last` propagation | flag | end-of-context decode, encap/decap copies |
| 5 | `wr_in_range` flag | flag | write-address range compare |
| 6 | `MSG_MEM` to distributed | memory | 4-word message memory block-RAM access |
| 7 | `mod_weight_minus_1` registered | flag | minus-one decode |
| 8 | `cnt_lt_mu` flag | flag | hash-input count vs HASH_M_U |
| 9 | FFT FIFO to distributed | memory | butterfly feedback self-loop |
| 10 | `cnt_lt_rb` flag (+ #8 straggler) | flag | hash count vs HASH_RAMBITS (`<`) |
| 11 | `cnt_le_rb` flag | flag | hash count vs HASH_RAMBITS (`<=`) |
| 12 | divider strength reduction | strength reduction | Reed-Muller address divide-by-COPIES |
| 13 | `mod_weight_zero` registered | flag | last combinational write-counter decode |
| 14 | `wc_lt_W` flag | flag | weight-counter compare (blocking-assign counter) |
| 15 | `cr_lt_lim` flag | flag | reduction-counter compare (read-side) |

(Wins 1–3 predate this documentation set and established the baseline
methodology; see `findings/` for the early experiments.)

## Cross-level worst negative slack (WNS), post-optimization

Worst-case slack at the 5.000 ns (200 MHz) constraint, out-of-context. Negative
is failing; closer to zero is better.

| Operation | HQC-128 | HQC-192 | HQC-256 |
|-----------|---------|---------|---------|
| keygen    | -0.091  | -0.041  | -0.084  |
| encap     | -0.685  | -0.525  | -0.249  |

keygen is within roughly 0.1 ns of full timing closure at every security level.
encap's remaining slack is dominated by placement-bound memory-write paths, not
logic depth (see below and the taxonomy).

### What remains is not logic depth

After the optimizations above, the surviving critical paths on every keygen and
encap board terminate at memory primitives (block-RAM data/address pins) or
trace through high-fanout broadcast nets. These are characterized by high
routing fraction (70 percent or more of the path delay is interconnect) and low
logic-level counts. They are addressed by floorplanning, register/net
duplication, or boundary pipelining, not by reducing combinational depth. The
decap operation's dominant cluster is the clearest example and is characterized
formally in [findings/decap_cluster_characterization.txt](findings/decap_cluster_characterization.txt).

## Measured PPA deltas

Resource deltas versus the pre-optimization baseline (HQC-128, out-of-context).
All wins are cycle-count neutral, so dynamic-energy-per-operation moves with
utilization rather than with cycle schedule.

| Operation | LUT delta | FF delta | BRAM delta | Notes |
|-----------|-----------|----------|------------|-------|
| keygen | +28 | +3 | 0 | roughly +2 percent LUTs |
| encap  | +100 | +36 | -0.5 | roughly +3.8 percent LUTs; half a block-RAM freed |
| decap  | +104 | +52 | -1.5 | roughly +1.4 percent LUTs; 1.5 block-RAMs freed |

DSP usage is zero before and after, on every module and every level.

The pattern is the expected one for the flag mechanism: a small number of
flip-flops are added (one per flag, plus the flag's update logic) in exchange
for removing combinational comparison logic from the critical path. The memory
retargets trade a block-RAM primitive for a modest number of LUTs configured as
distributed RAM, which is why BRAM count falls while LUT count rises slightly.

For the interpretation of these deltas in an ASIC context, where the FPGA-
specific block-RAM-versus-LUT distinction does not exist, see
[03_asic_ppa_analysis.md](03_asic_ppa_analysis.md).
