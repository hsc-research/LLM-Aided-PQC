#!/usr/bin/env python3
"""Bounded compile/lint-only check of an exact target profile using an installed tool.

This never simulates RTL, maps an ASIC/FPGA, installs software or executes HQC.
Compile success does not qualify target semantics, initialization, BRAM/FF
mapping, functionality, timing, PPA or any warning waiver.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.export_target_profiles import empty_destination, sha, verify_profile, write_json


def check(profile_path, out, compiler=None, timeout=120):
    profile_path = Path(profile_path).resolve()
    profile = verify_profile(profile_path)
    root = profile_path.parent
    e = profile["elaboration"]
    kind = "verilator" if profile["design"] == "mlkem" else "iverilog"
    executable = shutil.which(compiler or kind)
    if executable is None:
        raise ValueError("installed compiler not found: " + (compiler or kind))
    if type(timeout) is not int or not 1 <= timeout <= 600:
        raise ValueError("timeout must be an integer from 1 to 600 seconds")
    out = empty_destination(out)
    out.mkdir(parents=True, exist_ok=True)
    version_cmd = [executable, "--version" if kind == "verilator" else "-V"]
    version = subprocess.run(version_cmd, capture_output=True, text=True, timeout=10)
    if version.returncode != 0:
        raise ValueError("compiler version query failed")
    files = [str(root / row["path"]) for row in e["sources"]]
    definitions = ["-D" + d for d in e["defines"]]
    includes = ["-I" + str(root / directory) for directory in e["include_dirs"]]
    if kind == "verilator":
        command = [executable, "--lint-only", "--language", "1800-2017", "--timing", "-Wno-fatal", "--top-module", e["top"], *definitions, *includes, *files]
    else:
        # SLH uses 'type' as an identifier, so SystemVerilog is not equivalent.
        command = [executable, "-g2005", "-tnull", "-s", e["top"], *definitions, *includes, *files]
    cwd = root / e["working_directory"]
    status, returncode = "NOT_RUN", None
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        log = result.stdout + result.stderr
        returncode = result.returncode
        status = "ELABORATED_WARNINGS_UNREVIEWED" if returncode == 0 and log.strip() else "ELABORATED" if returncode == 0 else "COMPILE_FAILED"
    except subprocess.TimeoutExpired as exc:
        log = ((exc.stdout or b"") + (exc.stderr or b"")).decode(errors="replace")
        status = "TIMEOUT"
    (out / "compile.log").write_text(log)
    verify_profile(profile_path)
    record = {"schema_version": 1, "status": status, "compiler_returncode": returncode,
              "profile_fingerprint": profile["profile_fingerprint"], "profile_sha256": sha(profile_path),
              "design": profile["design"], "variant": profile["variant"], "parameter_set": profile["parameter_set"],
              "target": profile["target"], "tool_kind": kind,
              "tool_version": (version.stdout + version.stderr).splitlines()[0],
              "command": command, "working_directory": str(cwd), "timeout_seconds": timeout,
              "log_sha256": sha(out / "compile.log"), "source_hashes_unchanged": True,
              "functional_qualification": False, "target_tool_qualification": False,
              "memory_mapping_proven": False, "warning_waivers": [],
              "limits": ["Compile/lint-only, not functional simulation or target synthesis.",
                         "Verilator -Wno-fatal retains all warnings as unreviewed; a zero exit does not waive warnings.",
                         "Initial-state, collision, clock gating and technology memory behavior remain unqualified."]}
    write_json(out / "result.json", record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--compiler", help="Explicit installed Verilator (ML-KEM) or Icarus (ML-DSA/SLH) path")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    try:
        record = check(args.profile, args.out, args.compiler, args.timeout)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print("Target elaboration ERROR: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps({k: record[k] for k in ("status", "compiler_returncode", "profile_fingerprint", "target_tool_qualification")}, indent=2))
    return 0 if record["compiler_returncode"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
