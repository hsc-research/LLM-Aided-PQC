import shutil, sys
E = {
 "build/joint_design/data_path.v": (
  "\n      dout_internal <= dout_ram[dout_ram_idx * `PARALLEL_SLICES + dout_idx * `WOUT + `PARALLEL_SLICES - 1 -:\n",
  "\n      dout_internal = dout_ram[dout_ram_idx * `PARALLEL_SLICES + dout_idx * `WOUT + `PARALLEL_SLICES - 1 -:\n"),
 "build/joint_design/onegen.v": (
  "\n                state = s_wait_start;\n",
  "\n                state <= s_wait_start;\n"),
 "build/joint_design/onegen_ct.v": (
  "\n                state = s_wait_start;\n",
  "\n                state <= s_wait_start;\n"),
}
for p, (old, new) in E.items():
    s = open(p).read()
    n = s.count(old)
    if n != 1:
        print(f"ANCHOR_FAIL {p} count={n}"); sys.exit(1)
for p, (old, new) in E.items():
    shutil.copy(p, p + ".bak")
    s = open(p).read()
    open(p, "w").write(s.replace(old, new))
    print(f"EDITED {p}")
