"""Deterministic source-only SLH handoff checks; no hardware tool is invoked."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import export_slh_verified as export


class SLHSourceExport(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def inventory(self, root):
        return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}

    def test_export_is_deterministic_and_invokes_no_eda(self):
        first, second = self.root / 'one', self.root / 'two'
        before = export.portable.rtl_hashes(export.VARIANTS['corrected-baseline'])
        with patch.object(export.portable, 'run_process', side_effect=AssertionError('EDA called')), \
             patch.object(export.portable.subprocess, 'run', side_effect=AssertionError('subprocess called')):
            a = export.export_sources('corrected-baseline', '128f', first)
            b = export.export_sources('corrected-baseline', '128f', second)
        self.assertEqual(a, b)
        self.assertEqual(self.inventory(first), self.inventory(second))
        self.assertEqual(export.portable.rtl_hashes(export.VARIANTS['corrected-baseline']), before)
        self.assertEqual(a['top'], 'top')
        self.assertEqual(a['simulation_top'], 'tb')
        self.assertEqual(a['parameter_set'], 'SHA2-128f')
        self.assertEqual(len(a['sources']), 29)
        self.assertEqual(len(a['simulation_sources']), 30)
        self.assertFalse(any(s['path'].endswith('/tb.v') for s in a['sources']))
        self.assertEqual(len(a['data_files']), 4)
        self.assertEqual(a['memory_init_files'], [])
        self.assertEqual(set(a['source_relationship']['only_same_parameter_differences']), export.CORE_DIFFERENCES)
        self.assertEqual(a['source_relationship']['comparison_group'], 'corrected-SHA2-128f')
        self.assertEqual((first / 'sources.f').read_text().splitlines(), [s['path'] for s in a['sources']])
        for line in (first / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ', 1)
            self.assertEqual(export.sha(first / name), digest, name)
        for path, digest in a['bundle_files_sha256'].items():
            self.assertEqual(export.sha(first / path), digest, path)
        self.assertFalse((first / 'simulation/TECS_v8.srcs/sources_1/imports/data_sha2/SIG_file0_128f_w.hex').exists())

    def test_candidate192_export_matches_qualified_staged_hashes(self):
        target = self.root / 'candidate'
        manifest = export.export_sources('corrected-candidate', '192f', target)
        self.assertEqual(export.portable.rtl_hashes(target / 'rtl'), manifest['qualified_staged_source_sha256'])
        self.assertEqual(manifest['parameter_set'], 'SHA2-192f')
        self.assertEqual(manifest['source_relationship']['partner_variant'], 'corrected-baseline')
        self.assertTrue(manifest['tested_cases'][1]['negative_control_qualified'])

    def test_destination_and_unsupported_mode_are_fail_closed(self):
        out = self.root / 'occupied'
        out.mkdir()
        (out / 'mine.txt').write_text('keep')
        with self.assertRaisesRegex(ValueError, 'absent or empty'):
            export.export_sources('corrected-baseline', '128f', out)
        self.assertEqual((out / 'mine.txt').read_text(), 'keep')
        for bad in (export.VARIANTS['corrected-baseline'], ROOT, ROOT / 'agent/slh_dsa/pristine/inside'):
            with self.assertRaisesRegex(ValueError, 'protected source'):
                export.export_sources('corrected-baseline', '128f', bad)
        with self.assertRaisesRegex(ValueError, 'supports'):
            export.export_sources('corrected-baseline', '256f', self.root / 'unsupported')

    def test_stale_wrong_mode_or_incomplete_qualification_is_rejected(self):
        out = self.root / 'staged'
        original, _ = export.prepare_sources(export.VARIANTS['corrected-baseline'], out, '128f')
        report = json.loads((ROOT / 'docs/verification' / export.RECORDS[('corrected-baseline', '128f')]).read_text())
        kwargs = dict(parameter='128f', original_hashes=original, staged_hashes=export.portable.rtl_hashes(out), inputs=report['input_sha256'])
        export.validate_qualification(report, **kwargs)
        reordered = deepcopy(report)
        reordered['cases'].reverse()
        export.validate_qualification(reordered, **kwargs)  # Case identities bind controls, not list ordering.
        changes = [lambda r: r.update(status='FAIL'), lambda r: r.update(parameter_set='SHA2-192f'),
                   lambda r: r.update(auth_sensitivity_fix=False), lambda r: r.update(staged_source_sha256={}),
                   lambda r: r.update(input_sha256={}), lambda r: r.update(tracked_inputs_unchanged=False),
                   lambda r: r['cases'].pop(), lambda r: r['cases'][0].update(rtl_verification_flag=['1']),
                   lambda r: r['cases'][1].update(negative_control_qualified=False),
                   lambda r: r['cases'][1].update(output_words=2140),
                   lambda r: r.update(compile_returncode=False),
                   lambda r: r['cases'][0].update(simulator_returncode=False),
                   lambda r: r['cases'][0].update(output_words=2141.0),
                   lambda r: r['cases'][1].update(negative_control_contract_satisfied=False),
                   lambda r: r['cases'][1].update(observed_rejection=False),
                   lambda r: r.update(source_sha256=export.portable.rtl_hashes(export.VARIANTS['corrected-candidate'])),
                   lambda r: r.update(cases=[r['cases'][0], r['cases'][0]])]
        for change in changes:
            with self.subTest(change=change):
                bad = deepcopy(report)
                change(bad)
                with self.assertRaises(ValueError):
                    export.validate_qualification(bad, **kwargs)

    def test_absent_partner_is_explicit_and_failed_partner_is_not_exported(self):
        missing = ROOT / '.pqc_runs' / ('unit-test-partner-' + self.root.name + '.json')
        self.addCleanup(lambda: missing.unlink(missing_ok=True))
        with patch.dict(export.RECORDS, {('corrected-candidate', '128f'): str(missing)}):
            manifest = export.export_sources('corrected-baseline', '128f', self.root / 'alone')
            self.assertFalse(manifest['source_relationship']['partner_qualified'])
            self.assertIsNone(manifest['source_relationship']['partner_qualification_sha256'])
            self.assertFalse((self.root / 'alone/evidence/partner_qualification.json').exists())
            missing.parent.mkdir(parents=True, exist_ok=True)
            missing.write_text(json.dumps({'status': 'FAIL'}))
            with self.assertRaisesRegex(ValueError, 'qualification'):
                export.export_sources('corrected-baseline', '128f', self.root / 'bad-partner')
            self.assertFalse((self.root / 'bad-partner').exists())

    def test_invalid_explicit_mode_cannot_silently_use_original(self):
        for value in ('', False, 0, [], 'not-a-mode'):
            with patch.object(export.portable, 'run_process') as execute:
                report, code = export.portable.run_check(export.VARIANTS['corrected-baseline'], parameter_set=value)
            self.assertEqual(code, 2)
            self.assertEqual(report['status'], 'ERROR')
            execute.assert_not_called()

    def test_mode_override_changes_only_reviewed_selection(self):
        for variant, parameter in (('corrected-baseline', '192f'), ('corrected-candidate', '128f')):
            copied = self.root / variant
            shutil.copytree(export.VARIANTS[variant], copied)
            before = export.portable.rtl_hashes(copied)
            change = export.portable.select_parameter(copied, parameter)
            after = export.portable.rtl_hashes(copied)
            self.assertEqual({p for p in before if before[p] != after[p]}, {'sphincslet/setting.v'})
            self.assertEqual(change['after_sha256'], after['sphincslet/setting.v'])
            self.assertEqual(export.portable.gate.check_configuration(copied / 'sphincslet/setting.v'), parameter)
            self.assertIsNone(export.portable.select_parameter(copied, parameter))
            with self.assertRaises(ValueError):
                export.portable.select_parameter(copied, 'shake')


if __name__ == '__main__':
    unittest.main()
