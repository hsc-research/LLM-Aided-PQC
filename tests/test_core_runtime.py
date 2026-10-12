"""Offline regressions for proposal boundaries and installable discovery CLI."""
import copy
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent import edit_ops
from agent.__main__ import doctor, scheme_catalog, smoke
from agent.llm_client import create_client
from agent.run_safety import gate_passed

ROOT = Path(__file__).resolve().parents[1]


class TypedEdits(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "a.v"
        self.original = "module a;\nreg flag;\nendmodule\n"
        self.source.write_text(self.original)
        self.exp = {"name": "trial", "files": [{"path": str(self.source), "ops": [
            {"op": "replace_exact", "old": "reg flag;", "new": "reg other;", "expect": 1}]}]}
        self.options = {"allowed_paths": [self.source], "backup_dir": self.root / "backups"}

    def test_preview_never_writes(self):
        staged = edit_ops.preview_experiment(self.exp, allowed_paths=[self.source])
        self.assertIn("reg other;", staged[str(self.source)][1])
        self.assertEqual(self.source.read_text(), self.original)
        self.assertFalse((self.root / "backups").exists())

    def test_apply_and_revert(self):
        backups = edit_ops.apply_experiment(self.exp, **self.options)
        self.assertIn("reg other;", self.source.read_text())
        edit_ops.revert(backups)
        self.assertEqual(self.source.read_text(), self.original)

    def test_wrong_count_leaves_no_writes(self):
        self.exp["files"][0]["ops"][0]["expect"] = 2
        with self.assertRaises(edit_ops.EditError):
            edit_ops.apply_experiment(self.exp, **self.options)
        self.assertEqual(self.source.read_text(), self.original)
        self.assertFalse((self.root / "backups").exists())

    def test_simulator_side_effects_rejected(self):
        for replacement in ('initial $system("touch /tmp/bad");',
                            'initial $display("GATE: PASS");',
                            '`include "gate.v"'):
            self.exp["files"][0]["ops"][0]["new"] = replacement
            with self.subTest(replacement=replacement), self.assertRaises(edit_ops.EditError):
                edit_ops.apply_experiment(self.exp, **self.options)
        self.assertEqual(self.source.read_text(), self.original)

    def test_duplicate_paths_refused(self):
        self.exp["files"].append(copy.deepcopy(self.exp["files"][0]))
        with self.assertRaises(edit_ops.EditError):
            edit_ops.apply_experiment(self.exp, **self.options)

    def test_unsafe_slug_refused(self):
        self.exp["name"] = "../../escape"
        with self.assertRaises(edit_ops.EditError):
            edit_ops.apply_experiment(self.exp, **self.options)

    def test_arbitrary_paths_default_denied(self):
        with self.assertRaises(edit_ops.EditError):
            edit_ops.apply_experiment(self.exp)

    def test_testbench_targets_default_denied(self):
        for relative in ("build/keygen/tb/keygen_tb.v", "agent/slh_dsa/slh_src/sphincslet/tb.v"):
            with self.subTest(path=relative), self.assertRaises(edit_ops.EditError):
                edit_ops.validate_path(str(ROOT / relative))

    def test_symlink_denied(self):
        link = self.root / "link.v"
        link.symlink_to(self.source)
        self.exp["files"][0]["path"] = str(link)
        with self.assertRaises(edit_ops.EditError):
            edit_ops.apply_experiment(self.exp, **self.options)

    def test_gate_code_extension_denied_even_in_allowlist(self):
        file = self.root / "gate.py"
        file.write_text("pass")
        with self.assertRaises(edit_ops.EditError):
            edit_ops.validate_path(str(file), [file])

    def test_boolean_count_refused(self):
        self.exp["files"][0]["ops"][0]["expect"] = True
        with self.assertRaises(edit_ops.EditError):
            edit_ops.apply_experiment(self.exp, **self.options)

    def test_empty_anchor_refused(self):
        self.exp["files"][0]["ops"][0]["old"] = ""
        with self.assertRaises(edit_ops.EditError):
            edit_ops.apply_experiment(self.exp, **self.options)

    def test_delete_exact_text_allowed(self):
        self.exp["files"][0]["ops"][0]["new"] = ""
        edit_ops.apply_experiment(self.exp, **self.options)
        self.assertNotIn("reg flag;", self.source.read_text())

    def test_pair_site_count_enforced(self):
        self.source.write_text("module a;\nreg ctr;\nctr <= 0;\nendmodule\n")
        self.exp["files"][0]["ops"] = [
            {"op": "declare_reg", "name": "is_zero"},
            {"op": "pair_assignments", "reg": "ctr", "flag": "is_zero", "expr": "({rhs}) == 0", "expect_sites": 2}]
        with self.assertRaises(edit_ops.EditError):
            edit_ops.apply_experiment(self.exp, **self.options)

    def test_same_basename_backups_distinct(self):
        other = self.root / "second" / "a.v"
        other.parent.mkdir()
        other.write_text(self.original)
        spec = copy.deepcopy(self.exp["files"][0]); spec["path"] = str(other)
        self.exp["files"].append(spec)
        self.options["allowed_paths"].append(other)
        backups = edit_ops.apply_experiment(self.exp, **self.options)
        self.assertEqual(len(set(backups.values())), 2)
        edit_ops.revert(backups)
        self.assertEqual(other.read_text(), self.original)

    def test_partial_write_failure_rolls_back(self):
        other = self.root / "b.v"; other.write_text(self.original)
        spec = copy.deepcopy(self.exp["files"][0]); spec["path"] = str(other)
        self.exp["files"].append(spec)
        self.options["allowed_paths"].append(other)
        original_write = edit_ops._atomic_write
        def fail_second(path, text):
            if Path(path) == other:
                raise OSError("injected write failure")
            original_write(path, text)
        with patch.object(edit_ops, "_atomic_write", side_effect=fail_second):
            with self.assertRaises(OSError):
                edit_ops.apply_experiment(self.exp, **self.options)
        self.assertEqual(self.source.read_text(), self.original)
        self.assertEqual(other.read_text(), self.original)

    def test_optimized_python_still_rejects(self):
        self.exp["files"][0]["ops"][0]["expect"] = 9
        code = "from agent.edit_ops import apply_experiment; apply_experiment(" + repr(self.exp) + ", allowed_paths=" + repr([str(self.source)]) + ")"
        result = subprocess.run([sys.executable, "-O", "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("EditError", result.stderr)
        self.assertEqual(self.source.read_text(), self.original)


class OfflineRuntime(unittest.TestCase):
    def test_all_four_schemes_explicit(self):
        self.assertEqual({r["scheme"] for r in scheme_catalog()}, {"ML-KEM", "ML-DSA", "SLH-DSA", "HQC"})
        self.assertEqual(scheme_catalog()[0]["support"], "not_implemented")

    def test_smoke(self):
        self.assertEqual(smoke()["status"], "PASS")

    def test_doctor_is_read_only(self):
        with patch("subprocess.Popen", side_effect=AssertionError("must not launch")):
            result = doctor()
        self.assertEqual(result["audit_status"], "completed")
        self.assertTrue(all(not row["licensed_run_verified"] for row in result["schemes"]))

    def test_paid_calls_require_explicit_optin(self):
        with patch.dict(os.environ, {"PQC_ENABLE_LLM": "0"}):
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                create_client()

    def test_imports_without_sdk_or_key(self):
        sys.path.insert(0, str(ROOT / "agent"))
        with patch.dict(os.environ, {"PQC_ENABLE_LLM": "0"}), patch("subprocess.Popen", side_effect=AssertionError("no tool run")):
            for name in ("agent.optimizer", "agent.optimizer_v2", "agent.port.propose_fix", "agent.flow_orchestrator",
                         "agent.mldsa.orchestrator", "agent.hqc.transfer_orchestrator",
                         "agent.hqc.joint_top_orchestrator", "agent.slh_dsa.slh_orchestrator"):
                with self.subTest(module=name):
                    importlib.import_module(name)

    def test_gate_rejects_conflicting_or_inline_verdict(self):
        for text in ("GATE: PASS\nKAT RESULT: FAIL", "GATE: PASS\nERROR: simulator failed", "GATE: PASS\n  FATAL: crashed",
                     "prefix GATE: PASS and something", 'prose "status": "PASS" without JSON'):
            with self.subTest(text=text):
                self.assertFalse(gate_passed(subprocess.CompletedProcess([], 0, text)))

    def test_legacy_unsafe_workflows_block_before_writes_or_calls(self):
        from agent import optimizer, loop, flow_orchestrator
        with patch("subprocess.Popen", side_effect=AssertionError("must not run")):
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                optimizer.optimize_once("x", "x", "/nonexistent")
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                loop.run_loop("x", "x", "/nonexistent")
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                flow_orchestrator.main()

    def test_dashboard_has_no_dynamic_inline_handler(self):
        script = (ROOT / "agent/dashboard_static/app.js").read_text()
        self.assertNotIn("onclick='showFixByBlock", script)
        self.assertIn("data-core-index", script)
        self.assertIn("&#39;", script)

    def test_gate_accepts_structured_final_result(self):
        self.assertTrue(gate_passed(subprocess.CompletedProcess([], 0, '{"status": "PASS", "stage": "sim"}')))


if __name__ == "__main__":
    unittest.main()
