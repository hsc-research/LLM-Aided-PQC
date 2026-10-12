# SLH-DSA baseline and selected-parameter gate

## What is supported

`slh_kat_gate.py` reads the candidate's existing `sphincslet/setting.v` and
selects the matching frozen **SHA2** vendor reference for 128s, 128f, 192s,
192f, 256s or 256f. It never rewrites the candidate's parameter selection.

The tracked candidate currently selects **SHA2-192f**; the pristine vendor
snapshot selects **SHA2-128f**. These are distinct configurations. A candidate
192f run uses `gate/levels/SIG_192f.hex` and requires newly produced
`SIG_file0_192f_w.hex`. It cannot use the historical 128f filename or golden.
SHAKE, multiple selections, missing selections and unreviewed configuration
macro layouts fail before simulation. No SHAKE reference is assumed.

A `PASS` means that the selected candidate reproduces one frozen vendor-RTL
signing stream byte for byte and that the unchanged vendor testbench completes
signing and verification successfully. It is **differential regression evidence,
not independent FIPS 205/ACVP validation**, and does not establish all-message
correctness, side-channel resistance or implementation security. The JSON
result records this explicitly as `evidence_kind: vendor_rtl_differential` and
`independent_fips_205_validation: false`.

## Frozen evidence and testbench contract

All six reference files were already committed in
`25a9de8fb399644889f9d6f602b302f949a6e86f`. Their bytes are unchanged. The SHA2
input files and vendor testbench also match their versions at that commit.
The pristine source provenance is the CASLAB
[pqc-hw-sphincslet revision a1adc2b](https://github.com/caslab-code/pqc-hw-sphincslet/tree/a1adc2b324483d0f95ae42b3119997d3a61c77b6).

The gate contains fixed SHA-256 pins for each complete golden, the vendor
`tb.v`, and every selectable fixture. It does not trust a candidate-written
checksum sidecar or generate a golden during a verification run. The old
`gate/SIG_file0_128f_w.hex` and its checksum are retained unchanged; its contents
are identical to `gate/levels/SIG_128f.hex`.

| SHA2 set | Golden | 64-bit output words | Golden SHA-256 |
|---|---|---:|---|
| 128f | `SIG_128f.hex` | 2141 | `10f35fcc0cc98680d87cf7aaef1479ba359303a84ba2553d69a8b77771bdf2a8` |
| 128s | `SIG_128s.hex` | 987 | `df0b3ed56604db3ff59f3d657403f78724d2c4c941072636c3c60382b4a016bb` |
| 192f | `SIG_192f.hex` | 4463 | `22bfbe1c1130b0faf039268adf00504a0ffec308f8ac7a8692593c757371dfe3` |
| 192s | `SIG_192s.hex` | 2033 | `82659381c8e552f55e42cea313552b4e6505a41527831d90a5de87c2f9ec54fb` |
| 256f | `SIG_256f.hex` | 6237 | `9e9d24ad3abbba973fa11cd92814cb1b345c788a8d76f4612fddc76f8e4086a9` |
| 256s | `SIG_256s.hex` | 3729 | `cd388b37b2ecd17d621db43e897ebf402ceed3fb24dcccf2f181436ef0f16e4e` |

The testbench contract is pinned to SHA-256
`687a3c45d9a54dc9e6e3782ac75ee2023ea5756a250766790c82f479f6063b0c`:

- The four inputs for a parameter such as 192f are `SLH_192f_SK.hex`,
  `SLH_192f_PK.hex`, `192_optrand.hex` and `SLH_msg_33B.hex` in `data_sha2`.
  The testbench uses a 33-byte message.
- It writes the entire 64-bit `o_sig_valid` stream as `%X` lines to
  `SIG_file0_<parameter>_w.hex`. The golden streams end with the same message
  padded to five 64-bit words. They are vendor output dumps, not files that
  should be truncated to a standard signature byte length.
- Generation and verification operate in sequence, with verification using
  the testbench's captured signature memory. The gate requires standalone
  `sig gen done`, `sig verification done` and `The signature is matched!`
  markers, as well as the exact output bytes and successful simulator exits.
  Error, fatal, mismatch, incomplete, absent and stale evidence cannot pass.
- The gate validates the reviewed `setting.v` macro layout after normalizing
  comments, blank lines and surrounding indentation. The one parameter
  selection may vary; changes to its mappings or hash-selection logic require
  a separately reviewed harness update.

The gate snapshots the actual candidate, checks the staged source set/bytes,
and copies only the four pinned selected inputs into a fresh private run.
It preserves the vendor's four-level-relative `TECS_v8.srcs` data layout.
Candidate inputs default to `<selected RTL>/imports`; `SLH_DATA_ROOT` can
relocate identical fixtures but cannot change their contents. No existing
external signature is deleted, copied into the simulation data directory or
accepted as fresh output. Reference and input bytes are pinned and checked;
source and input changes during verification fail closed. `sources.json`,
`inputs.json`, `reference.json` and tool logs remain in each run directory.

## Run

From the repository root, with Vivado simulator tools available:

```sh
# Current selected SHA2-192f candidate
python3 agent/slh_dsa/slh_kat_gate.py

# Pristine SHA2-128f candidate, without changing either tree
python3 agent/slh_dsa/slh_kat_gate.py agent/slh_dsa/pristine
```

`VIVADO_BIN` optionally prepends the Vivado binary directory to `PATH`.
`PQC_RUN_DIR` selects the run directory parent (default: `.pqc_runs`).
The gate exits 0 only on `PASS`, 1 on a failed simulation/comparison and 2 on
setup/tool errors. It does not silently substitute another simulator.

`gate/run_sim.sh` and `level_sweep.py` are historical experiment scripts, not
the hardened verification entry point. In particular, the historical sweep
can regenerate reference files; do not use it to approve a candidate or to
replace the frozen evidence for this gate.

## Verification on 2026-10-12

The selected-mode and existing correctness-harness tests pass:

```sh
python3 -m unittest discover -s tests -p test_slh_selected_gate.py -v
python3 -m unittest discover -s tests -p test_correctness_gates.py -v
```

These are mocked harness tests, **not RTL execution**. Coverage includes all
six selections, 192f/128f reference and filename mismatches, every output byte
including the padded message and final newline, missing/bit-flipped inputs,
changed harness/configuration, rewritten golden plus checksum sidecar,
incomplete/contradictory logs, stale outputs and changes during verification.

Real gate invocations for both the unchanged candidate and pristine tree pass
the configuration/reference/input checks and then return `ERROR` at `xvlog`,
which is absent in this environment. No fresh SLH RTL `PASS` is claimed.

Existing Icarus Verilog 12.0 (`-g2005`) and Verilator (`--language 1364-2005`)
were also tried against the unmodified candidate. Both reject duplicate
`WOTS_FSM_start` and `WOTS_s_in_0_wr_en` declarations in `fsm/FSM.v`
(lines 190/202 versus output declarations 121/120). This is a portability
blocker; no RTL was altered to make an alternative simulator accept it.
Vivado simulation and later Vivado/DC/Genus implementation remain separate,
unexecuted stages in this environment.
