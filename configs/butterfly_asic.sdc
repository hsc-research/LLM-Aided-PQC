# Example only: review against the design's interface timing contract.
# PQC_PERIOD is supplied in the selected library's native time unit.
create_clock -name clk -period $PQC_PERIOD [get_ports clk]
set data_inputs [remove_from_collection [all_inputs] [get_ports clk]]
set_input_delay [expr {0.10 * $PQC_PERIOD}] -clock clk $data_inputs
set_output_delay [expr {0.10 * $PQC_PERIOD}] -clock clk [all_outputs]
# No automatic false paths. Reset/mode exceptions require a justified site SDC.
