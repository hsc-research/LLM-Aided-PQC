foreach params {hqc128 hqc192 hqc256} {
    file mkdir "./synth_out/keygen"

    read_verilog {
        ./build/keygen/clog2.v
        ./build/keygen/keygen.v
        ./build/keygen/vect_set_random.v
        ./build/keygen/fixed_weight.v
        ./build/keygen/onegen.v
        ./build/keygen/fixed_weight_ct.v
        ./build/keygen/onegen_ct.v
        ./build/keygen/hqc_barrett_red.v
        ./build/keygen/poly_mult.v
        ./build/keygen/mem_single.v
        ./build/keygen/mem_dual.v
        ./build/keygen/loc_based_adder.v
        ./build/keygen/xor_based_adder.v
        ./build/keygen/keccak_top.v
        ./build/keygen/keccak_pkg.v
        ./build/keygen/keccak_math.v
        ./build/keygen/control_path.v
        ./build/keygen/data_path.v
        ./build/keygen/rc.v
        ./build/keygen/state_ram.v
        ./build/keygen/stateram_inference.v
        ./build/keygen/transform.v
    }

    synth_design \
        -top keygen \
        -part xc7a200tfbg676-1 \
        -mode out_of_context \
        -generic parameter_set=$params

    create_clock -period 5.000 -name clk [get_ports clk]

    report_utilization \
        -file ./synth_out/keygen/keygen_${params}_util.rpt
    report_timing_summary \
        -file ./synth_out/keygen/keygen_${params}_timing.rpt

    puts "=== DONE: keygen $params ==="
}
