#!/usr/bin/env python3
"""Execute ML-DSA KeyGen, Sign and Verify RTL KATs without a vendor simulator.

GHDL synthesizes the pinned VHDL Keccak hierarchy to a Verilog netlist;
Icarus or Verilator then simulates that netlist with the actual Verilog design.
This is functional RTL/netlist simulation, not a PPA or mixed-language-equivalence
claim. All transformations occur in a unique run directory, never upstream/.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from agent.mldsa_sources import BUNDLED_ROOT, verify_snapshot
from agent.run_safety import hashes, run_process

OPERATIONS = {"keygen": ("KeyGen", 25), "sign": ("Sign", 15), "verify": ("Verify", 15)}
LEVELS = ("II", "III", "V")


def evaluate_log(text, operation, count, returncode=0):
    """Require exactly the expected unique completions, plus a terminal marker."""
    label = OPERATIONS[operation][0]
    pattern = re.compile(r"ML-DSA-(II|III|V)\." + label +
                         r", KAT #\s*(\d+) completed in\s*(\d+) clock cycles")
    results = [{"level": m[1], "kat": int(m[2]), "cycles": int(m[3])}
               for m in pattern.finditer(text)]
    keys = [(v["level"], v["kat"]) for v in results]
    expected = {(level, i) for level in LEVELS for i in range(count)}
    failures = [line for line in text.splitlines()
                if re.search(r"WRONG|\bFATAL\b|\bERROR\b|%Error|watchdog", line, re.I)]
    reason = None
    if returncode:
        reason = f"simulator exit {returncode}"
    elif failures:
        reason = failures[0]
    elif "testbench done" not in text.lower():
        reason = "missing terminal testbench marker"
    elif set(keys) != expected or len(keys) != len(expected):
        reason = "missing, duplicate, or unexpected vector completions"
    elif not all(v["cycles"] > 0 for v in results):
        reason = "nonpositive cycle count"
    return {"status": "FAIL" if reason else "PASS", "reason": reason,
            "operation": operation, "expected": len(expected),
            "completed": len(results), "vectors": results}


def hoist_declarations(source):
    """Same declaration-only shim as the historical Vivado KeyGen runner."""
    declaration = re.compile(
        r"^[ \t]*(reg|wire)(\s+(signed)?\s*(\[[^\]]+\])?)?\s+"
        r"([A-Za-z_][A-Za-z0-9_]*(\s*\[[^\]]+\])?"
        r"(\s*,\s*[A-Za-z_][A-Za-z0-9_]*(\s*\[[^\]]+\])?)*)\s*;\s*$", re.M)
    found = []
    for match in declaration.finditer(source):
        names = [re.split(r"\s*\[", n.strip())[0] for n in match[5].split(",")]
        if any(re.search(r"\b" + re.escape(n) + r"\b", source[:match.start()]) for n in names):
            found.append(match[0].strip())
    for decl in found:
        source = source.replace(decl, "", 1)
    end = source.find(");", source.find("module combined_top")) + 2
    if end < 2:
        raise ValueError("combined_top module header not found")
    return source[:end] + "\n" + "\n".join(found) + "\n" + source[end:], len(found)


def prepare_testbench(text, operation, count, cycle_limit):
    capacity = OPERATIONS[operation][1]
    pattern = re.compile(r"\blocalparam\s+NUM_TV\s*=\s*(\d+)\s*;")
    if pattern.findall(text) != [str(capacity)]:
        raise ValueError(f"unexpected {operation} testbench capacity")
    text = pattern.sub(f"localparam NUM_TV = {count};", text)
    # A simulator wall-time bound is not enough: ensure hardware deadlocks
    # explicitly fail rather than looking like a quiet, successful process.
    anchor = "\nendmodule"
    if text.count(anchor) != 1:
        raise ValueError("expected one testbench endmodule")
    watchdog = (f"\n    integer portable_cycles = 0;\n"
                f"    always @(posedge clk) begin\n"
                f"        portable_cycles <= portable_cycles + 1;\n"
                f"        if (portable_cycles >= {cycle_limit})\n"
                f"            $fatal(1, \"portable watchdog expired\");\n"
                f"    end\n")
    return text.replace(anchor, watchdog + anchor)


def stage_verify_mutations(kat, destination):
    """Four one-bit negatives from one verified-valid, nonempty-context case/level.

    The untouched positive control is part of the ordinary Verify KAT run.
    No expected value is obtained from the hardware being tested.
    """
    destination.mkdir(parents=True, exist_ok=True)
    metadata = []
    fields = ("message", "mlen", "pk", "ctx", "ctxlen", "signature", "result")
    mutations = ("signature", "message", "ctx", "pk")
    for level in (44, 65, 87):
        records = {name: (kat / f"SigVer_{name}_{level}.txt").read_text().split() for name in fields}
        if any(len(row) != 15 for row in records.values()):
            raise ValueError(f"unexpected Verify KAT shape for {level}")
        candidates = [i for i in range(15) if records["result"][i] == "1"
                      and int(records["mlen"][i], 16) and int(records["ctxlen"][i], 16)]
        if not candidates:
            raise ValueError(f"no valid positive control with message and context: {level}")
        index = candidates[0]
        generated = {name: [] for name in fields}
        for mutation in mutations:
            row = {name: records[name][index] for name in fields}
            original = row[mutation]
            # Least significant bit is inside the message/context even when
            # their files are left-zero-padded to their fixed maximum lengths.
            row[mutation] = format(int(original, 16) ^ 1, f"0{len(original)}x")
            row["result"] = "0"
            for name in fields:
                generated[name].append(row[name])
            metadata.append({"parameter_set": level, "positive_control_index": index,
                             "mutation": mutation + " least-significant bit", "expected": 0})
        for name, values in generated.items():
            (destination / f"SigVer_{name}_{level}.txt").write_text("\n".join(values) + "\n")
    return metadata


def run_gate(*, override=None, operations=("keygen", "sign", "verify"), vectors=None,
             simulator="iverilog", timeout=1800, cycle_limit=20000000, jobs=2,
             fifo_nonblocking=False, verify_mutations=False):
    if not operations or len(set(operations)) != len(operations) or any(x not in OPERATIONS for x in operations):
        raise ValueError("operations must be unique keygen, sign, or verify values")
    if vectors is not None and (isinstance(vectors, bool) or not isinstance(vectors, int)
                                or not 1 <= vectors <= min(OPERATIONS[x][1] for x in operations)):
        raise ValueError("vectors exceeds the selected operation capacity")
    if simulator not in ("iverilog", "verilator"):
        raise ValueError("unsupported simulator")
    if not 0 < timeout < float("inf") or cycle_limit < 1 or jobs < 1:
        raise ValueError("timeout, cycle limit and jobs must be positive")
    parent = Path(os.environ.get("PQC_RUN_DIR", REPO / ".pqc_runs")).resolve()
    parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="mldsa-portable-", dir=parent))
    outcome = {"status": "FAIL", "run_dir": str(work), "backend": "ghdl-synth+" + simulator,
               "variant": "candidate" if override else "pinned-baseline",
               "coverage": {}, "transformations": [], "commands": [], "tools": {}}
    started = time.monotonic()
    stage = "setup"
    input_hashes = {}
    staged_hashes = {}

    def execute(argv, name, cwd=None, stdout_file=None, allow_failure=False):
        log = work / (name + ".log")
        outcome["commands"].append({"argv": list(map(str, argv)), "cwd": str(cwd or work), "log": str(log)})
        if stdout_file is None:
            result = run_process(list(map(str, argv)), cwd=cwd or work, timeout=timeout, log_path=log)
        else:
            # Keep diagnostic stderr out of the generated Verilog file.
            with Path(stdout_file).open("w") as output, log.open("w") as errors:
                process = subprocess.Popen(list(map(str, argv)), cwd=cwd or work,
                                           stdout=output, stderr=errors, start_new_session=True)
                try:
                    process.wait(timeout=timeout)
                except BaseException:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    raise
            result = subprocess.CompletedProcess(argv, process.returncode, log.read_text(errors="replace"))
        if result.returncode and not allow_failure:
            raise RuntimeError(f"{name} failed (exit {result.returncode}): {result.stdout[-2000:]}")
        return result if allow_failure else result.stdout

    try:
        outcome["snapshot"] = verify_snapshot()
        source = BUNDLED_ROOT / "ref_combined/src"
        chosen = {p.name: p for p in source.iterdir() if p.is_file()}
        if override:
            directory = Path(override).resolve()
            replacements = [p for p in directory.iterdir() if p.suffix in (".v", ".vhd", ".vh")]
            if not replacements:
                raise ValueError("no candidate overrides")
            for path in replacements:
                if path.name not in chosen:
                    raise ValueError(f"unknown override: {path}")
                chosen[path.name] = path
            outcome["override"] = str(directory)
        inputs = list(chosen.values()) + [p for folder in ("KAT", "common", "ref_combined/src_tb")
                                          for p in (BUNDLED_ROOT / folder).iterdir() if p.is_file()]
        input_hashes = hashes(inputs)
        outcome["input_hashes"] = input_hashes
        staged = work / "ref_combined/src"
        staged.mkdir(parents=True)
        for name, path in chosen.items():
            shutil.copy2(path, staged / name)
        for folder in ("common", "KAT", "ref_combined/src_tb"):
            shutil.copytree(BUNDLED_ROOT / folder, work / folder)
        # Verify each copy before making declared transformations, not merely
        # the originals again after the run.
        copy_map = {staged / name: path for name, path in chosen.items()}
        copy_map.update({work / path.relative_to(BUNDLED_ROOT): path for path in inputs
                         if path not in chosen.values()})
        for copy, original in copy_map.items():
            if hashes([copy])[str(copy.resolve())] != input_hashes[str(original.resolve())]:
                raise RuntimeError(f"staged copy differs from selected input: {copy}")
        source_text, num_hoisted = hoist_declarations((staged / "combined_top.v").read_text())
        (staged / "combined_top.v").write_text(source_text)
        outcome["transformations"].append({"file": "combined_top.v", "edit": "hoist forward declarations", "count": num_hoisted})
        if fifo_nonblocking:
            fifo = staged / "ntt_fifo_piso.v"
            original = fifo.read_text()
            patched, changes = re.subn(r"(fifo\[[0-3]\]) = ", r"\1 <= ", original)
            if changes != 8:
                raise ValueError(f"expected eight FIFO assignment edits, found {changes}")
            fifo.write_text(patched)
            outcome["transformations"].append({"file": fifo.name, "edit": "eight clocked blocking assignments to nonblocking; semantic variant"})
            outcome["variant"] += "+fifo-nonblocking"
        for binary in ("ghdl", simulator, *(("vvp",) if simulator == "iverilog" else ())):
            if not shutil.which(binary):
                raise FileNotFoundError(f"required tool not on PATH: {binary}")
            flag = "-V" if binary in ("iverilog", "vvp") else "--version"
            outcome["tools"][binary] = execute([binary, flag], "version-" + binary).splitlines()[:4]
        stage = "ghdl-analyze"
        # Dependency order is explicit; no black boxes or software hash stub.
        order = ["sha3_pkg", "keccak_pkg", "regn", "piso", "sipo", "countern", "sr_reg",
                 "keccak_bytepad", "keccak_cons", "keccak_round", "keccak_fsm1",
                 "keccak_fsm2", "sha3_fsm3", "keccak_control", "keccak_datapath", "keccak_top"]
        if {p.stem for p in staged.glob("*.vhd")} != set(order):
            raise ValueError("VHDL manifest changed; update the dependency ordering explicitly")
        execute(["ghdl", "-a", "--std=08", "-fsynopsys", *[staged / (p + ".vhd") for p in order]], stage)
        stage = "ghdl-synth"
        netpath = staged / "keccak_top_ghdl.v"
        execute(["ghdl", "--synth", "--std=08", "-fsynopsys", "--out=verilog", "keccak_top"], stage, stdout_file=netpath)
        if not re.search(r"\bmodule keccak_top\b", netpath.read_text()):
            raise RuntimeError("GHDL did not emit the keccak_top module")
        outcome["transformations"].append({"file": netpath.name, "edit": "GHDL synthesized original VHDL hierarchy to Verilog"})
        outcome["staged_design_hashes"] = hashes(staged.iterdir())
        tbdir = work / "ref_combined/src_tb"
        for path in [*(work / "KAT").iterdir(), work / "common/zetas.txt"]:
            target = tbdir / path.name
            shutil.copy2(path, target)
            if hashes([target])[str(target.resolve())] != hashes([path])[str(path.resolve())]:
                raise RuntimeError(f"simulator data copy differs: {target}")
        runs = [(operation, operation, tbdir, vectors if vectors is not None else OPERATIONS[operation][1])
                for operation in operations]
        if verify_mutations:
            if "verify" not in operations:
                raise ValueError("--verify-mutations requires the Verify positive-control run")
            mutation_dir = work / "ref_combined/mutation_tb"
            outcome["verify_mutations"] = stage_verify_mutations(work / "KAT", mutation_dir)
            shutil.copy2(BUNDLED_ROOT / "ref_combined/src_tb/tb_verify_top.v", mutation_dir / "tb_verify_top.v")
            shutil.copy2(work / "common/zetas.txt", mutation_dir / "zetas.txt")
            runs.append(("verify_mutations", "verify", mutation_dir, 4))
        for case, operation, current_tbdir, count in runs:
            tb = current_tbdir / f"tb_{operation}_top.v"
            tb.write_text(prepare_testbench(tb.read_text(), operation, count, cycle_limit))
            top = tb.stem
            outcome.setdefault("testbench_hashes", {}).update(hashes([tb]))
            if case == "verify_mutations":
                outcome["mutation_input_hashes"] = hashes(current_tbdir.glob("SigVer_*.txt"))
            used_inputs = [*staged.iterdir(), *(work / "common").iterdir(), tb,
                           *current_tbdir.glob("*.txt")]
            case_hashes = hashes(used_inputs)
            staged_hashes.update(case_hashes)
            outcome.setdefault("simulation_input_hashes", {})[case] = case_hashes
            stage = case + "-compile"
            vfiles = sorted(staged.glob("*.v"))
            if simulator == "iverilog":
                executable = work / (case + ".vvp")
                execute(["iverilog", "-g2012", "-s", top, "-o", executable, *vfiles, tb], stage, current_tbdir)
                command = ["vvp", executable]
            else:
                objdir = work / ("obj_" + case)
                execute(["verilator", "--binary", "--timing", "--top-module", top, "--Mdir", objdir,
                         "-j", str(jobs), "-Wno-fatal", *vfiles, tb], stage, current_tbdir)
                command = [objdir / ("V" + top)]
            stage = case + "-sim"
            try:
                simulation = execute(command, stage, current_tbdir, allow_failure=True)
                result = evaluate_log(simulation.stdout, operation, count, simulation.returncode)
            except subprocess.TimeoutExpired:
                partial = (work / (stage + ".log")).read_text(errors="replace")
                result = evaluate_log(partial, operation, count, -9)
                result["reason"] = "simulator wall-time timeout"
                result["timed_out"] = True
            if hashes(case_hashes) != case_hashes:
                raise RuntimeError("staged simulation inputs changed during compilation or execution")
            if operation == "verify":
                expected = [(current_tbdir / f"SigVer_result_{level}.txt").read_text().split()[:count]
                            for level in ("44", "65", "87")]
                result["known_valid"] = sum(row.count("1") for row in expected)
                result["known_invalid"] = sum(row.count("0") for row in expected)
            outcome["coverage"][case] = result
            # Save incremental evidence even when a later stage fails.
            (work / "result.json").write_text(json.dumps(outcome, indent=2) + "\n")
            if result["status"] != "PASS":
                raise RuntimeError(result["reason"])
        outcome["status"] = "PASS"
        outcome["reason"] = "all selected RTL KATs completed with exact expected coverage"
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        outcome["reason"] = str(exc)
        outcome["stage"] = stage
    finally:
        try:
            if input_hashes and hashes(input_hashes) != input_hashes:
                raise RuntimeError("selected source or KAT changed during run")
            if staged_hashes and hashes(staged_hashes) != staged_hashes:
                raise RuntimeError("staged source or KAT changed during run")
        except (OSError, RuntimeError) as exc:
            outcome.update(status="FAIL", stage="integrity", reason=str(exc))
        outcome["runtime_s"] = round(time.monotonic() - started, 2)
        outcome["result_file"] = str(work / "result.json")
        (work / "result.json").write_text(json.dumps(outcome, indent=2) + "\n")
    return outcome


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--override")
    parser.add_argument("--operations", nargs="+", choices=tuple(OPERATIONS), default=list(OPERATIONS))
    parser.add_argument("--vectors", type=int, help="reduced per-level coverage")
    parser.add_argument("--simulator", choices=("iverilog", "verilator"), default="iverilog")
    parser.add_argument("--timeout", type=float, default=1800)
    parser.add_argument("--cycle-limit", type=int, default=20000000)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--verify-mutations", action="store_true", help="also reject modified signature, message, context and public key for each level")
    parser.add_argument("--fifo-nonblocking", action="store_true", help="explicit semantic portability variant")
    args = parser.parse_args()
    try:
        result = run_gate(**vars(args))
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
