# ASAP7 Genus synthesis, adapted from tutorial_innovus/scripts/genus.tcl
# NOTE: ASAP7 liberty time unit is PICOSECONDS. create_clock -period 600 = 600 ps.
set TUT   "/home/alco9414/pqc/tutorial_innovus"
set LIB_PATH   "$TUT/lib/"
set LEF_PATH   "$TUT/lef/scaled/"
set TLEF_PATH  "$TUT/techlef/"

set DESIGN  $env(GENUS_TOP)
set RTL_DIR $env(GENUS_SRCDIR)
set PERIOD  $env(GENUS_PERIOD_PS)
set OUTDIR  $env(GENUS_OUTDIR)

set LIB_LIST {  asap7sc7p5t_AO_LVT_TT_nldm_211120.lib   asap7sc7p5t_INVBUF_LVT_TT_nldm_220122.lib   asap7sc7p5t_OA_LVT_TT_nldm_211120.lib   asap7sc7p5t_SEQ_LVT_TT_nldm_220123.lib   asap7sc7p5t_SIMPLE_LVT_TT_nldm_211120.lib \
                asap7sc7p5t_AO_SLVT_TT_nldm_211120.lib  asap7sc7p5t_INVBUF_SLVT_TT_nldm_220122.lib  asap7sc7p5t_OA_SLVT_TT_nldm_211120.lib  asap7sc7p5t_SEQ_SLVT_TT_nldm_220123.lib  asap7sc7p5t_SIMPLE_SLVT_TT_nldm_211120.lib}
set LEF_LIST { asap7_tech_4x_201209.lef asap7sc7p5t_28_L_4x_220121a.lef asap7sc7p5t_28_SL_4x_220121a.lef}

set_db init_lib_search_path "$LIB_PATH $LEF_PATH $TLEF_PATH"
set_db init_hdl_search_path $RTL_DIR
set_db / .library "$LIB_LIST"
set_db lef_library "$LEF_LIST"

set_db hdl_error_on_blackbox false
# Mixed-language design (F10): the Keccak core is VHDL and a Verilog-only
# glob silently blackboxes it. VHDL packages must be analysed before their
# users, so alphabetical glob order fails.
set vhd [glob -nocomplain $RTL_DIR/*.vhd]
# Verilog-only arms get strict blackbox checking: a missing module source is a
# silent measurement error, not a tolerable condition. Mixed-language arms keep
# the tolerant setting because the VHDL read order above needs it.
if {[llength $vhd] == 0} { set_db hdl_error_on_blackbox true }
if {[llength $vhd] > 0} {
  set pkgs {}
  set rest {}
  foreach f $vhd {
    if {[string match "*sha3_pkg.vhd" $f] || [string match "*keccak_pkg.vhd" $f]} {
      lappend pkgs $f
    } else {
      lappend rest $f
    }
  }
  read_hdl -language vhdl [list $RTL_DIR/sha3_pkg.vhd $RTL_DIR/keccak_pkg.vhd]
  read_hdl -language vhdl [lsort $rest]
}
read_hdl [glob $RTL_DIR/*.v]
if {[info exists env(GENUS_PARAMS)]} {
  elaborate $DESIGN -parameters $env(GENUS_PARAMS)
} else {
  elaborate $DESIGN
}

set PERIOD_PS $PERIOD
if {[info exists env(GENUS_SDC)]} {
  source $env(GENUS_SDC)
} else {
  create_clock -name clk -period $PERIOD [get_ports clk]
  set_input_delay  -clock clk [expr $PERIOD * 0.10] [all_inputs]
  set_output_delay -clock clk [expr $PERIOD * 0.10] [all_outputs]
}

set_db syn_generic_effort high
set_db syn_map_effort     high
set_db syn_opt_effort     high

if {[llength [glob -nocomplain $OUTDIR/*]] > 0} {
  puts "ERROR: OUTDIR $OUTDIR is not empty. Refusing to overwrite."
  exit 1
}

proc stamp {msg} {
  puts "===== \[[clock format [clock seconds] -format %Y-%m-%d_%H:%M:%S]\] $msg"
  flush stdout
}

stamp "syn_generic START"
syn_generic
stamp "syn_generic DONE"
write_db $OUTDIR/${DESIGN}_p${PERIOD}_generic.db

stamp "syn_map START"
syn_map
stamp "syn_map DONE"
write_db $OUTDIR/${DESIGN}_p${PERIOD}_mapped.db
report timing -nworst 20 > $OUTDIR/${DESIGN}_p${PERIOD}_timing_mapped.rpt
report area > $OUTDIR/${DESIGN}_p${PERIOD}_area_mapped.rpt

stamp "syn_opt START"
syn_opt
stamp "syn_opt DONE"

write_hdl > $OUTDIR/${DESIGN}_p${PERIOD}_netlist.v
write_db $OUTDIR/${DESIGN}_p${PERIOD}_final.db
report timing -nworst 20 > $OUTDIR/${DESIGN}_p${PERIOD}_timing.rpt
report area   > $OUTDIR/${DESIGN}_p${PERIOD}_area.rpt
report gates  > $OUTDIR/${DESIGN}_p${PERIOD}_gates.rpt
report power  > $OUTDIR/${DESIGN}_p${PERIOD}_power.rpt
stamp "ALL DONE"
puts "ASAP7_RUN_DONE"
exit
