# Findings: full-design NIST KAT outer gate (xsim), validated

Purpose: prerequisite for latency-changing edits. Per-block lockstep gates
verify fixed-latency equivalence only; a block that shifts by a cycle can
pass its own gate while breaking the design. The outer gate runs the
ENTIRE keygen pipeline (~50 files, mixed Verilog/VHDL incl. Keccak) via
Vivado xsim against NIST KAT vectors: 25 vectors x 3 security levels.
PASS = "testbench done" and zero WRONG lines. Script:
agent/mldsa/full_kat_gate.py [override_dir] [--vectors N] [--timeout S].

## Build lessons (chronological, all fixed in the script)
1. VHDL compile order: multi-pass retry-to-fixpoint instead of manual
   ordering; robust to source changes.
2. xvlog rejects use-before-declaration (legal in some tools): general
   regex hoister moves forward-referenced reg/wire decls to just after
   the module header, in a shim copy; pristine untouched.
3. TIMEOUT TRAP: first full run used gui simmode + waveform database by
   default and exceeded the 7200 s subprocess timeout. Python died,
   deleted its tempdir, and ORPHANED xsim, which burned a core for 2.4 h
   producing a result nothing could collect. Fixes: xsim -R batch mode
   (no gui, no wdb), CLI-settable timeout (default 24 h), stdout teed
   live to agent/mldsa/fullkat_run.log, tempdir preserved on failure.
4. $readmem path resolution: xsim resolves relative paths against its
   cwd; ROM/KAT data files (zetas.txt, KeyGen_*_44/65/87.txt) must be
   flat in the run directory. Unloadable ROMs simulate as X. The TB
   compares with !== (X-safe), so this produces WRONGs, not vacuous
   passes; the gate additionally surfaced it via file-open warnings.
5. --vectors N subset mode patches localparam NUM_TV in the TB copy
   (assert count==1); "Too many words" warnings are expected artifacts.

## Performance
Batch mode: full 75-KAT pristine run 1m37s wall (simulation ~90 s).
The gui/wdb misconfiguration cost a factor of ~100. The outer gate is
therefore cheap enough to run on EVERY candidate edit, not only
pre-commit.

## Validation (corruption protocol, same standard as block gates)
- Pristine: PASS, 75/75 KATs.
- c1 live-branch: +1 on the Barrett remainder (rem = ul - quo*Q + 1):
  FAIL, 334,643 WRONG bytes, first at KAT #0 pk byte 33.
- c2 boundary-adjacent: remMinusQ constant off by one (7fe001->7fe002):
  FAIL, 334,722 WRONG bytes, same first-divergence location.
Both corruptions were delivered through the override-dir mechanism,
validating the exact path real candidate RTL will take.

## Status
Gate trustworthy. Latency-changing tier open. First target: butterfly
DSP pipelining (predicted ~1.3 ns), verified by this gate.
