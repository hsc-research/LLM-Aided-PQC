#!/usr/bin/env python3
import shutil, sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/PQC/hqc/agent/mldsa/mldsa_src"
F = D + "/gen_c.v"
shutil.copy(F, F + ".bak")
src = open(F).read()
EDITS = [
("    reg [7:0] sample_addr;",
 "    reg [7:0] sample_addr;\n    (* max_fanout = 16 *) reg [7:0] sample_addr_r = 0;"),
("            sample_addr = dout_buffer[{4'd7-ctr[2:0],3'd0}+:8];",
 "            sample_addr = sample_addr_r;  // precomputed 1 cycle ahead from dout"),
("""        S_SAMPLEC: begin
            if (sample_no <= 255) begin""",
 """        S_STALL: begin
            sample_addr_r <= dout[{4'd7-ctr[2:0],3'd0}+:8];
        end
        S_SAMPLEC: begin
            sample_addr_r <= dout[{4'd7-ctr_next[2:0],3'd0}+:8];
            if (sample_no <= 255) begin"""),
]
for i, (old, new) in enumerate(EDITS, 1):
    c = src.count(old)
    assert c == 1, f"EDIT {i}: anchor count={c}"
    src = src.replace(old, new)
    print(f"applied {i}/3")
open(F, "w").write(src)
final = open(F).read()
assert "sample_addr_r" in final and final.count("sample_addr_r") >= 4
print("ALL 3 APPLIED + POST-VERIFIED")
