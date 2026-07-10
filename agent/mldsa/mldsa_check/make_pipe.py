#!/usr/bin/env python3
# Timing-improving pipeline: split heavy stage a0_1<=a0_0-(a1_0*2gamma2) into:
#   mult_s <= a1_0*2gamma2   (cycle 1)
#   a0_1   <= a0_0_d - mult_s (cycle 2)
# a0_0 delayed (a0_0_d), a1 path +1 stage (a1_3), valid_sr +1.
import sys
s = open(sys.argv[1]).read()
s = s.replace("reg [4:0] valid_sr = 0;", "reg [5:0] valid_sr = 0;")
s = s.replace("valid_o = valid_sr[4];", "valid_o = valid_sr[5];")
s = s.replace("valid_sr <= (rst) ? 0 : {valid_sr[3:0], valid_i};",
              "valid_sr <= (rst) ? 0 : {valid_sr[4:0], valid_i};")
s = s.replace(
    "reg signed [55:0] a1_0, a1_1, a1_2, a0_0, a0_1, a0_2;",
    "reg signed [55:0] a1_0, a1_1, a1_2, a1_3, a0_0, a0_0_d, a0_1, a0_2;\n"
    "    reg signed [55:0] mult_s;")
s = s.replace("a1_2 <= a1_1;\n            dob  <= a1_2;",
              "a1_2 <= a1_1;\n            a1_3 <= a1_2;\n            dob  <= a1_3;")
s = s.replace("a0_0 <= di_buffer;",
              "a0_0 <= di_buffer;\n            a0_0_d <= a0_0;")
s = s.replace(
"""            if (sec_lvl == 2) begin
                a0_1 <= a0_0 - ((a1_0 << 17) + (a1_0 << 16) - (a1_0 << 12) - (a1_0 << 11));
            end else begin
                a0_1 <= a0_0 - ((a1_0 << 19) - (a1_0 << 9));
            end""",
"""            if (sec_lvl == 2) begin
                mult_s <= (a1_0 << 17) + (a1_0 << 16) - (a1_0 << 12) - (a1_0 << 11);
            end else begin
                mult_s <= (a1_0 << 19) - (a1_0 << 9);
            end
            a0_1 <= a0_0_d - mult_s;""")
open(sys.argv[2],"w").write(s)
print(f"wrote {sys.argv[2]}")
