"""Three-stage gate for cross-toolchain port fixes.

No single check is sufficient (F8 sub-finding):
  stage 1  sorted diff   catches added/removed lines, MISSES illegal scope
  stage 2  tool re-read  catches scope and syntax, MISSES semantic change
  stage 3  KAT           catches semantic change, slow

Every stage must pass. Ordered cheapest first so failures are cheap.
"""
import subprocess, shutil, os, sys


def stage1_pure_reorder(path_before, path_after):
    """Byte-level multiset equality. LC_ALL=C is mandatory: locale collation
    ignores leading whitespace and produces false differences."""
    env = dict(os.environ, LC_ALL="C")
    a = subprocess.run(["sort", path_before], capture_output=True, text=True, env=env).stdout
    b = subprocess.run(["sort", path_after],  capture_output=True, text=True, env=env).stdout
    if a == b:
        return True, "pure reorder"
    la, lb = a.split("\n"), b.split("\n")
    added   = [x for x in lb if x not in la]
    removed = [x for x in la if x not in lb]
    return False, f"not a pure reorder: +{len(added)} -{len(removed)}"


def stage2_tool_accepts(runner):
    """runner() -> (ok: bool, first_error: str). Catches what stage 1 cannot:
    a declaration hoisted into a procedural block is a pure reorder and is
    also illegal Verilog."""
    ok, err = runner()
    return ok, ("tool accepts" if ok else f"tool rejects: {err}")


def stage3_kat(cmd, cwd=".", pass_token="PASS"):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, shell=True)
    ok = pass_token in r.stdout
    return ok, ("KAT PASS" if ok else f"KAT FAIL: {r.stdout[-400:]}")


def run_gate(path, backup, tool_runner, kat_cmd, expect_pure_reorder=True, cwd="."):
    """Returns (accepted: bool, log: list[(stage, ok, detail)])."""
    log = []

    if expect_pure_reorder:
        ok, d = stage1_pure_reorder(backup, path)
        log.append(("pure_reorder", ok, d))
        if not ok:
            _revert(path, backup); return False, log
    else:
        log.append(("pure_reorder", None, "skipped: fix changes semantics by design"))

    ok, d = stage2_tool_accepts(tool_runner)
    log.append(("tool_accepts", ok, d))
    if not ok:
        _revert(path, backup); return False, log

    ok, d = stage3_kat(kat_cmd, cwd=cwd)
    log.append(("kat", ok, d))
    if not ok:
        _revert(path, backup); return False, log

    return True, log


def _revert(path, backup):
    shutil.copy(backup, path)
    print(f"  REVERTED {path} from {backup}")
