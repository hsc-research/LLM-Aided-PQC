set_db init_hdl_search_path /tmp/armtest
set_db hdl_error_on_blackbox false
read_hdl -define {SHARED=1 SHARED_ENCAP=1} [glob /tmp/armtest/*.v]
puts ARM_READ_OK
exit
