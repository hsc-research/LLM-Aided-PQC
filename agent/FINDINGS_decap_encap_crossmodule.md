# Findings: Decap & Encap Critical Paths + Cross-Module Analysis

**Modules:** decap, encap (and the shared fixed_weight address management)
**Date:** June 2-4, 2026
**Author:** Lloyd Alcorn
**Target:** Xilinx Artix-7 xc7a200tfbg676-1, 200 MHz (5.000 ns), OOC synthesis

## Summary

After landing the verified fixed_weight threshold-pipeline win (HQC-128),
the second critical paths in decap, encap, and the constant-time fixed_weight
variant were characterized. They share a common structure: routing-dominated
paths centered on fixed_weight context-address management. This is the central
analytical finding of the project so far.

## Decap

- **Worst path:** DECRYPT/V_MINUS_UY/uv_addr_1_reg -> comparison -> cross
  module boundary -> POLY_MULT/dshift_reg (barrel shifter). WNS -2.233 ns,
  79% routing.
- **Attempted fix:** registered the mux_word data into poly_mult plus a
  matched extra delay on the shift amount (loc_in_reg_2), to break the long
  cross-boundary route. Synthesis improved the path ~0.169 ns.
- **Result: KAT MISMATCH all three levels. REVERTED.** The barrel shifter
  consumes the data word in lockstep with an address-data-accumulate loop;
  delaying the data by one cycle misaligns the accumulate so products land
  in the wrong location. A correct fix requires retiming the entire
  address-data-accumulate loop together, not a single register.
- The KAT gate caught a corruption that synthesis accepted -- demonstrates
  the value of the correctness gate.
- The verified fixed_weight fix was propagated into decap's copy and KAT
  PASSES, but its benefit is currently masked by the worse poly_mult path.
- Decap is timing-starved across a cluster (-377 ns total violation, 388
  endpoints), not a single path. Needs systemic retiming.

## Encap

- **Worst path:** ENCRYPT/FIXEDWEIGHT/wr_addr_ctx_reg[9] -> ... ->
  wr_addr_ctx_reg[2]/R (reset pin). WNS -1.317 ns, 78% routing.
- **Attempted fix:** hoisted the state-independent reset
  (request_another_vector == 2'b01) out of the per-state FSM branches to a
  single top-level check, to simplify the reset decode.
- **Result:** synthesized logically identical, NO timing change. The reset
  decode was not the cost; the cost is routing. Reverted the hoist.
- The verified fixed_weight fix was propagated into encap's copy and KAT
  PASSES; benefit masked by the worse wr_addr_ctx path.

## Constant-Time fixed_weight (HQC-192/256 second path)

- **Worst path:** onegen_ct FSM -> rd_addr_ctx address logic -> reset pin.
  Routing-dominated (78%).
- FSM-encoding directive (sequential vs one-hot) produced identical results.
- The address comparison ladder (rd_addr_ctx > WEIGHT && <= 2*WEIGHT etc.)
  resists local rewrite because it is in the CONSTANT-TIME module: any change
  must preserve data-independent timing, which the KAT gate does not verify.
  Did not attempt a blind rewrite.

## Cross-Module Conclusion

The recurring critical-path limiter across keygen, encap, and decap is the
**fixed_weight context-address management** (rd_addr_ctx / wr_addr_ctx): an
address register fed back through a magnitude comparison and reset logic,
routing-dominated (~78% wire) at these dimensions. It is resistant to local
RTL edits (FSM encoding, reset hoisting both no-op) because the limiter is
physical routing, not logic depth.

**This points the remaining work toward:**
- Implementation-stage placement constraints (out of scope for OOC synthesis), or
- Datapath restructuring of context-address management.

Local RTL edits alone will not close it. All five modules are now characterized.
