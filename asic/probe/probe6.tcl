set LIBDIR /tools/cadence/pdk/gpdk045_v_6_0/gpdk045/gsclib045_svt_v4.8/gsclib045/timing
set_db library $LIBDIR/slow_vdd1v0_basicCells.lib
read_hdl -language v2001 [list \
  ../../build/keygen/clog2.v \
  ../../build/keygen/poly_mult.v ]
puts "PROBE6_READ_OK"
exit -force
