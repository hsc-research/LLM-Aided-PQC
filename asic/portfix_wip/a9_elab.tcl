set TUT   "/home/alco9414/pqc/tutorial_innovus"
set LIB_PATH   "$TUT/lib/"
set LEF_PATH   "$TUT/lef/scaled/"
set TLEF_PATH  "$TUT/techlef/"
set RTL_DIR "/home/alco9414/pqc/hqc/asic/portfix_wip"
set LIB_LIST {  asap7sc7p5t_AO_LVT_TT_nldm_211120.lib   asap7sc7p5t_INVBUF_LVT_TT_nldm_220122.lib   asap7sc7p5t_OA_LVT_TT_nldm_211120.lib   asap7sc7p5t_SEQ_LVT_TT_nldm_220123.lib   asap7sc7p5t_SIMPLE_LVT_TT_nldm_211120.lib \
                asap7sc7p5t_AO_SLVT_TT_nldm_211120.lib  asap7sc7p5t_INVBUF_SLVT_TT_nldm_220122.lib  asap7sc7p5t_OA_SLVT_TT_nldm_211120.lib  asap7sc7p5t_SEQ_SLVT_TT_nldm_220123.lib  asap7sc7p5t_SIMPLE_SLVT_TT_nldm_211120.lib}
set LEF_LIST { asap7_tech_4x_201209.lef asap7sc7p5t_28_L_4x_220121a.lef asap7sc7p5t_28_SL_4x_220121a.lef}
set_db init_lib_search_path "$LIB_PATH $LEF_PATH $TLEF_PATH"
set_db init_hdl_search_path $RTL_DIR
set_db / .library "$LIB_LIST"
set_db lef_library "$LEF_LIST"
set_db hdl_error_on_blackbox true
read_hdl -define {SHARED=1 SHARED_ENCAP=1} [concat [list $RTL_DIR/clog2.v] [lsort [glob $RTL_DIR/*.v]]]
puts ARM_READ_OK
elaborate hqc_kem_joint_design
puts ARM_ELAB_OK
check_design -unresolved > /tmp/hqc_unresolved.rpt
report_hierarchy > /tmp/hqc_hier.rpt
exit
