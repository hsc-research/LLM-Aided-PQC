# Original-candidate raw output retention

`keygen-sim.txt` intentionally retains the complete, unedited simulator output
for the original 14-file candidate's KeyGen stage, before its Sign stage hit the
watchdog. KeyGen completed all 75 cases; the overall run remains **FAIL**.

- Size: 3,072,623 bytes; 53,007 lines.
- SHA-256: `37f9337199a7ca2f477c4a8fd9aae2c39d05e63b06f00d408e0f57324e723769`.
- It is byte-identical to the original run's `keygen-sim.log`.
- 52,925 lines are `BANKPOP` diagnostics already present at
  `agent/mldsa/mldsa_src/encoder.v:200`, reporting simulation time, 64-bit FIFO
  data, accumulator length and a valid bit.
- The other 82 lines are 75 KAT completions, two level transitions, one terminal
  completion marker and four simulator footer lines. All lines were classified
  during the final packaging review on 2026-10-12.

These simulated words derive from the repository's public pinned KeyGen test
fixtures, not deployed keys or user credentials. The only absolute filesystem
path in this output is the known temporary run's testbench path beneath
`.pqc_runs/mldsa-portable-tqzkggfx/`. Review found no credentials, personal data,
external endpoints, or private paths outside that known workspace. The full
output is retained deliberately so the failed run remains independently auditable.
