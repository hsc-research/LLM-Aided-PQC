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
FPGA_LATCH_VARIANTS = ("fpga-latch-corrected-baseline", "fpga-latch-corrected-candidate")
ASIC_STARTUP_VARIANTS = ("asic-startup-baseline", "asic-startup-candidate")
DESIGNS = {
    "mlkem": ("baseline",),
    "mldsa": ("guarded-baseline", "corrected-candidate", *ASIC_STARTUP_VARIANTS, *FPGA_LATCH_VARIANTS),
    "slh": ("corrected-baseline", "corrected-candidate", *ASIC_STARTUP_VARIANTS),
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


def validate_mldsa_startup(variant, deployment, original, report, full):
    """Require fresh full-operation evidence bound to this exact boot derivative."""
    from tools.export_mldsa_verified import validate_report
    source_variant = {"asic-startup-baseline": "guarded-baseline",
                      "asic-startup-candidate": "corrected-candidate"}[variant]
    row = report.get("variants", {}).get(variant, {})
    functional = row.get("functional", {})
    if not (deployment.get("variant") == variant and deployment.get("source_variant") == source_variant
            and deployment.get("top") == "combined_top_asic" and deployment.get("defines") == []
            and deployment.get("parameter_overrides") == {} and deployment.get("include_dirs") == []
            and report.get("status") == "PASS" and row.get("status") == "PASS"
            and row.get("source_variant") == source_variant and row.get("top") == deployment["top"]
            and row.get("sources") == deployment.get("sources")
            and original.get("sources") == [{k: r[k] for k in ("path", "sha256")} for r in row["sources"]]
            and original.get("source_variant") == source_variant and original.get("top") == deployment["top"]
            and row.get("source_manifest_sha256") == deployment.get("immutable_source_manifest", {}).get("sha256")
            and row.get("full_kat_report_sha256") == deployment.get("full_kat_report", {}).get("sha256")
            and row.get("full_kat_report") == deployment["full_kat_report"].get("path")
            and full.get("status") == "PASS" and full.get("full_210_case_coverage") is True
            and full.get("source_hashes_unchanged") is True and full.get("collision_assertions") is True
            and full.get("variant") == source_variant + "+explicit-asic-startup"
            and full.get("design_manifest_sha256") == row["source_manifest_sha256"]
            and type(full.get("boot_restarts_per_process")) is int and full["boot_restarts_per_process"] == 2
            and functional.get("status") == "PASS" and functional.get("compile_status") == "PASS"
            and functional.get("exact_source_bound") is True
            and type(functional.get("completed_cases")) is int and functional["completed_cases"] == 630):
        raise ValueError("ML-DSA startup evidence is incomplete, stale or belongs to another derivative")
    source_rows = deployment["sources"]
    paths = [r["path"] for r in source_rows]
    if (len(paths) != 36 or len(set(paths)) != len(paths) or paths != sorted(paths)
            or any(r.get("language") != "verilog2005" for r in source_rows)):
        raise ValueError("ML-DSA startup source order/language differs from the frozen derivative")
    # Original absolute paths are provenance labels, never paths opened here.
    recorded = [("rtl/" + Path(p).name, h) for p, h in full.get("source_hashes", {}).items()
                if Path(p).parent.name == "rtl"]
    if len(recorded) != len(paths) or dict(recorded) != {r["path"]: r["sha256"] for r in source_rows}:
        raise ValueError("ML-DSA startup full report is not bound to the exact derivative sources")
    cases = ("keygen", "sign", "verify", "verify_mutations", "verify_canonical")
    seeds = ("0", "11", "29")
    if (set(functional.get("settings", {})) != set(seeds)
            or set(full.get("coverage", {})) != {c + ":seed-" + s for c in cases for s in seeds}):
        raise ValueError("ML-DSA startup evidence has missing or unexpected test settings")
    evidence_name = {"guarded-baseline": "pinned-baseline+canonical-hints",
                     "corrected-candidate": "candidate+encoder-fallthrough+canonical-hints"}[source_variant]
    for seed in seeds:
        setting = functional["settings"][seed]
        validate_report({"status": setting.get("status"), "variant": evidence_name,
                         "coverage": setting.get("coverage", {})}, source_variant)
        for case in cases:
            observed = full["coverage"][case + ":seed-" + seed]
            qualified = setting["coverage"][case]
            restart = qualified.get("restart_evidence", {})
            if (any(qualified.get(k) != v for k, v in observed.items())
                    or type(observed.get("seed")) is not int or observed["seed"] != int(seed)
                    or restart.get("observed_aborts") != 2 or restart.get("marker_count") != 1
                    or restart.get("marker_precedes_completed_kats") is not True
                    or qualified.get("postboot_cycle_counts_match_reference") is not True):
                raise ValueError("ML-DSA startup coverage or reboot evidence differs from full report")
    short = variant.removeprefix("asic-startup-")
    expected_logs = {"runs/release-" + short + "/" + c + "/simulate-seed-" + seed + ".log"
                     for c in cases for seed in seeds}
    expected_logs |= {"runs/release-" + short + "/" + c + "/compile.log" for c in cases}
    expected_logs.add("mapping/release-" + short + "-ff.log")
    if set(row.get("logs", {})) != expected_logs:
        raise ValueError("ML-DSA startup evidence lacks the exact complete simulation/compile/mapping logs")
    structural = row.get("structural", {})
    if not (structural == deployment.get("generic_ff_structural_qualification")
            and structural.get("status") == "PASS"
            and structural.get("production_ram_banks") == {"4096x96": 1, "1024x96": 6}
            and structural.get("production_storage_bits") == 983040
            and structural.get("production_ram_output_ff_bits") == 1344
            and structural.get("production_ram_total_ff_bits") == 984384
            and all(type(structural.get(k)) is int and structural[k] == 0 for k in
                    ("remaining_memory_cells", "remaining_latch_cells", "powerup_init_attributes", "tristate_cells", "blackboxes"))
            and structural.get("standard_cell_mapped") is False
            and structural.get("mapped_netlist_functional_equivalence") is False
            and report.get("standard_cell_qualification") is False
            and report.get("physical_timing_ppa_qualification") is False
            and report.get("fullcore_fourstate_qualification") is False
            and deployment.get("standard_cell_library_qualification") is False
            and deployment.get("physical_ppa_qualification") is False):
        raise ValueError("ML-DSA startup generic structural evidence is missing or overclaims target qualification")
    components = report.get("components", {})
    if (set(components) != {"ram", "shell", "hint_read", "knownness_negative_control"}
            or not report.get("component_report", {}).get("path")
            or not re.fullmatch(r"[0-9a-f]{64}", report.get("component_report", {}).get("sha256", ""))):
        raise ValueError("ML-DSA startup component evidence is incomplete")
    for name in ("ram", "shell", "hint_read"):
        c = components[name]
        if not (c.get("status") == "PASS" and c.get("input_hashes_unchanged") is True
                and type(c.get("compile_returncode")) is int and c["compile_returncode"] == 0
                and type(c.get("simulate_returncode")) is int and c["simulate_returncode"] == 0
                and type(c.get("observed_marker_count")) is int and c["observed_marker_count"] == 1):
            raise ValueError("ML-DSA startup component evidence failed: " + name)
    if components["knownness_negative_control"].get("status") != "EXPECTED_FAILURE":
        raise ValueError("ML-DSA startup negative knownness evidence is missing")
    startup = row.get("startup", {})
    if not (startup.get("status") == "PASS" and startup.get("observed_boot_aborts") == 30
            and startup.get("abort_markers_before_first_completed_kat") is True
            and startup.get("source_contract") == original.get("contract")):
        raise ValueError("ML-DSA startup contract is not bound to passing reboot evidence")


def qualified_mldsa_startup(variant, bundle):
    """Copy frozen derivative sources and portable fresh evidence; never execute RTL."""
    from agent.mldsa.portable_kat_gate import evaluate_log
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from tools.check_mldsa_startup_kats import check_restart_evidence
    source_variant = {"asic-startup-baseline": "guarded-baseline",
                      "asic-startup-candidate": "corrected-candidate"}[variant]
    source = ROOT / "asic/rtl/mldsa_startup" / source_variant
    deployment_path = source / "deployment.json"
    deployment_bytes = deployment_path.read_bytes()
    manifest = json.loads(deployment_bytes)
    original_path = checked_path(source, manifest["immutable_source_manifest"]["path"])
    report_path = checked_path(ROOT, manifest["qualification_report"]["path"])
    full_path = checked_path(ROOT, manifest["full_kat_report"]["path"])
    for path, record in ((original_path, manifest["immutable_source_manifest"]),
                         (report_path, manifest["qualification_report"]),
                         (full_path, manifest["full_kat_report"])):
        if sha(path) != record["sha256"]:
            raise ValueError("ML-DSA startup source/evidence hash mismatch: " + str(path))
    original, report, full = [json.loads(p.read_text()) for p in (original_path, report_path, full_path)]
    validate_mldsa_startup(variant, manifest, original, report, full)
    rows = manifest["sources"]
    if {str(p.relative_to(source)) for p in (source / "rtl").rglob("*") if p.is_file()} != {r["path"] for r in rows}:
        raise ValueError("ML-DSA startup tree has missing or unbound source files")
    bundle.mkdir()
    copied = []
    def copy_bound(src, dest, expected=None):
        expected = expected or sha(src)
        if sha(src) != expected:
            raise ValueError("ML-DSA startup source/evidence changed: " + str(src))
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        if sha(dest) != expected or sha(src) != expected:
            raise ValueError("ML-DSA startup source/evidence changed while copying: " + str(src))
        copied.append((src, expected))
    for row in rows:
        copy_bound(checked_path(source, row["path"]), bundle / row["path"], row["sha256"])
    copy_bound(original_path, bundle / "startup-source-manifest.json", manifest["immutable_source_manifest"]["sha256"])
    copy_bound(deployment_path, bundle / "startup-deployment.json", hashlib.sha256(deployment_bytes).hexdigest())
    copy_bound(full_path, bundle / "evidence/full-kat.json", manifest["full_kat_report"]["sha256"])
    copy_bound(report_path, bundle / "evidence/qualification.json", manifest["qualification_report"]["sha256"])
    record = report["variants"][variant]
    short = variant.removeprefix("asic-startup-")
    for name, digest in record["logs"].items():
        prefix = "runs/release-" + short + "/"
        if name.startswith(prefix):
            relative = name.removeprefix(prefix)
        elif name == "mapping/release-" + short + "-ff.log":
            relative = "generic-ff-synthesis.log"
        else:
            raise ValueError("unknown ML-DSA startup log binding: " + name)
        src = checked_path(full_path.parent, relative)
        copy_bound(src, checked_path(bundle, "evidence/" + relative), digest)
        if relative.startswith(("keygen/", "sign/", "verify/", "verify_mutations/", "verify_canonical/")) and "/simulate-seed-" in relative:
            case, filename = relative.split("/")
            seed = filename.removeprefix("simulate-seed-").removesuffix(".log")
            coverage = record["functional"]["settings"][seed]["coverage"][case]
            operation = "verify" if case.startswith("verify") else case
            count = {"keygen": 25, "sign": 15, "verify": 15, "verify_mutations": 4, "verify_canonical": 11}[case]
            text = src.read_text()
            parsed = evaluate_log(text, operation, count, coverage["simulator_returncode"])
            restart = check_restart_evidence(text)
            if (parsed["status"] != "PASS" or parsed["vectors"] != coverage["vectors"]
                    or restart != coverage["restart_evidence"]):
                raise ValueError("ML-DSA startup live log does not match completed KAT/reboot evidence")
        elif relative == "generic-ff-synthesis.log":
            text = src.read_text()
            if len(re.findall(r"Found and reported 0 problems\.", text)) != 2 or re.search(r"^ERROR:", text, re.MULTILINE):
                raise ValueError("ML-DSA startup structural log lacks both passing checks")
    component_row = report["component_report"]
    component_path = checked_path(ROOT, component_row["path"])
    copy_bound(component_path, bundle / "evidence/components/result.json", component_row["sha256"])
    component = json.loads(component_path.read_text())
    if not (component.get("status") == "PASS" and set(component.get("checks", {})) == {"ram", "shell", "hint_read"}
            and component.get("design_manifest_sha256") == report["variants"]["asic-startup-baseline"]["source_manifest_sha256"]):
        raise ValueError("ML-DSA startup component evidence is missing or stale")
    for name, row in component["checks"].items():
        if not (row == report.get("components", {}).get(name) and row.get("status") == "PASS"
                and type(row.get("compile_returncode")) is int and row["compile_returncode"] == 0
                and type(row.get("simulate_returncode")) is int and row["simulate_returncode"] == 0
                and type(row.get("observed_marker_count")) is int and row["observed_marker_count"] == 1
                and row.get("input_hashes_unchanged") is True):
            raise ValueError("ML-DSA startup component check did not pass: " + name)
        copy_bound(component_path.parent / (name + "-simulate.log"),
                   bundle / "evidence/components" / (name + "-simulate.log"), row["simulate_log_sha256"])
    negative = report.get("components", {}).get("knownness_negative_control", {})
    fault = report_path.parent / "diagnostics/trials/hint-unknown-fault.log"
    copy_bound(fault, bundle / "evidence/components/knownness-negative.log", negative["log_sha256"])
    if (negative.get("status") != "EXPECTED_FAILURE" or "unknown observable output" not in fault.read_text()
            or "ASIC_HINT_READ_VIEW_PASS" in fault.read_text()):
        raise ValueError("ML-DSA startup knownness negative control did not fail as intended")
    for name in ("LICENSES", "NOTICE", "UPSTREAM_NOTICE"):
        item = source / name
        if item.is_dir():
            for path in sorted(item.rglob("*")):
                if path.is_file():
                    copy_bound(path, bundle / path.relative_to(source))
        else:
            copy_bound(item, bundle / name)
    manifest["data_files"] = []
    manifest["immutable_source_manifest"]["path"] = "startup-source-manifest.json"
    manifest["qualification_report"] = {"path": "evidence/qualification.json",
                                        "repository_path": str(report_path.relative_to(ROOT)), "sha256": sha(report_path)}
    manifest["component_qualification_report"] = {"path": "evidence/components/result.json", "sha256": component_row["sha256"]}
    manifest["full_kat_report"] = {"path": "evidence/full-kat.json", "sha256": sha(full_path)}
    write_json(bundle / "manifest.json", manifest)
    if any(sha(p) != h for p, h in copied):
        raise ValueError("ML-DSA startup input changed during export")
    return manifest, report_path


def source_export(design, variant, parameter, bundle):
    if variant in FPGA_LATCH_VARIANTS:
        from tools.export_mldsa_fpga_latch_corrected import export
        manifest = export(bundle, variant)
        return manifest, ROOT / manifest["qualification_report"]
    if variant in ASIC_STARTUP_VARIANTS:
        if design == "mldsa":
            return qualified_mldsa_startup(variant, bundle)
        sys.path.insert(0, str(ROOT / "tools"))
        from tools.export_slh_asic_verified import export_sources
        manifest = export_sources(variant.replace("asic-startup-", "asic-boot-"), parameter, bundle)
        return manifest, ROOT / manifest["qualification_report"]["repository_path"]
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


def startup_boundary(design, manifest):
    boundary = profile_boundary(design)
    boundary["reset_ports"] += ["boot_rst" if design == "mldsa" else "i_boot_reset"]
    boundary["ready_ports"] = ["boot_ready" if design == "mldsa" else "o_boot_ready"]
    boundary["startup_contract"] = manifest["startup_contract"]
    boundary["memories"] = manifest["memories"]
    boundary["constants"] = manifest["constants"]
    boundary["source_metadata_directory"] = "source-bundle"
    if "memory_instances" in manifest:
        boundary["memory_instances"] = manifest["memory_instances"]
    if "generic_ff_lowering" in manifest:
        boundary["generic_ff_lowering"] = manifest["generic_ff_lowering"]
    boundary["notes"] = ([
        "Runtime mode and sec_lvl retained; no specialization.",
        "Explicit boot reset and serial RAM scrub replace FPGA power-up initialization.",
        "Ordinary rst preserves storage; asserting boot_rst discards stored context.",
        "Same-address simultaneous dual writes remain outside the qualified contract.",
        "Constant zetas and Keccak tables are synthesizable logic; no runtime file load.",
        "Exact generated Keccak Verilog is retained; original VHDL must not also be compiled.",
    ] if design == "mldsa" else [
        "The external signature store is excluded and must be supplied identically in both arms.",
        "setting.v fixes widths and SHA cores; never override parameter_set alone.",
        "INIT=1 mem_dual scrubs all DEPTH+1 words; INIT=0 storage and FIFO data are not zeroed.",
        "Ordinary rstn does not rerun boot or clear FIFO pointers/storage.",
        "Write/read latency is preserved; out-of-range reads and simultaneous same-address dual writes remain undefined.",
        "Control-history/bypass lowering is qualified only for the stated synchronous, settled-cycle contract.",
        "Repeated boot while inactive is covered; active-operation boot abort/recovery is unqualified.",
    ])
    return boundary


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
    if variant in FPGA_LATCH_VARIANTS and target != "fpga":
        raise ValueError("FPGA latch-corrected variants require target fpga; use ASIC startup variants for ASIC")
    startup = variant in ASIC_STARTUP_VARIANTS
    if startup and target != "asic":
        raise ValueError("ASIC startup variants require target asic; original FPGA exports are separate")
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
        report_bytes = report_path.read_bytes()
        report_digest = hashlib.sha256(report_bytes).hexdigest()
        if startup and manifest["qualification_report"]["sha256"] != report_digest:
            raise ValueError("startup qualification report changed after source validation")
        evidence = work / "evidence"
        evidence.mkdir()
        (evidence / "source-qualification.json").write_bytes(report_bytes)
        sources = [dict(row, path="source-bundle/" + row["path"],
                        language="verilog" if row["language"] in ("Verilog-2005", "verilog2005") else row["language"])
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
            "boundary": startup_boundary(design, manifest) if startup else profile_boundary(design),
            "compatibility_blockers": (["Generic clock-gate technology mapping and complete mapped-netlist checks remain pending."] if design == "mlkem" else
                                       ["RAM initial contents have no reset/scrub implementation in the current top.",
                                        "Control-state initializers require a target-specific reset/startup audit and full functional requalification."]) if target == "asic" else
                                      ["Selected FPGA part/tool elaboration, memory inference and collision/init semantics remain unqualified."],
            "qualification": {"report": {"path": "evidence/source-qualification.json", "sha256": report_digest},
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
        if startup:
            profile["compatibility_blockers"] = [
                "Licensed DC/Genus elaboration, standard-cell FF/logic mapping and constraints remain unqualified.",
                "Mapped-netlist startup, memory latency/collision behavior and implementation equivalence require separate qualification.",
                "Finite RTL tests do not prove arbitrary reset/abort sequences, all input behaviors or cryptographic certification.",
            ]
            if design == "slh":
                profile["compatibility_blockers"].append(
                    "Historical sign/verify vendor fixtures are not independent full-algorithm FIPS 205 qualification.")
                profile["compatibility_blockers"].append("Active-operation boot abort/recovery remains unqualified.")
            profile["qualification"].update(
                whole_algorithm_qualified=False,
                startup_rtl_tested=True, secure_zeroization_qualified=False,
                evidence_scope=("Fresh explicit-startup full-operation finite RTL tests; not certification"
                                if design == "mldsa" else
                                "Fresh explicit-startup historical vendor sign/verify differential; not independent FIPS validation"))
            generic_report = (profile["qualification"]["report"] if design == "mldsa" else
                              dict(manifest["structural_report"], path="source-bundle/" + manifest["structural_report"]["path"]))
            profile["qualification"]["generic_ff_evidence"] = {
                "report": generic_report, "scope": "generic FF/logic structural lowering only",
                "standard_cell_mapping_qualified": False, "mapped_netlist_equivalence_qualified": False}
            profile["provenance"]["source_derivative"] = manifest["variant"]
            profile["limitations"][0] = (
                "Explicit startup RTL derivative with fresh finite functional evidence; licensed target compatibility remains unqualified.")
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
    if profile["variant"] in ASIC_STARTUP_VARIANTS and target["kind"] != "asic":
        raise ValueError("ASIC startup variant cannot be relabeled as an FPGA profile")
    if profile["variant"] in FPGA_LATCH_VARIANTS and target["kind"] != "fpga":
        raise ValueError("FPGA latch-corrected variant cannot be relabeled as an ASIC profile")
    expected_memory = "flops" if target["kind"] == "asic" else "fpga_inferred_ram"
    if target.get("memory_implementation") != expected_memory:
        raise ValueError("target and memory policy disagree")
    hashes = profile["bundle_files_sha256"]
    for name, digest in hashes.items():
        item = checked_path(root, name)
        if not item.is_file() or sha(item) != digest:
            raise ValueError("bundle source/evidence hash mismatch: " + name)
    elab = profile["elaboration"]
    extra_evidence = ([profile["qualification"]["generic_ff_evidence"]["report"]]
                      if "generic_ff_evidence" in profile["qualification"] else [])
    for row in [*elab["sources"], *elab["include_files"], *elab["data_files"], profile["qualification"]["report"],
                profile["provenance"]["export_manifest"], *extra_evidence]:
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
    if tool == "vivado":
        if sys.version_info < (3, 10):
            raise ValueError("Vivado preparation requires Python 3.10 or newer")
        # Vivado can prepend its bundled Python to PATH. Retain the interpreter
        # used to prepare this run (including a virtual-environment path).
        python_executable = Path(sys.executable).absolute()
        if not python_executable.is_file():
            raise ValueError("preparation Python executable is unavailable")
        config["verification_python"] = {
            "executable": str(python_executable),
            "version": list(sys.version_info[:3]),
            "sha256": sha(python_executable),
        }
    out = empty_destination(out)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "launch-config.json", config)
    if tool == "vivado":
        script = ["# Source-only launcher. Generated but never run by preparation.", "if {[catch {",
                  "exec " + tcl_word(python_executable) + " -I " + tcl_word(root / "verify_profile.py") + " --verify-preparation " + tcl_word(out / "preparation.json"),
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
        bound_inputs += [out / "launch_vivado.tcl", python_executable, root / "verify_profile.py"]
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
