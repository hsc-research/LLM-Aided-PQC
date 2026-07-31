# Defect Survey: use-before-declaration across HQC RTL

Date: 2026-07-31

## Result

| Metric | Value |
|---|---|
| Files surveyed (`build/joint_design/*.v`) | 59 |
| Flagged by Genus `VLOGPT-20` | 17 |
| Flagged by static checker | 18 |
| **Confirmed by both** | **13** |
| Instances within the 13 (static count) | 102 |

Confirmed files: `decap`, `encap`, `encrypt`, `encrypt_parallel`, `fft_part1`,
`fixed_weight`, `fixed_weight_ct`, `fixed_weight_cww`, `keygen`,
`reed_muller_encode`, `reed_solomon_encode`, `state_ram`, `vect_set_random`.

Vivado accepts all of them. Genus rejects at `read_hdl`.

## Method

1. Genus elaboration per file, `asic/scripts/parse_sweep.sh`, log
   `asic/results/parse_sweep.txt`. Screen only: files are elaborated in
   isolation without `hdl_search_path`, so `include`-dependent files produce
   artifacts, and Genus cascades after the first error cluster.
2. Independent static check, `asic/scripts/declcheck.py`, log
   `asic/results/declcheck.txt`. Regex-based, so it does not implement full
   Verilog scoping.
3. **Only the intersection is claimed.** Neither method alone is authoritative.

Calibration: `poly_mult.v` is clean under both after the F1 fix, and
`v_minus_uy.v` is clean under both after F4/F5. An earlier checker version
reported false positives on port declarations followed by redundant `wire`
re-declarations; those are legal and were excluded.

## Verified examples

- `encrypt.v`: `sel_e` used at L212 in `assign rd_error_loc = (rd_fw|sel_e)...`,
  declared at L391.
- `state_ram.v`: `raddr_precalc` used at L24, declared at L75.

## Disagreements

Genus-clean but checker-flagged (`control_path`, `decrypt`, `hqc_barrett_red`,
`mod34`): likely legal forward net references that the regex does not model.
Checker-low but Genus-high (`fixed_weight_ct` 2 vs 10): isolation artifacts and
cascade inflation.

## Implication

Two of two modules ported by hand carried this defect, and the survey confirms
it is systemic rather than incidental: 13 of 59 files in published,
peer-reviewed PQC RTL. "Verified RTL" is verified relative to the verifying
tool. Porting to a second toolchain is itself a verification method.

Each fix is a pure reordering, mechanically checkable
(`LC_ALL=C sort` diff) and gate-verifiable (KAT at all three security levels).
This is a better-justified autonomous agent task than PPA optimization, because
it is deterministic and the correctness criterion is exact.

## Status

Survey complete. **No fixes applied beyond `poly_mult` (F1) and `v_minus_uy`
(F4, F5).** The remaining 11 files are unfixed and will block chip-level ASIC
elaboration.
