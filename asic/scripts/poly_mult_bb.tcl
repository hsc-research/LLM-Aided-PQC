set LIBDIR /tools/cadence/pdk/gpdk045_v_6_0/gpdk045/gsclib045_svt_v4.8/gsclib045/timing
set_db library $LIBDIR/slow_vdd1v0_basicCells.lib

set_db hdl_error_on_blackbox false

read_hdl -language v2001 [list \
  ../../build/keygen/clog2.v \
  ../../build/keygen/poly_mult.v ]

elaborate poly_mult

create_clock -name clk -period 5.0 [get_ports clk]
set_db syn_generic_effort medium

syn_generic
syn_map

report_timing > ../out/poly_mult_bb_timing.rpt
report_area   > ../out/poly_mult_bb_area.rpt
report_gates  > ../out/poly_mult_bb_gates.rpt
puts "BB_DONE"
exit -force
