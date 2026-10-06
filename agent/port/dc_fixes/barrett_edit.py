import shutil, sys
p = "build/joint_design/barrett_red_gen.v"
O = "\n    .a_in({0,n_in_reg_3}),\n"
N = "\n    .a_in(n_in_reg_3),\n"
c = open(p).read().count(O)
if c != 1: print(f"ANCHOR_FAIL {p} count={c}"); sys.exit(1)
shutil.copy(p, p + ".bak")
open(p, "w").write(open(p + ".bak").read().replace(O, N))
print(f"EDITED {p}")
