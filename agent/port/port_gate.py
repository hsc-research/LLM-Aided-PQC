"""Three-stage gate for cross-toolchain port fixes.

No single check is sufficient (F8 sub-finding):
  stage 1  sorted diff   catches added/removed lines, MISSES illegal scope
  stage 2  tool re-read  catches scope and syntax, MISSES semantic change
  stage 3  KAT           catches semantic change, slow

Every stage must pass. Ordered cheapest first so failures are cheap.
"""
import subprocess, shutil, os, sys, shlex
from pathlib import Path
try:
    from ..run_safety import gate_passed, run_process
except ImportError:
    from run_safety import gate_passed, run_process


def stage1_pure_reorder(path_before, path_after):
    """Byte-level multiset equality. LC_ALL=C is mandatory: locale collation
    ignores leading whitespace and produces false differences."""
    from collections import Counter
    try:
        ca = Counter(Path(path_before).read_bytes().splitlines(keepends=True))
        cb = Counter(Path(path_after).read_bytes().splitlines(keepends=True))
    except OSError as error:
        return False, f"Unable to read reorder inputs: {error}"
    if ca == cb:
        return True, "pure reorder"
    added, removed = cb - ca, ca - cb
    return False, f"not a pure reorder: +{sum(added.values())} -{sum(removed.values())}"



def stage2_tool_accepts(runner):
    """runner() -> (ok: bool, first_error: str). Catches what stage 1 cannot:
    a declaration hoisted into a procedural block is a pure reorder and is
    also illegal Verilog."""
    ok, err = runner()
    return ok, ("tool accepts" if ok else f"tool rejects: {err}")


def stage3_kat(cmd, cwd=".", pass_token="PASS"):
    # Legacy plain substring matching accepted FAIL logs that happened to
    # mention PASS, and ignored process status. Require the structured gate.
    if pass_token != "PASS":
        return False, "Custom pass tokens are unsupported; require GATE: PASS or status PASS"
    try:
        argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
        result = run_process(argv, cwd=cwd, timeout=3600)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        return False, f"KAT execution failed: {error}"
    ok = gate_passed(result)
    return ok, ("KAT PASS" if ok else f"KAT FAIL: {result.stdout[-400:]}")



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
