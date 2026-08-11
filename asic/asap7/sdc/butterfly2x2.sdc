# ASAP7 time unit is PICOSECONDS.
# PERIOD_PS is set by the caller via the GENUS_PERIOD_PS environment variable.
create_clock -name clk -period $PERIOD_PS [get_ports clk]
set_clock_uncertainty [expr $PERIOD_PS * 0.05] [get_clocks clk]
# Static configuration and async control are not timed paths.
set_false_path -from [get_ports mode*]
set_false_path -from [get_ports rst]
# Data interfaces, 10% of period each side.
set IO_DELAY [expr $PERIOD_PS * 0.10]
set_input_delay  -clock clk $IO_DELAY [get_ports {datai* zetai* acci* validi}]
set_output_delay -clock clk $IO_DELAY [all_outputs]
