"""Formal cluster characterization per Dr. Abideen's methodology request:
source/dest registers, route vs logic split, hierarchy crossings, high-fanout
nets, repeated control signals, endpoint proximity. Reads an existing top-N
report; no synthesis. Doubles as the code-side target-selection input for
agent loop v2.1 (reason over clusters, not the single worst path)."""
import re, sys
from collections import Counter, defaultdict

def parse(path):
    txt = open(path).read()
    paths = []
    for chunk in txt.split("Slack (VIOLATED)")[1:]:
        p = {}
        m = re.search(r":\s*(-[\d.]+)ns", chunk);            p["slack"] = float(m.group(1)) if m else None
        m = re.search(r"Source:\s+(\S+)/[A-Z]+\b", chunk);   p["src"] = m.group(1) if m else "?"
        m = re.search(r"Destination:\s+(\S+)", chunk);       p["dst"] = m.group(1) if m else "?"
        m = re.search(r"logic ([\d.]+)ns \(([\d.]+)%\)\s+route ([\d.]+)ns \(([\d.]+)%\)", chunk)
        if m:
            p["logic_ns"], p["logic_pct"] = float(m.group(1)), float(m.group(2))
            p["route_ns"], p["route_pct"] = float(m.group(3)), float(m.group(4))
        m = re.search(r"Logic Levels:\s+(\d+)", chunk);      p["levels"] = int(m.group(1)) if m else None
        p["nets"] = [(net, int(fo)) for fo, _, net in
                     re.findall(r"net \(fo=(\d+)(, unplaced)?\)\s+[\d.]+\s+[\d.]+\s+(\S+)", chunk)]
        paths.append(p)
    return paths

def top_module(name):
    parts = name.split("/")
    return parts[0] if len(parts) > 1 else "(top)"

def run(rpt):
    paths = [p for p in parse(rpt) if p["slack"] is not None]
    print(f"CLUSTER CHARACTERIZATION: {rpt}  ({len(paths)} violated paths)\n" + "=" * 70)
    print(f"\n1. SOURCE REGISTERS ({len(set(p['src'] for p in paths))} unique):")
    for s, n in Counter(p["src"] for p in paths).most_common():
        print(f"   {n:>3}x  {s}")
    print(f"\n2. DESTINATION REGISTERS ({len(set(p['dst'] for p in paths))} unique):")
    for d, n in Counter(p["dst"] for p in paths).most_common(10):
        print(f"   {n:>3}x  {d}")
    rp = [p["route_pct"] for p in paths if "route_pct" in p]
    lv = [p["levels"] for p in paths if p["levels"]]
    print(f"\n3. ROUTE vs LOGIC: route {min(rp):.1f}-{max(rp):.1f}% "
          f"(mean {sum(rp)/len(rp):.1f}%), levels {min(lv)}-{max(lv)}")
    crossings = Counter(f"{top_module(p['src'])} -> {top_module(p['dst'])}" for p in paths)
    print(f"\n4. HIERARCHY CROSSINGS:")
    for c, n in crossings.most_common():
        print(f"   {n:>3}x  {c}")
    net_hits = Counter(); net_fo = {}
    for p in paths:
        for net, fo in p["nets"]:
            net_hits[net] += 1; net_fo[net] = max(net_fo.get(net, 0), fo)
    print(f"\n5. COMMON NETS (appearing in >=3 paths, by max fanout):")
    common = [(net, c, net_fo[net]) for net, c in net_hits.items() if c >= 3]
    for net, c, fo in sorted(common, key=lambda x: -x[2])[:12]:
        print(f"   in {c:>2} paths, fo={fo:<5} {net}")
    print(f"\n6. ENDPOINT PROXIMITY:")
    for kw in ["dshift", "accum", "barrel", "poly_mult", "POLY_MULT"]:
        n = sum(1 for p in paths if kw.lower() in p["dst"].lower())
        if n: print(f"   {n:>3} endpoints match '{kw}'")
    print("\n7. VERDICT INPUTS: route-dominated + single-crossing + shared-fanout"
          "\n   nets => placement/floorplan, register duplication, or bundled"
          "\n   boundary pipeline (per PI). Local FSM rewrite contraindicated.")

if __name__ == "__main__":
    run(sys.argv[1])
