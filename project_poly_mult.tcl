create_project poly_mult_proj ./vivado_projects/poly_mult -part xc7a200tfbg676-1 -force
set_property target_language Verilog [current_project]

add_files -norecurse {
    ./build/keygen/clog2.v
    ./build/keygen/loc_based_adder.v
    ./build/keygen/xor_based_adder.v
    ./build/keygen/mem_dual.v
    ./build/keygen/mem_single.v
    ./build/keygen/poly_mult.v
}

set_property is_global_include true [get_files clog2.v]
set_property top poly_mult [current_fileset]
set_property generic {parameter_set=hqc128} [current_fileset]

set constraints_file "./vivado_projects/poly_mult_ooc.xdc"
set fp [open $constraints_file w]
puts $fp "create_clock -period 5.000 -name clk \[get_ports clk\]"
close $fp
add_files -fileset constrs_1 $constraints_file

update_compile_order -fileset sources_1
launch_runs synth_1 -jobs 4
wait_on_run synth_1
puts "Project created and synthesis complete."
