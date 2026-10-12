# Baseline-only unified ML-KEM-1024 / ML-DSA-87 OOC synthesis preparation.
# Locally authored 2026-10-12. Requires qualification on an installed Vivado.
# Usage: vivado -mode batch -source <this-file> -tclargs PART PERIOD_NS NEW_OUT_DIR
# No placement/routing, measured Fmax, board fit, or cryptographic pass is implied.
if {[catch {
    if {$argc != 3} {
        error "Usage: -tclargs PART PERIOD_NS NEW_OUT_DIR (period is a chosen target, not measured Fmax)"
    }
    lassign $argv abr_part abr_period_ns abr_out
    if {$abr_part eq "" || ![string is double -strict $abr_period_ns] ||
        $abr_period_ns <= 0 || $abr_period_ns == Inf || $abr_period_ns == -Inf} {
        error "Supply an FPGA part and a finite positive target period in ns"
    }
    source [file join [file dirname [info script]] sources.tcl]
    puts [exec python3 [file join $abr_root integration verify_sources.py]]
    set abr_out [file normalize $abr_out]
    if {[file exists $abr_out]} { error "Output path already exists; use a fresh path: $abr_out" }
    file mkdir $abr_out

    create_project -in_memory -part $abr_part
    set_property target_language Verilog [current_project]
    set_property include_dirs $abr_include_dirs [current_fileset]
    set_property verilog_define $abr_fpga_synthesis_defines [current_fileset]
    read_verilog -sv $abr_sources
    set_property top $abr_top [current_fileset]

    # These interface constraints are an explicit example, not a board contract.
    # Keep them identical for any paired run; review them before publishing PPA.
    set abr_xdc [file join $abr_out target.example.xdc]
    set abr_fh [open $abr_xdc w]
    puts $abr_fh "create_clock -name clk -period $abr_period_ns \[get_ports clk\]"
    puts $abr_fh {set data_inputs [remove_from_collection [all_inputs] [get_ports clk]]}
    puts $abr_fh "set_input_delay -max [expr {0.10 * $abr_period_ns}] -clock clk \$data_inputs"
    puts $abr_fh {set_input_delay -min 0 -clock clk $data_inputs}
    puts $abr_fh "set_output_delay -max [expr {0.10 * $abr_period_ns}] -clock clk \[all_outputs\]"
    puts $abr_fh {set_output_delay -min 0 -clock clk [all_outputs]}
    close $abr_fh
    read_xdc $abr_xdc
    synth_design -top $abr_top -part $abr_part -mode out_of_context \
        -flatten_hierarchy rebuilt -gated_clock_conversion off
    if {[llength [get_clocks]] != 1} { error "Expected one primary clock; review clock inference" }
    if {[llength [get_cells -hierarchical -filter {IS_BLACKBOX == 1}]] != 0} {
        error "Unresolved/black-box cells remain; refusing a complete-core result"
    }
    report_utilization -hierarchical -file [file join $abr_out utilization.rpt]
    report_timing_summary -file [file join $abr_out timing_summary.rpt]
    check_timing -verbose -file [file join $abr_out check_timing.rpt]
    report_drc -file [file join $abr_out drc.rpt]
    write_checkpoint [file join $abr_out synthesized.dcp]
    set abr_fh [open [file join $abr_out scope.txt] w]
    puts $abr_fh "scope=unified_mlkem1024_mldsa87_with_memories"
    puts $abr_fh "stage=out_of_context_synthesis_only"
    puts $abr_fh "part=$abr_part"
    puts $abr_fh "target_period_ns=$abr_period_ns"
    puts $abr_fh "tool_version=[version -short]"
    puts $abr_fh "defines=$abr_fpga_synthesis_defines"
    puts $abr_fh "upstream_commit=b77e3d899e828d626cfc2a0d26a6b5704cc121e0"
    puts $abr_fh "rtl_functional_qualification=separate_required_gate"
    puts $abr_fh "timing_closure=review_timing_and_drc_reports"
    close $abr_fh
    puts "Synthesis reports written to $abr_out; review scope, DRC, and timing. No PPA admission is implied."
} abr_error abr_options]} {
    puts stderr "Adam's Bridge baseline preparation/run failed: $abr_error"
    exit 1
}
exit 0
