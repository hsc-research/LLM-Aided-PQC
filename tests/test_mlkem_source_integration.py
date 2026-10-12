"""Offline provenance/configuration tests; these do not qualify cryptographic RTL."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent import asic_synthesis
from agent.__main__ import doctor, scheme_catalog

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "third_party/adams_bridge"


class MLKEMSourceIntegration(unittest.TestCase):
    def test_vendored_source_identity(self):
        result = subprocess.run([sys.executable, str(VENDOR / "integration/verify_sources.py")],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("220 upstream files are byte-identical", result.stdout)
        self.assertIn("NOT RUN: RTL compile", result.stdout)

    def test_tampered_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "adams_bridge"
            shutil.copytree(VENDOR, copied, ignore=shutil.ignore_patterns("__pycache__"))
            source = copied / "upstream/src/abr_top/rtl/abr_top.sv"
            source.write_text(source.read_text() + "\n// altered fixture\n")
            result = subprocess.run([sys.executable, str(copied / "integration/verify_sources.py")],
                                    text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("upstream blob mismatch", result.stderr)

    def test_wrapper_includes_core_and_all_memory_instances(self):
        wrapper = (VENDOR / "integration/abr_unified_top.sv").read_text()
        self.assertIn("abr_top #(", wrapper)
        self.assertIn("abr_mem_top memories", wrapper)
        self.assertEqual(wrapper.count(".abr_memory_export(memory_bus)"), 2)
        memory = (VENDOR / "upstream/src/abr_top/rtl/abr_mem_top.sv").read_text()
        self.assertEqual(sum(line.startswith("`ABR_MEM") for line in memory.splitlines()), 10)
        config = json.loads((VENDOR / "integration/manifest.json").read_text())
        self.assertEqual(config["top"], "abr_unified_top")
        self.assertIn("unified", config["scope"])
        self.assertIn("memories", config["scope"])
        self.assertEqual(len(config["files"]), 175)
        self.assertNotIn("CALIPTRA", config["generic_synthesis_defines"])

    def test_acvp_fixture_has_all_operations_and_implicit_rejections(self):
        fixture = json.loads((VENDOR / "test_vectors/nist_acvp_mlkem1024.json").read_text())
        self.assertEqual(len(fixture["cases"]), 80)
        rejected = []
        for case in fixture["cases"]:
            if case["operation"] != "decapsulation":
                continue
            dk = bytes.fromhex(case["input"]["dk"])
            ciphertext = bytes.fromhex(case["input"]["c"])
            fallback = hashlib.shake_256(dk[-32:] + ciphertext).digest(32).hex()
            if fallback.lower() == case["expected"]["k"].lower():
                rejected.append(case["tcId"])
        self.assertEqual(rejected, [96, 98, 101, 104, 105])

    @unittest.skipUnless(shutil.which("tclsh"), "tclsh unavailable")
    def test_tcl_manifest_is_location_independent(self):
        script = f'source {{{VENDOR / "integration/sources.tcl"}}}\n'
        script += 'puts "[llength $abr_sources] [llength $abr_include_dirs] $abr_top"\n'
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(["tclsh"], input=script, cwd=directory,
                                    text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("175 25 abr_unified_top", result.stdout)

    def test_asic_example_uses_actual_runner_and_user_libraries(self):
        original = json.loads((ROOT / "configs/mlkem_adams_bridge_asic.example.json").read_text())
        self.assertEqual(original["memory_model"], "flops")
        self.assertIn("full_unified", original["scope"])
        self.assertEqual(original["defines"], ["SYNTHESIS"])
        for tool in ("genus", "dc"):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as directory:
                directory = Path(directory)
                config = copy.deepcopy(original)
                config["root"] = str(ROOT)
                library = directory / ("fixture.lib" if tool == "genus" else "fixture.db")
                library.write_text('library (test) { time_unit : "1ns"; }')
                config["tools"][tool]["target_libraries"] = [str(library)]
                path = directory / "config.json"
                path.write_text(json.dumps(config))
                plan = asic_synthesis.load_config(path, tool=tool)
                self.assertEqual(len(plan["files"]), 175)
                self.assertEqual(plan["top"], "abr_unified_top")
                script = asic_synthesis.render_tcl(plan)
                self.assertIn("abr_unified_top", script)
                self.assertIn("SYNTHESIS", script)
                self.assertNotIn("RV_FPGA_OPTIMIZE", script)

    def test_asic_example_requires_external_library_setup(self):
        with patch.dict(os.environ, {}, clear=True):
            for tool in ("genus", "dc"):
                with self.subTest(tool=tool), self.assertRaisesRegex(ValueError, "Unresolved configuration path"):
                    asic_synthesis.load_config(ROOT / "configs/mlkem_adams_bridge_asic.example.json", tool)

    def test_catalog_does_not_confuse_import_with_qualification(self):
        row = next(item for item in scheme_catalog() if item["key"] == "mlkem")
        self.assertEqual(row["support"], "baseline_available_site_qualification_pending")
        self.assertFalse(row["automatic_optimization_dispatch"])
        with patch("subprocess.Popen", side_effect=AssertionError("discovery must not run tools")):
            row = next(item for item in doctor()["schemes"] if item["key"] == "mlkem")
        self.assertFalse(row["licensed_run_verified"])
        self.assertIn("pending", row["qualification"])

    @unittest.skipUnless(shutil.which("tclsh"), "tclsh unavailable")
    def test_vivado_script_requires_explicit_site_arguments(self):
        script = f'set argc 0\nset argv {{}}\nsource {{{VENDOR / "integration/vivado_synth.tcl"}}}\n'
        result = subprocess.run(["tclsh"], input=script, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Usage", result.stderr)

    @unittest.skipUnless(shutil.which("tclsh"), "tclsh unavailable")
    def test_vivado_tcl_with_explicit_test_doubles(self):
        # These stubs test Tcl wiring only. They neither parse nor synthesize RTL.
        for blackbox in (False, True):
            with self.subTest(blackbox=blackbox), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "new-output"
                script = r'''
proc create_project {args} {}
proc current_project {} {return TEST_DOUBLE_PROJECT}
proc current_fileset {} {return TEST_DOUBLE_FILESET}
proc set_property {args} {}
proc read_verilog {args} {
    if {[lindex $args 0] ne "-sv" || [llength [lindex $args 1]] != 175} {
        error "Expected full ordered SystemVerilog manifest"
    }
}
proc read_xdc {args} {}
proc synth_design {args} {
    if {[lindex $args [expr {[lsearch -exact $args -top] + 1}]] ne "abr_unified_top"} {
        error "Wrong synthesis top"
    }
    if {[lindex $args [expr {[lsearch -exact $args -mode] + 1}]] ne "out_of_context"} {
        error "Wrong synthesis stage"
    }
}
proc get_clocks {} {return clk}
proc report_utilization {args} {}
proc report_timing_summary {args} {}
proc check_timing {args} {}
proc report_drc {args} {}
proc write_checkpoint {args} {}
proc version {args} {return TEST_DOUBLE_NOT_VIVADO}
'''
                script += 'proc get_cells {args} {return ' + ('UNRESOLVED' if blackbox else '{}') + '}\n'
                script += f'set argc 3\nset argv [list TEST_PART 10 {{{output}}}]\n'
                script += f'source {{{VENDOR / "integration/vivado_synth.tcl"}}}\n'
                result = subprocess.run(["tclsh"], input=script, text=True, capture_output=True)
                if blackbox:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("black-box", result.stderr)
                    self.assertFalse((output / "scope.txt").exists())
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    scope = (output / "scope.txt").read_text()
                    self.assertIn("TEST_DOUBLE_NOT_VIVADO", scope)
                    self.assertIn("unified_mlkem1024_mldsa87_with_memories", scope)
                    self.assertIn("stage=out_of_context_synthesis_only", scope)
                    xdc = (output / "target.example.xdc").read_text()
                    self.assertIn("create_clock -name clk -period 10 [get_ports clk]", xdc)


if __name__ == "__main__":
    unittest.main()
