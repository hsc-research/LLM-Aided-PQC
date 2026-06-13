"""Ground-truth gatherer for agent v2.1. Given a selector target, emits a
machine-computed inventory: the model reads counts, never derives them."""
import re, sys, json

def gather(target):
    f, reg = target["file"], target["reg"]
    lines = open(f).read().split("\n")
    asn = re.compile(rf"^(\s*){re.escape(reg)}\s*<=\s*([^;]+);\s*$")
    cmp_pat = re.compile(rf"\b{re.escape(reg)}\s*(==|<=|<|>=|>|%)")
    any_asn = re.compile(r"^\s*\w+(\[\S+\])?\s*<=")

    sites, compares, flag_lines, sens = [], [], [], []
    for i, ln in enumerate(lines, 1):
        if ln.lstrip().startswith("//"):
            continue
        m = asn.match(ln)
        if m:
            sites.append({"line": i, "rhs": m.group(2).strip()}); continue
        if any_asn.match(ln):
            if re.search(rf"\b{re.escape(reg)}\b", ln):                      # flag machinery touching reg
                flag_lines.append({"line": i, "text": ln.strip()[:110]})
            continue
        if cmp_pat.search(ln):
            compares.append({"line": i, "text": ln.strip()[:110]}); continue
        if "always@" in ln.replace(" ", "") and re.search(rf"\b{re.escape(reg)}\b", ln):
            sens.append({"line": i, "text": ln.strip()[:160]})

    # Complete always-blocks mentioning reg (block = always.. to column-0 end)
    blocks, cur, in_blk = [], [], False
    for ln in lines:
        s = ln.strip()
        if s.startswith("always"):
            in_blk, cur = True, [ln]
        elif in_blk:
            cur.append(ln)
            if s.startswith("end") and (len(ln) - len(ln.lstrip())) == 0:
                in_blk = False
                blk = "\n".join(cur)
                if re.search(rf"\b{re.escape(reg)}\b", blk):
                    blocks.append(blk)

    assert not (compares and not sites), (
        f"inventory error: {reg} has {len(compares)} compares but 0 "
        f"assignment sites; a compared register must be assigned somewhere")
    return {
        "file": f, "register": reg,
        "assignment_sites": sites, "n_sites": len(sites),
        "live_compares": compares, "n_compares": len(compares),
        "existing_flag_machinery": flag_lines,
        "comb_sens_lists_with_reg": sens,
        "always_blocks": blocks,
    }

if __name__ == "__main__":
    sys.path.insert(0, "agent")
    from target_selector import select
    t = select(sys.argv[1], sys.argv[2], sys.argv[3])
    assert t, "no target"
    gt = gather(t)
    print(f"TARGET: {t['src_reg']}  worst {t['worst']}  file {gt['file']}")
    print(f"SITES: {gt['n_sites']}")
    for s in gt["assignment_sites"]: print(f"  L{s['line']}: {t['reg']} <= {s['rhs']}")
    print(f"LIVE COMPARES: {gt['n_compares']}")
    for c in gt["live_compares"]: print(f"  L{c['line']}: {c['text']}")
    print(f"EXISTING FLAG MACHINERY: {len(gt['existing_flag_machinery'])} lines")
    print(f"COMB SENS LISTS WITH REG: {len(gt['comb_sens_lists_with_reg'])}")
    for s in gt["comb_sens_lists_with_reg"]: print(f"  L{s['line']}: {s['text']}")
    print(f"ALWAYS BLOCKS CAPTURED: {len(gt['always_blocks'])}")
