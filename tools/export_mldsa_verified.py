#!/usr/bin/env python3
"""Export a passing ML-DSA derivative without invoking any EDA tool.

The default Verilog export exactly matches the tested RTL/netlist bytes.
Mixed exports retain original VHDL inputs; direct mixed-language equivalence
and FPGA/ASIC synthesis, constraints, libraries, timing and PPA are not claimed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO))
from agent.mldsa_sources import BUNDLED_ROOT, verify_snapshot
from agent.mldsa.portable_kat_gate import hoist_declarations, apply_canonical_hint_guard

VARIANTS = {
    "guarded-baseline": ("baseline_canonical_pass", "guarded_baseline"),
    "corrected-candidate": ("candidate_corrected_pass", "corrected_candidate"),
}
VHDL_ORDER = ["sha3_pkg", "keccak_pkg", "regn", "piso", "sipo", "countern", "sr_reg",
              "keccak_bytepad", "keccak_cons", "keccak_round", "keccak_fsm1", "keccak_fsm2",
              "sha3_fsm3", "keccak_control", "keccak_datapath", "keccak_top"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_report(report, variant):
    expected = {"keygen":25, "sign":15, "verify":15, "verify_mutations":4, "verify_canonical":11}
    name = {"guarded-baseline":"pinned-baseline+canonical-hints",
            "corrected-candidate":"candidate+encoder-fallthrough+canonical-hints"}[variant]
    coverage = report.get("coverage", {})
    if report.get("status") != "PASS" or report.get("variant") != name or set(coverage) != set(expected):
        raise ValueError("qualification report does not identify the complete passing named variant")
    for operation, per_level in expected.items():
        row = coverage[operation]
        vectors = row.get("vectors", [])
        keys = [(v.get("level"),v.get("kat")) for v in vectors]
        want = {(level,index) for level in ("II","III","V") for index in range(per_level)}
        if (row.get("status") != "PASS" or row.get("expected") != len(want)
            or row.get("completed") != len(want) or row.get("simulator_returncode") != 0
            or any(type(row.get(field)) is not int for field in ("expected", "completed", "simulator_returncode"))
            or len(keys) != len(want) or set(keys) != want
            or not all(type(v.get("kat")) is int and type(v.get("cycles")) is int
                       and v["cycles"]>0 for v in vectors)):
            raise ValueError("qualification report has missing, duplicate, failed or reduced coverage: " + operation)
    for operation, counts in {"verify":(9,36), "verify_mutations":(0,12), "verify_canonical":(18,15)}.items():
        row=coverage[operation]
        if ((row.get("known_valid"),row.get("known_invalid"))!=counts
            or any(type(row.get(field)) is not int for field in ("known_valid", "known_invalid"))):
            raise ValueError("qualification report has inconsistent Verify polarity or control coverage")


def export(out, variant="corrected-candidate", source_format="verilog"):
    verify_snapshot()
    out = Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError("output directory must be absent or empty; existing exports are never overwritten")
    if source_format not in ("verilog", "mixed"):
        raise ValueError("unsupported source format")
    label, netname = VARIANTS[variant]
    report_path = REPO / "docs/verification/mldsa-portable-2026-10-12" / label / "result.json"
    report = json.loads(report_path.read_text())
    validate_report(report, variant)
    expected = {Path(path).name: digest for path, digest in report["staged_design_hashes"].items()}
    staged = out / "rtl"; staged.mkdir(parents=True)
    chosen = {p.name:p for p in (BUNDLED_ROOT / "ref_combined/src").iterdir() if p.is_file()}
    if variant == "corrected-candidate":
        overrides = sorted((REPO / "agent/mldsa/mldsa_src").glob("*.v"))
        if len(overrides) != 14:
            raise ValueError("candidate override manifest changed")
        for source in overrides:
            if source.name not in chosen:
                raise ValueError("unknown override: " + source.name)
            chosen[source.name] = source
    for name, path in chosen.items():
        shutil.copy2(path, staged/name)
    top = staged / "combined_top.v"
    top.write_text(hoist_declarations(top.read_text())[0])
    if variant == "corrected-candidate":
        shutil.copy2(REPO / "verification/mldsa_osh/encoder_fallthrough.v", staged / "encoder.v")
    apply_canonical_hint_guard(staged)
    netlist = REPO / "verification/mldsa_osh/generated" / (netname+"_keccak_top.v")
    shutil.copy2(netlist, staged / "keccak_top_ghdl.v")
    actual = {path.name:sha(path) for path in staged.iterdir()}
    if actual != expected:
        changed = sorted(name for name in set(actual)|set(expected) if actual.get(name)!=expected.get(name))
        raise ValueError("export does not match recorded tested source bytes: " + ", ".join(changed))
    # Keep only the selected elaboration graph: never compile both VHDL and
    # generated-Verilog definitions of keccak_top together.
    if source_format == "verilog":
        for path in staged.glob("*.vhd"):
            path.unlink()
        ordered = []
    else:
        (staged / "keccak_top_ghdl.v").unlink()
        ordered = [staged/(name+".vhd") for name in VHDL_ORDER]
    ordered += sorted(path for path in staged.glob("*.v") if path.name != "combined_top.v")
    ordered += [staged/"combined_top.v"]
    shutil.copy2(BUNDLED_ROOT / "common/zetas.txt", out/"zetas.txt")
    (out/"common").mkdir(exist_ok=True)
    shutil.copy2(BUNDLED_ROOT / "common/mldsa_params.v", out/"common/mldsa_params.v")
    (out/"LICENSES").mkdir(exist_ok=True)
    for source, name in [(REPO/"LICENSE", "project-GPL-3.0.txt"),
                         (BUNDLED_ROOT/"LICENSE", "upstream-MIT.txt"),
                         (REPO/"LICENSES/Apache-2.0.txt", "Apache-2.0.txt")]:
        shutil.copy2(source,out/"LICENSES"/name)
    shutil.copy2(REPO/"NOTICE",out/"NOTICE")
    shutil.copy2(BUNDLED_ROOT/"NOTICE",out/"UPSTREAM_NOTICE")
    entries = [{"path":str(path.relative_to(out)), "language":"vhdl2008" if path.suffix==".vhd" else "verilog",
                "sha256":sha(path)} for path in ordered]
    manifest = {
        "variant":variant, "source_format":source_format, "top":"combined_top",
        "parameter_overrides":{}, "defines":[], "sources":entries,
        "clock_ports":["clk"], "reset_ports":["rst"], "constraints_supplied":False,
        "memory_model":"generic RTL/inferred RAM/ROM; no target technology macro substitution",
        "runtime_controls":{"mode":{"0":"KeyGen","1":"Verify","2":"Sign"},
                            "sec_lvl":{"2":"ML-DSA-44","3":"ML-DSA-65","5":"ML-DSA-87"}},
        "data_files":[{"path":"zetas.txt","sha256":sha(out/"zetas.txt"),
                       "note":"$readmemh uses this filename relative to the tool working directory"}],
        "reference_header":{"path":"common/mldsa_params.v","sha256":sha(out/"common/mldsa_params.v"),
                            "note":"testbench parameter definitions; not needed by the design source list"},
        "qualification_report":str(report_path.relative_to(REPO)), "qualification_report_sha256":sha(report_path),
        "tested_cases":210,
        "source_relationship":("Exact RTL and generated VHDL-to-Verilog netlist bytes from the passing simulation"
            if source_format=="verilog" else "Original VHDL source inputs used to generate the passing netlist; direct mixed-language simulation/equivalence has not been run"),
        "limits":["No FPGA/ASIC EDA tools run by export", "No constraints or target library supplied",
                  "No PPA, timing closure, formal equivalence, side-channel or FIPS certification claim",
                  "Run tools from this export root so zetas.txt resolves", "Do not mix original VHDL and generated keccak_top modules"],
    }
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    (out/"sources.f").write_text("\n".join(row["path"] for row in entries)+"\n")
    tcl = ['# Source lists only: this file does not invoke any EDA command.',
           'set mldsa_root [file dirname [file normalize [info script]]]',
           'set mldsa_top combined_top', 'set mldsa_sources [list \\']
    tcl += ['  [file join $mldsa_root '+row['path']+'] \\' for row in entries]
    tcl += [']', 'set mldsa_zetas [file join $mldsa_root zetas.txt]']
    (out/"sources.tcl").write_text("\n".join(tcl)+"\n")
    (out/"README.txt").write_text(
        f"ML-DSA {variant}, {source_format} source export\nTop: combined_top\n"
        "Use manifest.json and sources.f (or source-list-only sources.tcl).\n"
        "Run synthesis/elaboration from this directory for zetas.txt.\n"
        "Both compared arms include canonical-hint validation. The candidate also includes the encoder fallthrough repair.\n"
        +manifest['source_relationship']+".\n"
        "No FPGA/ASIC synthesis, target libraries, timing constraints, PPA, or FIPS certification were provided by this export.\n")
    return {"out":str(out),"variant":variant,"format":source_format,"sources":len(entries),"manifest":str(out/"manifest.json")}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",required=True)
    p.add_argument("--variant",choices=tuple(VARIANTS),default="corrected-candidate")
    p.add_argument("--format",choices=("verilog","mixed"),default="verilog")
    args=p.parse_args()
    print(json.dumps(export(args.out,args.variant,args.format),indent=2))
