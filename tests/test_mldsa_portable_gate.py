"""Portable ML-DSA gate control tests; these tests are not RTL evidence."""
from pathlib import Path
import unittest
import tempfile

from agent.mldsa.portable_kat_gate import (
    OPERATIONS, evaluate_log, hoist_declarations, prepare_testbench, stage_verify_mutations,
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
                self.assertEqual((destination / f"SigVer_result_{level}.txt").read_text().split(), ["0"] * 4)
                for changed, mutation in enumerate(fields):
                    for name in fields:
                        old = (kat / f"SigVer_{name}_{level}.txt").read_text().split()[0]
                        new = (destination / f"SigVer_{name}_{level}.txt").read_text().split()[changed]
                        self.assertEqual(int(old, 16) ^ int(new, 16), int(name == mutation))

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
