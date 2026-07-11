#!/usr/bin/env python3
import shutil
SRC = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src/butterfly2x2.v"
import sys, os
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/PQC/hqc/agent/mldsa/mldsa_src"
DST = os.path.join(D, "butterfly2x2.v")
shutil.copy(SRC, DST + ".bak")   # pristine-of-record in override dir
src = open(SRC).read()

# ORDER MATTERS: INTT [8]->[9] before FNTT [7]->[8]
EDITS = [
("    reg [23:0] z2_sr [8:0];\n    reg [23:0] z3_sr [8:0];",
 "    reg [23:0] z2_sr [9:0];\n    reg [23:0] z3_sr [9:0];"),
# INTT retap
("            z2 = z2_sr[8];\n            z3 = z3_sr[8];",
 "            z2 = z2_sr[9];\n            z3 = z3_sr[9];"),
# FNTT retap
("            z2 = z2_sr[7];\n            z3 = z3_sr[7];",
 "            z2 = z2_sr[8];\n            z3 = z3_sr[8];"),
# initial loop
("        for (i = 0; i < 8; i = i + 1) begin",
 "        for (i = 0; i < 10; i = i + 1) begin"),
# rst loop
("            for (i = 0; i < 9; i = i + 1) begin",
 "            for (i = 0; i < 10; i = i + 1) begin"),
# shift loops (two identical -> one combined anchor)
("""            for (i = 1; i < 9; i = i + 1)
                z2_sr[i] <= z2_sr[i-1];
            for (i = 1; i < 9; i = i + 1)
                z3_sr[i] <= z3_sr[i-1];""",
 """            for (i = 1; i < 10; i = i + 1)
                z2_sr[i] <= z2_sr[i-1];
            for (i = 1; i < 10; i = i + 1)
                z3_sr[i] <= z3_sr[i-1];"""),
]

for i, (old, new) in enumerate(EDITS, 1):
    c = src.count(old)
    assert c == 1, f"EDIT {i}: anchor count={c} (expected 1)"
    src = src.replace(old, new)
    print(f"applied {i}/6")

open(DST, "w").write(src)

final = open(DST).read()
for k in ["z2_sr [9:0]", "z2_sr[9];", "z2_sr[8];", "i < 10"]:
    assert k in final, f"POST-CHECK FAILED: {k}"
assert "z2_sr[7];" not in final
print("ALL 6 APPLIED + POST-VERIFIED ->", DST)
