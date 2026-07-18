#!/usr/bin/env python3
"""Binary-search the largest truly-closing frequency (WNS>=0) for a checkpoint
under a fixed directive recipe. Usage: python3 agent/fmax_search.py <ckpt> <tag> [lo_ns] [hi_ns]"""
import sys, os, re, subprocess, json
ckpt, tag = sys.argv[1], sys.argv[2]
lo = float(sys.argv[3]) if len(sys.argv) > 3 else 6.0   # period known to fail
hi = float(sys.argv[4]) if len(sys.argv) > 4 else 12.0  # period expected to pass
best = None
for it in range(5):
    mid = round((lo + hi) / 2, 2)
    rpt = f"/tmp/fsrch_{tag}_{mid}.rpt"
    tcl = f"""open_checkpoint {ckpt}
set_property SEVERITY {{Warning}} [get_drc_checks MDRV-1]
set_msg_config -id {{Opt 31-37}} -new_severity WARNING
set clk_port [lindex [get_ports -quiet {{clk clk_i}}] 0]
if {{$clk_port eq ""}} {{ set clk_port [lindex [get_ports -quiet *clk*] 0] }}
create_clock -period {mid:.3f} -name clk [get_ports $clk_port]
catch {{opt_design}}
place_design -directive ExtraTimingOpt
phys_opt_design -directive Explore
route_design -directive Explore
report_timing_summary -file {rpt}
puts "DONE"
"""
    open(f"/tmp/fsrch_{tag}_{mid}.tcl","w").write(tcl)
    subprocess.run(["vivado","-mode","batch","-source",f"/tmp/fsrch_{tag}_{mid}.tcl",
                    "-journal",f"/tmp/fsrch_{tag}_{mid}.jou","-log",f"/tmp/fsrch_{tag}_{mid}.log"],
                   text=True, stdout=subprocess.DEVNULL)
    txt = open(rpt).read() if os.path.exists(rpt) else ""
    m = re.search(r"Slack \((VIOLATED|MET)\)\s*:\s*(-?[\d.]+)", txt)
    if not m: print(f"iter {it}: {mid}ns NO RESULT"); break
    met = m.group(1) == "MET"; wns = float(m.group(2))
    print(f"iter {it}: {mid}ns -> WNS {wns} ({'MET' if met else 'VIOL'})")
    if met: best = (mid, wns); hi = mid
    else: lo = mid
print(json.dumps({"tag": tag, "closing_period_ns": best[0] if best else None,
                  "closing_fmax_mhz": round(1000/best[0],1) if best else None,
                  "wns_at_close": best[1] if best else None}))
