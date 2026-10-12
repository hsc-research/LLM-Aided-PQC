# Generated Keccak netlist provenance and notices

These two files are captured, byte-preserved GHDL outputs from the passing
ML-DSA regressions. This adjacent notice preserves provenance without changing
the tested `.v` bytes. They implement the same pinned VHDL hierarchy; the two
captured outputs differ only in their generated source-location comment paths.

## Original sources and notices

All 16 source files are in
[`third_party/mldsa_osh/upstream/ref_combined/src/`](../../../third_party/mldsa_osh/upstream/ref_combined/src/),
from KU Leuven / COSIC ML-DSA-OSH commit
`751009199ac081091a9059805e6921453bde0154`.
The original VHDL files and their copyright headers are retained unchanged.

The headers attribute these sources to the Cryptographic Engineering Research
Group (CERG), ECE Department, George Mason University, Fairfax, VA, U.S.A.:

- Copyright 2010–2012: `sha3_pkg`, `keccak_pkg`, `regn`, `piso`, `sipo`,
  `countern`, `sr_reg`, `keccak_cons`, `keccak_round`, `keccak_control`.
- Copyright 2019–2020, author Farnoud Farahmand: `keccak_bytepad`,
  `keccak_fsm1`, `keccak_fsm2`, `keccak_datapath`, `keccak_top`.
- Copyright 2020, author Farnoud Farahmand: `sha3_fsm3`.

Preserve the upstream [MIT license](../../../third_party/mldsa_osh/upstream/LICENSE)
and [NOTICE](../../../third_party/mldsa_osh/upstream/NOTICE):
Copyright (c) 2025 KU Leuven - COSIC. The NOTICE also attributes incorporated
Apache-2.0 material to CERG (2021); the full [Apache-2.0 license](../../../LICENSES/Apache-2.0.txt)
is retained in the repository. Those upstream notices, rather than GHDL's own
tool license, describe the source distribution. The VHDL headers themselves
contain the older CERG copyright/author notices reproduced above. See the
repository [NOTICE](../../../NOTICE) for the project-level attribution.
Do not detach these generated outputs from the original source attribution and
applicable license notices when redistributing them.

## Generation

The successful tool reports:

```text
GHDL 6.0.0 (Debian 6.0.0+dfsg3-1) [Dunoon edition]
Compiled with GNAT Version: 14.3.0
static elaboration, mcode JIT code generator
```

The pinned official-package setup, binary/source hashes and legacy Synopsys
compatibility-library commands are recorded in
[`toolchain.json`](../../../docs/verification/mldsa-portable-2026-10-12/toolchain.json)
and [`bootstrap_manifest.json`](../../../docs/verification/mldsa-portable-2026-10-12/bootstrap_manifest.json).
`tools/bootstrap_mldsa_ghdl.py --prefix /tmp/pqc-ghdl` reconstructs that local
setup. No GHDL 5 executable is used in the successful route.

The following shows the actual analysis order and synthesis command, normalized
to `$RUN` for the run directory. `$SRC` is the private, unchanged VHDL input copy
at `$RUN/ref_combined/src`. There were no generic overrides; top `keccak_top`
uses its source default `HS = HASH_SIZE_256`.

```sh
cd "$RUN"
SRC="$RUN/ref_combined/src"
ghdl -a --std=08 -fsynopsys \
  "$SRC/sha3_pkg.vhd" \
  "$SRC/keccak_pkg.vhd" \
  "$SRC/regn.vhd" \
  "$SRC/piso.vhd" \
  "$SRC/sipo.vhd" \
  "$SRC/countern.vhd" \
  "$SRC/sr_reg.vhd" \
  "$SRC/keccak_bytepad.vhd" \
  "$SRC/keccak_cons.vhd" \
  "$SRC/keccak_round.vhd" \
  "$SRC/keccak_fsm1.vhd" \
  "$SRC/keccak_fsm2.vhd" \
  "$SRC/sha3_fsm3.vhd" \
  "$SRC/keccak_control.vhd" \
  "$SRC/keccak_datapath.vhd" \
  "$SRC/keccak_top.vhd"
ghdl --synth --std=08 -fsynopsys --out=verilog keccak_top \
  > "$SRC/keccak_top_ghdl.v" 2> "$RUN/ghdl-synth.log"
```

Exact absolute argv/cwd values are in the qualifying reports below. GHDL embeds
source paths in comments, so generating in a different directory can change the
file hash without changing logic. The checked-in captures retain the tested
bytes; the no-EDA exporter verifies their recorded hashes instead of regenerating.
Raw `ghdl-analyze.txt` and `ghdl-synth.txt` diagnostics are retained beside each
report, including the unused `sel_cin` output warning. No source/netlist formal
equivalence or direct mixed-language simulation is claimed.

## Captured outputs and qualifying reports

- `guarded_baseline_keccak_top.v`: SHA-256 `49e5f9e2bf65a421b40807b5da5cbe6e9e4b65688bda2a8fe03ac0221f5ebc77`
  - [210-case report](../../../docs/verification/mldsa-portable-2026-10-12/baseline_canonical_pass/result.json), SHA-256 `b547875ecf00548547f7a9afde60fdd08a9d030d0b168863d450619fe2c9066b`
- `corrected_candidate_keccak_top.v`: SHA-256 `b0ed591464598a04a20a15c5f234eb246c4b556126e31a5517bb70de7fefba20`
  - [210-case report](../../../docs/verification/mldsa-portable-2026-10-12/candidate_corrected_pass/result.json), SHA-256 `3a13da09035d63493b961ab360d8aa7b569b5d38fd70d19c29f60e6a758fa341`

Each report's `input_hashes` and `staged_design_hashes` bind the source bytes to
that run. Both reports have the following same VHDL source hashes, listed in
analysis order; these were rechecked against the pinned originals at packaging:

| Source filename | SHA-256 |
| --- | --- |
| `sha3_pkg.vhd` | `1ad92e9207139819b3748b6a1521375c011ddad63f5a964cb557672eb923fbae` |
| `keccak_pkg.vhd` | `5f175032efe3e286a3181d13b72316a124931cdd5d323caf6d600d60b89c7e1e` |
| `regn.vhd` | `00e89f6986dfc59b2455ad33694d8fe89d29a4993649563fba81211213edc3a5` |
| `piso.vhd` | `9323f2659586498d5df464553651e3739c7651ee1e738c97055cbcbaac803add` |
| `sipo.vhd` | `9b63c7aa1464528f24eedd322eec883ec5573ee2df700466c8d6da26f9d28d4e` |
| `countern.vhd` | `ddb8bb1ced153d812ac2866c8662c4ea336efeafaec37c0919df516c6fdbf053` |
| `sr_reg.vhd` | `e2835ab11ee11b9e45a6b35d2d310ed8678b57669b405cb6b797206b0dd226d5` |
| `keccak_bytepad.vhd` | `1d1fe33197837578fde2b0f2f78605d12f2a0099d6caeac2ff51b388623f89bb` |
| `keccak_cons.vhd` | `b2702b861d274d824bba77d295b0640a776f6deff785fd10fba84507ea9a8166` |
| `keccak_round.vhd` | `64120dc5742dde93d21bd323b47aa5c90ca836c40155243c0518514d7f5ff074` |
| `keccak_fsm1.vhd` | `ca610bae9db4503a6ed2464ab9d1d517e4910f0b3fdbd36210ecb9aa3a5a7f4b` |
| `keccak_fsm2.vhd` | `286cdac53eee946342acc625117f994d3ffa1d9eb9eb224176f5d2a2253bde4f` |
| `sha3_fsm3.vhd` | `ac1ec7fa052fc951126c64f5b41e57bf22d59c8e7c91da4c162535cd06df7432` |
| `keccak_control.vhd` | `062eb959bb0a63a561b8584196e41d13fd2dbcf1477da553b55dd22584fde659` |
| `keccak_datapath.vhd` | `e0d6bf837b7ff6f4f46b3f9f99be3de8041be151c9a36d75d672e2bcc552e994` |
| `keccak_top.vhd` | `581fc52ec6611713bf2f64c225f10c31b17ad60ee0228637ad2025ac68573904` |
