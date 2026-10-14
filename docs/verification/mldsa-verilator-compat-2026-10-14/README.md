# ML-DSA exported-verifier compatibility

Scope: verifier-only staging/compiler compatibility. No RTL, vector fixture,
byte comparison, or per-vector cycle expression was modified. These finite
2-state RTL checks do not qualify mapped-memory behavior or target timing/PPA.

## Qualified tool versions

Both the official Debian package `5.048-1` (actual Verilator runtime 5.048)
and the historical development runtime 5.49 passed all 210 cases on the final
checker. Every individual latency and all 35 RTL source hashes match the
historical baseline; all frozen inputs remained unchanged during each replay.
Aggregate printed averages equal the
integer means of the individual vectors.

The 5.048 package came from Debian's **unstable** package index, not the Debian
stable distribution. Its package checksum was verified against Packages.xz,
which was checked against signed InRelease using the installed Debian archive
keyring. `debian-5048-package.txt`, `debian-5048-signatures.txt`, and
`debian-5048-sha256.txt` retain that provenance. The matching EPEL 5.022-3
provenance is in `epel-5022-provenance.txt` and `epel-5022-sha256.txt`.

The upstream release is [Verilator v5.048](https://github.com/verilator/verilator/releases/tag/v5.048).
For an EL9 host, use a separately installed/built upstream release through IT;
do not copy the Debian binary. Re-run the baseline gate on that host before
starting the agent or incurring model costs.

## Changes

- Normalize only staged `start_time` and `average` bookkeeping assignments using
  fail-closed exact assignment shapes/counts. Original bundled benches are intact.
- Correct three staged Verify aggregate averages to divide by `NUM_TV` now that
  the accumulator includes the final vector. Individual latency measurements
  remain untouched.
- Reject the known failing Verilator 5.022 release before compilation, with an
  actionable explanation. This does not claim every other release is qualified.
- Request compiler unrolling through `--unroll-count 512`; preserve all RTL
  nonblocking semantics and retain error diagnostics (no new warning waivers).

## Reproduction

Choose an already-installed Verilator on `PATH`, then run from the repository:

```sh
python docs/verification/mldsa-verilator-compat-2026-10-14/replay.py --out /absolute/new/run-directory
```

The script exports the historical baseline, checks identical source hashes,
binds fresh checker/fixture hashes, and invokes all 210 cases. Never edit the
immutable requests/manifests of an old autonomous run to accommodate new code.
Run the baseline gate locally before making paid proposal requests.

The official EPEL9 `5.022-3` executable/devel packages reproduce the reported
compile failures without this patch. With normalization/unrolling, compilation
succeeds but KeyGen byte comparisons fail. The first failure is ML-DSA-II KAT0,
public-key byte33: expected `d8`, got `13`. All75 KeyGen latency counts still
match the newer simulator; matching cycle counts alone cannot establish
cryptographic correctness. The gate correctly rejects these mismatches.

Package tests here run on Debian glibc2.41 with GCC14.2.0. An extracted Debian
binary is not an installation recommendation for EL9. A separately installed
or rebuilt simulator on the user's server still requires local baseline KAT
qualification; these results do not qualify that host automatically.

Final tool qualifications, package/binary provenance, source hashes, commands,
coverage, per-vector cycle comparisons and test exclusions are recorded in the
adjacent verification report. Raw temporary compile/simulation locations are
recorded there; generated C++ objects and executables are not committed.
