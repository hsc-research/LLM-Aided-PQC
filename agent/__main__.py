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

ROOT = Path(__file__).resolve().parents[1]


def scheme_catalog():
    """Repository support, not certification or a claim that a licensed run passed."""
    return [
        {"scheme": "ML-KEM", "key": "mlkem", "support": "not_implemented",
         "verification": "No ML-KEM RTL, test vectors, or registered flow is bundled."},
        {"scheme": "ML-DSA", "key": "mldsa", "support": "partial_external_sources",
         "verification": "Key-generation vectors and selected block differential checks; not all operations.",
         "source_environment": "MLDSA_ROOT", "fpga_designs": ["mldsa", "mldsa_baseline"]},
        {"scheme": "SLH-DSA", "key": "slh_dsa", "support": "partial_differential",
         "verification": "SHA2-128f frozen-signature differential gate only; check active setting.v mode.",
         "fpga_designs": ["slh_dsa"]},
        {"scheme": "HQC", "key": "hqc", "support": "legacy_rtl_consistency",
         "verification": "Legacy 128/192/256 shared-secret consistency; not independent standardized KATs.",
         "fpga_designs": ["hqc", "hqc_baseline"]},
    ]


def doctor():
    bin_dir = os.environ.get("VIVADO_BIN", "")
    path = os.pathsep.join(filter(None, (bin_dir, os.environ.get("PATH", ""))))
    executables = {name: shutil.which(name, path=path) for name in
                   ("vivado", "xvlog", "xvhdl", "xelab", "xsim", "iverilog", "vvp", "yosys", "genus", "dc_shell")}
    mldsa = Path(os.environ["MLDSA_ROOT"]).expanduser() if os.environ.get("MLDSA_ROOT") else None
    required = ("ref_combined/src", "ref_combined/src_tb/tb_keygen_top.v", "common", "KAT")
    missing = [str(mldsa / part) for part in required if not (mldsa / part).exists()] if mldsa else list(required)
    catalog = scheme_catalog()
    for row in catalog:
        row["licensed_run_verified"] = False
        blockers = []
        if row["key"] == "mlkem":
            blockers.append("Implementation and verification flow are absent")
        else:
            if not executables["vivado"]:
                blockers.append("Vivado is not on PATH/VIVADO_BIN")
            if row["key"] == "mldsa" and missing:
                blockers.append("Set MLDSA_ROOT to the complete external upstream tree")
            if row["key"] == "slh_dsa":
                setting = ROOT / "agent/slh_dsa/slh_src/sphincslet/setting.v"
                text = setting.read_text() if setting.is_file() else ""
                import re
                text = re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)
                modes = re.findall(r"^\s*`define\s+(PARAM_(?:128|192|256)[FS])\b", text, re.M)
                row["active_parameters"] = modes
                if modes != ["PARAM_128F"] or re.search(r"^\s*`define\s+SHAKE\b", text, re.M):
                    blockers.append("Current RTL mode is not the gate's supported PARAM_128F")
        row["blockers"] = blockers
        row["availability"] = "blocked" if blockers else "configured_not_verified"
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
