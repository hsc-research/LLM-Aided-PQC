#!/usr/bin/env python3
"""Flow-space directive search (roadmap Vector 1): synth ONCE, then sweep
place_design x phys_opt_design directives at a fixed constraint, reusing the
post-synth checkpoint. Post-route fmax per combo -> flow_sweep_log.jsonl.
Usage: python3 agent/flow_sweep.py <module> [period_ns] [--pristine]
"""
import sys, os, re, subprocess, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from synthesizer import MODULE_SOURCES, VHDL_SOURCES, PART, TOP_OVERRIDE

module = sys.argv[1]
period = float(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else 5.0
key = module + ("_pristine" if "--pristine" in sys.argv else "")
srcs = MODULE_SOURCES[key]
vhdl = VHDL_SOURCES.get(key, [])
top = TOP_OVERRIDE.get(key, TOP_OVERRIDE.get(module, module))
out = f"./synth_out/sweep_{key}"
os.makedirs(out, exist_ok=True)
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flow_sweep_log.jsonl")

# directive combos: (place, phys_opt, route). Curated, not full cross-product.
COMBOS = [
    ("Default",                 "Default",            "Default"),
    ("Explore",                 "Explore",            "Explore"),
    ("ExtraNetDelay_high",      "AggressiveExplore",  "Explore"),
    ("ExtraNetDelay_low",       "AggressiveExplore",  "Explore"),
    ("SSI_SpreadLogic_high",    "AggressiveExplore",  "Explore"),
    ("AltSpreadLogic_high",     "Explore",            "AggressiveExplore"),
    ("ExtraPostPlacementOpt",   "AggressiveExplore",  "AggressiveExplore"),
]

vhdl_block = ""
if vhdl:
    vhdl_block = "read_vhdl {\n  " + "\n  ".join(vhdl) + "\n}\n"
ckpt = f"{out}/post_synth_grade{PART.rsplit(chr(45),1)[1]}.dcp"

# 1) synth once -> checkpoint
synth_tcl = f"""{vhdl_block}read_verilog {{
  {"  ".join(chr(10)+s for s in srcs)}
}}
synth_design -top {top} -part {PART}
set clk_port [lindex [get_ports -quiet {{clk clk_i}}] 0]
if {{$clk_port eq ""}} {{ set clk_port [lindex [get_ports -quiet *clk*] 0] }}
create_clock -period {period:.3f} -name clk [get_ports $clk_port]
write_checkpoint -force {ckpt}
puts "=== SYNTH CKPT DONE ==="
"""
open(f"{out}/synth.tcl", "w").write(synth_tcl)
print("Synthesizing once ->", ckpt)
subprocess.run(["vivado","-mode","batch","-source",f"{out}/synth.tcl",
                "-journal",f"{out}/synth.jou","-log",f"{out}/synth.log"], text=True)
if not os.path.exists(ckpt):
    print("SYNTH FAILED — see", f"{out}/synth.log"); sys.exit(1)

def fmax_from(rpt):
    try: txt = open(rpt).read()
    except OSError: return None, None
    m = re.search(r"Slack \(VIOLATED\)\s*:\s*(-?[\d.]+)", txt) or \
        re.search(r"Slack \(MET\)\s*:\s*(-?[\d.]+)", txt)
    if not m: return None, None
    wns = float(m.group(1))
    return wns, round(1000.0/(period - wns), 1)

results = []
for pl, po, rt in COMBOS:
    tag = f"{pl}__{po}__{rt}"
    rpt = f"{out}/timing_{tag}.rpt"
    impl_tcl = f"""open_checkpoint {ckpt}
opt_design
place_design -directive {pl}
phys_opt_design -directive {po}
route_design -directive {rt}
report_timing_summary -file {rpt}
puts "=== IMPL {tag} DONE ==="
"""
    open(f"{out}/impl_{tag}.tcl", "w").write(impl_tcl)
    t0 = time.time()
    subprocess.run(["vivado","-mode","batch","-source",f"{out}/impl_{tag}.tcl",
                    "-journal",f"{out}/impl_{tag}.jou","-log",f"{out}/impl_{tag}.log"], text=True)
    wns, fmax = fmax_from(rpt)
    rec = {"module": key, "period": period, "place": pl, "phys_opt": po,
           "route": rt, "wns": wns, "fmax_mhz": fmax,
           "runtime_s": round(time.time()-t0,1), "ts": time.strftime("%H:%M:%S")}
    open(LOG,"a").write(json.dumps(rec)+"\n")
    results.append(rec)
    print(f"{tag}: WNS {wns} | fmax {fmax} MHz | {rec['runtime_s']}s")

best = max((r for r in results if r["fmax_mhz"]), key=lambda r: r["fmax_mhz"], default=None)
print("\n=== BEST ===")
print(json.dumps(best, indent=2) if best else "no valid result")
