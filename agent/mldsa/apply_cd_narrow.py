#!/usr/bin/env python3
import shutil, sys
D = sys.argv[1] if len(sys.argv) > 1 else "/mnt/c/PQC/hqc/agent/mldsa/mldsa_src"
F = D + "/coeff_decomposer.v"
shutil.copy(F, F + ".bak")
src = open(F).read()
old = "    reg signed [55:0] a1_0, a1_1, a1_2, a0_0, a0_1, a0_2;"
n = src.count(old)
assert n == 1, f"anchor count={n}"
src = src.replace(old,
  "    reg signed [27:0] a1_0, a1_1, a1_2, a0_0, a0_1, a0_2;  // narrowed 56->28b: max |a0_1| < 2^26")
open(F, "w").write(src)
print("applied 1/1")
final = open(F).read()
assert "[27:0] a1_0" in final and "[55:0]" not in final
print("APPLIED + POST-VERIFIED")
