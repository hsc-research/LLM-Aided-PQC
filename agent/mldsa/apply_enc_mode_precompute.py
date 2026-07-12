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
# registered mode/lvl pipes aligned to the data pipes:
# mode_r  (1 deep)  pairs with di_buffer        -> feeds uncenter_coeff
# lvl_r2  (2 deep)  pairs with di_uncentered_buffer -> feeds zero_strip
# buffer_len keeps combinational ENCODE_LVL (same-cycle with valid_i) - unchanged
("    reg [1:0] valid_buffer;",
 """    reg [1:0] valid_buffer;
    (* max_fanout = 16 *) reg [2:0] mode_r = 0;
    (* max_fanout = 16 *) reg [4:0] lvl_r1 = 0, lvl_r2 = 0;"""),
# uncenter consumes registered mode (aligned with di_buffer)
("            uncenter_coeff UNCENTER (sec_lvl, mode, di_buffer[23*i+:23], di_uncentered[23*i+:23]);",
 "            uncenter_coeff UNCENTER (sec_lvl, mode_r, di_buffer[23*i+:23], di_uncentered[23*i+:23]);"),
# zero_strip consumes 2-deep registered lvl (aligned with di_uncentered_buffer)
("    zero_strip Z_STRIP(ENCODE_LVL, di_uncentered_buffer, stripped);",
 "    zero_strip Z_STRIP(lvl_r2, di_uncentered_buffer, stripped);"),
# register the pipes
("        di_buffer <= di;",
 """        di_buffer <= di;
        mode_r <= mode;
        lvl_r1 <= ENCODE_LVL;
        lvl_r2 <= lvl_r1;"""),
]
for i, (old, new) in enumerate(EDITS, 1):
    c = src.count(old)
    assert c == 1, f"EDIT {i}: anchor count={c}"
    src = src.replace(old, new)
    print(f"applied {i}/4")
open(F, "w").write(src)
final = open(F).read()
assert final.count("mode_r") == 3 and final.count("lvl_r2") == 3
print("ALL 4 APPLIED + POST-VERIFIED")
