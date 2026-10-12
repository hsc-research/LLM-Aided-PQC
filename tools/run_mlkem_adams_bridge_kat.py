#!/usr/bin/env python3
"""Fail-closed public-AHB ACVP gate for pinned, unified Adams Bridge RTL.

0 = all 80 official cases simulated with exact output/status accounting.
1 = simulated mismatch, protocol failure, or untrustworthy result transcript.
2 = unavailable tool, compile failure, timeout, input-integrity error, or prepare only.
No external network, tool installation, upstream scripts, DPI, or oracle execution.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "third_party/adams_bridge"
TB = ROOT / "verification/mlkem_adams_bridge/tb_mlkem_acvp.sv"
RTL_COMMIT = "b77e3d899e828d626cfc2a0d26a6b5704cc121e0"
ACVP_COMMIT = "975de31eb83d87039ec88934fdc47d8c312b892d"
SOURCE_MANIFEST_SHA256 = "9eca4e7c082ec36f287713e56a4b47bca6f0c340ac4c10536c7bdbee68a9e907"
INTEGRATION_MANIFEST_SHA256 = "3f6207bd0dc7455004b61aab3596cf78e339be146cf927c1c9b4671d56579e1f"
WRAPPER_SHA256 = "b377aa515a3a6654208798437c35efe70d33329018b3a261ee38834bd8a32a87"
VECTOR_SHA256 = "b7b1ab2cb459632301bed7bf1cff8625f71cb241479abfbd20596702a5401c8e"
EXPECTED_COUNTS = {"keyGen": 25, "encapsulation": 25, "decapsulation": 10,
                   "decapsulationKeyCheck": 10, "encapsulationKeyCheck": 10}
ADDR = {"entropy": 0x18, "ctrl": 0x9010, "status": 0x9014,
        "d": 0x9018, "z": 0x9038, "k": 0x9058, "m": 0x9080,
        "dk": 0xa000, "ek": 0xb000, "c": 0xb800}
LENGTHS = {"d": 32, "z": 32, "m": 32, "k": 32, "dk": 3168,
           "ek": 1568, "c": 1568, "entropy": 64}
CASE_LINE = re.compile(r"MLKEM_CASE_PASS id=(\d+) checks=(\d+) cycles=(\d+)")
FINAL_LINE = re.compile(r"MLKEM_ACVP_PASS cases=(\d+) checks=(\d+)")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def byte_array(value: str, field: str) -> bytes:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9A-Fa-f]+", value):
        raise ValueError(f"{field}: non-hexadecimal input")
    data = bytes.fromhex(value)
    if len(data) != LENGTHS[field]:
        raise ValueError(f"{field}: expected {LENGTHS[field]} bytes, got {len(data)}")
    return data


def words_le(data: bytes) -> list[int]:
    if len(data) % 4:
        raise ValueError("partial 32-bit word")
    return [int.from_bytes(data[i:i + 4], "little") for i in range(0, len(data), 4)]


def load_vectors(path: Path) -> dict:
    if digest(path) != VECTOR_SHA256:
        raise ValueError("official ACVP fixture SHA256 does not match pinned fixture")
    vectors = json.loads(path.read_text())
    if (vectors.get("source_commit") != ACVP_COMMIT
            or vectors.get("parameter_set") != "ML-KEM-1024"
            or vectors.get("revision") != "FIPS203"
            or Counter(c["operation"] for c in vectors["cases"]) != EXPECTED_COUNTS):
        raise ValueError("unexpected ACVP identity or incomplete operation coverage")
    identities = [(c["operation"], c["tgId"], c["tcId"]) for c in vectors["cases"]]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate ACVP case identity")
    return vectors


def build_commands(vectors: dict) -> tuple[str, list[dict]]:
    """Only map FIPS byte arrays to public registers; implement no KEM oracle."""
    lines: list[str] = []
    cases: list[dict] = []

    def emit(op: int, address: int = 0, value: int = 0) -> None:
        lines.append(f"{op:08x} {address:08x} {value:08x}")

    def data_words(op: int, field: str, value: bytes) -> int:
        for i, word in enumerate(words_le(value)):
            emit(op, ADDR[field] + i * 4, word)
        return len(value) // 4

    for number, case in enumerate(vectors["cases"], 1):
        operation = case["operation"]
        if case["group"].get("parameterSet") != "ML-KEM-1024":
            raise ValueError("wrong parameter set in case")
        inputs = {**case["group"], **case["input"]}
        expected = case["expected"]
        item = {"id": number, "operation": operation, "tgId": case["tgId"],
                "tcId": case["tcId"], "checks": 1, "compared_output_bytes": 0,
                "implicit_rejection": False}
        emit(5, 0, number)  # reset; isolate every official vector
        emit(3)  # require clean READY after reset
        # Deterministic nonzero entropy only masks implementation internals.
        data_words(1, "entropy", bytes((i * 29 + number) % 256 for i in range(64)))
        if operation == "keyGen":
            command, input_fields, output_fields = 1, ("d", "z"), ("ek", "dk")
        elif operation == "encapsulation":
            command, input_fields, output_fields = 2, ("ek", "m"), ("c", "k")
        elif operation == "decapsulation":
            command, input_fields, output_fields = 3, ("dk", "c"), ("k",)
            # FIPS 203 implicit rejection J(z || c) must return this 32-byte K,
            # not an error or a zero secret. These are official expected bytes.
            dk, ciphertext = byte_array(inputs["dk"], "dk"), byte_array(inputs["c"], "c")
            rejection = hashlib.shake_256(dk[-32:] + ciphertext).digest(32)
            item["implicit_rejection"] = rejection == byte_array(expected["k"], "k")
        elif operation == "encapsulationKeyCheck":
            command, input_fields, output_fields = 2, ("ek", "m"), ()
            inputs["m"] = "00" * 32  # key validity is independent of message
        elif operation == "decapsulationKeyCheck":
            command, input_fields, output_fields = 3, ("dk", "c"), ()
            inputs["c"] = "00" * 1568  # key hash validity is independent of c
        else:
            raise ValueError(f"unhandled operation {operation}")
        for field in input_fields:
            data_words(1, field, byte_array(inputs[field], field))
        key_check = operation.endswith("KeyCheck")
        if key_check and type(expected.get("testPassed")) is not bool:
            raise ValueError("key check missing Boolean expected result")
        error_expected = key_check and not expected["testPassed"]
        item["expected_key_error"] = error_expected
        emit(1, ADDR["ctrl"], command)
        emit(4, ADDR["status"], 4 if error_expected else 3)
        for field in output_fields:
            data = byte_array(expected[field], field)
            item["checks"] += data_words(2, field, data)
            item["compared_output_bytes"] += len(data)
        if error_expected:
            # The pinned API must hide a shared secret after key-input failure.
            item["checks"] += data_words(2, "k", bytes(32))
            item["compared_output_bytes"] += 32
        emit(6, number, item["checks"])
        cases.append(item)
    if sum(c["implicit_rejection"] for c in cases) != 5:
        raise ValueError("missing official implicit-rejection coverage")
    emit(7, len(cases), sum(c["checks"] for c in cases))
    return "\n".join(lines) + "\n", cases


def source_inputs(vendor: Path) -> dict[str, str]:
    """Verify downloaded vendor files and hash every compile dependency."""
    upstream = vendor / "upstream"
    source_manifest = upstream / "SOURCE_MANIFEST.json"
    if digest(source_manifest) != SOURCE_MANIFEST_SHA256:
        raise ValueError("upstream manifest differs from reviewed pin")
    if digest(vendor / "integration/manifest.json") != INTEGRATION_MANIFEST_SHA256:
        raise ValueError("integration manifest differs from reviewed pin")
    if digest(vendor / "integration/abr_unified_top.sv") != WRAPPER_SHA256:
        raise ValueError("integration wrapper differs from reviewed pin")
    manifest = json.loads(source_manifest.read_text())
    if manifest.get("commit") != RTL_COMMIT:
        raise ValueError("wrong upstream RTL commit")
    hashes = {}
    for record in manifest["files"]:
        path = (upstream / record["path"]).resolve()
        if not path.is_relative_to(upstream.resolve()):
            raise ValueError("vendor manifest path escapes source root")
        actual = digest(path)
        if actual != record["sha256"]:
            raise ValueError(f"vendor file hash mismatch: {record['path']}")
        hashes[str(path.relative_to(vendor))] = actual
    integration = json.loads((vendor / "integration/manifest.json").read_text())
    if integration.get("top") != "abr_unified_top" or integration.get("upstream_commit") != RTL_COMMIT:
        raise ValueError("unexpected integration top or revision")
    for record in integration["files"]:
        path = (vendor / record["path"]).resolve()
        if not path.is_relative_to(vendor.resolve()):
            raise ValueError("integration source escapes vendor root")
        if record["path"].startswith("upstream/") and record["path"] not in hashes:
            raise ValueError("compile source absent from source manifest")
        hashes[str(path.relative_to(vendor))] = digest(path)
    for path in [source_manifest, vendor / "integration/manifest.json",
                 vendor / "integration/sources.f",
                 vendor / "test_vectors/nist_acvp_mlkem1024.json"]:
        hashes[str(path.relative_to(vendor))] = digest(path)
    hashes["independent_testbench"] = digest(TB)
    hashes["independent_runner"] = digest(Path(__file__))
    return hashes


PURE_SV_FUNCTIONS = {
    "$bits", "$clog2", "$size", "$left", "$right", "$low", "$high",
    "$signed", "$unsigned", "$countones", "$countbits", "$onehot", "$onehot0",
    "$isunknown", "$stable", "$past", "$rose", "$fell", "$changed",
}


def candidate_inputs(candidate_root: Path, vendor: Path = VENDOR) -> tuple[dict, list[dict]]:
    """Admit only an isolated same-inventory RTL tree, never a replacement oracle."""
    if candidate_root.is_symlink():
        raise ValueError("candidate root must not be a symlink")
    candidate_root = candidate_root.resolve()
    reference = (vendor / "upstream").resolve()
    if (candidate_root.is_relative_to(reference) or reference.is_relative_to(candidate_root)
            or not candidate_root.is_dir()):
        raise ValueError("candidate root must be a separate directory outside the reference tree")
    manifest = json.loads((reference / "SOURCE_MANIFEST.json").read_text())
    expected = {x["path"] for x in manifest["files"]} | {"SOURCE_MANIFEST.json"}
    entries = list(candidate_root.rglob("*"))
    if any(path.is_symlink() for path in entries):
        raise ValueError("candidate tree must contain no symlinks")
    actual = {str(path.relative_to(candidate_root)) for path in entries if path.is_file()}
    if actual != expected:
        raise ValueError("candidate inventory differs: copy the complete pinned upstream tree; no extra/missing files")
    hashes, changes = {}, []
    for relative in sorted(expected):
        path, original = candidate_root / relative, reference / relative
        actual_hash, original_hash = digest(path), digest(original)
        hashes[relative] = actual_hash
        if actual_hash == original_hash:
            continue
        rel = Path(relative)
        rtl = relative.startswith("src/") and "/rtl/" in relative and rel.suffix in {".sv", ".svh", ".v"}
        protected = (rel.name == "abr_config_defines.svh" or "assert" in rel.name
                     or rel.name == "abr_sva.svh")
        if not rtl or protected:
            raise ValueError(f"candidate may not change protected/non-RTL file: {relative}")
        text, old_text = path.read_text(), original.read_text()
        if re.findall(r"`include[^\n]*", text) != re.findall(r"`include[^\n]*", old_text):
            raise ValueError(f"candidate must preserve include directives: {relative}")
        # The candidate is a hardware implementation, not executable test code.
        # Conservatively reject changes to files containing non-hardware system
        # tasks rather than granting new file/process/DPI or simulation controls.
        uncommented = re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S)
        calls = set(re.findall(r"\$[A-Za-z_][A-Za-z_0-9]*", uncommented))
        if calls - PURE_SV_FUNCTIONS or re.search(r'\b(?:import|export)\s*"DPI', uncommented):
            raise ValueError(f"candidate contains non-hardware simulator calls: {relative}")
        if any(marker in text for marker in ("MLKEM_CASE_PASS", "MLKEM_ACVP_PASS", "MLKEM_FAIL")):
            raise ValueError(f"candidate contains reserved harness result markers: {relative}")
        changes.append({"path": relative, "reference_sha256": original_hash, "candidate_sha256": actual_hash})
    return hashes, changes


def compile_filelist(vendor: Path, manifest: dict, candidate_root: Path | None) -> str:
    def resolve(relative: str) -> str:
        relative_path = Path(relative)
        if candidate_root is not None and relative_path.parts[0] == "upstream":
            return str(candidate_root / Path(*relative_path.parts[1:]))
        return str(vendor / relative_path)
    return "\n".join(["+incdir+" + resolve(p) for p in manifest["include_dirs"]]
                     + [resolve(x["path"]) for x in manifest["files"]] + [str(TB)]) + "\n"


def check_transcript(log: str, cases: list[dict], returncode: int) -> tuple[bool, str]:
    if returncode:
        return False, f"simulator exited {returncode}"
    if re.search(r"MLKEM_FAIL|\b(?:FATAL|ERROR|Error)\b|%Error", log):
        return False, "simulator reported a failure"
    observed, summaries, events = [], [], []
    for line in log.splitlines():
        if "MLKEM_CASE_PASS" in line:
            match = CASE_LINE.fullmatch(line.strip())
            if not match:
                return False, "malformed case result"
            ident, checks, cycles = map(int, match.groups())
            if cycles < 1:
                return False, "nonpositive simulated case cycle count"
            observed.append((ident, checks))
            events.append("case")
        if "MLKEM_ACVP_PASS" in line:
            match = FINAL_LINE.fullmatch(line.strip())
            if not match:
                return False, "malformed completion marker"
            summaries.append(tuple(map(int, match.groups())))
            events.append("summary")
    expected = [(c["id"], c["checks"]) for c in cases]
    if observed != expected:
        return False, "missing, duplicate, out-of-order, or incorrect case result"
    if events != ["case"] * len(cases) + ["summary"]:
        return False, "completion marker out of order"
    if summaries != [(len(cases), sum(c["checks"] for c in cases))]:
        return False, "missing, duplicate, or incorrect completion marker"
    return True, "all official vectors and exact output/status checks passed"


def run_stage(command: list[str], cwd: Path, log: Path, timeout: int) -> tuple[int, float]:
    start = time.monotonic()
    # shell=False; only reviewed RTL and this authored testbench are compiled.
    with log.open("w") as output:
        process = subprocess.Popen(command, cwd=cwd, stdout=output, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Stop only our own process group, including compiler/make children.
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            raise
    return returncode, round(time.monotonic() - start, 3)


def run(args: argparse.Namespace) -> tuple[dict, int]:
    work = args.work_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    report = {"schema_version": 1, "status": "UNAVAILABLE", "rtl_kat_passed": False,
              "scope": "ML-KEM-1024 API of unified ML-KEM-1024 / ML-DSA-87 RTL with SRAM models",
              "upstream_commit": RTL_COMMIT, "acvp_commit": ACVP_COMMIT,
              "certification": False, "work_dir": str(work),
              "verification_target": "modified_candidate" if args.candidate_root else "pinned_reference",
              "ml_dsa_87_qualified": False,
              "full_unified_behavior_preservation_qualified": False}
    try:
        before = source_inputs(VENDOR)
        candidate_before = None
        candidate_root = args.candidate_root.resolve() if args.candidate_root else None
        if args.candidate_root:
            candidate_before, changes = candidate_inputs(args.candidate_root)
            report.update(candidate_root=str(candidate_root), candidate_input_sha256=candidate_before,
                          candidate_changes=changes, candidate_matches_pinned_upstream=not changes,
                          reference_source_integrity_verified=True,
                          candidate_integrity_scope="same inventory, permitted modifications hashed; not byte-exact upstream verification")
        vectors = load_vectors(VENDOR / "test_vectors/nist_acvp_mlkem1024.json")
        commands, cases = build_commands(vectors)
        script = work / "commands.hex"
        script.write_text(commands)
        report.update(input_sha256=before, commands_sha256=digest(script), cases=cases,
                      expected_cases=len(cases), expected_checks=sum(c["checks"] for c in cases),
                      expected_implicit_rejection_cases=5)
        (work / "case_manifest.json").write_text(json.dumps(cases, indent=2) + "\n")
        if args.prepare_only:
            report.update(status="PREPARED_NOT_VERIFIED", reason="No RTL compile or simulation requested")
            return report, 2
        simulator = args.simulator
        if simulator == "auto":
            simulator = "verilator" if shutil.which(args.verilator) else "iverilog"
        executable = shutil.which(args.verilator if simulator == "verilator" else args.iverilog)
        runtime = shutil.which(args.vvp) if simulator == "iverilog" else None
        if executable is None or (simulator == "iverilog" and runtime is None):
            report["reason"] = f"{simulator} compiler/runtime not available"
            return report, 2
        version = subprocess.run([executable, "--version" if simulator == "verilator" else "-V"],
                                 capture_output=True, text=True, timeout=30, check=False)
        if version.returncode:
            raise ValueError("simulator version command failed")
        report.update(simulator=simulator, tool_version=(version.stdout + version.stderr).splitlines()[0],
                      state_model="two-state" if simulator == "verilator" else "four-state")
        filelist = work / "sources.f"
        # Regenerate absolute paths from the reviewed, ordered integration manifest.
        manifest = json.loads((VENDOR / "integration/manifest.json").read_text())
        filelist.write_text(compile_filelist(VENDOR, manifest, candidate_root))
        report["compile_filelist_sha256"] = digest(filelist)
        if simulator == "verilator":
            binary = work / "obj_dir/Vtb_mlkem_acvp"
            compile_cmd = [executable, "--binary", "--timing", "--assert", "-Wno-fatal",
                           "--top-module", "tb_mlkem_acvp", "--Mdir", str(binary.parent),
                           "-j", str(args.jobs), "-f", str(filelist)]
            simulate_cmd = [str(binary)]
        else:
            binary = work / "tb.vvp"
            compile_cmd = [executable, "-g2012", "-s", "tb_mlkem_acvp", "-o", str(binary), "-f", str(filelist)]
            simulate_cmd = [runtime, str(binary)]
        report["compile_command"] = compile_cmd
        compile_log = work / "compile.log"
        rc, elapsed = run_stage(compile_cmd, VENDOR, compile_log, args.compile_timeout)
        report.update(compile_returncode=rc, compile_seconds=elapsed, compile_log=str(compile_log))
        if rc or not binary.is_file():
            report.update(status="COMPILE_FAILED", reason="Authentic RTL did not compile; see compile.log")
            return report, 2
        simulate_cmd += [f"+COMMANDS={script}", f"+MAX_CYCLES={args.max_cycles}"]
        report["simulate_command"] = simulate_cmd
        sim_log = work / "simulation.log"
        rc, elapsed = run_stage(simulate_cmd, VENDOR, sim_log, args.sim_timeout)
        report.update(simulate_returncode=rc, simulate_seconds=elapsed, simulation_log=str(sim_log))
        passed, reason = check_transcript(sim_log.read_text(), cases, rc)
        unchanged = before == source_inputs(VENDOR) and digest(script) == report["commands_sha256"]
        if candidate_root is not None:
            candidate_after, _ = candidate_inputs(candidate_root)
            candidate_unchanged = candidate_before == candidate_after
            report["candidate_inputs_unchanged"] = candidate_unchanged
            unchanged = unchanged and candidate_unchanged
        passed = passed and unchanged
        report.update(status="PASS" if passed else "FAIL", rtl_kat_passed=passed,
                      reason=reason if unchanged else "inputs changed during verification", inputs_unchanged=unchanged)
        return report, 0 if passed else 1
    except subprocess.TimeoutExpired as error:
        report.update(status="TIMEOUT", reason=f"Tool exceeded timeout: {error.timeout}s")
    except (OSError, ValueError, KeyError, TypeError) as error:
        report.update(status="ERROR", reason=f"{type(error).__name__}: {error}")
    return report, 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulator", choices=("auto", "verilator", "iverilog"), default="auto")
    parser.add_argument("--verilator", default="verilator")
    parser.add_argument("--iverilog", default="iverilog")
    parser.add_argument("--vvp", default="vvp")
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--candidate-root", type=Path,
                        help="Isolated complete copy of upstream tree; protected wrapper/harness/vectors remain original")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--compile-timeout", type=int, default=900)
    parser.add_argument("--sim-timeout", type=int, default=900)
    parser.add_argument("--max-cycles", type=int, default=200000)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    if args.work_dir is None:
        args.work_dir = ROOT / "build/mlkem_adams_bridge"
        if args.candidate_root:
            args.work_dir = args.work_dir / "candidate"
    if min(args.compile_timeout, args.sim_timeout, args.max_cycles, args.jobs) < 1:
        parser.error("timeouts, max-cycles and jobs must be positive")
    report_path = args.report or args.work_dir / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    # An interrupted rerun must never leave an old PASS at the selected path.
    report_path.write_text(json.dumps({"schema_version": 1, "status": "RUNNING",
                                       "rtl_kat_passed": False}) + "\n")
    report, code = run(args)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"cases", "input_sha256", "candidate_input_sha256"}}, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
