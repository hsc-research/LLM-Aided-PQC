"""Diagnostic logs must belong to the current isolated gate invocation."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from agent.mldsa.orchestrator_latency import _diagnostic_log


class CurrentDiagnosticLog(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.parent = self.root / "current-invocation"
        self.run = self.parent / "gate-run"
        self.run.mkdir(parents=True)
        self.log = self.run / "fullkat_run.log"
        self.log.write_text("BFI tb.dut 0 aa bb cc\nBFO tb.dut 0 dd\n")
        self.outcome = {"status": "PASS", "stage": "sim", "kats_expected": 3,
                        "kats_completed": 3, "run_dir": str(self.run), "log_file": str(self.log)}

    def result(self, code=0):
        return subprocess.CompletedProcess([], code, json.dumps(self.outcome), "")

    def test_reads_returned_current_log(self):
        archived = self.root / "fullkat_run.log"
        archived.write_text("BFO old.archive 0 stale\n")
        self.assertEqual(_diagnostic_log(self.result(), self.parent), self.log.read_text())

    def test_never_reads_archived_log(self):
        archived = self.root / "fullkat_run.log"
        archived.write_text("BFO old.archive 0 stale\n")
        self.outcome.update(run_dir=str(self.root), log_file=str(archived))
        with self.assertRaisesRegex(RuntimeError, "outside"):
            _diagnostic_log(self.result(), self.parent)

    def test_missing_log_is_inconclusive(self):
        self.log.unlink()
        with self.assertRaisesRegex(RuntimeError, "missing"):
            _diagnostic_log(self.result(), self.parent)

    def test_empty_stream_is_inconclusive(self):
        self.log.write_text("testbench done\n")
        with self.assertRaisesRegex(RuntimeError, "no stream"):
            _diagnostic_log(self.result(), self.parent)

    def test_incomplete_simulation_is_inconclusive(self):
        self.outcome["kats_completed"] = 0
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            _diagnostic_log(self.result(), self.parent)

    def test_failed_edited_simulation_can_show_divergence(self):
        self.outcome["status"] = "FAIL"
        self.assertIn("BFO", _diagnostic_log(self.result(1), self.parent))
        with self.assertRaisesRegex(RuntimeError, "pristine"):
            _diagnostic_log(self.result(1), self.parent, pristine=True)

    def test_exit_status_must_match(self):
        with self.assertRaisesRegex(RuntimeError, "contradicts"):
            _diagnostic_log(self.result(1), self.parent)

    def test_malformed_result_is_inconclusive(self):
        with self.assertRaisesRegex(RuntimeError, "JSON"):
            _diagnostic_log(subprocess.CompletedProcess([], 0, "GATE: PASS"), self.parent)
