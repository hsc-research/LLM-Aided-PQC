"""Typed, assertion-gated edit operations. The LLM proposes ops as JSON;
this module is the only thing that touches RTL. All-or-nothing per file set:
every assertion across every file must pass before any byte is written."""
import re, shutil, os, tempfile, hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = str(REPO_ROOT / ".pqc_runs" / "edit-backups")
EDIT_ROOTS = tuple(REPO_ROOT / p for p in (
    "build/keygen", "build/encap", "build/decap", "build/joint_design",
    "agent/mldsa/mldsa_src", "agent/slh_dsa/slh_src"))


class EditError(AssertionError):
    """Rejected proposal. Unlike assert statements, active under python -O."""


def _require(condition, message):
    if not condition:
        raise EditError(message)


def _positive_int(value):
    return type(value) is int and value > 0


def validate_path(path, allowed_paths=None):
    """Only candidate RTL may be edited. The caller controls any exact allowlist."""
    _require(isinstance(path, str) and path, "file path must be a nonempty string")
    candidate = Path(path)
    _require(not candidate.is_symlink(), "symlink edit targets are forbidden")
    resolved = candidate.resolve()
    _require(resolved.is_file(), f"missing edit target: {path}")
    _require(resolved.suffix in (".v", ".sv", ".vhd"), "only RTL files may be edited")
    if allowed_paths is None:
        _require(not any(part.lower() in ("tb", "testbench", "src_tb", "gate")
                         for part in resolved.parts)
                 and not re.match(r"(?:tb(?:_|\.)|test_|.*_tb\.)", resolved.name, re.I),
                 "testbenches and correctness gates are not candidate RTL")
        permitted = any(resolved.is_relative_to(root.resolve()) for root in EDIT_ROOTS)
    else:
        permitted = resolved in {Path(p).resolve() for p in allowed_paths}
    _require(permitted, f"edit target is outside the caller's candidate scope: {path}")
    return resolved


def _validate_experiment(experiment, allowed_paths=None):
    _require(isinstance(experiment, dict), "experiment must be an object")
    name = experiment.get("name")
    _require(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", name),
             "experiment name must be a short filename-safe slug")
    files = experiment.get("files")
    _require(isinstance(files, list) and 1 <= len(files) <= 32,
             "experiment needs 1..32 files")
    seen = set()
    for fs in files:
        _require(isinstance(fs, dict), "file specification must be an object")
        resolved = validate_path(fs.get("path"), allowed_paths)
        _require(resolved not in seen, "duplicate edit target")
        seen.add(resolved)
        ops = fs.get("ops")
        _require(isinstance(ops, list) and 1 <= len(ops) <= 64, "file needs 1..64 operations")
        for op in ops:
            _require(isinstance(op, dict) and op.get("op") in _OPS, "unknown edit operation")
            kind = op["op"]
            required = {"replace_exact": ("old", "new"),
                        "pair_assignments": ("reg", "flag", "expr"),
                        "regex_swap": ("pattern", "replacement"),
                        "declare_reg": ("name",)}[kind]
            for key in required:
                _require(isinstance(op.get(key), str), f"{kind}.{key} must be a string")
            if kind in ("replace_exact", "regex_swap"):
                _require(_positive_int(op.get("expect")), "expect must be a positive integer")
                anchor = op["old"] if kind == "replace_exact" else op["pattern"]
                _require(bool(anchor), "empty edit anchors are forbidden")
            if kind == "pair_assignments":
                _require(_positive_int(op.get("expect_sites")), "expect_sites must be positive")
                _require("{rhs}" in op["expr"], "pair expression must use {rhs}")
            for key in ("reg", "flag", "name", "guard_reg"):
                if key in op:
                    _require(isinstance(op[key], str) and re.fullmatch(r"[A-Za-z_]\w*", op[key]),
                             f"invalid identifier in {key}")
    return files


def _sens_add_only(old, new):
    # Sensitivity-list edits must be add-only. Flight 7 removed a signal;
    # synthesis ignores sens lists (guaranteed zero gain) and the removal
    # creates a sim/synth mismatch invisible to synth, timing, and possibly
    # KAT. Prompt rules are not enforcement; this is.
    if not re.search(r"\balways\s*@", old):
        return
    ids = lambda s: set(re.findall(r"[A-Za-z_]\w*", s))
    missing = ids(old) - ids(new)
    _require(not missing, f"sens-list edit removes identifiers {missing}; add-only")

def _apply_replace_exact(text, op):
    _sens_add_only(op["old"], op["new"])
    # Declaration-placement gate: a reg/wire declaration introduced by this op
    # must not be appended directly after a nonblocking assignment, which would
    # place it INSIDE an always block (illegal Verilog). Lesson from the first
    # v2.1 graduation flight: the model anchored a `reg` decl to a `<=` line in
    # a clocked block; counts passed but synthesis would have failed.
    added = [ln.strip() for ln in op["new"].split("\n")
             if ln.strip() not in op["old"].split("\n")]
    decl = re.compile(r"^(reg|wire)\b")
    new_lines = op["new"].split("\n")
    for i, ln in enumerate(new_lines):
        if decl.match(ln.strip()) and ln.strip() not in op["old"]:
            prev = new_lines[i-1].strip() if i > 0 else ""
            _require("<=" not in prev and "=" not in prev.rstrip(";"), f"decl-placement gate: '{ln.strip()[:50]}' is introduced "
                f"after an assignment ('{prev[:50]}'), which places it inside "
                f"an always block. Declare reg/wire at module scope instead.")
    if op.get("whole_line"):
        # Anchor to complete lines (post-strip equality). Prevents legal-but-
        # unintended substring hits, e.g. a declaration that has since gained
        # a prepended attribute. Lesson from the contract_smoke incident.
        lines = text.split("\n")
        hits = [i for i, ln in enumerate(lines) if ln.strip() == op["old"].strip()]
        n = len(hits)
        _require(n == op["expect"], f"replace_exact(whole_line): found {n}, expected {op['expect']}: {op['old'][:60]}")
        for i in hits:
            indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
            lines[i] = indent + op["new"]
        return "\n".join(lines)
    n = text.count(op["old"])
    _require(n == op["expect"], f"replace_exact: found {n}, expected {op['expect']}: {op['old'][:60]}")
    _require(not op["new"] or op["new"] not in text, f"replace_exact: new text already present: {op['new'][:60]}")
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
    _require(ns == op["expect_sites"],
             f"pair_assignments: found {ns} sites, expected {op['expect_sites']}")
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
            _require(not asn.match(ln), f"regex_swap: pattern hits an assignment line (flag-of-a-flag "
                f"guard): {ln.strip()[:70]}")
            out.append(pat.sub(op["replacement"], ln)); nc += 1
        else:
            out.append(ln)
    _require(nc == op["expect"], f"regex_swap: {nc} consumers, expected {op['expect']}")
    return "\n".join(out)

def _apply_declare_reg(text, op):
    import re as _re
    name = op["name"]
    _require(_re.match(r"^[A-Za-z_]\w*$", name), f"declare_reg: bad name {name!r}")
    _require(f"reg {name};" not in text and f"reg {name} " not in text, f"declare_reg: {name} already declared")
    lines = text.split("\n")
    last = None
    for i, ln in enumerate(lines):
        if (ln.startswith("reg ") or ln.startswith("wire ")) and ln.rstrip().endswith(";"):
            last = i
    _require(last is not None, "declare_reg: no module-scope reg/wire anchor found")
    lines.insert(last + 1, f"reg {name};")
    return "\n".join(lines)

_OPS = {"replace_exact": _apply_replace_exact,
        "pair_assignments": _apply_pair_assignments,
        "regex_swap": _apply_regex_swap,
        "declare_reg": _apply_declare_reg}

def _check_cross_register(fspec):
    # A flag paired to register R may only replace expressions that mention R.
    # Lesson: maiden flight #3 proposed swapping a hash_in_addr compare with a
    # count_hash_inputs-derived flag; counts happened to refuse, semantics
    # would not have. This makes it structural.
    paired = [op["reg"] for op in fspec["ops"] if op["op"] == "pair_assignments"]
    # New-flag gate (flight 11a): every pair_assignments flag must be a NEW
    # name declared by a replace_exact in this same experiment. Reusing an
    # existing flag double-drives another register's machinery.
    declared = " ".join(op.get("new", "") for op in fspec["ops"]
                        if op["op"] == "replace_exact")
    declared_names = {op["name"] for op in fspec["ops"]
                      if op["op"] == "declare_reg"}
    for op in fspec["ops"]:
        if op["op"] == "pair_assignments":
            _require(f"reg {op['flag']};" in declared
                    or op["flag"] in declared_names, f"new-flag gate: '{op['flag']}' is not declared by a "
                f"declare_reg or replace_exact in this experiment (flight-11a)")
    if not paired:
        return
    for op in fspec["ops"]:
        if op["op"] == "regex_swap":
            _require(any(r in set(re.findall(r"[A-Za-z_]\w*", op["pattern"])) for r in paired), f"cross-register: swap pattern '{op['pattern'][:60]}' does not "
                f"mention any paired register {paired}")

def validate_rtl_change(original, proposed):
    """Block obvious simulator I/O/process escapes. This is not an RTL sandbox."""
    safe = {"clog2", "signed", "unsigned", "bits", "size", "left", "right", "low", "high", "increment", "dimensions", "unpacked_dimensions"}
    def effects(text):
        calls = []
        for line in text.splitlines():
            names = re.findall(r"\$([A-Za-z_]\w*)", line)
            if any(name not in safe for name in names):
                calls.append(line.strip())
            if re.match(r"\s*`(?:include|line)\b", line):
                calls.append(line.strip())
        return calls
    _require(effects(original) == effects(proposed),
             "proposal changes simulator I/O, process/system tasks, or include directives")


def preview_experiment(experiment, *, allowed_paths=None):
    """Validate and stage all edits in memory without backups or filesystem writes."""
    files = _validate_experiment(experiment, allowed_paths)
    staged = {}
    for fspec in files:
        _check_cross_register(fspec)
        path = fspec["path"]
        with open(path, encoding="utf-8") as source:
            original = source.read()
        text = original
        for op in fspec["ops"]:
            try:
                text = _OPS[op["op"]](text, op)
            except (KeyError, TypeError, ValueError, re.error) as exc:
                raise EditError(f"invalid {op['op']} operation: {exc}") from exc
        validate_rtl_change(original, text)
        _require(text != original, f"experiment makes no change to {path}")
        staged[path] = (original, text)
    return staged


def _atomic_write(path, text):
    """Replace one file atomically, retaining its permission bits."""
    target = Path(path)
    fd, temp = tempfile.mkstemp(prefix=".pqc-edit-", dir=target.parent)
    try:
        os.fchmod(fd, target.stat().st_mode & 0o777)
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(text)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, target)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def apply_experiment(experiment, *, allowed_paths=None, backup_dir=None):
    """Validate before writing; roll back every changed file on a write failure.

    Backups are collision-free even for same-basename files. This is a
    single-process transaction, not a filesystem-wide isolation guarantee.
    The caller must serialize experiments and keep the correctness gate
    outside the candidate allowlist.
    """
    staged = preview_experiment(experiment, allowed_paths=allowed_paths)
    root = Path(backup_dir or BACKUP_DIR)
    root.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix=experiment["name"] + "-", dir=root))
    backups = {}
    for path, (original, _) in staged.items():
        digest = hashlib.sha256(str(Path(path).resolve()).encode()).hexdigest()[:16]
        backup = run / (Path(path).name + "." + digest + ".orig")
        backup.write_text(original, encoding="utf-8")
        backups[path] = str(backup)
    changed = []
    try:
        for path, (original, text) in staged.items():
            _require(Path(path).read_text(encoding="utf-8") == original,
                     f"target changed while staging: {path}")
            _atomic_write(path, text)
            changed.append(path)
    except BaseException:
        # A failed rollback is surfaced; retained backups enable recovery.
        for path in reversed(changed):
            _atomic_write(path, staged[path][0])
        raise
    return backups


def revert(backups):
    for path, backup in backups.items():
        _atomic_write(path, Path(backup).read_text(encoding="utf-8"))
