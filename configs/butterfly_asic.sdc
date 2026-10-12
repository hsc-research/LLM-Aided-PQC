# Example only: review against the design's interface timing contract.
# PQC_PERIOD is supplied in the selected library's native time unit.
# configs/asic_site.example.tcl explains the required load/slew/uncertainty.
foreach name {PQC_INPUT_TRANSITION PQC_CLOCK_UNCERTAINTY PQC_OUTPUT_LOAD} {
    if {![info exists $name]} { error "Required site constraint missing: $name" }
}
create_clock -name clk -period $PQC_PERIOD [get_ports clk]
set_clock_uncertainty $PQC_CLOCK_UNCERTAINTY [get_clocks clk]
set data_inputs [remove_from_collection [all_inputs] [get_ports clk]]
set_input_delay -max [expr {0.10 * $PQC_PERIOD}] -clock clk $data_inputs
set_input_delay -min 0 -clock clk $data_inputs
set_input_transition $PQC_INPUT_TRANSITION $data_inputs
set_output_delay -max [expr {0.10 * $PQC_PERIOD}] -clock clk [all_outputs]
set_output_delay -min 0 -clock clk [all_outputs]
set_load $PQC_OUTPUT_LOAD [all_outputs]
# No automatic false paths. Reset/mode exceptions require a justified site SDC.
