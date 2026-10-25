#!/usr/bin/env python3
"""HQC keygen -> encap -> decap round-trip gate for all three levels.

This is a functional consistency check, not an independent reference KAT.
Runs use snapshots of the current build trees; source and archived evidence
are never reset or overwritten. PQC_RUN_DIR selects the artifact parent.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[2]
VIVADO = os.environ.get("VIVADO", "vivado")
TIMEOUT_S = 3600
KEYGEN_SIM = "test_keygen/test_keygen.sim/sim_1/behav/xsim"
ENCAP_SIM = "test_encap/test_encap.sim/sim_1/behav/xsim"
DECAP_SIM = "test_decap/test_decap.sim/sim_1/behav/xsim"
PARAM_SETS = ("128", "192", "256")


def new_run_dir(prefix, repo_root=REPO_ROOT):
    parent = Path(os.environ.get("PQC_RUN_DIR", str(Path(repo_root) / ".pqc_runs"))).resolve()
    parent.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=parent))


def run_command(cmd, cwd, timeout=TIMEOUT_S):
    """Reap the whole simulator process group on timeout, including children."""
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            start_new_session=True)
    try:
        output, _ = proc.communicate(timeout=timeout)
    except BaseException as exc:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        output, _ = proc.communicate()
        if isinstance(exc, subprocess.TimeoutExpired):
            return False, "timeout\n" + (output or "")
        raise
    return proc.returncode == 0, output or ""


def _run_tcl(tcl_path, label, work):
    ok, out = run_command(
        [VIVADO, "-mode", "batch", "-nojournal", "-nolog", "-notrace",
         "-source", str(tcl_path)], work)
    (Path(work) / f"{label}.log").write_text(out)
    # Vivado may report Tcl/simulation errors without a failing shell status.
    if re.search(r"(?im)^\s*(?:ERROR|FATAL)(?:\s|:)", out):
        ok = False
    return ok, out[-1200:]


def copy_inputs(source, destination, prefixes, params=PARAM_SETS):
    """Require every newly generated binary stimulus; never reuse stale ones."""
    source, destination = Path(source), Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for param in params:
        for prefix in prefixes:
            path = source / f"{prefix}_{param}.in"
            value = re.sub(r"/\*.*?\*/|//[^\n]*", "", path.read_text(), flags=re.S)
            value = re.sub(r"@[0-9a-fA-F]+(?=\s|$)", "", value).strip()
            if not value or not re.fullmatch(r"[01\s]+", value):
                raise ValueError(f"empty or invalid binary stimulus: {path.name}")
            shutil.copy2(path, destination / path.name)


def compare_secrets(enc_file, dec_file):
    """The current HQC TB emits 16 32-bit words (128 hexadecimal digits)."""
    try:
        enc = Path(enc_file).read_text().strip()
        dec = Path(dec_file).read_text().strip()
    except FileNotFoundError:
        return "MISSING"
    if not all(re.fullmatch(r"[0-9a-fA-F]{128}", value) for value in (enc, dec)):
        return "INVALID"
    return "MATCH" if enc.lower() == dec.lower() else "MISMATCH"


def run_kat(repo_root=None):
    repo = Path(repo_root or REPO_ROOT).resolve()
    work = new_run_dir("hqc-kat-", repo)
    stage = "setup"
    source_hashes = {}
    staged_hashes = {}
    try:
        for name in ("keygen", "encap", "decap"):
            source = repo / "build" / name
            if not (source / "tb" / f"{name}.tcl").is_file():
                raise FileNotFoundError(f"missing staged build: {source}")
            for path in source.rglob("*"):
                if path.is_file() and path.suffix in (".v", ".vh", ".vhd", ".tcl"):
                    source_hashes[path] = hashlib.sha256(path.read_bytes()).hexdigest()
            shutil.copytree(source, work / "build" / name)
        for path, digest in source_hashes.items():
            staged = work / path.relative_to(repo)
            if hashlib.sha256(staged.read_bytes()).hexdigest() != digest:
                raise ValueError(f"source changed while staging: {path}")
            staged_hashes[staged] = digest
        (work / "sources.json").write_text(json.dumps({str(p): d for p, d in source_hashes.items()}, indent=2))
        for stage in ("keygen", "encap", "decap"):
            ok, reason = _run_tcl(f"./build/{stage}/tb/{stage}.tcl", stage, work)
            if not ok:
                return {"status": "FAIL", "stage": stage, "reason": reason,
                        "run_dir": str(work)}
            if stage == "keygen":
                for target in ("encap", "decap"):
                    copy_inputs(work / KEYGEN_SIM, work / "build" / target / "tb",
                                ("s", "h", "x", "y"))
            elif stage == "encap":
                copy_inputs(work / ENCAP_SIM, work / "build/decap/tb", ("u", "v", "d"))
        for path, digest in {**source_hashes, **staged_hashes}.items():
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError(f"candidate changed during verification: {path}")
        results = {p: compare_secrets(work / ENCAP_SIM / f"ss_output_{p}.out",
                                      work / DECAP_SIM / f"ss_output_{p}.out")
                   for p in PARAM_SETS}
        return {"status": "PASS" if all(v == "MATCH" for v in results.values()) else "FAIL",
                "stage": "compare", "per_param": results, "run_dir": str(work)}
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return {"status": "FAIL", "stage": stage, "reason": str(exc), "run_dir": str(work)}


if __name__ == "__main__":
    outcome = run_kat()
    print(json.dumps(outcome, indent=2))
    print("KAT RESULT:", outcome["status"])
    raise SystemExit(0 if outcome["status"] == "PASS" else 1)
