import shutil, sys
p = "build/joint_design/barrett_red_gen.v"
E = [
 ("\nwire [`CLOG2(N)-1:0]  n_in_reg;\n",
  "\nwire [`CLOG2(N)-1:0]  n_in_reg;\nwire [31:0]  n_in_reg_w;\nassign n_in_reg = n_in_reg_w[`CLOG2(N)-1:0];\n"),
 ("\n    .a_in_reg_out(n_in_reg) \n",
  "\n    .a_in_reg_out(n_in_reg_w) \n"),
]
s = open(p).read()
for o, n in E:
    c = s.count(o)
    if c != 1: print(f"ANCHOR_FAIL count={c} for {o!r}"); sys.exit(1)
shutil.copy(p, p + ".bak2")
for o, n in E: s = s.replace(o, n)
open(p, "w").write(s)
print("EDITED", p)
