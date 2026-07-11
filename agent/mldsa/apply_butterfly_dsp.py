#!/usr/bin/env python3
import shutil
import sys, os
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/PQC/hqc/agent/mldsa/mldsa_src"
F = os.path.join(D, "butterfly.v")
shutil.copy(F, F + ".bak2")
src = open(F).read()

EDITS = [
("    reg [45:0] mult_result;",
 "    reg [45:0] mult_result;\n    reg [45:0] mult_p = 0;"),
("        barrett_datai  <= mult_result;",
 "        mult_p         <= mult_result;\n        barrett_datai  <= mult_p;"),
("    reg [23:0] aj3  [4:0];",
 "    reg [23:0] aj3  [5:0];"),
("        aj3[4] = 0;",
 "        aj3[4] = 0;\n        aj3[5] = 0;"),
("        aj3[4] <= aj3[3];",
 "        aj3[4] <= aj3[3];\n        aj3[5] <= aj3[4];"),
("            adda = aj3[4];",
 "            adda = aj3[5];"),
("            suba = aj3[4];",
 "            suba = aj3[5];"),
("""            if (aj3[4][0] == 1)
                aj5 <= (aj3[4] >> 1) + (DILITHIUM_Q + 1) / 2;
            else
                aj5 <= (aj3[4] >> 1);""",
 """            if (aj3[5][0] == 1)
                aj5 <= (aj3[5] >> 1) + (DILITHIUM_Q + 1) / 2;
            else
                aj5 <= (aj3[5] >> 1);"""),
("            aj4    <= aj3[3];",
 "            aj4    <= aj3[4];"),
("            valido = valid_sr[8];",
 "            valido = valid_sr[9];"),
("""        else if (mode == MULT_MODE)
            valido = valid_sr[7];""",
 """        else if (mode == MULT_MODE)
            valido = valid_sr[8];"""),
("""        else if (mode == FORWARD_NTT_MODE)
            valido = valid_sr[7];""",
 """        else if (mode == FORWARD_NTT_MODE)
            valido = valid_sr[8];"""),
]

for i, (old, new) in enumerate(EDITS, 1):
    c = src.count(old)
    assert c == 1, f"EDIT {i}: anchor count={c} (expected 1)"
    src = src.replace(old, new)
    print(f"applied {i}/12")

open(F, "w").write(src)

final = open(F).read()
for k in ["mult_p", "aj3  [5:0]", "aj3[5] <= aj3[4]", "valid_sr[9]",
          "barrett_datai  <= mult_p;"]:
    assert k in final, f"POST-CHECK FAILED: {k}"
print("ALL 12 APPLIED + POST-VERIFIED")
