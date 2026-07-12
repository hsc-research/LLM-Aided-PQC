#!/usr/bin/env python3
import shutil, sys, os
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/PQC/hqc/agent/mldsa/mldsa_src"
SRC = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src/encoder.v"
F = os.path.join(D, "encoder.v")
if not os.path.exists(F):
    shutil.copy(SRC, F)
shutil.copy(F, F + ".bak")
src = open(F).read()
EDITS = [
# 1. declare stripped_r + widen pipes
("    reg [1:0] valid_buffer;",
 "    reg [2:0] valid_buffer;\n    reg [MAX_LVL*OUTPUT_W-1:0] stripped_r = 0;"),
("    reg [9:0] buffer_len [1:0];",
 "    reg [9:0] buffer_len [2:0];"),
# 2. register stripped, extend valid/len pipes
("        valid_buffer[1] <= valid_buffer[0];",
 "        valid_buffer[1] <= valid_buffer[0];\n        valid_buffer[2] <= valid_buffer[1];\n        stripped_r      <= stripped;"),
("        buffer_len[1] <= buffer_len[0];",
 "        buffer_len[1] <= buffer_len[0];\n        buffer_len[2] <= buffer_len[1];"),
# 3. retap consumers +1
("        piso_len <= piso_len_next + buffer_len[1];",
 "        piso_len <= piso_len_next + buffer_len[2];"),
("            if (valid_buffer[1]) begin",
 "            if (valid_buffer[2]) begin"),
("                    PISO <= (PISO >> W) | ({192'd0, stripped} << piso_len_next);",
 "                    PISO <= (PISO >> W) | ({192'd0, stripped_r} << piso_len_next);"),
("                    PISO <= PISO | ({192'd0, stripped} << piso_len_next);",
 "                    PISO <= PISO | ({192'd0, stripped_r} << piso_len_next);"),
]
for i, (old, new) in enumerate(EDITS, 1):
    c = src.count(old)
    assert c == 1, f"EDIT {i}: anchor count={c}"
    src = src.replace(old, new)
    print(f"applied {i}/8")
open(F, "w").write(src)
final = open(F).read()
assert final.count("stripped_r") == 4 and "valid_buffer[2]" in final and "buffer_len[2]" in final
print("ALL 8 APPLIED + POST-VERIFIED")
