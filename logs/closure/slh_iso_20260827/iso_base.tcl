open_checkpoint /mnt/c/PQC/slh_test/slh_128f_sha2_pristine.dcp
create_clock -period 11.980 -name clk [get_ports clk]
catch {opt_design}
place_design -directive ExtraTimingOpt
phys_opt_design -directive Explore
route_design -directive Explore
report_timing_summary -file /tmp/slh_iso_base.rpt
report_utilization -file /tmp/slh_iso_base.util
report_power -file /tmp/slh_iso_base.pwr
puts "ISO BASE DONE"
