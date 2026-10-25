#!/usr/bin/env python3
"""Optional real Icarus smoke/corruption check; never modifies tracked RTL.

Exit 0: baseline passes and both faults are rejected for output mismatches.
Exit 1: a verification failure. Exit 2: missing tools or an execution error.
No Vivado, API access, external source checkout, or downloaded software is used.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "agent/mldsa/mldsa_src/coeff_decomposer.v"
INPUTS = [SOURCE, ROOT / "agent/mldsa/mldsa_src/decomp_map1.v",
          ROOT / "agent/mldsa/mldsa_check/gen_vectors.py",
          ROOT / "agent/mldsa/mldsa_check/tb_coeff_decomposer.v"]
MUTATIONS = {
    "live-arithmetic": ("dob  <= a1_2;", "dob  <= a1_2 ^ 1;"),
    "boundary-constant": ("Q         = 23'd8380417;", "Q         = 23'd8380416;"),
}


def input_hashes():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in INPUTS}


def run_check(iverilog="iverilog", vvp="vvp", ivl_base=None):
    compiler, runtime = shutil.which(iverilog), shutil.which(vvp)
    report = {"schema_version": 1, "scope": "ML-DSA coeff_decomposer block only",
              "python_version": sys.version.split()[0], "status": "UNAVAILABLE", "cases": []}
    if not compiler or not runtime:
        report["reason"] = "Icarus compiler and runtime are required; install iverilog and vvp or pass explicit paths."
        return report, 2
    if ivl_base and not Path(ivl_base).is_dir():
        report["reason"] = "The supplied Icarus backend directory does not exist."
        return report, 2
    before = input_hashes()
    report["input_sha256"] = before
    try:
        compiler_command = [compiler] + (["-B", str(Path(ivl_base).resolve())] if ivl_base else [])
        for name, command in (("iverilog", compiler_command), ("vvp", [runtime])):
            result = subprocess.run([*command, "-V"], capture_output=True, text=True, timeout=30)
            version = (result.stdout + result.stderr).splitlines()
            if result.returncode or not version:
                raise RuntimeError(f"{name} version check failed")
            report[name + "_version"] = version[0]
        with tempfile.TemporaryDirectory(prefix="pqc-hdl-smoke-") as temp:
            work = Path(temp)
            # Reuse the existing gate unmodified. A private executable wrapper
            # supports non-system Icarus installations without altering PATH globally.
            binaries = work / "bin"
            binaries.mkdir()
            for name, command in (("iverilog", compiler_command), ("vvp", [runtime])):
                wrapper = binaries / name
                wrapper.write_text("#!/bin/sh\nexec " + shlex.join(command) + ' "$@"\n')
                wrapper.chmod(0o700)
            env = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ.get("PATH", ""))
            original = SOURCE.read_text()
            candidates = [("baseline", original)]
            for name, (old, new) in MUTATIONS.items():
                if original.count(old) != 1:
                    raise RuntimeError(f"{name} mutation anchor is no longer unique; review the test")
                candidates.append((name, original.replace(old, new, 1)))
            for name, text in candidates:
                candidate = work / (name + ".v")
                candidate.write_text(text)
                completed = subprocess.run(
                    [sys.executable, str(ROOT / "agent/mldsa/mldsa_block_gate.py"), str(candidate)],
                    cwd=ROOT, env=env, capture_output=True, text=True, timeout=300)
                result = json.loads(completed.stdout)
                if name == "baseline":
                    expected = (completed.returncode == 0 and result.get("status") == "PASS"
                                and set(result.get("levels", {})) == {"2", "3"}
                                and all(level.get("ok") and level.get("checked") == 200
                                        for level in result["levels"].values()))
                else:
                    # A compile error or absent simulator does not validate a gate.
                    expected = (completed.returncode == 1 and result.get("status") == "FAIL"
                                and result.get("reason") == "simulator reported MISMATCH"
                                and any(level.get("checked") == 200 for level in result.get("levels", {}).values()))
                report["cases"].append({"case": name, "returncode": completed.returncode,
                                        "expected_outcome_observed": expected, "result": result})
        report["tracked_inputs_unchanged"] = input_hashes() == before
        passed = report["tracked_inputs_unchanged"] and all(case["expected_outcome_observed"] for case in report["cases"])
        report["status"] = "PASS" if passed else "FAIL"
        return report, 0 if passed else 1
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        report.update(status="ERROR", reason=type(error).__name__ + ": HDL smoke did not complete")
        report["tracked_inputs_unchanged"] = input_hashes() == before
        return report, 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iverilog", default="iverilog", help="compiler executable name or path")
    parser.add_argument("--vvp", default="vvp", help="runtime executable name or path")
    parser.add_argument("--ivl-base", help="optional compiler backend directory for a relocated Icarus install")
    parser.add_argument("--output", type=Path, help="write the same small JSON report to this path")
    args = parser.parse_args(argv)
    report, code = run_check(args.iverilog, args.vvp, args.ivl_base)
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    print(encoded, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
