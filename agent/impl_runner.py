#!/usr/bin/env python3
"""Post-P&R implementation run (GMU-comparable flow): synth (default mode,
with IO buffers) -> opt -> place -> phys_opt -> route -> timing/util reports.
Usage: python3 agent/impl_runner.py <module> [period_ns] [--pristine]
Long run: 1-3h at 54k LUT / 12GB WSL. Reports in synth_out/impl_<module>/.
"""
import sys, os, re, subprocess, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from synthesizer import MODULE_SOURCES, VHDL_SOURCES, PART, TOP_OVERRIDE

module = sys.argv[1]
period = float(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else 8.6
key = module + ("_pristine" if "--pristine" in sys.argv else "")
srcs = MODULE_SOURCES[key]
vhdl = VHDL_SOURCES.get(key, [])
top = TOP_OVERRIDE.get(key, TOP_OVERRIDE.get(module, module))
out = f"./synth_out/impl_{key}"
os.makedirs(out, exist_ok=True)

vhdl_block = ""
if vhdl:
    vhdl_block = "read_vhdl {\n  " + "\n  ".join(vhdl) + "\n}\n"

tcl = f"""{vhdl_block}read_verilog {{
  {"  ".join(chr(10)+s for s in srcs)}
}}
synth_design -top {top} -part {PART}
set clk_port [lindex [get_ports -quiet {{clk clk_i}}] 0]
if {{$clk_port eq ""}} {{ set clk_port [lindex [get_ports -quiet *clk*] 0] }}
create_clock -period {period:.3f} -name clk [get_ports $clk_port]
opt_design
place_design
phys_opt_design
route_design
report_timing_summary -file {out}/timing_postroute.rpt
report_utilization -file {out}/util_postroute.rpt
report_power -file {out}/power_postroute.rpt
puts "=== IMPL DONE: {key} ==="
"""
tclf = os.path.join(out, "impl.tcl")
open(tclf, "w").write(tcl)
r = subprocess.run(["vivado", "-mode", "batch", "-source", tclf,
                    "-journal", out + "/vivado.jou", "-log", out + "/vivado.log"],
                   text=True)
rpt = open(out + "/timing_postroute.rpt").read() if os.path.exists(out + "/timing_postroute.rpt") else ""
m = re.search(r"WNS\(ns\)\s*.*?\n.*?\n\s*(-?[\d.]+)", rpt)
wns = float(m.group(1)) if m else None
fmax = round(1000.0 / (period - wns), 1) if wns is not None else None
print(json.dumps({"module": key, "period": period, "postroute_wns": wns,
                  "achievable_fmax_mhz": fmax}))
