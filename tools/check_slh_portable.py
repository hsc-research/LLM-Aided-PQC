#!/usr/bin/env python3
"""Explicit Icarus portability variant of the pinned SPHINCSLET vendor gate.

Never changes candidate/pristine sources or generates reference outputs.
PASS is historical vendor differential evidence, not independent FIPS 205.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import difflib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))
from run_safety import hashes, run_process
from slh_dsa import slh_kat_gate as gate

PORTABILITY_INPUTS = {
    "sphincslet/fsm/FSM.v": "b530eee47d389410af2608600300ae2af595475543f4be4ae71c5a9041bd1c43",
    "sphincslet/hash_tile/hash_mem_interface_sha.v": "0a48948094cb0dafdff4a1af7366baacc13dc0e281af5c6fb24cd5640fc53bd7",
    "sphincslet/tb.v": gate.TB_SHA256,
}
TAMPER_MARKER = "SLH_TAMPER: signature memory word 0 bit 0 flipped"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def rtl_hashes(rtl):
    return {str(Path(p).relative_to(rtl)): value for p, value in hashes(rtl.rglob("*.v")).items()}


def portability_variant(rtl):
    """Apply only reviewed transformations to a disposable staged source tree."""
    changes = []
    for name, expected in PORTABILITY_INPUTS.items():
        path = rtl / name
        before = path.read_bytes()
        if digest(before) != expected:
            raise ValueError(f"portability input differs from reviewed vendor bytes: {name}")
        text = before.decode()
        if name.endswith("/FSM.v"):
            text, count = re.subn(r"^wire[ \t]+(?:WOTS_FSM_start|WOTS_s_in_0_wr_en);[ \t]*$",
                                 "// Duplicate output-net declaration removed for IEEE portability.", text, flags=re.M)
            if count != 2:
                raise ValueError("duplicate-wire portability anchors changed")
        elif name.endswith("hash_mem_interface_sha.v"):
            old = "{{(BLOCK_SIZE-IO_WIDTH-1)}{1'b0}}"
            if text.count(old) != 1:
                raise ValueError("replication portability anchor changed")
            text = text.replace(old, "{(BLOCK_SIZE-IO_WIDTH-1){1'b0}}")
        else:
            anchor = "initial begin\n    //-- initial reset --//"
            if text.count(anchor) != 1 or text.count("$fscanf(") != 23:
                raise ValueError("testbench input-scan portability anchors changed")
            text = text.replace(anchor, "integer portability_fscanf_result;\n" + anchor)
            text = text.replace("$fscanf(", "portability_fscanf_result = $fscanf(")
            anchor = "    //-- main FSM start --//\n    //-- signature verification --//"
            if text.count(anchor) != 1:
                raise ValueError("negative-control injection anchor changed")
            text = text.replace(anchor, """    // Optional one-bit corruption AFTER signing, before the RTL verifier.
    if ($test$plusargs("SLH_TAMPER")) begin
        SIG_MEM.mem[0] = SIG_MEM.mem[0] ^ 64'h1;
        $display("SLH_TAMPER: signature memory word 0 bit 0 flipped");
    end
""" + anchor)
            anchor = "    if(c_flag) begin"
            if text.count(anchor) != 1:
                raise ValueError("verification-flag observation anchor changed")
            text = text.replace(anchor, '    $display("SLH_VERIFY_FLAG=%b", c_flag);\n' + anchor)
        path.write_bytes(text.encode())
        changes.append({"path": name, "before_sha256": digest(before), "after_sha256": digest(path.read_bytes()),
                        "diff": "".join(difflib.unified_diff(before.decode().splitlines(True), text.splitlines(True),
                                                          fromfile="vendor/" + name, tofile="portable/" + name))})
    return changes



def auth_sensitivity_variant(rtl):
    """Explicit diagnostic model correction; never silently added to baseline."""
    name = "sphincslet/fsm/XMSS_FSM.v"
    path = rtl / name
    before = path.read_bytes()
    if digest(before) != "1a9417e12c9a5d9ee8033ee85ae687c9cda2c6a57f58636fdeecc4459143aa74":
        raise ValueError("authentication-path sensitivity input differs from reviewed bytes")
    old = "always@(h_cnt2) begin"
    text = before.decode()
    if text.count(old) != 1:
        raise ValueError("authentication-path sensitivity anchor changed")
    text = text.replace(old, "always@(h_cnt2, leaf_idx) begin")
    path.write_bytes(text.encode())
    return {"path": name, "before_sha256": digest(before), "after_sha256": digest(path.read_bytes()),
            "diff": "".join(difflib.unified_diff(before.decode().splitlines(True), text.splitlines(True),
                                               fromfile="vendor/" + name, tofile="auth-sensitivity-fix/" + name))}


def check_case(expected, produced, output, returncode, parameter, tamper=False):
    ordinary = gate.check_signature(expected, produced, output, returncode, parameter)
    fresh = produced.is_file()
    raw = produced.read_bytes() if fresh else b""
    matched = raw == expected
    flags = re.findall(r"^SLH_VERIFY_FLAG=([01xXzZ])$", output, re.M)
    completed = all(re.search(r"^\s*" + marker + r"\s*$", output, re.M)
                    for marker in ("sig gen done", "sig verification done"))
    if tamper:
        passed = (returncode == 0 and matched and completed and flags == ["1"]
                  and output.count(TAMPER_MARKER) == 1
                  and "The signature is not matched!" in output
                  and "The signature is matched!" not in output
                  and not re.search(r"(?im)^\s*(?:ERROR|FATAL)(?:\s|:)", output))
        reason = "RTL verifier rejected a one-bit corrupted signature" if passed else "negative control did not establish RTL rejection"
    else:
        passed = ordinary["status"] == "PASS" and flags == ["0"] and TAMPER_MARKER not in output
        reason = ordinary["reason"] if passed else "baseline failed exact signature/verification-flag checks: " + ordinary["reason"]
    return {"case": "signature-memory-bitflip" if tamper else "baseline", "status": "PASS" if passed else "FAIL",
            "reason": reason, "simulator_returncode": returncode, "rtl_verification_flag": flags,
            "full_vendor_dump_matches": matched, "output_words": len(raw.splitlines()),
            "output_sha256": digest(raw) if fresh else None, "gate_result": ordinary}


def qualify_cases(cases):
    """A rejection is discriminating evidence only after a positive control passes."""
    baseline_ok = any(c['case'] == 'baseline' and c['status'] == 'PASS' for c in cases)
    for case in cases:
        if case['case'] != 'signature-memory-bitflip':
            continue
        contract_ok = case.get('negative_control_contract_satisfied', case['status'] == 'PASS')
        case['negative_control_contract_satisfied'] = contract_ok
        case['observed_rejection'] = (case.get('rtl_verification_flag') == ['1']
                                      and case.get('simulator_returncode') == 0)
        case['negative_control_qualified'] = contract_ok and baseline_ok
        if contract_ok and not baseline_ok:
            case['status'] = 'UNQUALIFIED'
            case['reason'] = 'untampered baseline did not verify; rejection is not a discriminating negative control'
    return cases


def run_check(rtl_dir=gate.DEFAULT_RTL, *, iverilog="iverilog", vvp="vvp", ivl_base=None, timeout=3600, jobs=2, fix_auth_sensitivity=False):
    report = {"schema_version": 1, "status": "ERROR", "evidence_kind": "portable_vendor_rtl_differential",
              "independent_fips_205_validation": False, "algorithm_version": "historical SPHINCSLET vendor SHA2 fixture; FIPS 205 conformance not established",
              "reference_commit": gate.REFERENCE_COMMIT, "pristine_upstream_commit": "a1adc2b324483d0f95ae42b3119997d3a61c77b6",
              "portability_variant": True, "auth_sensitivity_fix": fix_auth_sensitivity, "cases": []}
    stage = "setup"
    before = None
    try:
        if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        if jobs not in (1, 2):
            raise ValueError("jobs must be 1 or 2")
        rtl = Path(rtl_dir).resolve()
        report["selected_rtl_root"] = str(rtl)
        report["runner_sha256"] = digest(Path(__file__).read_bytes())
        parameter = gate.check_configuration(rtl / "sphincslet/setting.v")
        _, expected = gate.load_reference(parameter)
        inputs = gate.check_harness(rtl, parameter, rtl / "imports")
        report.update(parameter_set="SHA2-" + parameter, golden_sha256=digest(expected),
                      expected_output_words=gate.REFERENCES[parameter][1])
        compiler, runtime = shutil.which(iverilog), shutil.which(vvp)
        if not compiler or not runtime:
            report.update(status="UNAVAILABLE", reason="Icarus compiler and runtime are required; pass --iverilog and --vvp or put them on PATH")
            return report, 2
        compiler_cmd = [compiler]
        if ivl_base:
            if not Path(ivl_base).is_dir():
                raise ValueError("Icarus backend directory is missing")
            compiler_cmd += ["-B", str(Path(ivl_base).resolve())]
        for name, command in (("iverilog", compiler_cmd), ("vvp", [runtime])):
            version = subprocess.run([*command, "-V"], capture_output=True, text=True, timeout=30)
            lines = (version.stdout + version.stderr).splitlines()
            if version.returncode or not lines:
                raise RuntimeError(f"{name} version check failed")
            report[name + "_version"] = lines[0]
        before = rtl_hashes(rtl)
        report["source_sha256"] = before
        report["input_sha256"] = {Path(p).name: h for p, h in inputs.items()}
        parent = Path(os.environ.get("PQC_RUN_DIR", str(ROOT / ".pqc_runs"))).resolve()
        parent.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix="slh-portable-", dir=parent))
        report["run_dir"] = str(work)
        staged = work / "rtl"
        shutil.copytree(rtl, staged)
        if rtl_hashes(staged) != before:
            raise RuntimeError("source bytes changed while staging")
        gate.check_harness(staged, parameter, rtl / "imports")
        changes = portability_variant(staged)
        if fix_auth_sensitivity:
            changes.append(auth_sensitivity_variant(staged))
        report["portability_changes"] = [{k: v for k, v in c.items() if k != "diff"} for c in changes]
        (work / "portability.patch").write_text("".join(c["diff"] for c in changes))
        staged_before = rtl_hashes(staged)
        report["staged_source_sha256"] = staged_before
        main = sorted(p for p in staged.rglob("*.v") if p.name not in ("clog2.v", "setting.v", "fifo.v")
                      and "sha" not in p.relative_to(staged).parts)
        files = [staged / "imports/global_include/clog2.v", staged / "sphincslet/setting.v", *main,
                 staged / "imports/fifo.v", *sorted((staged / "sphincslet/sha").rglob("*.v"))]
        binary = work / "tb.vvp"
        command = [*compiler_cmd, "-g2005", "-s", "tb", "-o", str(binary)]
        for inc in ("sphincslet", "imports/global_include", "sphincslet/fsm"):
            command += ["-I", str(staged / inc)]
        command += list(map(str, files))
        (work / "compile-command.json").write_text(json.dumps(command, indent=2))
        stage = "compile"
        compiled = run_process(command, cwd=work, timeout=timeout, log_path=work / "compile.log")
        report["compile_returncode"] = compiled.returncode
        if compiled.returncode:
            report.update(status="FAIL", stage=stage, reason="Icarus compilation failed; see compile.log")
            return report, 1
        binary_sha256 = digest(binary.read_bytes())
        report["executable_sha256"] = binary_sha256
        def simulate(tamper):
            case = "signature-memory-bitflip" if tamper else "baseline"
            case_root = work / case
            sim = case_root / "a/b/c/d"
            sim.mkdir(parents=True)
            data = case_root / "TECS_v8.srcs/sources_1/imports/data_sha2"
            data.mkdir(parents=True)
            for source, wanted in inputs.items():
                dest = data / Path(source).name
                shutil.copy2(source, dest)
                if digest(dest.read_bytes()) != wanted:
                    raise RuntimeError("fixture changed while staging")
            produced = data / f"SIG_file0_{parameter}_w.hex"
            if produced.exists():
                raise RuntimeError("unexpected pre-existing signature")
            started = time.monotonic()
            argv = [runtime, str(binary)] + (["+SLH_TAMPER"] if tamper else [])
            (case_root / "command.json").write_text(json.dumps(argv, indent=2))
            result = run_process(argv, cwd=sim, timeout=timeout, log_path=case_root / "sim.log")
            for source, wanted in inputs.items():
                if digest((data / Path(source).name).read_bytes()) != wanted:
                    raise RuntimeError("staged fixture changed during simulation")
            checked = check_case(expected, produced, result.stdout, result.returncode, parameter, tamper)
            checked["elapsed_seconds"] = round(time.monotonic() - started, 3)
            return checked
        stage = "simulation"
        with ThreadPoolExecutor(max_workers=jobs) as executor:
            report["cases"] = qualify_cases(list(executor.map(simulate, (False, True))))
        report["tracked_inputs_unchanged"] = (rtl_hashes(rtl) == before and hashes(inputs) == inputs
                                              and gate.load_reference(parameter)[1] == expected)
        report["staged_inputs_unchanged"] = rtl_hashes(staged) == staged_before and digest(binary.read_bytes()) == binary_sha256
        passed = (all(c["status"] == "PASS" for c in report["cases"])
                  and report["tracked_inputs_unchanged"] and report["staged_inputs_unchanged"])
        report.update(status="PASS" if passed else "FAIL", reason="baseline and live signature-corruption control passed" if passed else "verification failed")
        return report, 0 if passed else 1
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        report.update(status="ERROR", stage=stage, reason=str(exc))
        if before is not None:
            try:
                report["tracked_sources_unchanged"] = rtl_hashes(rtl) == before
            except (OSError, RuntimeError):
                report["tracked_sources_unchanged"] = False
        return report, 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rtl-dir", type=Path, default=gate.DEFAULT_RTL)
    parser.add_argument("--iverilog", default="iverilog")
    parser.add_argument("--vvp", default="vvp")
    parser.add_argument("--ivl-base")
    parser.add_argument("--timeout", type=float, default=3600)
    parser.add_argument("--jobs", type=int, choices=(1, 2), default=2)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fix-auth-sensitivity", action="store_true",
                        help="Explicitly add leaf_idx to the vendor authentication-path sensitivity list")
    args = parser.parse_args()
    output = args.output
    values = vars(args).copy()
    values.pop("output")
    report, code = run_check(**values)
    text = json.dumps(report, indent=2) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text)
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
