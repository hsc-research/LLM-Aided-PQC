#!/usr/bin/env python3
# Round-2: INTT-only +1 input-side stage. Registers subtractor/adder into
# sub_r/add_r before ajlen2_INTT/aj2 load them (INTT branch only).
# INTT total latency +2 vs pristine; FNTT/MULT stay +1. Layered on top of
# the committed round-1 state (apply AFTER the three round-1 scripts, or
# on the committed mldsa_src which already contains round-1).
# Edits three files. Every anchor assert count==1; trailing-whitespace
# anchors probed via repr() beforehand.
import sys, os

D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/PQC/hqc/agent/mldsa/mldsa_src"

def apply(fname, edits):
    p = os.path.join(D, fname)
    s = open(p).read()
    for i, (old, new) in enumerate(edits, 1):
        c = s.count(old)
        assert c == 1, f"{fname} EDIT {i}: anchor count={c} (expected 1)"
        s = s.replace(old, new)
        print(f"{fname} applied {i}/{len(edits)}")
    open(p, "w").write(s)

# ---------------- butterfly.v ----------------
BF = [
# new regs
("    reg [45:0] mult_p = 0;",
 "    reg [45:0] mult_p = 0;\n    reg [23:0] sub_r = 0, add_r = 0;   // round-2: INTT input-side stage\n    reg [23:0] zeta_delay3 = 0;"),
# register subtractor/adder every cycle (harmless outside INTT; only INTT consumes)
("        mult_p         <= mult_result;",
 "        sub_r          <= subtractor;\n        add_r          <= adder;\n        mult_p         <= mult_result;"),
# zeta_delay3 for INTT multb (+1 on zeta path to match operand delay)
("        zeta_delay2 <= zeta_delay;",
 "        zeta_delay2 <= zeta_delay;\n        zeta_delay3 <= zeta_delay2;"),
("        multb = (modei == INVERSE_NTT_MODE) ? zeta_delay2 : zeta_delay;",
 "        multb = (modei == INVERSE_NTT_MODE) ? zeta_delay3 : zeta_delay;"),
# INTT loads from the registered stage
# a-lane (adder->aj2->aj3 pipe) already gets +1 from the aj3[5]->[6] retap;
# only the multiply operand (subtractor->ajlen2_INTT) takes the sub_r stage.
("            aj2    <= adder;\n            ajlen2_INTT <= subtractor;",
 "            aj2    <= adder;\n            ajlen2_INTT <= sub_r;"),
# INTT output-side pipe +1: aj3 widen [5:0]->[6:0], INTT taps 5->6
("    reg [23:0] aj3  [5:0];",
 "    reg [23:0] aj3  [6:0];"),
("        aj3[5] = 0;",
 "        aj3[5] = 0;\n        aj3[6] = 0;"),
("        aj3[5] <= aj3[4];",
 "        aj3[5] <= aj3[4];\n        aj3[6] <= aj3[5];"),
# INTT aj5 source 5->6 (both odd/even branches read aj3[5] in INTT after round-1)
("            if (aj3[5][0] == 1)\n                aj5 <= (aj3[5] >> 1) + (DILITHIUM_Q + 1) / 2;\n            else\n                aj5 <= (aj3[5] >> 1);",
 "            if (aj3[6][0] == 1)\n                aj5 <= (aj3[6] >> 1) + (DILITHIUM_Q + 1) / 2;\n            else\n                aj5 <= (aj3[6] >> 1);"),
# NOTE: FNTT adda/suba stay aj3[5]; MULT aj4 stays aj3[4] (round-1 values).
# INTT valido tap +1: [9] -> [10]; widen valid_sr 10 -> 11 bits
("    reg [9:0] valid_sr;",
 "    reg [10:0] valid_sr;"),
("            valid_sr <= {valid_sr[8:0], validi};",
 "            valid_sr <= {valid_sr[9:0], validi};"),
("        if (mode == INVERSE_NTT_MODE) \n            valido = valid_sr[9];",
 "        if (mode == INVERSE_NTT_MODE) \n            valido = valid_sr[10];"),
]

# ---------------- butterfly2x2.v ----------------
# INTT z-tap 9 -> 10; widen z2_sr/z3_sr [9:0] -> [10:0]
B2 = [
("    reg [23:0] z2_sr [9:0];\n    reg [23:0] z3_sr [9:0];",
 "    reg [23:0] z2_sr [10:0];\n    reg [23:0] z3_sr [10:0];"),
("        for (i = 0; i < 10; i = i + 1) begin\n            z2_sr[i] = 0;",
 "        for (i = 0; i < 11; i = i + 1) begin\n            z2_sr[i] = 0;"),
("            for (i = 0; i < 10; i = i + 1) begin\n                z2_sr[i] <= 0;",
 "            for (i = 0; i < 11; i = i + 1) begin\n                z2_sr[i] <= 0;"),
("            for (i = 1; i < 10; i = i + 1)\n                z2_sr[i] <= z2_sr[i-1];",
 "            for (i = 1; i < 11; i = i + 1)\n                z2_sr[i] <= z2_sr[i-1];"),
("            for (i = 1; i < 10; i = i + 1)\n                z3_sr[i] <= z3_sr[i-1];",
 "            for (i = 1; i < 11; i = i + 1)\n                z3_sr[i] <= z3_sr[i-1];"),
("            z2 = z2_sr[9];\n            z3 = z3_sr[9];",
 "            z2 = z2_sr[10];\n            z3 = z3_sr[10];"),
]

# ---------------- operation_module.v ----------------
# INTT writeback +1: addr1_sr [24] -> [25] (array already [25:0] from round-1).
# INTT pause-drain 6 -> 7 (round-1 value; pristine was 4).
# INTT: writeback is addrb1 (via data_out FIFO path), web1=valid_sr[3] is
# valido_bf-relative and AUTO-TRACKS the +1 (valid_sr shifts in valido_bf).
# Only the unconditional addr delay tap and the pause drain need +1.
OM = [
("    reg [5:0] addr1_sr [25:0];",
 "    reg [5:0] addr1_sr [26:0];"),
("""        for (i = 0; i < 25; i = i + 1)
            addr1_sr[i] = 0;""",
 """        for (i = 0; i < 26; i = i + 1)
            addr1_sr[i] = 0;"""),
("""            for (i = 0; i < 25; i = i + 1)
                addr1_sr[i] <= 0;""",
 """            for (i = 0; i < 26; i = i + 1)
                addr1_sr[i] <= 0;"""),
("""                for (i = 0; i < 25; i = i + 1)
                    addr1_sr[i+1] <= addr1_sr[i];""",
 """                for (i = 0; i < 26; i = i + 1)
                    addr1_sr[i+1] <= addr1_sr[i];"""),
("            addrb1 = addr1_sr[24];",
 "            addrb1 = addr1_sr[26];"),
("                    pause <= (pause_ctr == 6) ? 0 : 1;",
 "                    pause <= (pause_ctr == 8) ? 0 : 1;"),
]

apply("butterfly.v", BF)
apply("butterfly2x2.v", B2)
apply("operation_module.v", OM)
print("ALL APPLIED — round-2 INTT input stage")
