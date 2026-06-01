foreach params {hqc128 hqc192 hqc256} {
    file mkdir "./synth_out/encap"

    read_verilog [glob ./build/encap/*.v]

    synth_design \
        -top encap \
        -part xc7a200tfbg676-1 \
        -mode out_of_context \
        -generic parameter_set=$params

    create_clock -period 5.000 -name clk [get_ports clk]

    report_utilization \
        -file ./synth_out/encap/encap_${params}_util.rpt
    report_timing_summary \
        -file ./synth_out/encap/encap_${params}_timing.rpt

    puts "=== DONE: encap $params ==="
}
