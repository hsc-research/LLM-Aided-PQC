# Example constraints for the WHOLE UNIFIED ML-KEM-1024/ML-DSA-87 wrapper.
# Review the interface assumptions and target period before any measurement.
# PQC_PERIOD is set in the selected library's native time unit by the runner.
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
# No reset/debug false-path exception is silently added. Clock-gating and
# asynchronous reset recovery/removal need site-qualified timing review.
