# HQC Agent - Top-N Critical Path Extractor
# Runs OOC synthesis for a module and extracts the top-N worst timing paths
# as structured records, then groups them by source/destination block so
# shared structure across paths is visible.
#
# Usage: python3 agent/path_extractor.py <module> <param_set> <N>
# Example: python3 agent/path_extractor.py encap hqc128 10

import subprocess, re, sys, os

sys.path.insert(0, os.path.dirname(__file__))
from synthesizer import MODULE_SOURCES, PART, VHDL_SOURCES, TOP_OVERRIDE, ordered_sources, synth_flags

def build_tcl(module, param_set, n_paths):
    sources = ordered_sources(module)
    vhdl = VHDL_SOURCES.get(module, [])
    source_lines = "\n        ".join(sources)
    top = TOP_OVERRIDE.get(module, module)
    defines = synth_flags(module)
    vhdl_block = ""
    if vhdl:
        vhdl_lines = "\n        ".join(vhdl)
        vhdl_block = f"read_vhdl {{\n        {vhdl_lines}\n}}\n"
    return f"""file mkdir "./synth_out/paths"
{vhdl_block}read_verilog {{
        {source_lines}
}}
synth_design \\
    -top {top} \\
    -part {PART} \\
    -mode out_of_context{defines} \\
    -generic parameter_set={param_set}
set clk_port [lindex [get_ports -quiet {{clk clk_i}}] 0]
if {{$clk_port eq ""}} {{ set clk_port [lindex [get_ports -quiet *clk*] 0] }}
create_clock -period 5.000 -name clk [get_ports $clk_port]
report_timing -max_paths {n_paths} -sort_by slack \\
    -file ./synth_out/paths/{module}_{param_set}_top{n_paths}.rpt
puts "=== PATHS DONE: {module} {param_set} top{n_paths} ==="
"""

def run_extraction(module, param_set, n_paths, repo_root="."):
    tcl_path = f"./synth_out/paths/extract_{module}_{param_set}.tcl"
    os.makedirs("./synth_out/paths", exist_ok=True)
    with open(tcl_path, "w") as f:
        f.write(build_tcl(module, param_set, n_paths))
    print(f"Running synthesis + top-{n_paths} path extraction: {module}/{param_set} ...")
    result = subprocess.run(
        ["vivado", "-mode", "batch", "-nojournal", "-nolog", "-notrace",
         "-source", tcl_path],
        cwd=repo_root, capture_output=True, text=True)
    if result.returncode != 0:
        print("VIVADO FAILED:", result.stderr[-500:])
        return None
    return f"./synth_out/paths/{module}_{param_set}_top{n_paths}.rpt"

PATH_RE = re.compile(
    r"Slack \((VIOLATED|MET)\)\s*:\s*(-?[\d.]+)ns.*?"
    r"Source:\s*(\S+).*?"
    r"Destination:\s*(\S+).*?"
    r"Data Path Delay:\s*([\d.]+)ns\s*\(logic\s*([\d.]+)ns\s*\(([\d.]+)%\)\s*route\s*([\d.]+)ns\s*\(([\d.]+)%\)\).*?"
    r"Logic Levels:\s*(\d+)",
    re.DOTALL)

def parse_paths(rpt_file):
    text = open(rpt_file).read()
    paths = []
    for m in PATH_RE.finditer(text):
        status, slack, src, dst, total, logic_ns, logic_pct, route_ns, route_pct, levels = m.groups()
        paths.append({
            "slack": float(slack), "status": status,
            "source": src, "dest": dst,
            "total_ns": float(total),
            "logic_pct": float(logic_pct), "route_pct": float(route_pct),
            "levels": int(levels),
        })
    return paths

def block_of(signal):
    # group key: hierarchy + logical signal name (bit index and pin stripped)
    import re as _re
    parts = signal.split("/")
    # drop the pin (last element like C, D, R, CE, CLKARDCLK)
    if len(parts) > 1:
        parts = parts[:-1]
    # strip _reg[N] / [N] from the signal element
    parts[-1] = _re.sub(r"(_reg)?(\[\d+\])?$", "", parts[-1])
    return "/".join(parts)

def sigbase(signal):
    # strip _reg[N]/PIN endings to get the logical signal name
    s = signal.split("/")[-1]
    s = re.sub(r"_reg(\[\d+\])?$", "", s)
    return s

def summarize(paths):
    print(f"\n{'='*70}")
    print(f"{'#':>2} {'slack':>8} {'logic%':>7} {'route%':>7} {'lvls':>4}  source -> dest")
    print("-"*70)
    for i, p in enumerate(paths, 1):
        print(f"{i:>2} {p['slack']:>8.3f} {p['logic_pct']:>6.1f}% {p['route_pct']:>6.1f}% {p['levels']:>4}  {p['source']}")
        print(f"{'':>33}-> {p['dest']}")
    # group by destination block
    groups = {}
    for p in paths:
        key = block_of(p["dest"])
        groups.setdefault(key, []).append(p)
    print(f"\n--- GROUPED BY DESTINATION BLOCK ---")
    for key, ps in sorted(groups.items(), key=lambda kv: min(q["slack"] for q in kv[1])):
        worst = min(q["slack"] for q in ps)
        rd = sum(q["route_pct"] for q in ps)/len(ps)
        sigs = sorted(set(sigbase(q["dest"]) for q in ps))
        print(f"{len(ps):>2} paths | worst {worst:>7.3f} | avg route {rd:>5.1f}% | {key}")
        print(f"     dest signals: {', '.join(sigs[:6])}")
    print("="*70)

if __name__ == "__main__":
    module, param_set, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    rpt = run_extraction(module, param_set, n)
    if rpt:
        paths = parse_paths(rpt)
        print(f"Parsed {len(paths)} paths from {rpt}")
        summarize(paths)
