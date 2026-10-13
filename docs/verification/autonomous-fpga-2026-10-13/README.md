# Autonomous FPGA validation

634 permitted tests passed in each of normal and `python -O` modes: zero failures, errors or skips. The same 19 HQC-restricted tests were excluded in both runs. This is not a full-suite or hardware qualification claim.

See `verification.json` for exact source hashes, commands, test IDs, execution scope and limitations. `unittest-O0.log.txt` and `unittest-O1.log.txt` retain complete output. The real-export smoke uses the existing qualified source bundle but does not run a simulator or EDA. Existing permitted AHB plumbing tests use open-source simulators. No paid API, licensed EDA, new full PQC KAT or HQC run occurred.

Strict admission remains blocked without exact-netlist memory behavioral evidence. All accepted-path unit-test measurements are explicitly synthetic.
