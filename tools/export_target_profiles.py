#!/usr/bin/env python3
"""Freeze qualified source exports for explicit FPGA/ASIC preparation, without EDA.

Source qualification is not target qualification. In particular, these profiles
do not establish BRAM inference, ASIC startup semantics, FF mapping, or PPA.
HQC has no admitted source profile here and is never imported or executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DESIGNS = {
    "mlkem": ("baseline",),
    "mldsa": ("guarded-baseline", "corrected-candidate"),
    "slh": ("corrected-baseline", "corrected-candidate"),
}
HDL_SUFFIXES = {".v", ".vh", ".sv", ".svh", ".vhd", ".vhdl"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def fingerprint(profile):
    return hashlib.sha256(canonical({k: v for k, v in profile.items() if k != "profile_fingerprint"})).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def checked_path(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError("profile paths must be relative and remain within the bundle")
    path = root / name
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("profile path escapes bundle or is a symlink: " + name)
    return path


def empty_destination(out):
    out = Path(out).resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("destination must be absent or empty; never overwrite a prior run")
    return out


def qualified_mlkem(bundle):
    # Importing the local runner only reads its definitions; do not execute RTL.
    from tools.run_mlkem_adams_bridge_kat import source_inputs, VENDOR, RTL_COMMIT, EXPECTED_COUNTS
    inputs = source_inputs(VENDOR)
    report_path = ROOT / "docs/verification/mlkem-adams-bridge-acvp-2026-10-12.json"
    report = json.loads(report_path.read_text())
    if not (report.get("status") == "PASS" and report.get("rtl_kat_passed") is True
            and report.get("pinned_sources_unchanged") is True and report.get("upstream_commit") == RTL_COMMIT
            and type(report.get("cases_passed")) is int and report["cases_passed"] == 80
            and type(report.get("checks_passed")) is int and report["checks_passed"] == 39840
            and report.get("operation_counts") == EXPECTED_COUNTS
            and type(report.get("compile_returncode")) is int and report["compile_returncode"] == 0
            and type(report.get("simulate_returncode")) is int and report["simulate_returncode"] == 0):
        raise ValueError("ML-KEM report lacks the complete pinned passing qualification")
    for name in ("upstream/SOURCE_MANIFEST.json", "integration/manifest.json", "integration/abr_unified_top.sv",
                 "test_vectors/nist_acvp_mlkem1024.json"):
        if report.get("sha256", {}).get(name) != inputs[name]:
            raise ValueError("ML-KEM qualification source binding mismatch: " + name)
    for name, digest in inputs.items():
        if not name.startswith(("upstream/", "integration/")):
            continue
        dest = bundle / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(VENDOR / name, dest)
        if sha(dest) != digest:
            raise ValueError("ML-KEM source changed during export")
    for name in ("README.md",):
        shutil.copyfile(VENDOR / name, bundle / name)
    for name in ("LICENSE", "NOTICE"):
        shutil.copyfile(ROOT / name, bundle / ("PROJECT_" + name))
    manifest = json.loads((bundle / "integration/manifest.json").read_text())
    manifest["sources"] = [dict(row, sha256=sha(bundle / row["path"])) for row in manifest["files"]]
    manifest["parameter_overrides"] = {}
    manifest["data_files"] = []
    write_json(bundle / "manifest.json", manifest)
    return manifest, report_path


def source_export(design, variant, parameter, bundle):
    if design == "mlkem":
        bundle.mkdir()
        return qualified_mlkem(bundle)
    if design == "mldsa":
        from tools.export_mldsa_verified import export
        export(bundle, variant, "verilog")
        manifest = json.loads((bundle / "manifest.json").read_text())
        return manifest, ROOT / manifest["qualification_report"]
    # The existing SLH exporter is a script with script-local imports.
    sys.path.insert(0, str(ROOT / "tools"))
    from tools.export_slh_verified import export_sources
    manifest = export_sources(variant, parameter, bundle)
    return manifest, ROOT / manifest["qualification_report"]["repository_path"]


def profile_boundary(design):
    if design == "mlkem":
        return {
            "scope": "full_unified_mlkem1024_mldsa87_with_memories",
            "external_memories": [], "clock_ports": ["clk"], "reset_ports": ["rst_b"],
            "notes": ["Whole abr_unified_top including all ten abr_mem_top instances; not ML-KEM-only area.",
                      "ML-DSA-87 functionality in the shared core is not qualified.",
                      "abr_ram_regout zeroization/full-array outputs require register implementation; not every memory is BRAM eligible.",
                      "Generic latch-based clock gating requires technology-specific review."],
        }
    if design == "mldsa":
        return {
            "scope": "full_mldsa_44_65_87_runtime_selection_with_internal_memories",
            "external_memories": [], "clock_ports": ["clk"], "reset_ports": ["rst"],
            "notes": ["Runtime mode and sec_lvl retained; no specialization.",
                      "dual_port_ram uses initial zero/readmemh without a memory reset port. ASIC startup equivalence is unqualified.",
                      "Two RAM write processes and read-during-write/collision semantics need target elaboration review.",
                      "dual_port_rom requests distributed ROM; BRAM allocation is not established.",
                      "Exact GHDL-generated Keccak Verilog is retained; original VHDL must not also be compiled."],
        }
    return {
        "scope": "slh_top_with_internal_memories_external_signature_store_excluded",
        "external_memories": [{"name": "signature_store", "included": False,
                               "interface": ["sig_mem_out0", "sig_mem_addr0_w"],
                               "requirement": "Supply and account for the same store in both arms before whole-system PPA admission."}],
        "clock_ports": ["clk"], "reset_ports": ["rstn"],
        "notes": ["Testbench SIG_MEM is not part of top or the design source list.",
                  "setting.v fixes widths and selected SHA cores; never override parameter_set alone.",
                  "mem_dual retains DEPTH+1 entries, write-through outputs and unspecified simultaneous same-address dual writes.",
                  "mem_single preserves its final old-data read assignment.",
                  "Initial zero/file contents have no memory reset port; ASIC startup equivalence is unqualified."],
    }


def site_template(profile):
    target = profile["target"]["kind"]
    common = {"schema_version": 1, "profile_fingerprint": profile["profile_fingerprint"],
              "target": target, "period_ns": None, "constraints": "REPLACE_ME_REVIEWED_XDC" if target == "fpga" else "REPLACE_ME_REVIEWED_SDC",
              "tool_version": "REPLACE_ME_EXACT_INSTALLED_VERSION", "output_root": "REPLACE_ME_FRESH_RUN_DIRECTORY"}
    if target == "fpga":
        return dict(common, tool="vivado", part="REPLACE_ME_EXACT_PART_AND_SPEEDGRADE")
    return dict(common, tool="genus", target_libraries=["REPLACE_ME_STDCELL_LIBRARY.lib"],
                link_libraries=[], time_unit="REPLACE_ME_ps_ns_us", corner="REPLACE_ME_PROCESS_VOLTAGE_TEMPERATURE",
                setup_tcl="REPLACE_ME_REVIEWED_SITE_TCL", admission_adapter=None,
                note="Use tool=dc and compiled .db libraries for DC. Only standard-cell libraries; no memory compiler/macros.")


def export_profile(design, variant, parameter_set, target, out):
    if design not in DESIGNS or variant not in DESIGNS[design]:
        raise ValueError("unsupported design/variant; HQC has no qualified export")
    if target not in ("fpga", "asic"):
        raise ValueError("target must be fpga or asic")
    allowed = ("128f", "192f") if design == "slh" else (None, "1024") if design == "mlkem" else (None, "44-65-87")
    if parameter_set not in allowed:
        raise ValueError("select a supported exact parameter set (SLH requires 128f or 192f)")
    parameter_set = parameter_set or ("1024" if design == "mlkem" else "44-65-87")
    out = empty_destination(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".target-profile-", dir=out.parent) as temporary:
        work = Path(temporary) / "profile"
        work.mkdir()
        bundle = work / "source-bundle"
        manifest, report_path = source_export(design, variant, parameter_set, bundle)
        evidence = work / "evidence"
        evidence.mkdir()
        shutil.copyfile(report_path, evidence / "source-qualification.json")
        sources = [dict(row, path="source-bundle/" + row["path"],
                        language="verilog" if row["language"] == "Verilog-2005" else row["language"])
                   for row in manifest["sources"]]
        includes = ["source-bundle/" + name for name in manifest.get("include_dirs", [])]
        # Freeze all possible HDL include inputs, even those already in the ordered file list.
        include_files = {str(p.relative_to(work)): sha(p) for name in includes
                         for p in (work / name).rglob("*") if p.is_file() and p.suffix in HDL_SUFFIXES}
        defines = (manifest["fpga_synthesis_defines"] if target == "fpga" else manifest["generic_synthesis_defines"]) if design == "mlkem" else manifest["defines"]
        # SLH's data_files are test fixtures, not production memory initialization.
        data = manifest.get("data_files", []) if design == "mldsa" else []
        data = [dict(row, path="source-bundle/" + row["path"]) for row in data]
        required = ["mlkem_keygen", "mlkem_encaps", "mlkem_decaps", "mldsa_keygen", "mldsa_sign", "mldsa_verify"] if design == "mlkem" else ["keygen", "sign", "verify"]
        observed = ["mlkem_keygen", "mlkem_encaps", "mlkem_decaps"] if design == "mlkem" else required if design == "mldsa" else ["sign", "verify"]
        profile = {
            "schema_version": 1, "profile_kind": "qualified_source_target_preparation",
            "design": design, "variant": variant, "parameter_set": parameter_set,
            "target": {"kind": target, "memory_implementation": "fpga_inferred_ram" if target == "fpga" else "flops",
                       "technology_mapping_verified": False, "memory_macros": [], "memory_compiler_allowed": False},
            "elaboration": {"top": manifest["top"], "sources": sources, "include_dirs": includes,
                            "include_files": [{"path": name, "sha256": digest} for name, digest in sorted(include_files.items())],
                            "defines": defines, "parameters": manifest.get("parameter_overrides", {}),
                            "language_standard": "systemverilog2017" if design == "mlkem" else "verilog2005",
                            "compilation_unit": "single_ordered_compilation_unit_with_persistent_preprocessor_state",
                            "global_include_files": ["source-bundle/rtl/imports/global_include/clog2.v", "source-bundle/rtl/sphincslet/setting.v"] if design == "slh" else [],
                            "data_files": data, "working_directory": "source-bundle"},
            "boundary": profile_boundary(design),
            "compatibility_blockers": (["Generic clock-gate technology mapping and complete mapped-netlist checks remain pending."] if design == "mlkem" else
                                       ["RAM initial contents have no reset/scrub implementation in the current top.",
                                        "Control-state initializers require a target-specific reset/startup audit and full functional requalification."]) if target == "asic" else
                                      ["Selected FPGA part/tool elaboration, memory inference and collision/init semantics remain unqualified."],
            "qualification": {"report": {"path": "evidence/source-qualification.json", "sha256": sha(report_path)},
                              "source_qualified": True, "target_define_equivalence_qualified": False,
                              "target_tool_qualified": False, "whole_algorithm_qualified": design == "mldsa",
                              "required_operations": required,
                              "observed_operations": observed,
                              "required_operations_meaning": "Future strict optimization admission requirements; not a claim of completed target qualification.",
                              "evidence_scope": "Historical vendor stream differential, not independent FIPS validation" if design == "slh" else "Recorded sampled RTL simulation; not certification"},
            "provenance": {"export_manifest": {"path": "source-bundle/manifest.json", "sha256": sha(bundle / "manifest.json")},
                           "qualification_repository_path": str(report_path.relative_to(ROOT)),
                           "source_bytes_modified_by_target_preparation": False,
                           "exporter_sha256": sha(Path(__file__))},
            "limitations": ["This is source-only target preparation, not an ASIC RTL port completion or FPGA/ASIC compatibility certificate.",
                            "No EDA tool, license, cloud API, download or upstream executable is invoked by export or prepare.",
                            "Target defines, memory initialization/collisions, elaboration and post-mapping equivalence require separate qualification.",
                            "ASIC intent is generic register/logic mapping only, with no memory compiler or RAM/ROM macro substitution.",
                            "Flop mapping, blackbox absence, initialization semantics and constraints must be proven by mapped tool evidence.",
                            "No PPA, timing closure, power, side-channel, certification or whole-system claim."],
        }
        profile["bundle_files_sha256"] = {str(p.relative_to(work)): sha(p) for p in sorted(work.rglob("*")) if p.is_file()}
        profile["profile_fingerprint"] = fingerprint(profile)
        write_json(work / "profile.json", profile)
        write_json(work / ("site." + target + ".example.json"), site_template(profile))
        (work / "sources.f").write_text("".join(row["path"] + "\n" for row in sources))
        (work / "include_dirs.f").write_text("".join("+incdir+" + path + "\n" for path in includes))
        tcl = ["# Source-list data only; invokes no EDA command.",
               "set pqc_root [file dirname [file normalize [info script]]]",
               "set pqc_top " + tcl_word(manifest["top"]),
               "set pqc_defines " + tcl_list(defines),
               "set pqc_sources [list " + " ".join("[file join $pqc_root " + tcl_word(row["path"]) + "]" for row in sources) + "]",
               "set pqc_include_dirs [list " + " ".join("[file join $pqc_root " + tcl_word(path) + "]" for path in includes) + "]"]
        (work / "sources.tcl").write_text("\n".join(tcl) + "\n")
        # Copy this stdlib-only entry point: --verify/--prepare work outside the repository.
        shutil.copyfile(Path(__file__), work / "verify_profile.py")
        (work / "README.txt").write_text(
            f"{design} {variant} {parameter_set}: {target} source preparation only.\n"
            "python3 verify_profile.py --verify profile.json\n"
            f"Copy site.{target}.example.json to site.local.json and fill every site value.\n"
            "python3 verify_profile.py --prepare --profile profile.json --site site.local.json --out NEW_LAUNCH_DIR\n"
            "Preparation never launches an EDA process. Read profile.json boundary, qualification and limitations.\n"
            "Preserve source/profile hashes; any RTL changes require their own functional qualification.\n")
        verify_profile(work / "profile.json")
        if out.exists():
            out.rmdir()
        work.rename(out)
    return profile


def verify_profile(path):
    path = Path(path).resolve()
    root = path.parent
    profile = json.loads(path.read_text())
    if profile.get("schema_version") != 1 or profile.get("profile_kind") != "qualified_source_target_preparation":
        raise ValueError("unsupported target profile schema")
    if profile.get("profile_fingerprint") != fingerprint(profile):
        raise ValueError("profile fingerprint mismatch")
    if profile.get("design") not in DESIGNS or profile.get("variant") not in DESIGNS[profile["design"]]:
        raise ValueError("unqualified design or variant")
    target = profile.get("target", {})
    if target.get("kind") not in ("fpga", "asic") or target.get("memory_macros") != [] or target.get("memory_compiler_allowed") is not False:
        raise ValueError("invalid target/memory policy")
    expected_memory = "flops" if target["kind"] == "asic" else "fpga_inferred_ram"
    if target.get("memory_implementation") != expected_memory:
        raise ValueError("target and memory policy disagree")
    hashes = profile["bundle_files_sha256"]
    for name, digest in hashes.items():
        item = checked_path(root, name)
        if not item.is_file() or sha(item) != digest:
            raise ValueError("bundle source/evidence hash mismatch: " + name)
    elab = profile["elaboration"]
    for row in [*elab["sources"], *elab["include_files"], *elab["data_files"], profile["qualification"]["report"], profile["provenance"]["export_manifest"]]:
        if hashes.get(row["path"]) != row["sha256"]:
            raise ValueError("elaboration/evidence binding differs from bundle: " + row["path"])
    if not elab["sources"] or len({row["path"] for row in elab["sources"]}) != len(elab["sources"]):
        raise ValueError("empty or duplicate source order")
    for name in elab["include_dirs"]:
        directory = checked_path(root, name)
        if not directory.is_dir():
            raise ValueError("missing include directory")
        if any(str(p.relative_to(root)) not in hashes for p in directory.rglob("*") if p.is_file() and p.suffix in HDL_SUFFIXES):
            raise ValueError("unbound HDL file added to include directory")
    return profile


def require_text(value, label):
    if not isinstance(value, str) or not value.strip() or any(token in value for token in ("REPLACE_ME", "${", "<", ">", "\n", "\r")):
        raise ValueError("missing or unresolved site value: " + label)
    return value


def site_path(value, label, parent):
    path = Path(require_text(value, label)).expanduser()
    path = path if path.is_absolute() else parent / path
    path = path.resolve()
    if not path.is_file():
        raise ValueError("site file does not exist: " + label)
    return str(path)


def tcl_word(value):
    text = str(value)
    for old, new in (("\\", "\\\\"), ('"', '\\"'), ("$", "\\$"), ("[", "\\["), ("]", "\\]"), ("\n", "\\n"), ("\r", "\\r")):
        text = text.replace(old, new)
    return '"' + text + '"'


def tcl_list(values):
    return "[list " + " ".join(tcl_word(v) for v in values) + "]"


def prepare(profile_path, site_path_arg, out):
    profile_path = Path(profile_path).resolve()
    profile = verify_profile(profile_path)
    root = profile_path.parent
    site_file = Path(site_path_arg).resolve()
    site = json.loads(site_file.read_text())
    if site.get("profile_fingerprint") != profile["profile_fingerprint"] or site.get("target") != profile["target"]["kind"]:
        raise ValueError("site configuration is not bound to this profile and target")
    period = site.get("period_ns")
    if type(period) not in (int, float) or not math.isfinite(period) or period <= 0:
        raise ValueError("site period_ns must be finite and positive")
    version = require_text(site.get("tool_version"), "tool_version")
    constraints = site_path(site.get("constraints"), "constraints", site_file.parent)
    output_root = require_text(site.get("output_root"), "output_root")
    output_root = str((site_file.parent / output_root).resolve())
    if Path(output_root).exists():
        raise ValueError("site output_root must be a fresh path")
    elab = profile["elaboration"]
    files = [dict(row, path=str(root / row["path"])) for row in elab["sources"]]
    config = {"schema_version": 1, "root": str(root), "top": elab["top"], "scope": "full_design",
              "design_boundary": profile["boundary"],
              "period_ns": period, "files": files, "include_dirs": [str(root / p) for p in elab["include_dirs"]],
              "defines": elab["defines"], "parameters": elab["parameters"], "compilation_unit": elab["compilation_unit"],
              "language_standard": elab["language_standard"],
              "data_files": [str(root / p["path"]) for p in elab["data_files"]],
              "output_root": output_root, "target_profile": str(profile_path), "profile_fingerprint": profile["profile_fingerprint"]}
    tool = site.get("tool")
    if profile["target"]["kind"] == "asic":
        if tool not in ("genus", "dc"):
            raise ValueError("ASIC preparation requires genus or dc")
        libraries = [site_path(p, "target_libraries", site_file.parent) for p in site.get("target_libraries", [])]
        if not libraries or (tool == "dc" and any(not p.endswith(".db") for p in libraries)):
            raise ValueError("supply standard-cell target libraries; DC requires compiled .db")
        unit = site.get("time_unit")
        if unit not in ("ps", "ns", "us"):
            raise ValueError("supply actual library time_unit")
        spec = {"executable": "genus" if tool == "genus" else "dc_shell", "version": version, "time_unit": unit,
                "corner": require_text(site.get("corner"), "corner"), "target_libraries": libraries,
                "link_libraries": [site_path(p, "link_libraries", site_file.parent) for p in site.get("link_libraries", [])],
                "setup_tcl": site_path(site.get("setup_tcl"), "setup_tcl", site_file.parent),
                "power_activity": "unspecified; no power admission"}
        adapter = site.get("admission_adapter")
        if adapter is not None:
            spec["admission_adapter"] = {"tcl": site_path(adapter.get("tcl"), "admission_adapter.tcl", site_file.parent),
                "qualification": site_path(adapter.get("qualification"), "admission_adapter.qualification", site_file.parent),
                "inputs": [site_path(p, "admission_adapter.inputs", site_file.parent) for p in adapter.get("inputs", [])]}
        config.update(synthesis_tool=tool, sdc=constraints, memory_model="flops", tools={tool: spec},
                      admission={"policy": "strict-rtl-flops-v1", "waivers": []})
    else:
        if tool != "vivado":
            raise ValueError("FPGA preparation requires vivado")
        part = require_text(site.get("part"), "part")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", part):
            raise ValueError("invalid FPGA part string")
        config.update(tool="vivado", part=part, xdc=constraints, tool_version=version)
    out = empty_destination(out)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "launch-config.json", config)
    if tool == "vivado":
        script = ["# Source-only launcher. Generated but never run by preparation.", "if {[catch {",
                  "exec python3 " + tcl_word(root / "verify_profile.py") + " --verify-preparation " + tcl_word(out / "preparation.json"),
                  "if {[version -short] ne " + tcl_word(version) + '} {error "Vivado version differs from frozen site config"}',
                  "set run_dir " + tcl_word(output_root), 'if {[file exists $run_dir]} {error "Use a fresh run directory"}',
                  "file mkdir $run_dir", "cd $run_dir", "create_project -in_memory -part " + tcl_word(config["part"]),
                  "set_property include_dirs " + tcl_list(config["include_dirs"]) + " [current_fileset]",
                  "set_property verilog_define " + tcl_list(config["defines"]) + " [current_fileset]"]
        for data in config["data_files"]:
            script.append("file copy " + tcl_word(data) + " " + tcl_word(Path(data).name))
        flag = " -sv" if all(row["language"] == "systemverilog" for row in files) else ""
        script.append("read_verilog" + flag + " " + tcl_list(row["path"] for row in files))
        for header in elab["global_include_files"]:
            script.append("set_property is_global_include true [get_files " + tcl_word(root / header) + "]")
        script += ["read_xdc " + tcl_word(constraints), "synth_design -top " + tcl_word(elab["top"]) + " -part " + tcl_word(config["part"]) + " -mode out_of_context -gated_clock_conversion off",
                   "set primary_clocks [get_clocks -of_objects [get_ports " + tcl_word(profile["boundary"]["clock_ports"][0]) + "]]",
                   'if {[llength $primary_clocks] != 1 || [llength [get_clocks]] != 1} {error "Expected one constrained primary clock"}',
                   "if {abs([get_property PERIOD $primary_clocks] - " + str(period) + ') > 1.0e-9} {error "Constraint clock period differs from site config"}',
                   'if {[llength [get_cells -hierarchical -filter {IS_BLACKBOX == 1}]] != 0} {error "Unresolved/blackbox cells"}',
                   "report_utilization -hierarchical -file utilization.rpt", "report_timing_summary -file timing.rpt",
                   "check_timing -verbose -file check_timing.rpt", "report_drc -file drc.rpt",
                   "write_checkpoint synthesized.dcp", '} message]} {puts stderr $message; exit 1}', "exit 0"]
        (out / "launch_vivado.tcl").write_text("\n".join(script) + "\n")
    bound_inputs = [site_file, Path(constraints), out / "launch-config.json"]
    if tool != "vivado":
        bound_inputs += [Path(p) for p in spec["target_libraries"] + spec["link_libraries"] + [spec["setup_tcl"]]]
        if adapter is not None:
            bound_inputs += [Path(p) for p in spec["admission_adapter"]["inputs"] + [spec["admission_adapter"]["tcl"], spec["admission_adapter"]["qualification"]]]
    else:
        bound_inputs.append(out / "launch_vivado.tcl")
    write_json(out / "preparation.json", {"schema_version": 1, "status": "SOURCE_PREPARED_NOT_RUN",
               "profile": str(profile_path), "profile_fingerprint": profile["profile_fingerprint"],
               "input_sha256": {str(p): sha(p) for p in bound_inputs},
               "target_tool_qualified": False, "memory_mapping_proven": False})
    (out / "README.txt").write_text("Prepared only. No EDA process ran.\n" + (
        "From the repository: python3 -m agent.run --target asic --synth-tool " + tool + " --config " + str(out / "launch-config.json") + " --dry-run\n"
        "A licensed run additionally needs a qualified site admission adapter. Mapped FF proof and startup equivalence remain required.\n" if tool != "vivado" else
        "After site review: vivado -mode batch -source " + str(out / "launch_vivado.tcl") + "\nNo BRAM inference or PPA admission is inferred from a successful launch.\n"))
    return {"status": "SOURCE_PREPARED_NOT_RUN", "out": str(out), "tool": tool}


def verify_preparation(path):
    record = json.loads(Path(path).read_text())
    if record.get("schema_version") != 1 or record.get("status") != "SOURCE_PREPARED_NOT_RUN":
        raise ValueError("unsupported preparation record")
    profile = verify_profile(record["profile"])
    if record["profile_fingerprint"] != profile["profile_fingerprint"]:
        raise ValueError("prepared profile binding mismatch")
    for name, digest in record["input_sha256"].items():
        if sha(name) != digest:
            raise ValueError("prepared site/config/script changed: " + name)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", choices=tuple(DESIGNS))
    parser.add_argument("--variant")
    parser.add_argument("--parameter-set")
    parser.add_argument("--target", choices=("fpga", "asic"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--verify-preparation", type=Path)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--site", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    try:
        if args.verify_preparation:
            record = verify_preparation(args.verify_preparation)
            result = {"status": "PREPARATION_INPUTS_VERIFIED_NOT_RUN", "profile_fingerprint": record["profile_fingerprint"]}
        elif args.verify:
            profile = verify_profile(args.verify)
            result = {"status": "SOURCE_PROFILE_VERIFIED", "profile_fingerprint": profile["profile_fingerprint"], "target_tool_qualified": False}
        elif args.prepare:
            if not all((args.profile, args.site, args.out)):
                parser.error("--prepare requires --profile, --site and --out")
            result = prepare(args.profile, args.site, args.out)
        else:
            if not all((args.design, args.variant, args.target, args.out)):
                parser.error("export requires --design, --variant, --target and --out")
            profile = export_profile(args.design, args.variant, args.parameter_set, args.target, args.out)
            result = {"status": "SOURCE_EXPORTED_TARGET_UNQUALIFIED", "profile": str(args.out / "profile.json"),
                      "profile_fingerprint": profile["profile_fingerprint"], "source_count": len(profile["elaboration"]["sources"])}
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("Target profile ERROR: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
