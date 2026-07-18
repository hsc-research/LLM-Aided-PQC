# DESIGN: banked PISO for encoder (architectural tier, manual specimen)

## Problem (measured)
Chip closure bound by encoder cone at every corner: 19-20 levels, ~72% route,
256-bit variable shift `stripped << piso_len_next` (10-bit amount) + 256-wide
PISO D fanout. RTL menu closed (4-angle campaign).

## Design
Replace monolithic PISO with:
- ACC[143:0], acc_len[7:0]: insert `stripped << acc_len` — shift amount < 64
  after word-pop invariant, width 144 = 80 (max insert) + 64 (word)
- FIFO 4 x 64b (simple regs, CE loads, no shift): when acc_len >= 64, pop
  ACC[63:0] -> FIFO, ACC >>= 64 (FIXED shift), acc_len -= 64
- dout = FIFO head; valid_o = !fifo_empty
Variable shifter: 256-wide/10-bit -> 144-wide/6-bit. PISO fanout eliminated.

## Latency/occupancy
+1 cycle insert->dout (via FIFO). Latency-tolerant gate verifies. Capacity:
144 + 256 = 400 bits >> measured max occupancy 156. FIFO depth 4 sufficient
(worst burst 156/64 = 3 words).

## Verification plan
encoder_equiv_gate (18 cfg + mode-switch, corruption-validated) -> full-KAT
75 -> block synth filter -> closure search on selective composition (judge).

## Contract preserved
Interface identical (di/valid_i/encode_mode/sec_lvl -> dout/valid_o/ready_o).
Same byte stream, same order; timing shifted +1, permitted by consumer
(combined_top drains via ready handshake).
