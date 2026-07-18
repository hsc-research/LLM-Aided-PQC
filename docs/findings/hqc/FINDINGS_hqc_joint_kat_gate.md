# Findings: HQC Joint-Design KAT Gate — First Functional Verification of the Joint Configuration

## Summary
Built `agent/hqc/joint_kat_gate.py`, the first end-to-end functional
verification of the Yale HQC joint design (`hqc_kem_joint_design.v`,
SHARED+SHARED_ENCAP config). The joint configuration **was never functional
as shipped**: five independent defects prevented the joint decap simulation
from ever completing correctly. All are now root-caused, fixed in tracked
overrides (`build/joint_design/`), and the gate passes:

- Pristine joint top: PASS (ss match, 128 hex chars, hqc128)
- Registered pm client-select optimization (pm_start kept combinational): PASS

## Gate architecture
Standalone keygen TB -> standalone encap TB generate binary `.in` stimulus
(h/s/x/y, then u/v/d + reference `ss_output`); the joint decap TB is the DUT
(exercises decrypt + encap_inside_decap re-encrypt + compare + K derivation);
gate compares joint `test_ss_output` vs standalone `ss_output` byte-for-byte.
Watchdog process-group kill; default hqc128, `--all` for 3 levels.

## Defects found in the pristine repo (in discovery order)
1. **joint_design.tcl verilog_define overwrite**: two sequential
   `set_property verilog_define` calls; the second silently overwrites the
   first, so `SHARED` was never defined at compile. All `ifdef SHARED` pm
   plumbing was compiled out; pm_start floated Z; instant deadlock.
   Fix: single call `{SHARED=1 SHARED_ENCAP=1}`.
2. **Joint decap TB incomplete**: u/v arms of `decap_in` commented out and
   U_MEM/V_MEM address wires undriven in the shipped TB. (Later analysis
   showed the DUT reads u/v via direct ports and drives those addresses
   itself; see defect 5 for how our first fix over-corrected.)
3. **decap.v shake outputs undriven under SHARED_ENCAP**: all four shake
   outputs are only driven by ENCAP_FOR_RENCRYPT, which is compiled out in
   the shared config; Z propagated into the shared Keccak during the decrypt
   phase. Fix: tie-offs in the SHARED_ENCAP block (decrypt never uses SHAKE).
4. **CT_DESIGN skew**: joint top defaults to CT_DESIGN=2'b10 (cww sampler);
   the KAT-verified standalone flow uses 2'b01 (fixed_weight_ct). The joint
   decap TB inherits the default; the cww sampler variant stalls
   (weight_count stuck at 0, every candidate rejected). The joint encap TB
   passes CT_DESIGN explicitly; only the decap TB omitted it.
   Fix: TB passes `.CT_DESIGN(2'b01)`.
5. **Self-inflicted during fix 2**: TB-side `assign u_addr_1 = 0` (etc.)
   double-drove wires the DUT also drives -> X on U_MEM/V_MEM address ports
   -> X dense words into POLY_MULT mid-multiplication -> X message -> X theta
   -> all-reject sampling. Fix: removed TB-side address drivers entirely.

## Debugging methodology notes (reusable)
- `launch_simulation` auto-runs the stored `xsim.simulate.runtime`; set it
  low and use incremental `run` for mid-flight probes (early probes sampled
  post-completion idle state and produced misleading zeros).
- Coarse-grid sampling misses SHAKE bursts (~1us) and multi-cycle pulses;
  conclusions like "no SHAKE traffic" require sub-us grids in the right
  window.
- X-propagation chains surface far from their origin: the observable failure
  (all-X shared secret) was five causal steps from the root in every case.

## Optimization status (registered pm client-select)
Chip-level synth filter after KAT-verified retiming: worst path moved to the
address->dense-word return cone (KEYGEN rand addressing -> POLY_MULT
dshift), post-synth WNS -3.397 vs pristine -2.752. Post-synth comparisons
mispredict post-route outcomes (established measurement law); post-route
closure on hqc_joint_opt vs hqc_joint_pristine is the pending judge, queued
behind the current Minerva run.

## Paper relevance
- Transfer evidence: same disease class as ML-DSA (control fanning into a
  shared wide datapath), same fix family (select retiming), now KAT-gated on
  a second design.
- The "never functional as shipped" finding materially strengthens the
  verification-first methodology narrative and is worth communicating to
  Sanjay Deshpande (upstream fixes are candidate contributions).
