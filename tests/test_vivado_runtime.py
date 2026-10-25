"""License-free Vivado runtime tests; no EDA executable is launched."""
import contextlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent import fmax_search as fmax
from agent import ppa_reader as ppa
from agent import synthesizer as synth
from agent.backends.vivado import VivadoBackend
from agent.slh_dsa import regen_slh_ckpt as slh_regen

ROOT = Path(__file__).resolve().parents[1]
ROUTE = """Design Route Status
# of routable nets........ : 10 :
# of fully routed nets.... : 10 :
# of nets with routing errors.... : 0 :
"""
UTIL = """| Slice LUTs* | 1,234 | 0 | 10000 |
| Slice Registers | 2,345 | 0 | 10000 |
| Block RAM Tile | 1.5 | 0 | 100 |
| DSPs | 0 | 0 | 100 |
"""
POWER = """| Total On-Chip Power (W) | 1.25 |
| Dynamic (W) | 1.00 |
| Device Static (W) | 0.25 |
"""


def timing(slack=0.1, period=8.0, status=None):
    if status is None:
        status = "MET" if slack >= 0 else "VIOLATED"
    return f"""WNS(ns) TNS(ns) TNS Failing Endpoints TNS Total Endpoints
------- ------- --------------------- -------------------
{slack} 0.000 0 10
Slack ({status}) : {slack}ns (required time - arrival time)
  Source: src_reg/C
    (rising edge-triggered cell FDRE clocked by clk {{period={period:.3f}ns}})
  Destination: dst_reg/D
  Path Type: Setup (Max at Slow Process Corner)
"""


class Reports(unittest.TestCase):
    def test_global_wns_is_not_a_clock_or_hold_row(self):
        text = "clk 5.0 0.0 0.0 0.0 0.0 0.0\n" + timing(-0.5)
        self.assertEqual(ppa.extract_wns(text), -0.5)

    def test_fractional_bram_and_thousands(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "util.rpt"
            report.write_text(UTIL)
            self.assertEqual(ppa.parse_util(report), {"luts": 1234, "ffs": 2345, "bram": 1.5, "dsp": 0})

    def test_fractional_logic_counts_are_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "util.rpt"
            report.write_text(UTIL.replace("1,234", "1.5"))
            with self.assertRaises(ValueError):
                ppa.parse_util(report)

    def test_empty_endpoint_table_is_invalid(self):
        with self.assertRaises(ValueError):
            ppa.timing_from_text(timing().replace("0.000 0 10", "0.000 0 0"))

    def test_summary_cannot_override_violating_setup_path(self):
        with self.assertRaises(ValueError):
            ppa.timing_from_text(timing(-0.1).replace("-0.1 0.000", "0.1 0.000"))

    def test_no_retracted_projection(self):
        result = ppa.timing_from_text(timing(0.5, 12.0), period=12.0)
        self.assertIsNone(result["fmax_mhz"])
        self.assertEqual(result["period_ns"], 12.0)
        self.assertEqual(result["fmax_method"], "not_measured")

    def test_nonfinite_summary_is_invalid(self):
        for token in ("nan", "inf", "-inf", "1e999", "--"):
            text = timing().replace("0.1 0.000", token + " 0.000")
            with self.subTest(token=token), self.assertRaises(ValueError):
                ppa.timing_from_text(text)

    def test_nonfinite_path_is_invalid_even_with_summary(self):
        with self.assertRaises(ValueError):
            ppa.timing_from_text(timing().replace("0.1ns", "nanns"))

    def test_contradictory_slack_is_invalid(self):
        for slack, status in ((-0.1, "MET"), (0.1, "VIOLATED")):
            with self.assertRaises(ValueError):
                ppa.timing_from_text(timing(slack, status=status))

    def test_hold_only_is_not_setup(self):
        text = timing().split("Slack", 1)[1]
        with self.assertRaises(ValueError):
            ppa.timing_from_text("Slack" + text.replace("Setup", "Hold"))

    def test_bad_periods(self):
        for period in (True, 0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                ppa.timing_from_text(timing(), period)

    def test_missing_reports_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ppa.read_ppa("unit", "default", tmp)
        self.assertFalse(result["measurement_valid"])
        self.assertIn("error", result)

    def test_incomplete_routing_is_invalid(self):
        with self.assertRaises(ValueError):
            ppa.timing_from_text(timing() + "Routing Is Not Complete")

    def test_route_requires_positive_complete_evidence(self):
        fmax.validate_route(ROUTE)
        for bad in ("", ROUTE.replace(": 10 :", ": 9 :", 1),
                    ROUTE.replace(": 0 :", ": 1 :"),
                    ROUTE + "# of unrouted nets... : 1 :\n"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                fmax.validate_route(bad)

    def test_routed_timing_requires_worst_path_and_correct_period(self):
        self.assertTrue(fmax.validate_timing(timing(), 8)["timing_met"])
        for bad in (timing(period=9), timing().replace("0.1 0.000", "0.3 0.000"),
                    timing().split("Slack")[0], timing().replace("Source:", "Unknown:")):
            with self.assertRaises(ValueError):
                fmax.validate_timing(bad, 8)


class SearchRuntime(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.checkpoint = self.root / "test [checkpoint] {draft}.dcp"
        self.checkpoint.write_text("mock checkpoint, not EDA data")
        self.periods = []
        self.policy = lambda period, count: 0.1 if period >= 8 else -0.1
        self.returncode = 0
        self.marker = "PQC_FMAX_PROBE_DONE\n"
        self.route = ROUTE

    def tearDown(self):
        self.tmp.cleanup()

    def tool(self, argv, **kwargs):
        work = Path(kwargs["cwd"])
        script = Path(argv[argv.index("-source") + 1]).read_text()
        period = float(re.search(r"create_clock -period (\S+)", script)[1])
        self.periods.append(period)
        slack = self.policy(period, len(self.periods))
        if slack is not None:
            (work / "timing.rpt").write_text(timing(slack, period))
            (work / "timing.rpt.route").write_text(self.route)
        return subprocess.CompletedProcess(argv, self.returncode, self.marker, "")

    def run_search(self, **kwargs):
        with patch.object(fmax, "run_process", self.tool):
            return fmax.search(self.checkpoint, "unit", 6, 10, output_dir=self.root / "runs",
                               legacy_dir=self.root / "aliases", **kwargs)

    def test_endpoints_measured_and_legacy_alias_kept(self):
        result = self.run_search(iterations=3)
        self.assertEqual(self.periods[:2], [6.0, 10.0])
        self.assertEqual(result["closing_period_ns"], 8.0)
        self.assertTrue(result["search_complete"])
        self.assertTrue(result["measurement_valid"])
        self.assertFalse(result["global_maximum_proven"])
        self.assertEqual(Path(result["legacy_report_path"]).name, "fsrch_unit_8.0.rpt")
        self.assertEqual(Path(result["legacy_report_path"]).read_text(), Path(result["report_path"]).read_text())

    def test_upper_endpoint_can_be_only_closing_sample(self):
        self.policy = lambda period, count: 0.1 if period == 10 else -0.1
        result = self.run_search(iterations=3)
        self.assertEqual(result["closing_period_ns"], 10.0)

    def test_lower_endpoint_closed_is_not_global_maximum(self):
        self.policy = lambda period, count: 0.1
        result = self.run_search()
        self.assertEqual(self.periods, [6, 10])
        self.assertTrue(result["lower_bound_closed"])
        self.assertEqual(result["closing_period_ns"], 6)
        self.assertFalse(result["global_maximum_proven"])

    def test_no_closed_endpoint_is_not_success(self):
        self.policy = lambda period, count: -0.1
        result = self.run_search()
        self.assertEqual(result["status"], "NO_CLOSURE_OBSERVED")
        self.assertIsNone(result["closing_period_ns"])
        self.assertFalse(result["measurement_valid"])

    def test_nonmonotonic_outcome_is_disclosed(self):
        self.policy = lambda period, count: 0.1 if period == 6 else -0.1
        result = self.run_search()
        self.assertTrue(result["nonmonotonic_observed"])
        self.assertEqual(result["closing_period_ns"], 6)
        self.assertFalse(result["global_maximum_proven"])

    def test_invalid_midpoint_cannot_return_earlier_closure_as_success(self):
        self.policy = lambda period, count: (0.1 if period == 10 else -0.1) if count <= 2 else None
        result = self.run_search()
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertFalse(result["search_complete"])
        self.assertIsNone(result["closing_period_ns"])
        self.assertEqual(result["trace"][1]["wns_ns"], 0.1)
        self.assertEqual(result["trace"][-1]["attempts"], 2)

    def test_retry_uses_fresh_attempt_directory(self):
        self.policy = lambda period, count: None if count == 1 else 0.1
        result = self.run_search()
        self.assertTrue(result["measurement_valid"])
        self.assertEqual(result["trace"][0]["attempts"], 2)
        stale_dir = result["trace"][0]["failures"][0]["run_dir"]
        self.assertNotEqual(stale_dir, str(Path(result["trace"][0]["report_path"]).parent))

    def test_nonzero_return_even_with_valid_reports_is_invalid(self):
        self.returncode = 1
        result = self.run_search()
        self.assertFalse(result["measurement_valid"])
        self.assertIsNone(result["closing_period_ns"])

    def test_missing_or_echoed_marker_is_invalid(self):
        for marker in ("", 'puts "PQC_FMAX_PROBE_DONE"\n', "PQC_FMAX_PROBE_DONE\nERROR: bad\n"):
            self.marker = marker
            self.assertFalse(self.run_search()["measurement_valid"])

    def test_missing_tool_is_invalid(self):
        with patch.object(fmax, "run_process", side_effect=FileNotFoundError("missing vivado")):
            result = fmax.search(self.checkpoint, "unit", output_dir=self.root)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertIsNone(result["closing_period_ns"])

    def test_bad_arguments_do_not_launch(self):
        for lo, hi in ((0, 10), (10, 10), (12, 10), (float("nan"), 10), (6, float("inf")), (True, 10), (6.001, 10)):
            with patch.object(fmax, "run_process") as run:
                result = fmax.search(self.checkpoint, "unit", lo, hi)
                run.assert_not_called()
            self.assertEqual(result["status"], "INVALID_INPUT")

    def test_cli_failure_returns_nonzero_with_json(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = fmax.main([str(self.root / "missing.dcp"), "unit"])
        self.assertEqual(code, 1)
        self.assertIsNone(json.loads(output.getvalue())["closing_period_ns"])

    def test_tcl_does_not_swallow_opt_failure_or_downgrade_drc(self):
        script = fmax.build_tcl(self.checkpoint, 8, self.root / "report.rpt")
        self.assertIn("opt_design\n", script)
        self.assertNotIn("catch {opt_design}", script)
        self.assertNotIn("MDRV-1", script)
        self.assertNotIn("new_severity", script)
        self.assertIn("exit 1", script)


class SynthesisRuntime(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo with spaces"
        self.root.mkdir()
        (self.root / "unit.v").write_text("module unit(input clk); endmodule")
        self.sources = patch.dict(synth.MODULE_SOURCES, {"unit": ["unit.v"]})
        self.sources.start()
        self.marker = "PQC_SYNTHESIS_DONE\n"
        self.returncode = 0
        self.write_reports = True
        self.scripts = []

    def tearDown(self):
        self.sources.stop()
        self.tmp.cleanup()

    def tool(self, argv, **kwargs):
        work = Path(kwargs["cwd"])
        script = Path(argv[argv.index("-source") + 1]).read_text()
        self.scripts.append(script)
        period = float(re.search(r"create_clock -period (\S+)", script)[1])
        if self.write_reports:
            out = work / "reports/unit"
            out.mkdir(parents=True)
            for suffix, text in (("util", UTIL), ("power", POWER), ("timing", timing(period=period))):
                (out / f"unit_default_{suffix}.rpt").write_text(text)
        return subprocess.CompletedProcess(argv, self.returncode, self.marker, "")

    def run_synth(self, **kwargs):
        with patch.object(synth, "run_process", self.tool):
            return synth.run_synthesis("unit", "default", self.root, **kwargs)

    def test_correct_repo_root_period_part_and_ooc(self):
        result = self.run_synth(period=9, part="xc7a100tcsg324-1", ooc=False)
        self.assertTrue(result["measurement_valid"])
        self.assertEqual(result["period_ns"], 9)
        self.assertEqual(result["_config"]["part"], "xc7a100tcsg324-1")
        self.assertNotIn("-mode out_of_context", self.scripts[0])
        self.assertIn('-part xc7a100tcsg324-1', self.scripts[0])
        self.assertIn(str(self.root / "unit.v"), self.scripts[0])
        self.assertTrue((self.root / "synth_out/unit/unit_default_timing.rpt").is_file())
        self.assertIsNone(result["fmax_mhz"])

    def test_stale_reports_cannot_be_accepted(self):
        first = self.run_synth()
        self.assertTrue(first["measurement_valid"])
        self.write_reports = False
        second = self.run_synth()
        self.assertFalse(second["measurement_valid"])
        self.assertIn("error", second)
        self.assertNotEqual(first["run_dir"], second["run_dir"])

    def test_nonzero_exit_overrides_reports(self):
        self.returncode = 1
        result = self.run_synth()
        self.assertFalse(result["measurement_valid"])
        self.assertIn("Vivado failed", result["error"])

    def test_missing_or_echoed_marker_and_tool_errors(self):
        for marker in ("", 'puts "PQC_SYNTHESIS_DONE"\n', "PQC_SYNTHESIS_DONE\nERROR: bad\n"):
            self.marker = marker
            self.assertFalse(self.run_synth()["measurement_valid"])

    def test_missing_tool_and_timeout_are_reported(self):
        for error in (FileNotFoundError("missing tool"), subprocess.TimeoutExpired("vivado", 3)):
            with patch.object(synth, "run_process", side_effect=error):
                result = synth.run_synthesis("unit", "default", self.root)
            self.assertFalse(result["measurement_valid"])
            self.assertIn("error", result)

    def test_missing_sources_never_launch(self):
        (self.root / "unit.v").unlink()
        with patch.object(synth, "run_process") as run:
            result = synth.run_synthesis("unit", "default", self.root)
            run.assert_not_called()
        self.assertIn("missing selected RTL", result["error"])

    def test_backend_forwards_actual_settings(self):
        with patch("agent.backends.vivado.run_synthesis", return_value={"wns_ns": 0.1}) as run:
            result = VivadoBackend(part="other-part", period=7, ooc=False).synthesize("unit", "default", self.root)
        run.assert_called_once_with("unit", "default", self.root, 7, part="other-part", ooc=False)
        self.assertEqual(result["stage"], "post_synth")

    def test_imports_work_outside_checkout_without_launch_or_output(self):
        code = "import sys; sys.path.insert(0, " + repr(str(ROOT)) + "); import agent.synthesizer; import agent.fmax_search; import agent.backends.vivado"
        result = subprocess.run([sys.executable, "-c", code], cwd=self.root, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse((self.root / ".pqc_runs").exists())

    def test_mldsa_root_controls_all_external_paths(self):
        external = self.root / "external mldsa"
        code = "import sys; sys.path.insert(0, " + repr(str(ROOT)) + "); from agent import synthesizer as s; print(s.MODULE_SOURCES['sampler_s_pristine'][0]); print(s.MODULE_SOURCES['bf2x2_baseline'][0])"
        env = dict(os.environ, MLDSA_ROOT=str(external))
        result = subprocess.run([sys.executable, "-c", code], cwd=self.root, env=env, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(all(line.startswith(str(external / "ref_combined/src")) for line in result.stdout.splitlines()))


class SLHCheckpointRuntime(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.rtl = self.root / "RTL [quoted] {literal}"
        (self.rtl / "sphincslet").mkdir(parents=True)
        (self.rtl / "imports/global_include").mkdir(parents=True)
        (self.rtl / "sphincslet/setting.v").write_text("//`define PARAM_128F\n`define PARAM_192F\n")
        (self.rtl / "sphincslet/top.v").write_text("module top(input clk); endmodule")
        (self.rtl / "imports/global_include/clog2.v").write_text("// fixture")
        self.destination = self.root / "published.dcp"
        self.destination.write_text("old checkpoint")
        self.code, self.marker = 0, "PQC_SLH_REGEN_DONE\n"
        self.fresh = b"fresh checkpoint"
        self.mutate = False

    def tearDown(self):
        self.tmp.cleanup()

    def tool(self, argv, **kwargs):
        work = Path(kwargs["cwd"])
        if self.fresh is not None:
            (work / "post_synth.dcp").write_bytes(self.fresh)
        if self.mutate:
            (self.rtl / "sphincslet/top.v").write_text("changed during synthesis")
        return subprocess.CompletedProcess(argv, self.code, self.marker, "")

    def regenerate(self):
        with patch.object(slh_regen, "run_process", self.tool):
            return slh_regen.regenerate(self.rtl, self.destination, run_root=self.root / "runs")

    def test_fresh_checkpoint_published_with_actual_configuration(self):
        result = self.regenerate()
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["configuration"], {"parameter_set": "PARAM_192F", "hash": "SHA2"})
        self.assertEqual(self.destination.read_bytes(), self.fresh)
        script = (Path(result["run_dir"]) / "regen.tcl").read_text()
        self.assertIn("is_global_include true", script)
        self.assertNotIn("i_sig_mode", (Path(result["run_dir"]) / "constraints.xdc").read_text())

    def test_old_output_does_not_count_as_new_checkpoint(self):
        for fresh in (None, b""):
            self.fresh = fresh
            result = self.regenerate()
            self.assertEqual(result["status"], "ERROR")
            self.assertEqual(self.destination.read_text(), "old checkpoint")

    def test_nonzero_status_with_valid_marker_and_dcp_rejected(self):
        self.code = 1
        self.assertEqual(self.regenerate()["status"], "ERROR")
        self.assertEqual(self.destination.read_text(), "old checkpoint")

    def test_missing_echoed_marker_or_logged_error_rejected(self):
        for marker in ("", 'puts "PQC_SLH_REGEN_DONE"\n', "PQC_SLH_REGEN_DONE\nERROR: failed\n"):
            self.marker = marker
            self.assertEqual(self.regenerate()["status"], "ERROR")
            self.assertEqual(self.destination.read_text(), "old checkpoint")

    def test_missing_global_include_does_not_launch(self):
        (self.rtl / "imports/global_include/clog2.v").unlink()
        with patch.object(slh_regen, "run_process") as run:
            result = slh_regen.regenerate(self.rtl, self.destination)
            run.assert_not_called()
        self.assertEqual(result["status"], "ERROR")

    def test_mutated_source_does_not_publish(self):
        self.mutate = True
        self.assertEqual(self.regenerate()["status"], "ERROR")
        self.assertEqual(self.destination.read_text(), "old checkpoint")

    def test_timeout_does_not_publish(self):
        with patch.object(slh_regen, "run_process", side_effect=subprocess.TimeoutExpired("vivado", 1)):
            result = slh_regen.regenerate(self.rtl, self.destination, run_root=self.root)
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(self.destination.read_text(), "old checkpoint")

    def test_default_paths_are_checkout_relative_and_import_safe(self):
        self.assertEqual(slh_regen.RTL, ROOT / "agent/slh_dsa/slh_src")
        self.assertEqual(slh_regen.CKPT, ROOT / "synth_out/slh_dsa/post_synth.dcp")
        code = "import sys; sys.path.insert(0, " + repr(str(ROOT)) + "); sys.argv=['script','BAD','ARGS']; import agent.slh_dsa.regen_slh_ckpt as r; print(r.CKPT)"
        result = subprocess.run([sys.executable, "-c", code], cwd=self.root, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(slh_regen.CKPT))


@unittest.skipUnless(shutil.which("tclsh"), "Tcl interpreter unavailable")
class TclQuoting(unittest.TestCase):
    def test_quotes_survive_braced_catch_body(self):
        value = 'a path [error unexpected] $env(HOME) "quoted" {unbalanced'
        quoted = synth.tcl_quote(value)
        script = 'if {[catch {set value ' + quoted + '; puts $value} message]} {puts stderr $message; exit 1}\n'
        result = subprocess.run(["tclsh"], input=script, text=True, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, value + "\n")
        self.assertEqual(fmax._quote(value), quoted)

    def test_generated_scripts_parse_with_stubbed_eda_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prelude = "proc unknown {args} {return {}}\nproc get_ports {args} {return clk}\n"
            scripts = [fmax.build_tcl(root / "fake [name] {odd.dcp", 8, root / "report.rpt"),
                       synth.build_tcl("poly_mult", "hqc128", synth_out=root / "reports", repo_root=ROOT),
                       slh_regen.build_tcl(root, [root / "fake {file.v"], root)]
            for script in scripts:
                result = subprocess.run(["tclsh"], input=prelude + script, text=True, capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertRegex(result.stdout, r"PQC_(?:FMAX_PROBE|SYNTHESIS|SLH_REGEN)_DONE")


if __name__ == "__main__":
    unittest.main()
