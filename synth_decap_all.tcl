foreach params {hqc128 hqc192 hqc256} {
    file mkdir "./synth_out/decap"

    read_verilog [glob ./build/decap/*.v]

    synth_design \
        -top decap \
        -part xc7a200tfbg676-1 \
        -mode out_of_context \
        -generic parameter_set=$params

    create_clock -period 5.000 -name clk [get_ports clk]

    report_utilization \
        -file ./synth_out/decap/decap_${params}_util.rpt
    report_timing_summary \
        -file ./synth_out/decap/decap_${params}_timing.rpt

    puts "=== DONE: decap $params ==="
}
