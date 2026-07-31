set LIBDIR /tools/cadence/pdk/gpdk045_v_6_0/gpdk045/gsclib045_svt_v4.8/gsclib045/timing
set_db library $LIBDIR/slow_vdd1v0_basicCells.lib
set_db hdl_error_on_blackbox false

set PERIOD $env(GENUS_PERIOD)
set TOP    $env(GENUS_TOP)
set SRCDIR $env(GENUS_SRCDIR)
set OUTDIR $env(GENUS_OUTDIR)

read_hdl -language v2001 [list \
  $SRCDIR/clog2.v \
  $SRCDIR/xor_based_adder.v \
  $SRCDIR/v_minus_uy.v ]

elaborate $TOP
create_clock -name clk -period $PERIOD [get_ports clk]
set_db syn_generic_effort high
set_db syn_map_effort high
set_db syn_opt_effort high

syn_generic
syn_map
syn_opt

report_timing > $OUTDIR/${TOP}_p${PERIOD}_timing.rpt
report_area   > $OUTDIR/${TOP}_p${PERIOD}_area.rpt
puts "GENUS_RUN_DONE"
exit -force
