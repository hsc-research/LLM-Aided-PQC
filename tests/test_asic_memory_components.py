"""Static guardrails; HDL simulation/mapping use the explicit component runner."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools import check_asic_memory_components as components


class ASICMemoryComponentsTests(unittest.TestCase):
    def test_checked_in_rom_matches_all_pinned_constants(self):
        components.verify_rom_constants()

    def test_constant_mutation_is_rejected(self):
        text = components.ROM.read_text()
        with tempfile.TemporaryDirectory() as folder:
            altered = Path(folder) / "rom.v"
            altered.write_text(text.replace("lookup = 24'h000000", "lookup = 24'h000001", 1))
            with patch.object(components, "ROM", altered):
                with self.assertRaisesRegex(ValueError, "does not match"):
                    components.verify_rom_constants()

    def test_missing_duplicate_or_reordered_address_is_rejected(self):
        text = components.ROM.read_text()
        for replacement in ("8'd2:", "8'd257:"):
            with tempfile.TemporaryDirectory() as folder:
                altered = Path(folder) / "rom.v"
                altered.write_text(text.replace("8'd1:", replacement, 1))
                with patch.object(components, "ROM", altered):
                    with self.assertRaisesRegex(ValueError, "every zeta"):
                        components.verify_rom_constants()

    def test_powerup_or_runtime_file_loading_is_rejected(self):
        text = components.ROM.read_text()
        for statement in ("initial doa = 0;", '$readmemh("zetas.txt", words);'):
            with tempfile.TemporaryDirectory() as folder:
                altered = Path(folder) / "rom.v"
                altered.write_text(text + "\n" + statement + "\n")
                with patch.object(components, "ROM", altered):
                    with self.assertRaisesRegex(ValueError, "initialization"):
                        components.verify_rom_constants()

    def test_only_bounded_memory_sources_are_in_abr_list(self):
        self.assertEqual(set(components.MODULES), {
            "abr_1r1w_ram", "abr_1r1w_be_ram", "abr_1r1w_512x4_ram", "abr_ram_regout"})


if __name__ == "__main__":
    unittest.main()
