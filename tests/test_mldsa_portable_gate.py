"""Portable ML-DSA gate control tests; these tests are not RTL evidence."""
from pathlib import Path
import unittest
import tempfile
import shutil

from agent.mldsa.portable_kat_gate import (
    OPERATIONS, evaluate_log, hoist_declarations, prepare_testbench, normalize_timing_bookkeeping, stage_verify_mutations, stage_canonical_cases, apply_canonical_hint_guard, run_gate,
)
from agent.mldsa_sources import BUNDLED_ROOT


class PortableMLDSAGateTests(unittest.TestCase):
    def output(self, operation="keygen", count=2):
        return "\n".join(f"ML-DSA-{level}.{OPERATIONS[operation][0]}, KAT #{i} completed in 42 clock cycles"
                         for level in ("II", "III", "V") for i in range(count)) + "\nTestbench done.\n"

    def test_all_operation_names_and_exact_coverage(self):
        for operation in OPERATIONS:
            result = evaluate_log(self.output(operation), operation, 2)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["completed"], 6)

    def test_fail_closed(self):
        good = self.output()
        for text in (good.replace("KAT #1", "KAT #0", 1),
                     good.replace("42 clock", "0 clock", 1),
                     good.replace("Testbench done.", ""),
                     good + "WRONG: expected ff, got xx\n",
                     good + "ERROR: input file not found\n",
                     good + "FATAL: watchdog expired\n",
                     good.replace("ML-DSA-V", "ML-DSA-VI")):
            self.assertEqual(evaluate_log(text, "keygen", 2)["status"], "FAIL", text)
        self.assertEqual(evaluate_log(good, "keygen", 2, 1)["status"], "FAIL")

    def test_each_bench_staged_with_watchdog(self):
        for operation in OPERATIONS:
            path = BUNDLED_ROOT / f"ref_combined/src_tb/tb_{operation}_top.v"
            original = path.read_text()
            result = prepare_testbench(original, operation, 1, 12345)
            self.assertIn("localparam NUM_TV = 1;", result)
            self.assertIn("portable_cycles >= 12345", result)
            self.assertIn('$fatal(1, "portable watchdog expired")', result)
            self.assertEqual(path.read_text(), original)

    def test_bookkeeping_normalization_changes_only_exact_assignments(self):
        import re
        for operation in OPERATIONS:
            path = BUNDLED_ROOT / f"ref_combined/src_tb/tb_{operation}_top.v"
            original = path.read_text()
            # Identically named substrings and comparisons must not be rewritten.
            normalized = normalize_timing_bookkeeping(original, operation)
            expected = re.sub(r"(?m)^(\s*(?:average|start_time)) <= (.*);$", r"\1 = \2;", original)
            if operation == "verify":
                self.assertEqual(expected.count("average/(NUM_TV-1)"), 3)
                expected = expected.replace("average/(NUM_TV-1)", "average/NUM_TV")
                self.assertEqual(normalized.count("average/NUM_TV"), 3)
            self.assertEqual(normalized, expected)
            # Prefix/suffix variables are outside the supported names.
            extra = "\n    other_average <= 7;\n    start_time_copy <= 8;\n    if (average <= 12) $display(\"diagnostic\");\n"
            self.assertEqual(normalize_timing_bookkeeping(original + extra, operation), expected + extra)
            self.assertEqual(path.read_text(), original)

    def test_prepared_stimulus_captures_and_checks_are_unchanged(self):
        from unittest.mock import patch
        for operation in OPERATIONS:
            original = (BUNDLED_ROOT / f"ref_combined/src_tb/tb_{operation}_top.v").read_text()
            with patch("agent.mldsa.portable_kat_gate.normalize_timing_bookkeeping", side_effect=lambda text, op: text):
                prior = prepare_testbench(original, operation, OPERATIONS[operation][1], 12345)
            current = prepare_testbench(original, operation, OPERATIONS[operation][1], 12345)
            self.assertEqual(current, normalize_timing_bookkeeping(prior, operation))

    def test_bookkeeping_normalization_fails_closed_on_drift(self):
        for operation in OPERATIONS:
            original = (BUNDLED_ROOT / f"ref_combined/src_tb/tb_{operation}_top.v").read_text()
            for changed in (original.replace("start_time <= $time;", "start_time <= $time + 1;", 1),
                            original.replace("average <= 0;", "average = 0;", 1),
                            original + "\n    average <= 0;\n",
                            original + "\n    average <= 7;\n"):
                with self.assertRaisesRegex(ValueError, "timing bookkeeping"):
                    normalize_timing_bookkeeping(changed, operation)

    def test_verify_summary_drift_is_rejected(self):
        original = (BUNDLED_ROOT / "ref_combined/src_tb/tb_verify_top.v").read_text()
        changed = original.replace("average/(NUM_TV-1)", "average/NUM_TV", 1)
        with self.assertRaisesRegex(ValueError, "timing bookkeeping summary"):
            normalize_timing_bookkeeping(changed, "verify")

    def test_capacity_mutation_rejected(self):
        path = BUNDLED_ROOT / "ref_combined/src_tb/tb_sign_top.v"
        with self.assertRaisesRegex(ValueError, "capacity"):
            prepare_testbench(path.read_text().replace("NUM_TV = 15", "NUM_TV = 14"), "sign", 1, 99)

    def test_mutations_change_one_bit_and_require_rejection(self):
        fields = ("signature", "message", "ctx", "pk")
        kat = BUNDLED_ROOT / "KAT"
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)
            metadata = stage_verify_mutations(kat, destination)
            self.assertEqual(len(metadata), 12)
            for level in (44, 65, 87):
                self.assertEqual((destination / f"SigVer_result_{level}.txt").read_text().split(), ["1"] * 4)
                for changed, mutation in enumerate(fields):
                    for name in fields:
                        control = next(row["positive_control_index"] for row in metadata if row["parameter_set"] == level)
                        self.assertEqual((kat / f"SigVer_result_{level}.txt").read_text().split()[control], "0")
                        old = (kat / f"SigVer_{name}_{level}.txt").read_text().split()[control]
                        new = (destination / f"SigVer_{name}_{level}.txt").read_text().split()[changed]
                        self.assertEqual(int(old, 16) ^ int(new, 16), int(name == mutation))

    def test_mutations_require_positive_control_coverage(self):
        with self.assertRaisesRegex(ValueError, "positive control"):
            run_gate(vectors=1, verify_mutations=True)

    def test_bounded_hint_word_io_is_testbench_only(self):
        for op, marker in (("sign", "data_o[63-j*8 -: 8]"), ("verify", "data_i[63-j*8 -: 8]")):
            original = (BUNDLED_ROOT / f"ref_combined/src_tb/tb_{op}_top.v").read_text()
            bounded = prepare_testbench(original, op, 15, 100)
            self.assertIn(marker, bounded)
            for level in (2, 3, 5):
                self.assertIn(f"< `h_BYTES_{level}", bounded)
            self.assertIn("!==", bounded)

    def test_canonical_cases_interleave_valid_controls(self):
        from tools.check_mldsa_hint_guard import canonical_hint
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder)
            metadata = stage_canonical_cases(BUNDLED_ROOT / "KAT", destination)
            self.assertEqual(len(metadata), 33)
            for level, omega, k in ((44,80,4), (65,55,6), (87,75,8)):
                flags = (destination / f"SigVer_result_{level}.txt").read_text().split()
                signatures = (destination / f"SigVer_signature_{level}.txt").read_text().split()
                self.assertEqual(flags, ["0", "1"] * 5 + ["0"])
                for flag, sig in zip(flags, signatures):
                    self.assertEqual(canonical_hint(bytes.fromhex(sig)[-omega-k:], omega, k), flag == "0")
                self.assertTrue(all(sig == signatures[0] for sig in signatures[::2]))

    def test_guard_failure_is_sticky_until_new_operation(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            for name in ("usehint.v", "combined_top.v"):
                shutil.copy2(BUNDLED_ROOT / "ref_combined/src" / name, folder / name)
            apply_canonical_hint_guard(folder)
            hint = (folder / "usehint.v").read_text()
            top = (folder / "combined_top.v").read_text()
            self.assertIn("if (start) invalid_hint <= 0;", hint)
            self.assertIn("invalid_hint <= invalid_hint | encoding_invalid;", hint)
            self.assertIn("? (fail | invalid_hint) : 0;", top)
            self.assertTrue((folder / "mldsa_hint_guard.v").is_file())

    def test_hoisting_preserves_declarations_and_upstream(self):
        path = BUNDLED_ROOT / "ref_combined/src/combined_top.v"
        original = path.read_text()
        transformed, count = hoist_declarations(original)
        self.assertGreater(count, 0)
        self.assertEqual(path.read_text(), original)
        self.assertEqual(transformed.count("module combined_top"), 1)
        again, repeated = hoist_declarations(transformed)
        self.assertEqual(repeated, 0)


if __name__ == "__main__":
    unittest.main()
