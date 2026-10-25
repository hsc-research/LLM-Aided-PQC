"""Offline source/config checks. Test doubles are not RTL or EDA evidence."""
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
from agent.__main__ import doctor
from agent.mldsa_sources import BUNDLED_ROOT, COMMIT, missing_inputs, source_root, verify_snapshot

ROOT = Path(__file__).resolve().parents[1]


class MLDSASourceIntegration(unittest.TestCase):
    def test_all_source_bytes_and_keygen_vector_shapes(self):
        result = verify_snapshot()
        self.assertEqual((result['files'], result['bytes'], result['keygen_cases_present']), (106, 3300503, 75))
        self.assertEqual(result['commit'], COMMIT)
        self.assertIn('NOT RUN', result['qualification'])
        self.assertEqual(missing_inputs(BUNDLED_ROOT), [])

    def test_tampered_source_and_manifest_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'snapshot'
            shutil.copytree(BUNDLED_ROOT, root)
            zetas = root / 'common/zetas.txt'
            original = zetas.read_bytes()
            zetas.write_bytes(b'100000' + original[6:])
            with self.assertRaisesRegex(ValueError, 'upstream blob mismatch'):
                verify_snapshot(root)
            zetas.write_bytes(original)
            manifest = root / 'SOURCE_MANIFEST.json'
            manifest.write_bytes(manifest.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'manifest differs'):
                verify_snapshot(root)

    def test_extra_or_missing_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'snapshot'
            shutil.copytree(BUNDLED_ROOT, root)
            extra = root / 'unexpected.v'
            extra.write_text('module unexpected; endmodule\n')
            with self.assertRaisesRegex(ValueError, 'Unexpected or missing'):
                verify_snapshot(root)
            extra.unlink()
            (root / 'KAT/KeyGen_pk_87.txt').unlink()
            self.assertEqual(len(missing_inputs(root)), 1)
            with self.assertRaises(OSError):
                verify_snapshot(root)

    def test_bundled_default_and_environment_override(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(source_root(), BUNDLED_ROOT)
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'MLDSA_ROOT': directory}):
            self.assertEqual(source_root(), Path(directory))
            code = 'from agent.mldsa.full_kat_gate import ROOT; from agent.mldsa.gate_result import pristine_source; from agent.synthesizer import MLDSA_ROOT; print(ROOT); print(MLDSA_ROOT); print(pristine_source())'
            run = subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(run.stdout.splitlines(), [directory, directory, str(Path(directory) / 'ref_combined/src')])

    def test_doctor_checks_integrity_without_running_tools(self):
        with patch.dict(os.environ, {}, clear=True), patch('subprocess.Popen', side_effect=AssertionError('Must not launch EDA')):
            row = next(x for x in doctor()['schemes'] if x['key'] == 'mldsa')
        self.assertTrue(row['source_available'])
        self.assertEqual(row['source_integrity']['source_integrity'], 'PASS')
        self.assertFalse(row['licensed_run_verified'])
        self.assertIn('pending', row['qualification'])

    def test_external_tree_is_not_reported_pin_verified(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'MLDSA_ROOT': directory}):
            row = next(x for x in doctor()['schemes'] if x['key'] == 'mldsa')
        self.assertFalse(row['source_available'])
        self.assertEqual(row['source_integrity']['status'], 'external_override_not_pin_verified')
        self.assertTrue(row['missing_inputs'])

    def test_all_candidate_overrides_have_pinned_counterparts(self):
        candidates = list((ROOT / 'agent/mldsa/mldsa_src').glob('*.v'))
        self.assertEqual(len(candidates), 14)
        self.assertTrue(all((BUNDLED_ROOT / 'ref_combined/src' / p.name).is_file() for p in candidates))

    def test_asic_manifest_and_zetas_staging_plan(self):
        original = json.loads((ROOT / 'configs/mldsa_osh_asic.example.json').read_text())
        for tool in ('genus', 'dc'):
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as directory:
                directory = Path(directory)
                config = copy.deepcopy(original)
                config['root'] = str(ROOT)
                library = directory / ('fixture.lib' if tool == 'genus' else 'fixture.db')
                library.write_text('library(test) { time_unit : "1ns"; }')
                config['tools'][tool]['target_libraries'] = [str(library)]
                path = directory / 'config.json'
                path.write_text(json.dumps(config))
                plan = asic_synthesis.load_config(path, tool)
                self.assertEqual(plan['top'], 'combined_top')
                self.assertEqual(len(plan['files']), 50)
                self.assertEqual([Path(x['path']).name for x in plan['files'][:2]], ['sha3_pkg.vhd', 'keccak_pkg.vhd'])
                zetas = str(BUNDLED_ROOT / 'common/zetas.txt')
                self.assertEqual(plan['data_files'], [zetas])
                self.assertIn(zetas, plan['input_hashes'])
                self.assertEqual(hashlib.sha256(Path(zetas).read_bytes()).hexdigest(), '07d0eabbd7a102982b11d39b748758d34baf309aa71cf3d1bac518b9dded0241')
                script = asic_synthesis.render_tcl(plan)
                self.assertIn('combined_top', script)
                self.assertIn('sha3_pkg.vhd', script)

    def test_asic_example_needs_real_site_libraries(self):
        with patch.dict(os.environ, {}, clear=True):
            for tool in ('genus', 'dc'):
                with self.subTest(tool=tool), self.assertRaisesRegex(ValueError, 'Unresolved configuration path'):
                    asic_synthesis.load_config(ROOT / 'configs/mldsa_osh_asic.example.json', tool)



if __name__ == '__main__':
    unittest.main()
