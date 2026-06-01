file mkdir "./synth_out/poly_mult"

read_verilog {
    ./build/keygen/clog2.v
    ./build/keygen/loc_based_adder.v
    ./build/keygen/xor_based_adder.v
    ./build/keygen/mem_dual.v
    ./build/keygen/mem_single.v
    ./build/keygen/poly_mult.v
}

synth_design \
    -top poly_mult \
    -part xc7a200tfbg676-1 \
    -mode out_of_context \
    -generic {parameter_set=hqc128}

# Check what ports exist
puts "=== PORTS ==="
foreach p [get_ports] { puts $p }

# Create clock on whatever the clock port is
create_clock -period 5.000 -name clk [get_ports clk]

report_utilization -file ./synth_out/poly_mult/poly_mult_hqc128_util.rpt
report_timing_summary -file ./synth_out/poly_mult/poly_mult_hqc128_timing.rpt
puts "Done."
