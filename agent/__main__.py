"""License-free discovery and smoke checks. Use agent.run for actual EDA work."""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from .mldsa_sources import BUNDLED_ROOT, COMMIT as MLDSA_COMMIT, missing_inputs, source_root, verify_snapshot

ROOT = Path(__file__).resolve().parents[1]


def scheme_catalog():
    """Repository support, not certification or a claim that a licensed run passed."""
    mlkem_root = ROOT / "third_party/adams_bridge"
    mlkem_sources = all((mlkem_root / part).is_file() for part in (
        "upstream/src/abr_top/rtl/abr_top.sv", "upstream/src/abr_top/rtl/abr_mem_top.sv",
        "integration/abr_unified_top.sv", "test_vectors/nist_acvp_mlkem1024.json"))
    mlkem_gate = (ROOT / "tools/run_mlkem_adams_bridge_kat.py").is_file()
    return [
        {"scheme": "ML-KEM", "key": "mlkem",
         "support": "baseline_available_site_qualification_pending" if mlkem_sources else "source_missing",
         "baseline_scope": "unified ML-KEM-1024 / ML-DSA-87 accelerator including memories",
         "source_available": mlkem_sources,
         "upstream_commit": "b77e3d899e828d626cfc2a0d26a6b5704cc121e0",
         "verification": ("Upstream KAT/formal evidence; 80 official FIPS203 ACVP sample cases. "
                          "Pinned baseline passed 80 ACVP cases with Verilator 5.032 on 2026-10-12; licensed PPA remains unrun. Doctor does not reverify current source bytes. "
                          + ("A fail-closed simulation gate is bundled." if mlkem_gate
                             else "The local simulation gate is not present.")),
         "functional_gate": "tools/run_mlkem_adams_bridge_kat.py" if mlkem_gate else None,
         "recorded_baseline_evidence": "docs/verification/mlkem-adams-bridge-acvp-2026-10-12.json",
         "fpga_synthesis_entrypoint": "third_party/adams_bridge/integration/vivado_synth.tcl",
         "asic_config": "configs/mlkem_adams_bridge_asic.example.json",
         "automatic_optimization_dispatch": False},
        {"scheme": "ML-DSA", "key": "mldsa", "support": "baseline_available_site_qualification_pending",
         "verification": "75 bundled KeyGen vectors (25 each at 44/65/87); current RTL simulation unrun. No Sign/Verify or FIPS proof.",
         "source_available": not missing_inputs(source_root()),
         "default_source_root": str(BUNDLED_ROOT), "selected_source_root": str(source_root()),
         "upstream_commit": MLDSA_COMMIT,
         "asic_config": "configs/mldsa_osh_asic.example.json",
         "source_environment": "MLDSA_ROOT", "fpga_designs": ["mldsa", "mldsa_baseline"]},
        {"scheme": "SLH-DSA", "key": "slh_dsa", "support": "partial_differential",
         "verification": "Selected-mode SHA2 frozen vendor-stream differential gate (all six parameter sets); RTL simulation unrun, no independent FIPS 205 oracle. SHAKE unsupported.",
         "fpga_designs": ["slh_dsa"]},
        {"scheme": "HQC", "key": "hqc", "support": "legacy_rtl_consistency",
         "verification": "Legacy 128/192/256 shared-secret consistency; not independent standardized KATs.",
         "fpga_designs": ["hqc", "hqc_baseline"]},
    ]


def doctor():
    bin_dir = os.environ.get("VIVADO_BIN", "")
    path = os.pathsep.join(filter(None, (bin_dir, os.environ.get("PATH", ""))))
    executables = {name: shutil.which(name, path=path) for name in
                   ("vivado", "xvlog", "xvhdl", "xelab", "xsim", "verilator", "iverilog", "vvp", "yosys", "genus", "dc_shell")}
    mldsa = source_root()
    missing = missing_inputs(mldsa)
    catalog = scheme_catalog()
    for row in catalog:
        row["licensed_run_verified"] = False
        blockers = []
        if row["key"] == "mlkem":
            if not row["source_available"]:
                blockers.append("Pinned Adams Bridge RTL, wrapper, or official vectors are missing")
            if not row["functional_gate"]:
                blockers.append("The local fail-closed RTL simulation gate is missing")
            if not executables["verilator"]:
                blockers.append("Verilator is not on PATH; Icarus currently rejects upstream SystemVerilog")
            if not executables["vivado"]:
                blockers.append("Vivado is not on PATH/VIVADO_BIN for FPGA synthesis")
            row["qualification"] = "pending; tool discovery does not run or qualify RTL"
            row["asic_tools_available"] = {name: bool(executables[name]) for name in ("genus", "dc_shell")}
            row["asic_site_setup_required"] = True
        else:
            if not executables["vivado"]:
                blockers.append("Vivado is not on PATH/VIVADO_BIN")
            if row["key"] == "mldsa":
                row["missing_inputs"] = missing
                row["qualification"] = "pending; input integrity is not RTL or licensed-tool qualification"
                for name in ("xvhdl", "xvlog", "xelab", "xsim"):
                    if not executables[name]:
                        blockers.append(name + " is not on PATH/VIVADO_BIN for the mixed-language KeyGen gate")
                if missing:
                    blockers.append("Restore bundled inputs or set MLDSA_ROOT to a complete matching upstream tree")
                if mldsa == BUNDLED_ROOT.resolve():
                    try:
                        row["source_integrity"] = verify_snapshot(mldsa)
                    except (OSError, ValueError, KeyError) as exc:
                        row["source_integrity"] = {"status": "FAIL", "reason": str(exc)}
                        blockers.append("Pinned ML-DSA source integrity failed")
                else:
                    row["source_integrity"] = {"status": "external_override_not_pin_verified"}
            if row["key"] == "slh_dsa":
                from .slh_dsa import slh_kat_gate as slh
                rtl = ROOT / "agent/slh_dsa/slh_src"
                row["qualification"] = "pending; reference/input integrity is not RTL or licensed-tool qualification"
                row["independent_fips_205_validation"] = False
                row["portable_simulator_limit"] = "Unmodified vendor FSM.v has duplicate declarations rejected by Icarus/Verilator"
                for name in ("xvlog", "xelab", "xsim"):
                    if not executables[name]:
                        blockers.append(name + " is not on PATH/VIVADO_BIN for the SHA2 differential gate")
                try:
                    parameter = slh.check_configuration(rtl / "sphincslet/setting.v")
                    row["active_parameters"] = ["PARAM_" + parameter.upper()]
                    row["active_parameter_set"] = "SHA2-" + parameter
                    golden, _ = slh.load_reference(parameter)
                    data_root = Path(os.environ.get("SLH_DATA_ROOT", str(rtl / "imports"))).resolve()
                    slh.check_harness(rtl, parameter, data_root)
                    row["gate_inputs"] = {"status": "verified", "golden": str(golden),
                                          "golden_sha256": slh.REFERENCES[parameter][0],
                                          "signature_words": slh.REFERENCES[parameter][1]}
                except (OSError, ValueError, RuntimeError, KeyError) as exc:
                    row["gate_inputs"] = {"status": "ERROR", "reason": str(exc)}
                    blockers.append("SLH selected configuration/reference/input check failed: " + str(exc))
        row["blockers"] = blockers
        row["availability"] = ("blocked" if blockers else
                               "baseline_available_site_qualification_pending" if row["key"] == "mlkem" else
                               "configured_not_verified")
    return {"audit_status": "completed", "repository": str(ROOT),
            "python": sys.version.split()[0], "executables": executables,
            "optional_dependencies": {name: importlib.util.find_spec(name) is not None for name in ("anthropic", "flask")},
            "paid_llm_enabled": os.environ.get("PQC_ENABLE_LLM") == "1",
            "schemes": catalog,
            "note": "Read-only prerequisite audit; no synthesis, simulation, paid API calls, or remote jobs were launched."}


def smoke():
    from . import edit_ops
    with tempfile.TemporaryDirectory(prefix="pqc-smoke-") as directory:
        root = Path(directory)
        source = root / "candidate.v"
        original = "module candidate;\nreg flag;\nendmodule\n"
        source.write_text(original)
        proposal = {"name": "offline-smoke", "files": [{"path": str(source), "ops": [
            {"op": "replace_exact", "old": "reg flag;", "new": "reg flag2;", "expect": 1}]}]}
        allowed = [source]
        preview = edit_ops.preview_experiment(proposal, allowed_paths=allowed)
        if source.read_text() != original or "reg flag2;" not in preview[str(source)][1]:
            raise RuntimeError("read-only preview failed")
        backups = edit_ops.apply_experiment(proposal, allowed_paths=allowed, backup_dir=root / "backups")
        if "reg flag2;" not in source.read_text():
            raise RuntimeError("edit was not applied")
        edit_ops.revert(backups)
        if source.read_text() != original:
            raise RuntimeError("rollback changed original bytes")
        proposal["files"][0]["ops"][0]["expect"] = 2
        try:
            edit_ops.apply_experiment(proposal, allowed_paths=allowed, backup_dir=root / "backups")
        except edit_ops.EditError:
            pass
        else:
            raise RuntimeError("corrupted proposal was not rejected")
        if source.read_text() != original:
            raise RuntimeError("refused proposal modified source")
    return {"status": "PASS", "checks": ["preview", "apply", "rollback", "reject_wrong_count"],
            "scope": "Python harness only; no cryptographic or EDA result was measured."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("doctor", "list", "smoke"):
        command = commands.add_parser(name)
        command.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "list":
        result = scheme_catalog()
    elif args.command == "doctor":
        result = doctor()
    else:
        result = smoke()
    if args.json or args.command != "list":
        print(json.dumps(result, indent=2))
    else:
        for row in result:
            print(f"{row['scheme']}: {row['support']}\n  {row['verification']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
