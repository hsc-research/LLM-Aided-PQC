# Decap Top-20 Recon (post fixed_weight_ct precompute W)

- fixed_weight threshold signature ABSENT from decap top-20: the
  write-time precompute fix is confirmed live in decap's elaboration.
- Cluster 1 (11/20 paths, worst -2.233, ~77% route): V_MINUS_UY addr regs
  -> POLY_MULT dshift_reg data pins. Wide AND routing-bound. Needs
  lockstep loop retiming or placement; flagged for Sanjay.
- Cluster 2 (NEW, 8/20 paths, worst -1.952, 44-46% logic, 4 levels):
  RS_DECOD/COMPUTE_ERRVALS - GF inverse table BRAM -> combinational
  gfmul (Forney) -> e_j LUTRAM / inv_power. Write-time precompute does
  NOT apply (gfmul operands known only at read). Candidate: gfmul
  REG_IN=1 (hooks exist in module) - time-domain, requires Forney FSM
  schedule analysis first. Module is 409 self-contained lines
  (hqc_rsdecod_err_val.v). Next-session target.
- FFT FIFO self-loop path noted at -1.647 (fifo read->write same BRAM).
