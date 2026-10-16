"""Read-only saved-run diagnosis contracts; never execute licensed Vivado."""
import json
import subprocess
import unittest
from unittest.mock import patch

from agent import vivado_qualification as q
from agent.run_safety import hashes
from agent.whole_design import save
from tests import test_vivado_qualification as fixture_module
from tests.test_vivado_qualification import encoded
from tools import diagnose_vivado_reports as diagnostic

IDENTITY = {'tool_version': '2022.2', 'design_name': 'checkpoint_synthesized',
            'top': 'combined_top', 'part': 'xc7a200tfbg676-1'}


class Diagnostics(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module.QualificationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.fixture()
        self.root, self.run = self.fixture.root, self.fixture.run
        objects = self.run / 'objects.tsv'
        objects.write_text(objects.read_text().replace(encoded('meta', 'top', 'combined_top'),
                                                      encoded('meta', 'top', 'design_1')))
        self.bind_producer(diagnostic.LEGACY_NAME_PRODUCER_SHA256)

    def bind_producer(self, producer_sha):
        producer = q.dependencies()[1]
        self.fixture.cfg['immutable_hashes'][producer] = producer_sha
        save(self.fixture.request_file, self.fixture.request)
        request_sha = hashes([self.fixture.request_file])[str(self.fixture.request_file)]
        manifest = q.input_manifest(self.fixture.request, request_sha)
        manifest['producer_hashes'][producer] = producer_sha
        save(self.run / 'input-manifest.json', manifest)
        self.bind_response()

    def bind_response(self):
        save(self.root / 'response.json', {
            'request_sha256': hashes([self.fixture.request_file])[str(self.fixture.request_file)],
            'configuration': self.fixture.cfg, 'source_hashes': self.fixture.request['source_hashes'],
            'executed': True, 'tool_returncode': 0, 'status': 'BLOCKED', 'qualification': None,
            'reports': {name: {'path': 'vivado/' + name,
                              'sha256': hashes([self.run / name])[str(self.run / name)]}
                        for name in q.RAW_REPORTS}})

    def diagnose(self, identity=IDENTITY):
        with patch.object(diagnostic, 'checkpoint_identity', return_value=identity):
            return diagnostic.diagnose(self.root)

    def test_diagnostic_preserves_every_original_byte_and_admission_remains_blocked(self):
        before = hashes(path for path in self.root.rglob('*') if path.is_file())
        with patch.object(q, 'build_qualification', side_effect=AssertionError('Must not build qualification')):
            result = self.diagnose()
        self.assertFalse(result['admission_eligible'])
        self.assertTrue(result['evidence_unchanged_verified'])
        combined = result['checks']['combined_diagnostic_evaluation']
        self.assertEqual(combined['status'], 'PARSED')
        self.assertEqual(combined['summary']['gates']['mapped_memory_semantics'], 'UNVERIFIED')
        self.assertEqual(before, hashes(path for path in self.root.rglob('*') if path.is_file()))
        with self.assertRaisesRegex(ValueError, 'Observed Vivado top differs'):
            q.evaluate(self.run, self.fixture.request)
        self.assertFalse((self.run / 'qualification.json').exists())

    def test_wrong_checkpoint_top_cannot_be_overridden_by_expected_top(self):
        result = self.diagnose({**IDENTITY, 'top': 'wrong'})
        check = result['checks']['combined_diagnostic_evaluation']
        self.assertEqual(check['status'], 'BLOCKED')
        self.assertIn('Checkpoint top differs', check['error'])

    def test_unknown_producer_mismatch_is_not_a_generic_design_name_exemption(self):
        for producer in ('0' * 64, hashes([q.dependencies()[1]])[q.dependencies()[1]]):
            with self.subTest(producer=producer):
                self.bind_producer(producer)
                # Even matching reopened NAME cannot justify a TOP mismatch.
                result = self.diagnose({**IDENTITY, 'design_name': 'design_1'})
                self.assertIn('not from the known legacy NAME producer',
                              result['checks']['combined_diagnostic_evaluation']['error'])

    def test_current_producer_matching_top_needs_no_legacy_interpretation(self):
        objects = self.run / 'objects.tsv'
        objects.write_text(objects.read_text().replace(encoded('meta', 'top', 'design_1'),
                                                      encoded('meta', 'top', 'combined_top')))
        self.bind_producer(hashes([q.dependencies()[1]])[q.dependencies()[1]])
        result = self.diagnose()
        self.assertEqual(result['checks']['combined_diagnostic_evaluation']['status'], 'PARSED')
        self.assertFalse(result['diagnostic_metadata_interpretation']['legacy_name_producer'])

    def test_checkpoint_part_and_tool_must_match(self):
        for key, value in (('part', 'wrong_part'), ('tool_version', '2023.1')):
            with self.subTest(key=key):
                result = self.diagnose({**IDENTITY, key: value})
                self.assertIn('Checkpoint part/tool version differs',
                              result['checks']['combined_diagnostic_evaluation']['error'])

    def test_producer_drift_is_disclosed_without_rebinding_original_manifest(self):
        path = q.dependencies()[1]
        self.fixture.cfg['immutable_hashes'][path] = '0' * 64
        save(self.fixture.request_file, self.fixture.request)
        sha = hashes([self.fixture.request_file])[str(self.fixture.request_file)]
        manifest = q.input_manifest(self.fixture.request, sha)
        manifest['producer_hashes'][path] = '0' * 64
        save(self.run / 'input-manifest.json', manifest)
        self.bind_response()
        before = (self.run / 'input-manifest.json').read_bytes()
        result = self.diagnose()
        self.assertIn(path, result['producer_drift'])
        self.assertEqual(result['original_producer_hashes'][path], '0' * 64)
        self.assertNotEqual(result['diagnostic_parser_hashes'][path], '0' * 64)
        self.assertEqual((self.run / 'input-manifest.json').read_bytes(), before)
        self.assertFalse(result['admission_eligible'])

    def test_original_producer_disagreement_is_rejected(self):
        path = self.run / 'input-manifest.json'
        manifest = json.loads(path.read_text())
        manifest['producer_hashes'][q.dependencies()[1]] = '0' * 64
        save(path, manifest)
        self.bind_response()
        with self.assertRaisesRegex(ValueError, 'Original producer identity disagrees'):
            self.diagnose()

    def test_symlinked_report_directory_is_rejected(self):
        target = self.root / 'saved-vivado'
        self.run.rename(target)
        self.run.symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlinked Vivado report directory'):
            self.diagnose()

    def test_stale_report_is_rejected_against_original_response(self):
        (self.run / 'synthesized.dcp').write_text('changed checkpoint')
        with self.assertRaisesRegex(ValueError, 'Report differs from original saved response: synthesized.dcp'):
            self.diagnose()

    def test_missing_original_response_binding_is_rejected(self):
        (self.root / 'response.json').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing, empty or symlinked evidence'):
            self.diagnose()

    def test_source_changes_are_rejected(self):
        self.fixture.source.write_text('module wrong; endmodule')
        with self.assertRaisesRegex(ValueError, 'Frozen source bytes changed'):
            self.diagnose()

    def test_concurrent_checkpoint_mutation_invalidates_results(self):
        def changed(*args):
            (self.run / 'synthesized.dcp').write_text('changed during diagnosis')
            return IDENTITY
        with patch.object(diagnostic, 'checkpoint_identity', side_effect=changed):
            with self.assertRaisesRegex(ValueError, 'Evidence changed during diagnosis'):
                diagnostic.diagnose(self.root)

    def test_independent_parsers_continue_after_timing_failure(self):
        (self.run / 'timing.rpt').write_text('malformed timing')
        self.bind_response()
        result = self.diagnose()
        self.assertEqual(result['checks']['timing_summary']['status'], 'BLOCKED')
        self.assertEqual(result['checks']['check_timing']['status'], 'PARSED')
        self.assertEqual(result['checks']['critical_paths']['status'], 'PARSED')
        self.assertEqual(result['checks']['combined_diagnostic_evaluation']['status'], 'BLOCKED')

    def test_checkpoint_probe_script_only_reads_and_parses_observed_properties(self):
        def run(argv, **kwargs):
            from pathlib import Path
            script = Path(argv[-1]).read_text()
            self.assertIn('open_checkpoint ', script)
            self.assertIn('get_property TOP [current_design]', script)
            self.assertNotIn('synth_design', script)
            self.assertNotIn('write_checkpoint', script)
            self.assertNotEqual(Path(kwargs['cwd']), self.run)
            stdout = '\n'.join('PQC_DIAG_' + k + ' ' + v.encode().hex() for k, v in IDENTITY.items())
            return subprocess.CompletedProcess(argv, 0, stdout, '')
        with patch.object(diagnostic.subprocess, 'run', side_effect=run):
            self.assertEqual(diagnostic.checkpoint_identity(self.run / 'synthesized.dcp'), IDENTITY)

    def test_missing_or_failed_checkpoint_probe_fails_closed(self):
        for code, stdout in ((0, ''), (1, 'checkpoint failed')):
            with self.subTest(code=code), patch.object(diagnostic.subprocess, 'run',
                    return_value=subprocess.CompletedProcess([], code, stdout, '')):
                with self.assertRaises(ValueError):
                    diagnostic.checkpoint_identity(self.run / 'synthesized.dcp')


if __name__ == '__main__':
    unittest.main()
