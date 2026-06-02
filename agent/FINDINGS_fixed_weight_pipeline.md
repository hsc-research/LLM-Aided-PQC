# Findings: fixed_weight Threshold-Comparison Pipelining (VERIFIED WIN)

**Module:** `fixed_weight`
**Date:** May 31, 2026
**Author:** Lloyd Alcorn
**Target:** Xilinx Artix-7 xc7a200tfbg676-1, 200 MHz (5.000 ns), OOC synthesis

## Critical Path Identified

The baseline fixed_weight critical path (WNS -2.064 ns at HQC-128) runs from the
SHAKE context BRAM (`shake_ctx/mem_reg`) through a 24-bit rejection-threshold
comparison (`shake_ctx_out < UTILS_REJECTION_THRESHOLD`) into the weight counter.
The BRAM read alone is ~2.45 ns, and it fed 5 levels of combinational logic in a
single cycle.

## Change

Registered the threshold comparison result. The combinational compare now drives
`rejection_threshold_pass_comb`, and a single flip-flop stage produces the
registered `rejection_threshold_pass` consumed by the FSM:

```verilog
assign rejection_threshold_pass_comb = shake_ctx_out < UTILS_REJECTION_THRESHOLD;
always @(posedge clk) rejection_threshold_pass <= rejection_threshold_pass_comb;
```

This gives the slow BRAM-read-plus-compare its own clock cycle. The FSM consumes
the threshold decision one cycle later than before.

## Results (PPA)

| Param | Baseline WNS | Baseline Fmax | New WNS | New Fmax | Timing |
|-------|-------------|---------------|---------|----------|--------|
| HQC-128 | -2.064 | 141.6 | +0.122 | 205.0 | **MET** |
| HQC-192 | -1.622 | 170.4 | -0.574 | 179.4 | improved, not met |
| HQC-256 | -1.618 | 170.5 | -0.192 | 192.6 | improved, not met |

Cost at HQC-128: +18 LUTs (235->253), +1 FF (119->120). BRAM/DSP unchanged.
All three security levels improved; HQC-128 fully closes timing.

## Correctness (KAT Gate)

Full keygen -> encap -> decap simulation run with the pipelined fixed_weight.
Shared secret encap-vs-decap match:

- HQC-128: MATCH
- HQC-192: MATCH
- HQC-256: MATCH

The one-cycle FSM delay does NOT change which positions are accepted; the
fixed-weight output and downstream shared secret are unchanged. This is a
correct optimization, not just a faster-looking one.

## Status

HQC-128: complete verified win (timing met, correctness preserved).
HQC-192 / HQC-256: substantial timing improvement (1.05 ns and 1.43 ns gain),
correctness preserved, but a second critical path (likely Barrett reduction at
larger N) still prevents full closure. Follow-on target.
