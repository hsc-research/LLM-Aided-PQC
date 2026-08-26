#!/usr/bin/env python3
"""Rebuild the SLH-DSA post-synthesis checkpoint from current tracked sources.

SLH-DSA cannot use chip_orchestrator.regen_ckpt(): that function emits a bare
read_verilog + synth_design, and SPHINCSLET requires setting.v and clog2.v as
GLOBAL INCLUDES. Without them, Vivado's per-file compilation units leave
PARAM_* undefined, chain_lengths.v declares no ports or registers, and
elaboration fails with 21 errors. Established 2026-08-25.

Usage: python3 agent/slh_dsa/regen_slh_ckpt.py [rtl_dir] [out_dcp]
"""
import os, sys, glob, subprocess

RTL   = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/PQC/hqc/agent/slh_dsa/slh_src"
CKPT  = sys.argv[2] if len(sys.argv) > 2 else "/mnt/c/PQC/slh_test/slh_128f_sha2_synth.dcp"
PART  = "xc7a200tfbg676-1"
PROJ  = "/mnt/c/PQC/slh_test/slh_regen"
# Matches the 2026-08-25 baseline. Changing this makes runs non-comparable.
REGEN_PERIOD_NS = 12.0

XDC = """set_false_path -from [get_ports rstn]
set_false_path -from [get_ports i_FSM_start]
set_false_path -from [get_ports i_msg_in_size*]
"""
# i_sig_mode is deliberately NOT false-pathed: tb.v sets it 0 at line 405 and
# 1 at line 448 within one run, so it is a live selector, not a tie-off.

def main():
    srcs = sorted(glob.glob(f"{RTL}/**/*.v", recursive=True))
    srcs = [s for s in srcs if os.path.basename(s) != "tb.v"]
    assert srcs, f"no sources found under {RTL}"

    os.makedirs(os.path.dirname(CKPT), exist_ok=True)
    xdc_path = "/tmp/slh_regen.xdc"
    open(xdc_path, "w").write(XDC)

    nl = chr(10)
    files = nl.join(f"  {s}" for s in srcs)
    tcl = f"""create_project slh_regen {PROJ} -part {PART} -force
add_files [list
{files}
]
set_property include_dirs {{{RTL}/sphincslet {RTL}/imports/global_include}} [current_fileset]
set_property is_global_include true [get_files {RTL}/sphincslet/setting.v]
set_property is_global_include true [get_files {RTL}/imports/global_include/clog2.v]
add_files -fileset constrs_1 {xdc_path}
set_property used_in_synthesis true [get_files {xdc_path}]
set_property top top [current_fileset]
update_compile_order -fileset sources_1
synth_design -top top -part {PART} -mode out_of_context
create_clock -period {REGEN_PERIOD_NS:.3f} -name clk [get_ports clk]
write_checkpoint -force {CKPT}
puts "SLH REGEN DONE"
"""
    tf = "/tmp/regen_slh.tcl"
    open(tf, "w").write(tcl)
    r = subprocess.run(["vivado", "-mode", "batch", "-source", tf,
                        "-nojournal", "-log", "/tmp/regen_slh.log"],
                       capture_output=True, text=True)
    if "SLH REGEN DONE" not in r.stdout:
        errs = [l for l in r.stdout.splitlines() if l.startswith("ERROR")]
        print(nl.join(errs[:20]) or r.stdout[-2000:])
        raise SystemExit("SLH checkpoint regen failed")
    print(f"wrote {CKPT}")

if __name__ == "__main__":
    main()
