import shutil, sys
p = "asic/arms/hqc_optimized/encrypt.v"
O = "\n  assign cdw_out_addr = xor_add_addr_div;\n  assign cdw_out_addr = xor_add_addr/COPIES_OF_CDW;\n"
N = "\n  assign cdw_out_addr = xor_add_addr_div;\n"
s = open(p).read(); c = s.count(O)
if c != 1: print(f"ANCHOR_FAIL count={c}"); sys.exit(1)
shutil.copy(p, p + ".bak"); open(p, "w").write(s.replace(O, N)); print("EDITED", p)
