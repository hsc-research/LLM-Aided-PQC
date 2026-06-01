# Measure cycle count for poly_mult optimized (RAMWIDTH=32 pipelined, HQC-128)
create_project cycle_test_optimized ./agent/cycle_test_optimized -part xc7a200tfbg676-1 -force
set_property target_language verilog [current_project]

add_files -norecurse {
    ./build/keygen/clog2.v
    ./build/keygen/loc_based_adder.v
    ./build/keygen/xor_based_adder.v
    ./build/keygen/mem_dual.v
    ./build/keygen/mem_single.v
    ./build/keygen/poly_mult_ramwidth32_pipelined.v
}

set_property is_global_include true [get_files clog2.v]
update_compile_order -fileset sources_1

add_files -fileset sim_1 -norecurse ./agent/poly_mult_cycle_tb_32.v
update_compile_order -fileset sim_1
set_property generic parameter_set="hqc128" [get_filesets sim_1]
set_property top poly_mult_hqc_v1_tb [get_filesets sim_1]

launch_simulation
run 5000 us
puts "=== OPTIMIZED COMPLETE ==="
