#!/usr/bin/env python3
import shutil, sys, os
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/PQC/hqc/agent/mldsa/mldsa_src"
SRC = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src/encoder.v"
F = os.path.join(D, "encoder.v")
if not os.path.exists(F):
    shutil.copy(SRC, F)
shutil.copy(F, F + ".bak")
src = open(F).read()
old = "    reg [9:0]  piso_len, piso_len_next;"
new = "    (* max_fanout = 16 *) reg [9:0]  piso_len;\n    reg [9:0] piso_len_next;"
c = src.count(old)
assert c == 1, f"anchor count={c}"
src = src.replace(old, new)
open(F, "w").write(src)
assert "max_fanout" in open(F).read()
print("APPLIED + POST-VERIFIED")
