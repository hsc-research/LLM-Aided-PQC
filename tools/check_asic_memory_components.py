#!/usr/bin/env python3
"""Check bounded ASIC-memory behavior and generic FF mapping; never run HQC.

This is component evidence, not whole-design qualification, PPA, technology
mapping, or certification. Original FPGA-qualified sources are never edited.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ABR = ROOT / "third_party/adams_bridge/upstream/src/abr_libs/rtl"
MLDSA = ROOT / "third_party/mldsa_osh/upstream"
SLH = ROOT / "agent/slh_dsa/pristine/imports"
ROM = ROOT / "asic/rtl/mldsa_zetas/dual_port_rom.v"
TB = ROOT / "verification/asic_memory"
MODULES = ("abr_1r1w_ram", "abr_1r1w_be_ram", "abr_1r1w_512x4_ram", "abr_ram_regout")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command, work, label, *, success=True):
    result = subprocess.run(list(map(str, command)), cwd=work, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    (work / (label + ".log")).write_text(result.stdout)
    if success and result.returncode:
        raise RuntimeError(f"{label} failed ({result.returncode}): {result.stdout[-4000:]}")
    return result


def verify_rom_constants():
    """Fail if the checked-in constant derivative is stale or incomplete."""
    data = MLDSA / "common/zetas.txt"
    expected = [int(x, 16) for x in data.read_text().split()]
    matches = re.findall(r"8'd(\d+): lookup = 24'h([0-9A-Fa-f]+);", ROM.read_text())
    if len(expected) != 256 or [int(i) for i, _ in matches] != list(range(256)):
        raise ValueError("ROM derivative must contain every zeta exactly once, in address order")
    if [int(x, 16) for _, x in matches] != expected or sha(data) not in ROM.read_text():
        raise ValueError("ROM derivative does not match the pinned zetas file/hash")
    if re.search(r"\binitial\b|\$readmem[hb]\b", re.sub(r"//[^\n]*", "", ROM.read_text())):
        raise ValueError("ROM derivative contains runtime/power-up initialization")


def synthesize(yosys, work, name, sources, top, *, parameters="", expected_ff_bits=None):
    netlist = work / (name + ".json")
    command = "read_verilog -sv " + " ".join(str(p) for p in sources) + "; "
    if parameters:
        command += "chparam " + parameters + " " + top + "; "
    command += (f"hierarchy -check -top {top}; proc; opt; memory_map; opt; "
                f"techmap; opt; check -assert; write_json {netlist}; stat")
    run([yosys, "-Q", "-T", "-p", command], work, "synth-" + name)
    modules = json.loads(netlist.read_text())["modules"]
    if set(modules) != {top}:
        raise ValueError(name + ": unexpected remaining hierarchy")
    module = modules[top]
    if module.get("memories") or module.get("attributes", {}).get("blackbox"):
        raise ValueError(name + ": memory array or blackbox remains")
    cells = Counter(c["type"] for c in module.get("cells", {}).values())
    if any(not t.startswith("$_") or "LATCH" in t.upper() for t in cells):
        raise ValueError(name + ": unmapped memory, latch, or non-generic cell remains: " + str(cells))
    if any("init" in n.get("attributes", {}) for n in module.get("netnames", {}).values()):
        raise ValueError(name + ": power-up initialization remains after mapping")
    ff = sum(n for kind, n in cells.items() if "DFF" in kind)
    if not ff or expected_ff_bits is not None and ff != expected_ff_bits:
        raise ValueError(f"{name}: unexpected FF-bit count {ff}, expected {expected_ff_bits}")
    return {"status": "PASS", "top": top, "parameters": parameters or "source defaults",
            "defines": [], "ff_bits": ff, "cell_types": dict(sorted(cells.items())),
            "remaining_memories": 0, "remaining_latches": 0,
            "power_up_init_attributes": 0, "mapping": "generic one-bit FF and logic cells, no technology library",
            "netlist_sha256": sha(netlist)}


def check(work, tool_dir=None):
    verify_rom_constants()
    work = Path(work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    tools = {}
    versions = {}
    for name in ("iverilog", "vvp", "yosys"):
        path = str(Path(tool_dir) / name) if tool_dir else shutil.which(name)
        if not path or not Path(path).is_file():
            raise ValueError("missing tool: " + name)
        tools[name] = path
        result = run([path, "-V"], work, "version-" + name)
        versions[name] = result.stdout.splitlines()[0]
    inputs = [*(ABR / (name + ".sv") for name in MODULES), ROM,
              MLDSA / "common/zetas.txt", MLDSA / "ref_combined/src/dual_port_rom.v",
              *(SLH / name for name in ("mem_dual.v", "mem_single.v", "global_include/clog2.v")),
              *sorted(TB.glob("*.sv")), Path(__file__).resolve()]
    before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    reference = work / "reference_rom.v"
    reference.write_text((MLDSA / "ref_combined/src/dual_port_rom.v").read_text().replace(
        "module dual_port_rom", "module reference_dual_port_rom", 1))
    shutil.copyfile(MLDSA / "common/zetas.txt", work / "zetas.txt")
    simulations = {}
    for name, top, sources, defines in (
        ("mldsa-rom", "tb_mldsa_rom", [reference, ROM, TB / "tb_mldsa_rom.sv"], []),
        ("abr-asic", "tb_abr_memories", [*(ABR / (m + ".sv") for m in MODULES), TB / "tb_abr_memories.sv"], []),
        ("abr-fpga", "tb_abr_memories", [*(ABR / (m + ".sv") for m in MODULES), TB / "tb_abr_memories.sv"], ["-DRV_FPGA_OPTIMIZE"]),
        ("slh-original", "tb_slh_memories", [SLH / "global_include/clog2.v", SLH / "mem_dual.v", SLH / "mem_single.v", TB / "tb_slh_memories.sv"], []),
    ):
        binary = work / (name + ".vvp")
        run([tools["iverilog"], "-g2012", *defines, "-s", top, "-o", binary, *sources], work, "compile-" + name)
        result = run([tools["vvp"], binary], work, "simulate-" + name)
        if not any(line.startswith("PASS ") for line in result.stdout.splitlines()):
            raise ValueError(name + ": missing explicit test completion marker")
        simulations[name] = {"status": "PASS", "details": result.stdout.strip()}
    bad = work / "unsupported_rom.v"
    bad.write_text('module bad; dual_port_rom #(.WIDTH(24),.LENGTH(256),.INIT_FILE("other.txt")) x(); endmodule\n')
    rejected = run([tools["iverilog"], "-g2012", "-s", "bad", "-o", work / "bad.vvp", ROM, bad], work, "reject-unsupported-rom", success=False)
    if rejected.returncode == 0 or "PQC_ASIC_ROM_REQUIRES" not in rejected.stdout:
        raise ValueError("unsupported ROM file must fail elaboration")
    simulations["unsupported-rom"] = {"status": "PASS", "details": "unsupported nonempty INIT_FILE fails elaboration"}
    mappings = {}
    for name in MODULES:
        count = 2052 if name == "abr_1r1w_512x4_ram" else 2080
        mappings[name] = synthesize(tools["yosys"], work, name, [ABR / (name + ".sv")], name, expected_ff_bits=count)
    mappings["mldsa-zetas-rom"] = synthesize(tools["yosys"], work, "mldsa-zetas-rom", [ROM], "dual_port_rom",
        parameters='-set WIDTH 24 -set LENGTH 256 -set INIT_FILE "zetas.txt"')
    for name in ("mem_dual", "mem_single"):
        mappings["slh-" + name + "-uninitialized"] = synthesize(tools["yosys"], work, "slh-" + name,
            [SLH / "global_include/clog2.v", SLH / (name + ".v")], name,
            parameters="-set WIDTH 8 -set DEPTH " + ("7" if name == "mem_dual" else "8") + " -set INIT 0",
            expected_ff_bits=80 if name == "mem_dual" else 72)
    if before != {str(p.relative_to(ROOT)): sha(p) for p in inputs}:
        raise ValueError("tracked source changed during component checks")
    return {"schema_version": 1, "status": "PASS", "scope": "selected-memory-components-only",
            "whole_design_asic_qualification": "NOT_RUN", "tool_versions": versions,
            "source_sha256": before, "simulations": simulations, "generic_ff_mappings": mappings,
            "limits": ["No standard-cell library mapping, timing, area, power or full-design synthesis.",
                       "No full MLDSA target KAT after ROM substitution; portable qualification is not inherited.",
                       "SLH INIT=0 mappings exclude power-up initialized hash-tile RAMs and FIFO pointers.",
                       "MLDSA RAM/control-state and SLH initialization still block a complete ASIC-ready baseline.",
                       "No HQC source execution or repair."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool-dir", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    (ROOT / ".pqc_runs").mkdir(exist_ok=True)
    work = args.work_dir or Path(tempfile.mkdtemp(prefix="asic-memory-", dir=ROOT / ".pqc_runs"))
    try:
        report = check(work, args.tool_dir)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        report = {"status": "FAIL", "scope": "selected-memory-components-only", "error": str(exc)}
    report["work_dir"] = str(work)
    output = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output)
    print(output, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
