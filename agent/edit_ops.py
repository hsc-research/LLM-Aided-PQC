"""Typed, assertion-gated edit operations. The LLM proposes ops as JSON;
this module is the only thing that touches RTL. All-or-nothing per file set:
every assertion across every file must pass before any byte is written."""
import re, shutil, os, time

BACKUP_DIR = "agent/fw_variants"

def _apply_replace_exact(text, op):
    if op.get("whole_line"):
        # Anchor to complete lines (post-strip equality). Prevents legal-but-
        # unintended substring hits, e.g. a declaration that has since gained
        # a prepended attribute. Lesson from the contract_smoke incident.
        lines = text.split("\n")
        hits = [i for i, ln in enumerate(lines) if ln.strip() == op["old"].strip()]
        n = len(hits)
        assert n == op["expect"], f"replace_exact(whole_line): found {n}, expected {op['expect']}: {op['old'][:60]}"
        for i in hits:
            indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
            lines[i] = indent + op["new"]
        return "\n".join(lines)
    n = text.count(op["old"])
    assert n == op["expect"], f"replace_exact: found {n}, expected {op['expect']}: {op['old'][:60]}"
    assert op["new"] not in text, f"replace_exact: new text already present: {op['new'][:60]}"
    return text.replace(op["old"], op["new"])

def _apply_pair_assignments(text, op):
    # After every nonblocking assignment to `reg`, insert `flag <= expr` with
    # {rhs} substituted by that site's RHS. Guards against compare-vs-assign
    # ambiguity by requiring the line to BE an assignment (ends with ;).
    lines, out, ns = text.split("\n"), [], 0
    pat = re.compile(r"^(\s*)" + re.escape(op["reg"]) + r"\s*<=\s*([^;]+);\s*$")
    for ln in lines:
        out.append(ln)
        m = pat.match(ln)
        if m:
            rhs = m.group(2).strip()
            out.append(m.group(1) + op["flag"] + " <= " + op["expr"].replace("{rhs}", rhs) + ";")
            ns += 1
    assert ns == op["expect_sites"], f"pair_assignments: {ns} sites, expected {op['expect_sites']}"
    return "\n".join(out)

def _apply_regex_swap(text, op):
    # Swap consumer expressions; never touches assignment lines of guard_reg.
    pat = re.compile(op["pattern"])
    guard = re.compile(r"^\s*" + re.escape(op.get("guard_reg", "\x00")) + r"\s*<=") if op.get("guard_reg") else None
    asn = re.compile(r"^\s*\w+\s*<=")
    lines, out, nc = text.split("\n"), [], 0
    for ln in lines:
        if pat.search(ln) and not (guard and guard.match(ln)):
            # Structural rule: swaps live in conditions, never in assignment
            # lines. A hit on an assignment means the proposer is editing
            # flag machinery (flight-6 failure class). Refuse outright.
            assert not asn.match(ln), (
                f"regex_swap: pattern hits an assignment line (flag-of-a-flag "
                f"guard): {ln.strip()[:70]}")
            out.append(pat.sub(op["replacement"], ln)); nc += 1
        else:
            out.append(ln)
    assert nc == op["expect"], f"regex_swap: {nc} consumers, expected {op['expect']}"
    return "\n".join(out)

_OPS = {"replace_exact": _apply_replace_exact,
        "pair_assignments": _apply_pair_assignments,
        "regex_swap": _apply_regex_swap}

def _check_cross_register(fspec):
    # A flag paired to register R may only replace expressions that mention R.
    # Lesson: maiden flight #3 proposed swapping a hash_in_addr compare with a
    # count_hash_inputs-derived flag; counts happened to refuse, semantics
    # would not have. This makes it structural.
    paired = [op["reg"] for op in fspec["ops"] if op["op"] == "pair_assignments"]
    if not paired:
        return
    for op in fspec["ops"]:
        if op["op"] == "regex_swap":
            assert any(r in op["pattern"] for r in paired), (
                f"cross-register: swap pattern '{op['pattern'][:60]}' does not "
                f"mention any paired register {paired}")

def apply_experiment(experiment):
    """experiment = {"name": str, "files": [{"path": str, "ops": [op, ...]}, ...]}
    Returns dict of backups made. Raises AssertionError (no writes) on any gate."""
    staged, backups = {}, {}
    for fspec in experiment["files"]:
        _check_cross_register(fspec)
    for fspec in experiment["files"]:
        path = fspec["path"]
        text = open(path).read()
        for op in fspec["ops"]:
            assert op["op"] in _OPS, f"unknown op type {op['op']}"
            text = _OPS[op["op"]](text, op)          # raises -> nothing written
        staged[path] = text
    stamp = time.strftime("%Y%m%d_%H%M%S")
    for path, text in staged.items():
        bk = os.path.join(BACKUP_DIR, os.path.basename(path) + f".{experiment['name']}.{stamp}.orig")
        shutil.copy(path, bk)
        backups[path] = bk
        open(path, "w").write(text)
    return backups

def revert(backups):
    for path, bk in backups.items():
        shutil.copy(bk, path)
