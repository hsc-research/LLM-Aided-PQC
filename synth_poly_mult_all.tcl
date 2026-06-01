foreach params {hqc128 hqc192 hqc256} {
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
        -generic parameter_set=$params

    create_clock -period 5.000 -name clk [get_ports clk]

    report_utilization \
        -file ./synth_out/poly_mult/poly_mult_${params}_util.rpt
    report_timing_summary \
        -file ./synth_out/poly_mult/poly_mult_${params}_timing.rpt

    puts "=== DONE: poly_mult $params ==="
}
