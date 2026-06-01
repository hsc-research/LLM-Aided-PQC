foreach params {hqc128 hqc192 hqc256} {
    file mkdir "./synth_out/fixed_weight"

    read_verilog {
        ./build/keygen/clog2.v
        ./build/keygen/fixed_weight.v
        ./build/keygen/onegen.v
        ./build/keygen/fixed_weight_ct.v
        ./build/keygen/onegen_ct.v
        ./build/keygen/hqc_barrett_red.v
        ./build/keygen/mem_single.v
        ./build/keygen/mem_dual.v
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
        -top fixed_weight \
        -part xc7a200tfbg676-1 \
        -mode out_of_context \
        -generic parameter_set=$params

    create_clock -period 5.000 -name clk [get_ports clk]

    report_utilization \
        -file ./synth_out/fixed_weight/fixed_weight_${params}_util.rpt
    report_timing_summary \
        -file ./synth_out/fixed_weight/fixed_weight_${params}_timing.rpt

    puts "=== DONE: fixed_weight $params ==="
}
