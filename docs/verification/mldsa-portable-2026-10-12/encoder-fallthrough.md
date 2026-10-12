# ML-DSA banked encoder: Sign stall isolation and recovery

## Result

The existing fourteen-file candidate stalls in Sign. Restoring only `encoder.v`
to the pinned encoder restores all 165 original upstream KATs: 75 KeyGen,
45 Sign and 45 Verify. This isolates the regression to the banked encoder
integration, without changing the other thirteen candidate overrides.

A separate correction is preserved at
`verification/mldsa_osh/encoder_fallthrough.v`. It also passes all 165 KATs,
with exactly the same individual cycle counts as the pinned-encoder rollback
variant. The original candidate and pinned upstream sources remain untouched.
The 45 upstream Verify cases comprise nine expected accepts and 36 expected
rejects. These runs do not contain the separate canonical-hint fix or added
malformed-hint regressions. Results from any combined recovery must be reported separately.

## Failure mechanism

The banked encoder unconditionally moves each complete accumulator word into
its output FIFO before exposing it. Compared with the pinned PISO encoder,
this adds an output cycle. The surrounding controller has fixed drain schedules:

- `FSM2_DECOMP` resets the encoder and transitions to challenge generation at
  `ctr0fsm2 >= K*64-1+6`.
- `FSM0_UNLOAD_Z` resets the encoder and transitions to hints at
  `ctr == L*64*2+4`.

In the first failing ML-DSA-II Sign operation, the instrumented banked encoder
pushes 96 W1 words but completes only 94 FIFO dequeues before reset. At
58,350 ns it resets with two words queued, zero accumulator bits,
and output valid/ready both asserted. One queued word can transfer on that
reset edge; the remaining word is discarded. The challenge-generation stream
is incomplete and Sign never finishes.

The instrumentation log is retained as `encoder-instrumented-stall.txt`.
A diagnostic that changes only the four DECOMP `+6` thresholds to `+7` gets
past the initial failure but still watchdogs later, near Z output. It is not a
recovery and must not be adopted. Latency-tolerant block stream tests alone
miss this controller integration requirement because they allow arbitrarily
long output draining.

## Minimal separate correction

When the output FIFO is empty, expose a completed accumulator word directly.
If the consumer accepts it, remove it from the accumulator without enqueueing
it. Otherwise, enqueue the word as before. If the FIFO already contains data,
continue consuming its oldest word in order. FIFO counts and pointers change
only for real enqueue/dequeue events. The correction also removes the old
unconditional `BANKPOP` diagnostic display.

The patch is retained as `encoder-fallthrough.patch`. It changes only the
encoder source; no controller deadline is extended. Original copyright and
license notices are retained.

## Verification

`verification/mldsa_osh/tb_encoder_cycle_equiv.v` strengthens the existing
latency-tolerant block test: it explicitly rejects X/Z on either output-valid
signal and rejects X/Z in either valid output word, then checks output valid
and output data on every active cycle, including output-backpressure cycles.
Accepted-stream count/order/value comparison is retained. Equal unknowns on
both sides cannot pass. It covers 18 security-level/mode
configurations and two mode-switch sequences, 2,278 accepted words, randomized
input gaps and output backpressure. Its stimulus respects the original
256-bit buffer occupancy envelope. Only the default parameters are covered:
OUTPUT_W=4, COEFF_W=23, MAX_LVL=20 and W=64. Independent configurations reset
before input; switch sequences drain between modes. Reset with pending data
is not exercised, and this is not an arbitrary/full-backpressure proof.

Run it with Icarus Verilog and `vvp` on `PATH`:

    python3 tools/check_mldsa_encoder_fallthrough.py

Controls:

    python3 tools/check_mldsa_encoder_fallthrough.py --encoder agent/mldsa/mldsa_src/encoder.v
    python3 tools/check_mldsa_encoder_fallthrough.py --encoder third_party/mldsa_osh/upstream/ref_combined/src/encoder.v

The recovery and pinned encoder each pass 11,659 checked active cycles and
2,278 accepted words with zero errors and zero unknown values. The original
banked candidate fails with 3,628 cycle mismatches. Their exact source/testbench
hashes, commands, tool hashes, return codes, raw-log hashes and output markers
are retained in:

- `encoder-fallthrough-cycle-result.json`
- `encoder-original-cycle-result.json`
- `encoder-pinned-cycle-control.json`

Every invocation preserves a unique `.pqc_runs/mldsa-encoder-cycle-*` directory;
`--run-root` selects another parent directory. Each contains byte-exact selected
candidate and helper copies, original pinned gold sources, separately renamed
gold sources, the testbench, simulator binary, raw compile/simulation/version
logs, and a result manifest. The checker does not delete these run directories.
The manifest hashes all inputs and staged files and verifies they stayed unchanged.

Two explicit negative controls verify that equal unknowns fail independently
of output equality: forcing both valid signals to X produces exactly one
unknown-valid error; forcing both valid data words to X produces exactly one
unknown-data error. Both produce `GATE RESULT: FAIL (1 errors)`.
`encoder-knownness-negative-controls.json` retains their injection text, exact
staged-source hashes, commands, raw-log paths/hashes and output markers.

The original upstream KATs ran through the actual Verilog RTL plus GHDL 6 synthesized
pinned VHDL Keccak netlist, under Verilator. The portable harness uses explicit
bounded testbench reads/writes for partial final hint words and a cycle
watchdog. Provenance, exact run paths, commands, source hashes and individual
KAT cycle counts are in `encoder-fallthrough-provenance.json`.

## Limits

These are finite functional simulation checks, not formal equivalence,
unconstrained-buffer correctness, constant-time/leakage analysis, or FIPS
certification. The added fallthrough mux changes a physical timing path. No
new PPA was measured and historical banked-encoder PPA must not be attributed
to this corrected source without fresh measurement. The simpler rollback to
the pinned encoder is independently passing but likewise has no newly
measured PPA result.
