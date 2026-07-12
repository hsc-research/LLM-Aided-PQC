# ML-DSA gen_c: sample_addr Precompute — Largest Single-Block Timing Win of the Latency-Preserving Tier

Documents the gen_c (SampleInBall) sample_addr precompute win:
WNS -5.029 -> -3.307 ns (+20.8% fmax), full-KAT 25/25 PASS, latency-
preserving. This was gen_c's second accepted edit; the autonomous
orchestrator's earlier campaign had landed max_fanout=16 on dout_buffer
(-5.233 -> -5.029) and then correctly closed at no_action — the lever it
had was exhausted. This edit came from human-in-loop analysis of the
residual path and is attributed as a guided win, not an autonomous one.

---
## 1. The path
Post-max_fanout residual critical path (82.5% route, 9 levels):
`dout_buffer[35]` -> combinational byte-select into `sample_addr`
(`dout[{4'd7-ctr[2:0],3'd0}+:8]`, an 8-way byte mux indexed by ctr) ->
fan-out through the 256-way C_POLY accept/write decode
(`C_POLY[sample_no] <= C_POLY[sample_addr]`, the Fisher-Yates swap).
Two expensive structures back-to-back in one cycle: byte mux, then a
256-deep indexed read AND write decode both driven by the mux output.
max_fanout had already replicated the source register; the mux + decode
depth itself was untouched by any prior lever.

## 2. The edit
Register the byte-select result one cycle ahead:
```verilog
(* max_fanout = 16 *) reg [7:0] sample_addr_r = 0;
...
sample_addr_r <= dout[{4'd7-ctr[2:0],3'd0}+:8];       // steady state
sample_addr_r <= dout[{4'd7-ctr_next[2:0],3'd0}+:8];  // ctr-advance cycle
...
sample_addr = sample_addr_r;  // consumer: now a registered 8-bit value
```
The 256-way decode now starts from a clean registered 8-bit address; the
byte mux runs in the *previous* cycle with the whole period to itself.

## 3. Why it is latency-preserving (the correctness argument)
This is the flag_precompute pattern generalized to an address:
`dout_buffer <= dout` every cycle, so the value selected from `dout` at
cycle t equals the value selected from `dout_buffer` at cycle t+1 — the
precomputed register holds a provably identical value to what the
combinational mux would have produced, one cycle later, on the same
consuming cycle. Two ctr phases (steady / advance) each select with the
index that will be current when the value is consumed. No cycle schedule
changes, no gate modification needed; verified by the existing gen_c
lockstep gate AND full-KAT 25/25.

## 4. Result
- Full-KAT: 25/25 PASS, sec_lvl 2/3/5.
- OOC synth: WNS -5.029 -> **-3.307 ns** (fmax +20.8%), cost +268 LUTs
  (decode replication off the registered address).
- gen_c was the worst block on the board pre-edit (-5.233 at campaign
  start); it is now better-placed than decoder (-4.756) and rejection_y
  (-4.230).

## 5. Placement in the strategy taxonomy
Extends flag_precompute from 1-bit flags (makehint's hint_needed) to
multi-bit registered addresses. Orchestrator prior to encode: when a
route-heavy path runs mux -> wide indexed decode and the mux inputs are
one register behind an every-cycle-copied source (X_buffer <= X), the
mux result can be registered from the source one cycle early with a
provable value-identity argument. The residual gen_c path after this win
has not been re-extracted; the serial Fisher-Yates RMW architecture
remains the known architectural ceiling beyond it.
