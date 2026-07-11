#!/usr/bin/env python3
import shutil
SRC = "/mnt/c/PQC/ML_DSA/ML-DSA-OSH-main_7653/ML-DSA-OSH-main/ref_combined/src/operation_module.v"
import sys, os
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/PQC/hqc/agent/mldsa/mldsa_src"
DST = os.path.join(D, "operation_module.v")
shutil.copy(SRC, DST + ".bak")
src = open(SRC).read()

EDITS = [
# --- MULT drain extension for +1 mult latency ---
("    reg [7:0] valid_sr = 0;",
 "    reg [8:0] valid_sr = 0;  // widened: MULT valido now +1 cycle"),
("                if (running)\n                    valid_sr <= {valid_sr[6:0], valido_bf};",
 "                if (running)\n                    valid_sr <= {valid_sr[7:0], valido_bf};"),
("if (running && ~done_addr && ~done_latch)\n                    valid_sr <= {valid_sr[6:0], 1'b1};",
 "if (running && ~done_addr && ~done_latch)\n                    valid_sr <= {valid_sr[7:0], 1'b1};"),
("if (running && ~done_addr && ~done_latch)\n                    valid_sr <= {valid_sr[7:0], 1'b1};\n                else \n                    valid_sr <= {valid_sr[6:0], 1'b0};",
 "if (running && ~done_addr && ~done_latch)\n                    valid_sr <= {valid_sr[7:0], 1'b1};\n                else \n                    valid_sr <= {valid_sr[7:0], 1'b0};"),
("                else if (done_latch && valid_sr[6:0] == 0) begin",
 "                else if (done_latch && valid_sr[7:0] == 0) begin"),

("    reg [5:0] addr1_sr [23:0];",
 "    reg [5:0] addr1_sr [25:0];"),
("""        for (i = 0; i < 23; i = i + 1)
            addr1_sr[i] = 0;""",
 """        for (i = 0; i < 25; i = i + 1)
            addr1_sr[i] = 0;"""),
("""            for (i = 0; i < 23; i = i + 1)
                addr1_sr[i] <= 0;""",
 """            for (i = 0; i < 25; i = i + 1)
                addr1_sr[i] <= 0;"""),
("""                for (i = 0; i < 23; i = i + 1)
                    addr1_sr[i+1] <= addr1_sr[i];""",
 """                for (i = 0; i < 25; i = i + 1)
                    addr1_sr[i+1] <= addr1_sr[i];"""),
("            addrb1 = addr1_sr[21];",
 "            addrb1 = addr1_sr[23];"),
("            addrb1 = addr1_sr[22];",
 "            addrb1 = addr1_sr[24];"),
("            addrb2 = addr1_sr[8];",
 "            addrb2 = addr1_sr[9];"),
("                    pause <= (pause_ctr == 6) ? 0 : 1;",
 "                    pause <= (pause_ctr == 8) ? 0 : 1;"),
("                    pause <= (pause_ctr == 4) ? 0 : 1;",
 "                    pause <= (pause_ctr == 6) ? 0 : 1;"),
]

for i, (old, new) in enumerate(EDITS, 1):
    c = src.count(old)
    assert c == 1, f"EDIT {i}: anchor count={c} (expected 1)"
    src = src.replace(old, new)
    print(f"applied {i}/9")

open(DST, "w").write(src)
final = open(DST).read()
for k in ["addr1_sr [25:0]", "addr1_sr[23];", "addr1_sr[24];", "addr1_sr[9];",
          "pause_ctr == 8"]:
    assert k in final, f"POST-CHECK FAILED: {k}"
assert "addr1_sr[21]" not in final and "addr1_sr[22]" not in final
print("ALL 9 APPLIED + POST-VERIFIED ->", DST)
