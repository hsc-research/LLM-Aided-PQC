# HQC Agent - Synthesizer
# Generates a TCL script and runs Vivado OOC synthesis on a module.
# Returns parsed PPA results via ppa_reader.

import subprocess
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from ppa_reader import read_ppa

VIVADO = "vivado"
PART   = "xc7a200tfbg676-1"

MODULE_SOURCES = {
    "poly_mult": [
        "./build/keygen/clog2.v",
        "./build/keygen/loc_based_adder.v",
        "./build/keygen/xor_based_adder.v",
        "./build/keygen/mem_dual.v",
        "./build/keygen/mem_single.v",
        "./build/keygen/poly_mult.v",
    ]
}

def build_tcl(module, param_set):
    sources = MODULE_SOURCES[module]
    source_lines = "\n        ".join(sources)
    return f"""file mkdir "./synth_out/{module}"
read_verilog {{
        {source_lines}
}}
synth_design \\
    -top {module} \\
    -part {PART} \\
    -mode out_of_context \\
    -generic parameter_set={param_set}
set clk_port [lindex [get_ports -quiet {{clk clk_i}}] 0]
if {{$clk_port eq ""}} {{ set clk_port [lindex [get_ports -quiet *clk*] 0] }}
create_clock -period 5.000 -name clk [get_ports $clk_port]
report_utilization \\
    -file ./synth_out/{module}/{module}_{param_set}_util.rpt
report_timing_summary \\
    -file ./synth_out/{module}/{module}_{param_set}_timing.rpt
puts "=== DONE: {module} {param_set} ==="
"""

def run_synthesis(module, param_set, repo_root="."):
    if module not in MODULE_SOURCES:
        return {"error": f"module {module} not registered in synthesizer"}

    tcl_path = os.path.join(repo_root, f"_agent_synth_{module}_{param_set}.tcl")

    with open(tcl_path, "w") as f:
        f.write(build_tcl(module, param_set))

    print(f"Running synthesis: {module} / {param_set} ...")
    result = subprocess.run(
        [VIVADO, "-mode", "batch", "-nojournal", "-nolog", "-notrace",
         "-source", tcl_path],
        cwd=repo_root,
        capture_output=True,
        text=True
    )

    os.remove(tcl_path)

    if result.returncode != 0:
        return {"error": f"Vivado failed: {result.stderr[-1000:]}"}

    return read_ppa(module, param_set)

if __name__ == "__main__":
    result = run_synthesis("poly_mult", "hqc128")
    print(result)

MODULE_SOURCES["keygen"] = [
    "./build/keygen/clog2.v",
    "./build/keygen/keygen.v",
    "./build/keygen/vect_set_random.v",
    "./build/keygen/fixed_weight.v",
    "./build/keygen/onegen.v",
    "./build/keygen/fixed_weight_ct.v",
    "./build/keygen/onegen_ct.v",
    "./build/keygen/hqc_barrett_red.v",
    "./build/keygen/poly_mult.v",
    "./build/keygen/mem_single.v",
    "./build/keygen/mem_dual.v",
    "./build/keygen/loc_based_adder.v",
    "./build/keygen/xor_based_adder.v",
    "./build/keygen/keccak_top.v",
    "./build/keygen/keccak_pkg.v",
    "./build/keygen/keccak_math.v",
    "./build/keygen/control_path.v",
    "./build/keygen/data_path.v",
    "./build/keygen/rc.v",
    "./build/keygen/state_ram.v",
    "./build/keygen/stateram_inference.v",
    "./build/keygen/transform.v",
]


MODULE_SOURCES["decap"] = [
    "./build/decap/add_fft.v",
    "./build/decap/barrett_red_gen.v",
    "./build/decap/cdw_xor_tmp.v",
    "./build/decap/clog2.v",
    "./build/decap/concat_code.v",
    "./build/decap/control_path.v",
    "./build/decap/data_path.v",
    "./build/decap/decap.v",
    "./build/decap/decrypt.v",
    "./build/decap/encap.v",
    "./build/decap/encrypt.v",
    "./build/decap/encrypt_parallel.v",
    "./build/decap/fft_leaves_butterfly.v",
    "./build/decap/fft_part1.v",
    "./build/decap/fft_part2.v",
    "./build/decap/fft_retrieve_error_poly.v",
    "./build/decap/fixed_weight.v",
    "./build/decap/fixed_weight_ct.v",
    "./build/decap/fixed_weight_cww.v",
    "./build/decap/gf_mul.v",
    "./build/decap/gfmul.v",
    "./build/decap/hqc_barrett_red.v",
    "./build/decap/hqc_decod_top.v",
    "./build/decap/hqc_rmdecod_ctrl.v",
    "./build/decap/hqc_rmdecod_expnsum.v",
    "./build/decap/hqc_rmdecod_findpeaks.v",
    "./build/decap/hqc_rmdecod_hadamard.v",
    "./build/decap/hqc_rmdecod_top.v",
    "./build/decap/hqc_rsdecod_elp.v",
    "./build/decap/hqc_rsdecod_err_val.v",
    "./build/decap/hqc_rsdecod_roots.v",
    "./build/decap/hqc_rsdecod_syndromes.v",
    "./build/decap/hqc_rsdecod_top.v",
    "./build/decap/hqc_rsdecod_zpoly.v",
    "./build/decap/karatsuba_small.v",
    "./build/decap/keccak_math.v",
    "./build/decap/keccak_pkg.v",
    "./build/decap/keccak_top.v",
    "./build/decap/loc_based_adder.v",
    "./build/decap/mem_dual.v",
    "./build/decap/mem_single.v",
    "./build/decap/mod34.v",
    "./build/decap/onegen.v",
    "./build/decap/onegen_ct.v",
    "./build/decap/poly_mult.v",
    "./build/decap/rc.v",
    "./build/decap/reed_muller_encode.v",
    "./build/decap/reed_solomon_encode.v",
    "./build/decap/rm_encoder.v",
    "./build/decap/state_ram.v",
    "./build/decap/stateram_inference.v",
    "./build/decap/syncfifo.v",
    "./build/decap/transform.v",
    "./build/decap/v_minus_uy.v",
    "./build/decap/xor_based_adder.v",
]
