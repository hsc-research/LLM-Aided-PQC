"""Code-side target selection for agent v2.1. Picks ONE cluster per run:
parses the board, groups by source register, skips exhausted/skip-listed
clusters, returns the best live target with its file resolved via the
elaboration map. The model never chooses targets."""
import re, json, os, sys
from collections import defaultdict

SKIPLIST = "agent/hqc/skiplist.json"

# Elaboration map: instance name -> actual elaborated file.
# fixed_weight variants: ALL operations elaborate fixed_weight_ct.
INSTANCE_FILE = {
    "FIXEDWEIGHT": "fixed_weight_ct.v",
    "POLY_MULT": "poly_mult.v",
    "XOR_BASED_ADDER": "xor_based_adder.v",
    "REED_MULLER_ENCODE": "reed_muller_encode.v",
    "ENCODE": "encrypt.v",
    "ENCRYPT": "encrypt.v",
    "onegen_instance": "onegen_ct.v",
    "shake_ctx": "mem_dual.v",
}

def load_skiplist():
    return json.load(open(SKIPLIST)) if os.path.exists(SKIPLIST) else {}

def save_skip(key, reason):
    sl = load_skiplist(); sl[key] = reason
    json.dump(sl, open(SKIPLIST, "w"), indent=2)

def parse_board(rpt):
    txt = open(rpt).read()
    paths = []
    for chunk in txt.split("Slack (VIOLATED)")[1:]:
        m_s = re.search(r":\s*(-[\d.]+)ns", chunk)
        m_src = re.search(r"Source:\s+(\S+?)_reg(?:_reg)?\[", chunk)
        m_dst = re.search(r"Destination:\s+(\S+)", chunk)
        if m_s and m_src and m_dst:
            paths.append({"slack": float(m_s.group(1)),
                          "src_reg": m_src.group(1),   # hierarchical, no _reg suffix
                          "dst": m_dst.group(1)})
    return paths

def reg_base(src_reg):
    return src_reg.split("/")[-1]

def src_file(src_reg, module):
    parts = src_reg.split("/")
    for inst in reversed(parts[:-1]):          # innermost instance wins
        if inst in INSTANCE_FILE:
            return f"build/{module}/{INSTANCE_FILE[inst]}"
    return f"build/{module}/{module}.v"        # top-level register

def live_compares(path, reg):
    """Comparison expressions on reg in conditions, excluding nonblocking
    assignment lines (our flag machinery) and comments."""
    if not os.path.exists(path):
        return None                            # unknown file: caller decides
    hits = []
    asn = re.compile(r"^\s*\w+(\[\S+\])?\s*<=")
    cmp_pat = re.compile(rf"\b{re.escape(reg)}\s*(==|<=|<|>=|>|%)")
    for i, ln in enumerate(open(path), 1):
        if ln.lstrip().startswith("//") or asn.match(ln):
            continue
        if cmp_pat.search(ln):
            hits.append((i, ln.strip()[:90]))
    return hits

def select(rpt, module, level):
    paths = parse_board(rpt)
    sl = load_skiplist()
    clusters = defaultdict(list)
    for p in paths:
        clusters[p["src_reg"]].append(p)
    ranked = sorted(clusters.items(), key=lambda kv: min(p["slack"] for p in kv[1]))
    for src_reg, ps in ranked:
        key = f"{module}/{level}/{src_reg}"
        worst = min(p["slack"] for p in ps)
        if key in sl:
            print(f"  skip (listed: {sl[key]}): {src_reg}  worst {worst}")
            continue
        f = src_file(src_reg, module)
        reg = reg_base(src_reg)
        hits = live_compares(f, reg)
        if hits is None:
            print(f"  skip (no file map): {src_reg} -> {f}")
            save_skip(key, "no file mapping"); continue
        if not hits:
            print(f"  skip (exhausted, 0 live compares on {reg} in {f}): worst {worst}")
            save_skip(key, "exhausted: all compares flagged"); continue
        return {"key": key, "src_reg": src_reg, "reg": reg, "file": f,
                "worst": worst, "n_paths": len(ps),
                "live_compares": hits,
                "dsts": sorted({p["dst"] for p in ps})[:6]}
    return None

if __name__ == "__main__":
    rpt, module, level = sys.argv[1], sys.argv[2], sys.argv[3]
    t = select(rpt, module, level)
    print(json.dumps(t, indent=2) if t else "NO LIVE TARGETS on this board")
