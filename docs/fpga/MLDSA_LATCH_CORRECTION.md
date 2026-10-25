# ML-DSA FPGA selector correction

Use the explicit corrected FPGA variants for the new Artix-7 timing experiment:

- `fpga-latch-corrected-baseline`
- `fpga-latch-corrected-candidate`

The earlier `guarded-baseline` and `corrected-candidate` exports remain unchanged.
Keep their old reports as historical results. Do not compare a new candidate
against the earlier baseline timing without rerunning the corrected baseline.

## What changed

The `gen_c.v` security-level selection assigned `ch` and `C_SIPO_START` for
supported levels 2, 3 and 5, but omitted both assignments in its default branch.
This permits storage to be inferred when the security-level input is unsupported.
The correction assigns zero to both signals in that branch. Every supported
branch and every other RTL file is unchanged. Invalid levels remain unsupported
cryptographic configurations; defining two outputs does not make them valid.

The user-reported Vivado run had 66 live latch bits (64 `ch` and 2
`C_SIPO_START` bits). The extracted generic selector has 74 bits before constant
optimization; the corrected selector has zero. Both corrected whole cores also
have zero `$dlatch`/`$adlatch` cells after generic `proc; opt` processing.
Vivado must be rerun to establish the target-specific result. Do not add a false
path or declare `sec_lvl` to be a clock to suppress the latch warnings.

## Verification

[Saved evidence](../verification/mldsa-fpga-latch-correction-2026-10-13/README.md):

- 210 complete KAT cases per arm, including all supported security levels,
  KeyGen, Sign, Verify, mutation rejection and canonical-encoding checks.
- 1,542 supported selector comparisons per arm: every 512-bit input basis
  vector, all-zero and all-one inputs, for levels 2, 3 and 5.
- Unsupported and unknown selector checks return zero for the corrected outputs.
- Icarus Verilog-2005 full-core elaboration passes without diagnostics.
- Generic whole-core process lowering and optimization find zero latches;
  other synthesis warnings remain in the logs and are not waived.

These are finite RTL checks, not formal whole-design equivalence, FPGA timing
closure, power measurements, or FIPS certification. The FPGA variants retain
the original inferred-memory initialization; ASIC users must select the
separate ASIC startup variants.

## Start a fresh FPGA run

```bash
python3 tools/export_target_profiles.py \
  --design mldsa --variant fpga-latch-corrected-baseline --target fpga \
  --out build/profiles/mldsa-latch-corrected-baseline-fpga
python3 tools/export_target_profiles.py \
  --verify build/profiles/mldsa-latch-corrected-baseline-fpga/profile.json
```

Create a fresh site file from this export's example, using the same Artix-7 part,
Vivado version and 15 ns period as the earlier run. Use the new profile
fingerprint. Prepare into a new launch directory and write results into a new
output directory; preserve the earlier results. Repeat with
`fpga-latch-corrected-candidate` after the baseline is checked.

Check `check_timing.rpt`, latch warnings, DRC and timing again before starting
optimization. Post-synthesis timing is preliminary; routed timing is needed
for the final FPGA comparison.
