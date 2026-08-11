set_db init_hdl_search_path /home/alco9414/pqc/hqc/asic/portfix_wip
set_db hdl_error_on_blackbox false
read_hdl -define {SHARED=1 SHARED_ENCAP=1} [concat [list /home/alco9414/pqc/hqc/asic/portfix_wip/clog2.v] [lsort [glob /home/alco9414/pqc/hqc/asic/portfix_wip/*.v]]]
puts ARM_READ_OK
exit
