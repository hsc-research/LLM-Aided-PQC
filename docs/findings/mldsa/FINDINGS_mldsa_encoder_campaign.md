# FINDINGS: encoder campaign — chip bottleneck attacked from 4 angles, closed at RTL level

Chip-level critical path (both 5.0ns and 8.6ns clocks, pristine and optimized):
DECODER length/mode regs -> cross-module handshake -> encoder 256-bit variable
shift -> PISO_reg fanout (19-20 levels, ~72% route). Four angles tried, each
adjudicated by measurement:

1. stripped_r insert delay (+1 insert latency): gate-caught under backpressure
   — PISO occupancy-unsafe (see FINDINGS_mldsa_encoder_insert_delay.md).
2. piso_len max_fanout: block -2.900 -> -4.334 REGRESSED — heterogeneous
   arithmetic loads, load-profile rule confirmed in the negative direction.
3. mode/lvl precompute (mode_r, lvl_r2, per-use aligned to the data pipes):
   CORRECT and kept. Gate PASS incl. new mode-switch coverage (TB extended
   with same-cycle mode+valid sequences; corruption-validated against a
   mode-lag corruption the old configs provably missed). Block -2.900 ->
   -2.837; chip -6.445 -> -6.418 (8.6ns). Cut the encode_mode segment off the
   cone (path start moved DECODER/encode_mode -> DECODER/sipo_in_len),
   chip-level gain within noise.
4. Output skid buffer (registered ready): EXCLUDED by capacity measurement
   before any design work — instrumented max PISO occupancy under real KAT
   stimulus is 156 bits; skid safety requires occ_max + 2x80 <= 256, i.e.
   occ_max <= 96. Also documented: pristine's own overflow safety under
   indefinite AXI stall rests on FSM drain discipline, not local backpressure
   (encoder ready_i=1 unconditionally).

Conclusion: encoder's residual cone is architectural (PISO organization /
interface redesign), consistent with GMU's published statement that the
design's critical path is interconnect-bound. This is the boundary exemplar
for the papers. Occupancy instrumentation via the full-KAT gate (candidate-
copy $display probe) is a reusable capacity-proof method.

GMU flow gap (their 116 MHz post-P&R vs our 87-89 synth-only OOC at 8.6ns)
remains open — a post-P&R or directive-sweep run is the comparison to make
before quoting chip numbers against theirs.
