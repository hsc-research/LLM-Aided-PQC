# FPGA ML-DSA selector-default correction, 2026-10-13

Both `fpga-latch-corrected-baseline` and `fpga-latch-corrected-candidate` pass
210 finite whole-core RTL KAT checks (75 KeyGen, 45 Sign, 45 Verify, 12 mutated
Verify and 33 canonical Verify). Full logs and testbench inputs are retained.
The unchanged upstream KAT fixtures are hash-listed in `raw-kat-result.json`.
Each `result.json` ties the corrected source bytes and zetas data to those logs.
`selector/` retains the extracted original/corrected selector, testbench, generic
netlists and logs. `checks/` retains full-core Icarus elaboration and generic
Yosys process-lowering results. No simulation binaries are included.

## Reproduction

From the repository root, export an explicit corrected variant using
`tools/export_mldsa_fpga_latch_corrected.py --variant VARIANT --out NEW_DIR`.
Then run:

```bash
python3 tools/check_mldsa_fpga_latch_kats.py --repo . --design NEW_DIR \
  --out NEW_KAT_RUN --tool-dir /path/to/installed/tools --jobs 4
python3 tools/check_mldsa_fpga_selector.py \
  --original third_party/mldsa_osh/upstream/ref_combined/src/gen_c.v \
  --corrected NEW_DIR/rtl/gen_c.v --out NEW_SELECTOR_RUN
```

For the candidate selector, use `agent/mldsa/mldsa_src/gen_c.v` as `--original`.
The checker needs installed Icarus/vvp and Yosys in PATH. Whole-core KAT checks
use Verilator and the original vendor fixtures; they are not independent FIPS
certification. Tool versions, commands and hashes are in the saved records.

For generic structure checking, use the exported ordered source list with
`read_verilog`, followed by `hierarchy -check -top combined_top; proc; opt;
select -assert-none t:$dlatch t:$adlatch; stat`. Run from the export directory
so `zetas.txt` resolves. YoWASP users can use the existing
`tools/run_yosys_large_stack.py` wrapper with their installed package path and a
writable `XDG_CACHE_HOME`. Saved scripts include this run's absolute source
paths and must be regenerated for a relocated export.

## Diagnostic attempts and limits

The first adapted KAT harness omitted `zetas.txt` from its simulation directory,
so it failed the byte comparisons. The final harness copies and hashes this
required input; both full reruns passed. Default-stack YoWASP failed with stack
exhaustion; the existing per-process larger-stack wrapper succeeded. An initial
proc-only latch assertion included dead intermediate storage; the final check
uses normal `opt` removal and reports the resulting netlist. These setup and
intermediate checks are not counted as passing verification.

Vivado has not run here. The exported corrected FPGA profiles remain target
unqualified until the user's selected-part flow is rerun. No timing improvement,
power result, ASIC mapping or paid API optimization is claimed.
