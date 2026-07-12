#!/usr/bin/env python3
import shutil, sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/PQC/hqc/agent/mldsa/mldsa_src"
F = D + "/decoder.v"
shutil.copy(F, F + ".bak")
src = open(F).read()
EDITS = [
# declare per-lane signed diffs
("    reg [199:0] SIPO_OUT;",
 "    reg [199:0] SIPO_OUT;\n    reg signed [24:0] sd_t0 [3:0];\n    reg signed [24:0] sd_z  [3:0];"),
# T0: single subtract + sign select
("""                sipo_out_in[i*COEFF_W+:COEFF_W] =  (SIPO_IN[i*13+:13] > 4096) ? DILITHIUM_Q - SIPO_IN[i*13+:13] + 4096 : 4096 - SIPO_IN[i*13+:13];""",
 """            begin
                sd_t0[i] = $signed(25'd4096) - $signed({12'd0, SIPO_IN[i*13+:13]});
                sipo_out_in[i*COEFF_W+:COEFF_W] = sd_t0[i][24] ? sd_t0[i] + $signed({2'd0, DILITHIUM_Q}) : sd_t0[i];
            end"""),
# Z sec2 (GAMMA1_2, 18b)
("""                    sipo_out_in[i*COEFF_W+:COEFF_W] = (SIPO_IN[i*18+:18] > GAMMA1_2) ? GAMMA1_2 + (DILITHIUM_Q - SIPO_IN[i*18+:18]) : GAMMA1_2 - SIPO_IN[i*18+:18];""",
 """                begin
                    sd_z[i] = $signed({7'd0, GAMMA1_2}) - $signed({7'd0, SIPO_IN[i*18+:18]});
                    sipo_out_in[i*COEFF_W+:COEFF_W] = sd_z[i][24] ? sd_z[i] + $signed({2'd0, DILITHIUM_Q}) : sd_z[i];
                end"""),
# Z sec3/5 (GAMMA1_35, 20b)
("""                    sipo_out_in[i*COEFF_W+:COEFF_W] = (SIPO_IN[i*20+:20] > GAMMA1_35) ? GAMMA1_35 + DILITHIUM_Q - SIPO_IN[i*20+:20] : GAMMA1_35 - SIPO_IN[i*20+:20];""",
 """                begin
                    sd_z[i] = $signed({5'd0, GAMMA1_35}) - $signed({5'd0, SIPO_IN[i*20+:20]});
                    sipo_out_in[i*COEFF_W+:COEFF_W] = sd_z[i][24] ? sd_z[i] + $signed({2'd0, DILITHIUM_Q}) : sd_z[i];
                end"""),
]
for i, (old, new) in enumerate(EDITS, 1):
    c = src.count(old)
    assert c == 1, f"EDIT {i}: anchor count={c}"
    src = src.replace(old, new)
    print(f"applied {i}/4")
open(F, "w").write(src)
final = open(F).read()
assert final.count("sd_t0") >= 3 and final.count("sd_z") >= 5
print("ALL 4 APPLIED + POST-VERIFIED")
