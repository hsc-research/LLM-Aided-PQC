#!/usr/bin/env python3
"""Preserved, four-state cycle checks of the separate encoder recovery.

Finite default-parameter tests with reset between independent configurations
and a bounded legal input envelope; not formal equivalence, reset-pending
coverage, an arbitrary-backpressure proof, or an area/timing measurement.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from agent.mldsa.gate_result import encoder_result
from agent.mldsa_sources import BUNDLED_ROOT, verify_snapshot
from agent.run_safety import hashes, run_process


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gold_rename(text):
    """Only isolate gold module names; do not alter RTL behavior."""
    for name in ("encoder", "uncenter_coeff", "zero_strip"):
        text = re.sub(r"\b" + name + r"\b", name + "_gold", text)
    return text


def run_check(encoder, run_root):
    run_root.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="mldsa-encoder-cycle-", dir=run_root))
    source = BUNDLED_ROOT / "ref_combined/src"
    tb = REPO / "verification/mldsa_osh/tb_encoder_cycle_equiv.v"
    started = time.monotonic()
    result = {
        "status": "FAIL", "reason": "setup incomplete", "run_dir": str(work),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "check": "four-state knownness, cycle-exact output valid/data and accepted-stream comparison",
        "parameters": {"OUTPUT_W": 4, "COEFF_W": 23, "MAX_LVL": 20, "W": 64},
        "scope": "18 configurations and 2 mode-switch sequences; fixed randomized seed; reset between independent configurations; complete draining between modes in switch sequences; legal 256-bit occupancy envelope",
        "limits": ["No reset with pending input/output", "No arbitrary/full-backpressure proof", "No nondefault parameter coverage", "No formal equivalence or PPA claim"],
        "encoder": str(encoder), "testbench": str(tb),
        "commands": [], "transformations": [], "output_markers": [],
    }

    def execute(argv, label, timeout):
        log = work / (label + ".log")
        command = {"argv": list(map(str, argv)), "cwd": str(work), "log": str(log)}
        result["commands"].append(command)
        try:
            completed = run_process(command["argv"], cwd=work, timeout=timeout, log_path=log)
            command["returncode"] = completed.returncode
            return completed
        finally:
            if log.exists():
                command["log_sha256"] = sha256(log)

    try:
        result["snapshot"] = verify_snapshot()
        inputs = [encoder, tb, Path(__file__).resolve(), REPO / "agent/mldsa/gate_result.py",
                  REPO / "agent/run_safety.py", REPO / "agent/mldsa_sources.py"]
        inputs += [source / name for name in ("encoder.v", "uncenter_coeff.v", "zero_strip.v")]
        result["input_hashes"] = hashes(inputs)
        result["encoder_sha256"] = sha256(encoder)
        result["testbench_sha256"] = sha256(tb)
        result["pinned_encoder_sha256"] = sha256(source / "encoder.v")
        staged = []
        for name in ("encoder.v", "uncenter_coeff.v", "zero_strip.v"):
            original = work / ("pinned_" + name)
            shutil.copyfile(source / name, original)
            gold = work / ("gold_" + name)
            gold.write_text(gold_rename(original.read_text()))
            candidate = work / name
            shutil.copyfile(encoder if name == "encoder.v" else source / name, candidate)
            staged += [gold, candidate]
            result["transformations"].append({"input": str(original), "output": str(gold),
                                               "edit": "rename encoder/uncenter_coeff/zero_strip identifiers to *_gold"})
        staged_tb = work / "tb_encoder_cycle_equiv.v"
        shutil.copyfile(tb, staged_tb)
        staged.insert(0, staged_tb)
        result["staged_hashes"] = hashes(work.glob("*.v"))
        result["tools"] = {}
        for tool in ("iverilog", "vvp"):
            path = shutil.which(tool)
            if path is None:
                raise RuntimeError(f"required tool not found: {tool}")
            result["tools"][tool] = {"path": path, "sha256": sha256(path)}
            version = execute([path, "-V"], "version-" + tool, 30)
            result["tools"][tool]["version_returncode"] = version.returncode
        binary = work / "sim"
        compile_result = execute([result["tools"]["iverilog"]["path"], "-g2012", "-s", "tb_encoder",
                                  "-o", binary, *staged], "compile", 120)
        if compile_result.returncode:
            result["reason"] = "compile failed"
        else:
            result["binary_sha256"] = sha256(binary)
            sim = execute([result["tools"]["vvp"]["path"], binary], "sim", 600)
            result.update(encoder_result(sim))
            summaries = re.findall(r"^CYCLE CHECK SUMMARY checked=(\d+) errors=(\d+) unknown_valid=(\d+) unknown_data=(\d+)$", sim.stdout, re.M)
            if len(summaries) != 1:
                result.update(status="FAIL", reason="missing or duplicate cycle-check summary")
            else:
                checked, errors, unknown_valid, unknown_data = map(int, summaries[0])
                result["cycle_summary"] = dict(checked=checked, errors=errors,
                                               unknown_valid=unknown_valid, unknown_data=unknown_data)
                if checked <= 0 or errors or unknown_valid or unknown_data:
                    result.update(status="FAIL", reason="cycle-check errors, unknown values or no checked cycles")
            result["output_markers"] = [line for line in sim.stdout.splitlines()
                                        if line.startswith(("CFG ", "SWITCHSEQ ", "CYCLE CHECK SUMMARY", "GATE RESULT:"))]
            result["first_diagnostics"] = [line for line in sim.stdout.splitlines()
                                           if re.search(r"\b(?:MISMATCH|ERROR)\b", line)][:10]
        if result["input_hashes"] != hashes(inputs):
            result.update(status="FAIL", reason="input changed during check")
        if result["staged_hashes"] != hashes(work.glob("*.v")):
            result.update(status="FAIL", reason="staged RTL/testbench changed during check")
    except Exception as exc:
        result.update(status="FAIL", reason=f"{type(exc).__name__}: {exc}")
    result["runtime_s"] = round(time.monotonic() - started, 3)
    result["result_file"] = str(work / "result.json")
    (work / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encoder", type=Path,
                        default=REPO / "verification/mldsa_osh/encoder_fallthrough.v")
    parser.add_argument("--run-root", type=Path,
                        default=Path(os.environ.get("PQC_RUN_DIR", REPO / ".pqc_runs")))
    args = parser.parse_args()
    result = run_check(args.encoder.resolve(), args.run_root.resolve())
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
