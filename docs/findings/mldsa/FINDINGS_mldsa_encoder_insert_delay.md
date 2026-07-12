# FINDINGS: encoder stripped_r insert delay — unsound, excluded

Registering zero_strip's output (+1 insert latency, pipes retapped) passed
continuous-flow gating but FAILED under backpressure: PISO can legitimately
approach full occupancy in-system (combined_top wires ready_o_enc to external
AXI, unbounded stall; encoder asserts ready_i=1 unconditionally), and the +1
delay moves the overflow-clip boundary, dropping a word. Rule: input-side
insert delay on an occupancy-limited SIPO/PISO with unconditional ready_i is
EXCLUDED unless occupancy is provably bounded below capacity minus one insert.
The latency-tolerant encoder gate (18 configs, gold-vs-candidate) caught this
exactly at the stall interaction; continuous-only testing would have accepted
a broken edit. Chip-level path (piso_len -> PISO fanout) remains the target;
next angles must not delay the insert.
