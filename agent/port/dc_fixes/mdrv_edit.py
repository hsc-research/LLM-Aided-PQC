import shutil, sys
MD_OLD = "\n  end\n\n  always @ (posedge clock)\n  begin\n    if (wren_1)\n"
MD_NEW = "\n\n    if (wren_1)\n"
KG_OLD = "\n            rd_y <= 1'b0;\n            rd_x <= 1'b0;\n            rand_out_rd <= 1'b0;\n"
KG_NEW = "\n            rd_y <= 1'b0;\n            rand_out_rd <= 1'b0;\n"
E = {
 "build/joint_design/mem_dual.v":       (MD_OLD, MD_NEW),
 "build/joint_design/keygen.v":         (KG_OLD, KG_NEW),
 "asic/arms/hqc_baseline/keygen.v":     (KG_OLD, KG_NEW),
}
for p, (o, n) in E.items():
    c = open(p).read().count(o)
    if c != 1: print(f"ANCHOR_FAIL {p} count={c}"); sys.exit(1)
for p, (o, n) in E.items():
    shutil.copy(p, p + ".bak")
    open(p, "w").write(open(p + ".bak").read().replace(o, n))
    print(f"EDITED {p}")
