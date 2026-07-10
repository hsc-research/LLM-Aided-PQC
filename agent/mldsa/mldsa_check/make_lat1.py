#!/usr/bin/env python3
import sys
s = open(sys.argv[1]).read()
s = s.replace("reg [4:0] valid_sr = 0;", "reg [5:0] valid_sr = 0;")
s = s.replace("valid_o = valid_sr[4];", "valid_o = valid_sr[5];")
s = s.replace("valid_sr <= (rst) ? 0 : {valid_sr[3:0], valid_i};",
              "valid_sr <= (rst) ? 0 : {valid_sr[4:0], valid_i};")
s = s.replace("reg signed [55:0] a1_0, a1_1, a1_2, a0_0, a0_1, a0_2;",
              "reg signed [55:0] a1_0, a1_1, a1_2, a0_0, a0_1, a0_2;\n    reg [23:0] doa_p, dob_p;")
s = s.replace("dob  <= a1_2;",
              "dob_p <= a1_2;\n            dob   <= dob_p;")
s = s.replace("doa  <= (a0_2 < 0) ? a0_2 + Q : a0_2;",
              "doa_p <= (a0_2 < 0) ? a0_2 + Q : a0_2;\n            doa   <= doa_p;")
open(sys.argv[2],"w").write(s)
print(f"wrote {sys.argv[2]}")
for ln in s.splitlines():
    if any(k in ln for k in ["valid_sr","valid_o =","doa_p","dob_p","doa  <=","dob   <="]):
        print("   ", ln.strip())
