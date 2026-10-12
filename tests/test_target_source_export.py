"""Offline exact-source target preparation checks; no licensed EDA process."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.export_target_profiles import export_profile, verify_profile, prepare, verify_preparation, fingerprint, ASIC_STARTUP_VARIANTS, validate_mldsa_startup
from tools.check_target_profile_elaboration import check


class TargetSourceExportTests(unittest.TestCase):
    def export(self, root, design="mldsa", target="asic", variant=None, parameter=None):
        variant = variant or {"mlkem": "baseline", "mldsa": "guarded-baseline", "slh": "corrected-baseline"}[design]
        path = Path(root) / "profile"
        value = export_profile(design, variant, parameter, target, path)
        return path, value

    def site(self, path, profile, root):
        root = Path(root)
        extension = ".xdc" if profile["target"]["kind"] == "fpga" else ".sdc"
        constraints = root / ("reviewed" + extension)
        constraints.write_text("# TEST FIXTURE, NOT ACTUAL TARGET CONSTRAINTS\n")
        (root / "site.tcl").write_text("# TEST FIXTURE\n")
        (root / "stdcells.lib").write_text('library(test) { time_unit : "1ns"; }\n')
        value = json.loads((path / ("site." + profile["target"]["kind"] + ".example.json")).read_text())
        value.update(period_ns=10, constraints=str(constraints), tool_version="TEST_ONLY_VERSION", output_root=str(root / "new-run"))
        if value["target"] == "fpga":
            value.update(part="TEST_ONLY_PART")
        else:
            value.update(target_libraries=[str(root / "stdcells.lib")], time_unit="ns", corner="TEST_ONLY_CORNER", setup_tcl=str(root / "site.tcl"))
        site = root / "site.json"
        site.write_text(json.dumps(value))
        return site, value

    def test_all_fourteen_profiles_preserve_exact_sources_and_target_intent(self):
        combinations = [("mlkem", "baseline", None)]
        combinations += [("mldsa", v, None) for v in ("guarded-baseline", "corrected-candidate")]
        combinations += [("slh", v, p) for v in ("corrected-baseline", "corrected-candidate") for p in ("128f", "192f")]
        for design, variant, parameter in combinations:
            with self.subTest(design=design, variant=variant, parameter=parameter), tempfile.TemporaryDirectory() as folder:
                profiles = []
                for target in ("fpga", "asic"):
                    out = Path(folder) / target
                    p = export_profile(design, variant, parameter, target, out)
                    self.assertEqual(verify_profile(out / "profile.json"), p)
                    self.assertEqual(len(p["elaboration"]["sources"]), {"mlkem": 175, "mldsa": 35, "slh": 29}[design])
                    self.assertFalse(p["target"]["technology_mapping_verified"])
                    self.assertFalse(p["qualification"]["target_tool_qualified"])
                    self.assertFalse(p["provenance"]["source_bytes_modified_by_target_preparation"])
                    self.assertEqual(p["target"]["memory_macros"], [])
                    self.assertTrue(p["compatibility_blockers"])
                    self.assertEqual(p["elaboration"]["parameters"], {})
                    self.assertEqual(p["profile_fingerprint"], fingerprint(p))
                    profiles.append(p)
                self.assertEqual(profiles[0]["elaboration"]["sources"], profiles[1]["elaboration"]["sources"])
                self.assertNotEqual(profiles[0]["profile_fingerprint"], profiles[1]["profile_fingerprint"])
                if design == "mlkem":
                    self.assertEqual(profiles[0]["elaboration"]["defines"], ["SYNTHESIS", "RV_FPGA_OPTIMIZE"])
                    self.assertEqual(profiles[1]["elaboration"]["defines"], ["SYNTHESIS"])
                    self.assertEqual(profiles[1]["qualification"]["required_operations"], ["mlkem_keygen", "mlkem_encaps", "mlkem_decaps", "mldsa_keygen", "mldsa_sign", "mldsa_verify"])
                    self.assertEqual(profiles[1]["qualification"]["observed_operations"], ["mlkem_keygen", "mlkem_encaps", "mlkem_decaps"])
                if design == "slh":
                    self.assertFalse(profiles[0]["boundary"]["external_memories"][0]["included"])
                    self.assertEqual(profiles[0]["qualification"]["observed_operations"], ["sign", "verify"])

    def test_startup_profiles_bind_new_evidence_and_explicit_boot_contract(self):
        combinations = [("mldsa", v, None) for v in ASIC_STARTUP_VARIANTS]
        combinations += [("slh", v, p) for v in ASIC_STARTUP_VARIANTS for p in ("128f", "192f")]
        for design, variant, parameter in combinations:
            with self.subTest(design=design, variant=variant, parameter=parameter), tempfile.TemporaryDirectory() as root:
                out = Path(root) / "startup"
                p = export_profile(design, variant, parameter, "asic", out)
                self.assertEqual(verify_profile(out / "profile.json"), p)
                self.assertEqual(p["elaboration"]["top"], "combined_top_asic" if design == "mldsa" else "top")
                self.assertEqual(p["elaboration"]["language_standard"], "verilog2005")
                self.assertEqual(p["elaboration"]["parameters"], {})
                self.assertTrue(all(r["language"] == "verilog" for r in p["elaboration"]["sources"]))
                self.assertIn("boot_rst" if design == "mldsa" else "i_boot_reset", p["boundary"]["reset_ports"])
                self.assertEqual(p["boundary"]["ready_ports"], ["boot_ready" if design == "mldsa" else "o_boot_ready"])
                self.assertTrue(p["boundary"]["startup_contract"])
                self.assertTrue(p["boundary"]["memories"])
                self.assertTrue(p["boundary"]["constants"])
                self.assertEqual(p["elaboration"]["data_files"], [])
                self.assertTrue(p["qualification"]["startup_rtl_tested"])
                self.assertFalse(p["qualification"]["secure_zeroization_qualified"])
                self.assertTrue(p["qualification"]["source_qualified"])
                self.assertFalse(p["qualification"]["whole_algorithm_qualified"])
                self.assertFalse(p["qualification"]["target_tool_qualified"])
                self.assertFalse(p["qualification"]["generic_ff_evidence"]["standard_cell_mapping_qualified"])
                self.assertFalse(p["qualification"]["generic_ff_evidence"]["mapped_netlist_equivalence_qualified"])
                generic = p["qualification"]["generic_ff_evidence"]["report"]
                self.assertEqual(p["bundle_files_sha256"][generic["path"]], generic["sha256"])
                self.assertFalse(p["qualification"]["target_define_equivalence_qualified"])
                self.assertFalse(p["target"]["technology_mapping_verified"])
                self.assertEqual(p["target"]["memory_implementation"], "flops")
                self.assertIn("asic", p["provenance"]["qualification_repository_path"])
                if design == "mldsa":
                    manifest = json.loads((out / "source-bundle/manifest.json").read_text())
                    for key in ("immutable_source_manifest", "qualification_report", "full_kat_report", "component_qualification_report"):
                        row = manifest[key]
                        self.assertEqual(p["bundle_files_sha256"]["source-bundle/" + row["path"]], row["sha256"])
                self.assertNotIn("RAM initial contents have no reset/scrub", str(p["compatibility_blockers"]))
                # Export is an exact source copy/declared transform, not a target-time RTL edit.
                self.assertFalse(p["provenance"]["source_bytes_modified_by_target_preparation"])

    def test_startup_pair_has_identical_boot_and_memory_overhead(self):
        for design, parameter in (("mldsa", None), ("slh", "128f"), ("slh", "192f")):
            with self.subTest(design=design, parameter=parameter), tempfile.TemporaryDirectory() as root:
                pairs = [export_profile(design, v, parameter, "asic", Path(root) / v) for v in ASIC_STARTUP_VARIANTS]
                for field in ("startup_contract", "memories", "constants", "reset_ports", "ready_ports"):
                    self.assertEqual(pairs[0]["boundary"][field], pairs[1]["boundary"][field])
                sources = [{r["path"]: r["sha256"] for r in p["elaboration"]["sources"]} for p in pairs]
                if design == "slh":
                    changed = {n for n in sources[0] if sources[0][n] != sources[1][n]}
                    self.assertEqual(changed, {"source-bundle/rtl/sphincslet/sha/sha256_core.v", "source-bundle/rtl/sphincslet/sha/sha512_core.v"})
                else:
                    for name in ("combined_top_asic.v", "mldsa_sameclock_ff_ram.v", "dual_port_rom.v"):
                        self.assertEqual(sources[0]["source-bundle/rtl/" + name], sources[1]["source-bundle/rtl/" + name])

    def test_mldsa_startup_rejects_reduced_stale_or_predecessor_evidence(self):
        root = Path(__file__).resolve().parents[1]
        source = root / "asic/rtl/mldsa_startup/guarded-baseline"
        deployment = json.loads((source / "deployment.json").read_text())
        original = json.loads((source / "manifest.json").read_text())
        report = json.loads((root / deployment["qualification_report"]["path"]).read_text())
        full = json.loads((root / deployment["full_kat_report"]["path"]).read_text())
        variant = "asic-startup-baseline"
        validate_mldsa_startup(variant, deployment, original, report, full)
        for change in ("predecessor", "source", "missing_seed", "missing_case", "duplicate_vector", "reboot", "full_report", "logs", "structural", "components"):
            with self.subTest(change=change):
                r, f = copy.deepcopy(report), copy.deepcopy(full)
                if change == "predecessor":
                    r = json.loads((root / "docs/verification/mldsa-portable-2026-10-12/baseline_canonical_pass/result.json").read_text())
                elif change == "source":
                    name = next(p for p in f["source_hashes"] if "/rtl/" in p)
                    f["source_hashes"][name] = "0" * 64
                elif change == "missing_seed":
                    del r["variants"][variant]["functional"]["settings"]["29"]
                elif change == "missing_case":
                    del f["coverage"]["sign:seed-11"]
                elif change == "duplicate_vector":
                    v = r["variants"][variant]["functional"]["settings"]["0"]["coverage"]["keygen"]["vectors"]
                    v[-1] = dict(v[0])
                elif change == "reboot":
                    r["variants"][variant]["functional"]["settings"]["0"]["coverage"]["keygen"]["restart_evidence"]["marker_precedes_completed_kats"] = False
                elif change == "logs":
                    r["variants"][variant]["logs"] = {}
                elif change == "structural":
                    r["variants"][variant]["structural"]["remaining_latch_cells"] = 1
                elif change == "components":
                    r["components"] = {}
                else:
                    f["design_manifest_sha256"] = "0" * 64
                with self.assertRaises(ValueError):
                    validate_mldsa_startup(variant, deployment, original, r, f)

    def test_mldsa_startup_export_uses_portable_inputs_and_rejects_missing_or_changed_files(self):
        root = Path(__file__).resolve().parents[1]
        source_name = "asic/rtl/mldsa_startup/guarded-baseline"
        report_name = "docs/verification/mldsa-asic-startup-2026-10-12"
        for change in (None, "missing", "stale", "source", "log"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                relocated = Path(folder) / "relocated"
                shutil.copytree(root / source_name, relocated / source_name)
                shutil.copytree(root / report_name / "baseline", relocated / report_name / "baseline")
                shutil.copytree(root / report_name / "components", relocated / report_name / "components")
                shutil.copytree(root / report_name / "diagnostics/trials", relocated / report_name / "diagnostics/trials")
                shutil.copyfile(root / report_name / "result.json", relocated / report_name / "result.json")
                if change == "missing":
                    (relocated / report_name / "result.json").unlink()
                elif change is not None:
                    item = (relocated / source_name / "rtl/combined_top_asic.v" if change == "source" else
                            relocated / report_name / "baseline/keygen/simulate-seed-0.log" if change == "log" else
                            relocated / report_name / "result.json")
                    item.write_bytes(item.read_bytes() + b"\n")
                with patch("tools.export_target_profiles.ROOT", relocated):
                    out = Path(folder) / "export"
                    if change is None:
                        p = export_profile("mldsa", "asic-startup-baseline", None, "asic", out)
                        self.assertEqual(verify_profile(out / "profile.json"), p)
                    else:
                        with self.assertRaises((ValueError, OSError)):
                            export_profile("mldsa", "asic-startup-baseline", None, "asic", out)
                        self.assertFalse(out.exists())

    def test_mldsa_startup_live_log_rejects_late_restart_marker(self):
        root = Path(__file__).resolve().parents[1]
        name = root / "docs/verification/mldsa-asic-startup-2026-10-12/baseline/keygen/simulate-seed-0.log"
        original = Path.read_text
        def read(path, *args, **kwargs):
            value = original(path, *args, **kwargs)
            if path == name:
                value = value.replace("ASIC_RESTARTS_PASS count=2\n", "") + "\nASIC_RESTARTS_PASS count=2\n"
            return value
        # Keep the bytes/hash intact, then corrupt only the parser's log view to
        # ensure ordering is rederived rather than trusted from summary flags.
        with tempfile.TemporaryDirectory() as folder, patch.object(Path, "read_text", read):
            with self.assertRaisesRegex(ValueError, "KAT completed before"):
                export_profile("mldsa", "asic-startup-baseline", None, "asic", Path(folder) / "profile")

    def test_startup_variants_reject_fpga_before_export(self):
        with tempfile.TemporaryDirectory() as root:
            for design, parameter in (("mldsa", None), ("slh", "128f"), ("slh", "192f")):
                for variant in ASIC_STARTUP_VARIANTS:
                    with self.subTest(design=design, variant=variant, parameter=parameter):
                        with self.assertRaisesRegex(ValueError, "require target asic"):
                            export_profile(design, variant, parameter, "fpga", Path(root) / "forbidden")
                        self.assertFalse((Path(root) / "forbidden").exists())

    def test_startup_profiles_are_deterministic_relocatable_and_nonoverwriting(self):
        for design, parameter in (("mldsa", None), ("slh", "128f"), ("slh", "192f")):
            with self.subTest(design=design, parameter=parameter), tempfile.TemporaryDirectory() as root:
                outs = [Path(root) / n for n in ("a", "b")]
                for out in outs:
                    export_profile(design, "asic-startup-candidate", parameter, "asic", out)
                snapshots = [{str(p.relative_to(out)): p.read_bytes() for p in out.rglob("*") if p.is_file()} for out in outs]
                self.assertEqual(*snapshots)
                with self.assertRaisesRegex(ValueError, "never overwrite"):
                    export_profile(design, "asic-startup-candidate", parameter, "asic", outs[0])
                moved = Path(root) / "moved"
                outs[0].rename(moved)
                proc = subprocess.run([sys.executable, "-I", str(moved / "verify_profile.py"), "--verify", str(moved / "profile.json")],
                                      cwd="/tmp", text=True, capture_output=True, timeout=30)
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_startup_manifest_report_and_source_tampering_fail_closed(self):
        for design, parameter in (("mldsa", None), ("slh", "128f"), ("slh", "192f")):
            for kind in ("source", "report", "manifest"):
                with self.subTest(design=design, kind=kind), tempfile.TemporaryDirectory() as root:
                    path, p = self.export(root, design=design, variant="asic-startup-baseline", parameter=parameter)
                    row = (p["elaboration"]["sources"][0] if kind == "source" else
                           p["qualification"]["report"] if kind == "report" else p["provenance"]["export_manifest"])
                    item = path / row["path"]
                    item.write_bytes(item.read_bytes() + b"\n")
                    with self.assertRaisesRegex(ValueError, "hash mismatch"):
                        verify_profile(path / "profile.json")

    def test_startup_preparation_preserves_boot_boundary_and_stays_unqualified(self):
        for design, parameter in (("mldsa", None), ("slh", "128f"), ("slh", "192f")):
            with self.subTest(design=design), tempfile.TemporaryDirectory() as root:
                path, p = self.export(root, design=design, variant="asic-startup-baseline", parameter=parameter)
                site, _ = self.site(path, p, root)
                out = Path(root) / "prepared"
                result = prepare(path / "profile.json", site, out)
                cfg = json.loads((out / "launch-config.json").read_text())
                self.assertEqual(result["status"], "SOURCE_PREPARED_NOT_RUN")
                self.assertEqual(cfg["design_boundary"], p["boundary"])
                self.assertEqual(cfg["memory_model"], "flops")
                self.assertEqual(cfg["admission"], {"policy": "strict-rtl-flops-v1", "waivers": []})
                self.assertEqual(cfg["data_files"], [])
                self.assertEqual(cfg["language_standard"], "verilog2005")
                self.assertFalse(verify_preparation(out / "preparation.json")["target_tool_qualified"])

    def test_exact_profile_export_is_deterministic_and_nonoverwriting(self):
        with tempfile.TemporaryDirectory() as root:
            paths = [Path(root) / name for name in ("a", "b")]
            for out in paths:
                export_profile("mldsa", "corrected-candidate", None, "asic", out)
            snapshots = [{str(p.relative_to(out)): p.read_bytes() for p in out.rglob("*") if p.is_file()} for out in paths]
            self.assertEqual(*snapshots)
            with self.assertRaisesRegex(ValueError, "never overwrite"):
                export_profile("mldsa", "corrected-candidate", None, "asic", paths[0])

    def test_unqualified_hqc_mlkem_candidate_and_cross_mode_fail_before_export(self):
        with tempfile.TemporaryDirectory() as root:
            for design, variant, parameter in (("hqc", "baseline", None), ("mlkem", "candidate", None),
                                              ("slh", "corrected-baseline", None), ("slh", "corrected-baseline", "256f")):
                with self.subTest(design=design, variant=variant, parameter=parameter), self.assertRaises(ValueError):
                    export_profile(design, variant, parameter, "asic", Path(root) / "out")
            self.assertFalse((Path(root) / "out").exists())

    def test_tamper_source_report_and_order_fail_closed(self):
        for kind in ("source", "report", "order"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as root:
                path, p = self.export(root)
                if kind == "order":
                    p["elaboration"]["sources"].reverse()
                    (path / "profile.json").write_text(json.dumps(p))
                else:
                    row = p["elaboration"]["sources"][0] if kind == "source" else p["qualification"]["report"]
                    item = path / row["path"]
                    item.write_bytes(item.read_bytes() + b"\n")
                with self.assertRaises(ValueError):
                    verify_profile(path / "profile.json")

    def test_added_include_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            path, p = self.export(root, design="slh", parameter="128f")
            (path / p["elaboration"]["include_dirs"][0] / "unexpected.vh").write_text("// extra\n")
            with self.assertRaisesRegex(ValueError, "unbound HDL"):
                verify_profile(path / "profile.json")

    def test_placeholders_cross_target_and_nonfinite_periods_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            path, p = self.export(root)
            with self.assertRaisesRegex(ValueError, "period_ns"):
                prepare(path / "profile.json", path / "site.asic.example.json", Path(root) / "bad")
            site, value = self.site(path, p, root)
            for change in ({"target": "fpga"}, {"profile_fingerprint": "0" * 64}, {"period_ns": True}, {"period_ns": float("nan")}, {"corner": "REPLACE_ME"}):
                bad = dict(value, **change)
                site.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):
                    prepare(path / "profile.json", site, Path(root) / "bad")
            self.assertFalse((Path(root) / "bad").exists())

    def test_asic_preparation_is_strict_flops_and_hash_bound_without_adapter(self):
        with tempfile.TemporaryDirectory() as root:
            path, p = self.export(root)
            site, value = self.site(path, p, root)
            output = Path(root) / "prepared"
            result = prepare(path / "profile.json", site, output)
            self.assertEqual(result["status"], "SOURCE_PREPARED_NOT_RUN")
            cfg = json.loads((output / "launch-config.json").read_text())
            self.assertEqual(cfg["memory_model"], "flops")
            self.assertEqual(cfg["admission"], {"policy": "strict-rtl-flops-v1", "waivers": []})
            self.assertNotIn("admission_adapter", cfg["tools"]["genus"])
            self.assertEqual(cfg["compilation_unit"], p["elaboration"]["compilation_unit"])
            self.assertEqual(cfg["language_standard"], "verilog2005")
            self.assertEqual(cfg["scope"], "full_design")
            self.assertEqual(len(cfg["files"]), 35)
            verify_preparation(output / "preparation.json")
            Path(value["constraints"]).write_text("# altered\n")
            with self.assertRaisesRegex(ValueError, "changed"):
                verify_preparation(output / "preparation.json")

    def test_fpga_preparation_preserves_file_order_and_uses_no_fake_part(self):
        with tempfile.TemporaryDirectory() as root:
            path, p = self.export(root, design="slh", target="fpga", parameter="192f")
            site, value = self.site(path, p, root)
            output = Path(root) / "prepared"
            prepare(path / "profile.json", site, output)
            script = (output / "launch_vivado.tcl").read_text()
            self.assertIn("--verify-preparation", script)
            self.assertIn("is_global_include true", script)
            self.assertIn("-gated_clock_conversion off", script)
            self.assertIn("Unresolved/blackbox", script)
            self.assertNotIn("tb.v", script)
            verify_preparation(output / "preparation.json")
            self.assertFalse(Path(value["output_root"]).exists())

    def test_verifier_is_relocatable_and_stdlib_only(self):
        with tempfile.TemporaryDirectory() as root:
            path, p = self.export(root)
            moved = Path(root) / "moved"
            path.rename(moved)
            proc = subprocess.run([sys.executable, "-I", str(moved / "verify_profile.py"), "--verify", str(moved / "profile.json")],
                                  cwd="/tmp", text=True, capture_output=True, timeout=30)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("SOURCE_PROFILE_VERIFIED", proc.stdout)

    def test_compile_checker_preserves_dialect_and_does_not_turn_warnings_into_qualification(self):
        with tempfile.TemporaryDirectory() as root:
            path, p = self.export(root, design="slh", target="asic", parameter="128f")
            version = subprocess.CompletedProcess([], 0, "Icarus TEST DOUBLE", "")
            compiler = subprocess.CompletedProcess([], 0, "", "TEST DOUBLE warning: width mismatch\n")
            with patch("tools.check_target_profile_elaboration.shutil.which", return_value="/test/iverilog"), patch("tools.check_target_profile_elaboration.subprocess.run", side_effect=[version, compiler]) as runner:
                report = check(path / "profile.json", Path(root) / "compile")
            command = runner.call_args.args[0]
            self.assertIn("-g2005", command)
            self.assertIn("-tnull", command)
            self.assertEqual(report["status"], "ELABORATED_WARNINGS_UNREVIEWED")
            self.assertFalse(report["functional_qualification"])
            self.assertFalse(report["target_tool_qualification"])
            self.assertFalse(report["memory_mapping_proven"])
            self.assertEqual(report["warning_waivers"], [])

    def test_compile_checker_missing_tool_and_timeout_remain_unqualified(self):
        with tempfile.TemporaryDirectory() as root:
            path, p = self.export(root)
            with patch("tools.check_target_profile_elaboration.shutil.which", return_value=None), self.assertRaisesRegex(ValueError, "not found"):
                check(path / "profile.json", Path(root) / "missing")
            version = subprocess.CompletedProcess([], 0, "Icarus TEST DOUBLE", "")
            timeout = subprocess.TimeoutExpired(["TEST"], 1, output=b"partial output", stderr=b"timeout")
            with patch("tools.check_target_profile_elaboration.shutil.which", return_value="/test/iverilog"), patch("tools.check_target_profile_elaboration.subprocess.run", side_effect=[version, timeout]):
                report = check(path / "profile.json", Path(root) / "timeout", timeout=1)
            self.assertEqual(report["status"], "TIMEOUT")
            self.assertIsNone(report["compiler_returncode"])

    @unittest.skipUnless(shutil.which("tclsh"), "tclsh unavailable")
    def test_source_only_tcl_is_location_independent(self):
        with tempfile.TemporaryDirectory() as root:
            path, p = self.export(root, design="slh", target="fpga", parameter="128f")
            proc = subprocess.run(["tclsh"], input="source {" + str(path / "sources.tcl") + "}\nputs \"[llength $pqc_sources] $pqc_top\"\n",
                                  cwd="/tmp", text=True, capture_output=True, timeout=30)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("29 top", proc.stdout)


if __name__ == "__main__":
    unittest.main()
