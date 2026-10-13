"""Synthetic source/report fixtures only: no API, HDL execution or EDA."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent import proposal_source_context as s
from tools import export_target_profiles as e
from tools import prepare_fpga_proposal as p
from tools import run_fpga_proposal as r


class SourceContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.top = self.root / 'top.v'
        self.top.write_bytes(b'module top;\r\nchild C();\r\nendmodule')
        self.edit = self.root / 'edit.v'
        self.edit.write_text('module child; wire x; endmodule\n')
        self.other = self.root / 'other.v'
        self.other.write_text('module other;\nwire a;\nwire b;\nendmodule\n')
        self.hidden = self.root / 'hidden.v'
        self.hidden.write_text('module hidden; endmodule\n')
        self.sources = [self.other, self.top, self.hidden, self.edit]
        self.report_root = self.root / 'reports'
        self.report_root.mkdir()
        for name in p.REPORTS:
            (self.report_root / name).write_bytes(b'fixture imported report\r\n')
        self.launch = self.root / 'launch-config.json'
        p.save(self.launch, {'tool': 'vivado', 'output_root': str(self.report_root),
                            'part': 'fixture', 'tool_version': 'fixture', 'period_ns': 15})
        self.profile = self.root / 'profile.json'
        self.preparation = self.root / 'preparation.json'
        self.out = self.root / 'proposal'
        self.freeze()

    def freeze(self):
        for name in ('qualification.json', 'manifest.json'):
            (self.root / name).write_text('{}\n')
        def row(path):
            return {'path': path.name, 'sha256': p.sha(path)}
        profile = {'schema_version': 1, 'profile_kind': 'qualified_source_target_preparation',
                   'design': 'mldsa', 'variant': 'guarded-baseline',
                   'target': {'kind': 'fpga', 'memory_macros': [], 'memory_compiler_allowed': False,
                              'memory_implementation': 'fpga_inferred_ram'},
                   'elaboration': {'top': 'top', 'sources': [row(path) for path in self.sources],
                                   'include_files': [], 'data_files': [], 'include_dirs': [],
                                   'parameters': {}, 'defines': [], 'global_include_files': []},
                   'qualification': {'report': row(self.root / 'qualification.json')},
                   'provenance': {'export_manifest': row(self.root / 'manifest.json')},
                   'bundle_files_sha256': {path.name: p.sha(path) for path in
                                          [*self.sources, self.root / 'qualification.json', self.root / 'manifest.json']}}
        profile['profile_fingerprint'] = e.fingerprint(profile)
        p.save(self.profile, profile)
        p.save(self.preparation, {'schema_version': 1, 'status': 'SOURCE_PREPARED_NOT_RUN',
                                 'profile': str(self.profile), 'profile_fingerprint': profile['profile_fingerprint'],
                                 'input_sha256': {str(self.launch): p.sha(self.launch)}})

    def prepare(self, specs=None, editable=None):
        return p.prepare(self.preparation, editable or [self.edit], self.out, specs or [])

    def test_exact_roles_profile_order_and_top_down_instructions(self):
        self.prepare([str(self.top) + ':1:2', str(self.other) + ':2:3'])
        prompt = json.loads((self.out / 'prompt.json').read_text())
        context = json.loads((self.out / 'proposal-context.json').read_text())
        user = prompt['user']
        self.assertEqual(user['allowed_files'], [str(self.edit)])
        self.assertEqual(list(user['rtl']), [str(self.edit)])
        self.assertEqual(user['source_order'], list(map(str, self.sources)))
        self.assertEqual([row['path'] for row in user['design_overview']['ordered_sources']], list(map(str, self.sources)))
        self.assertEqual([row['path'] for row in user['read_only_rtl']], [str(self.top), str(self.other)])
        self.assertEqual(user['design_overview']['top'], 'top')
        self.assertIn('top-level', user['design_overview']['analysis_order'][0])
        self.assertIn('Only allowed_files are editable', prompt['system'])
        self.assertIn('not elaborated hierarchy', user['design_overview']['evidence'])
        self.assertEqual(context['allowed_files'], [str(self.edit)])
        self.assertEqual(context['input_sha256'][str(self.hidden)], p.sha(self.hidden))
        self.assertEqual(context['prompt_payload_bytes'], len((prompt['system'] + json.dumps(user, allow_nan=False)).encode()))
        self.assertLessEqual(context['prompt_payload_bytes'], 192 * 1024)

    def test_exact_crlf_span_hash_and_omissions(self):
        self.prepare([str(self.top) + ':2:3'])
        row = json.loads((self.out / 'prompt.json').read_text())['user']['read_only_rtl'][0]
        expected = b'child C();\r\nendmodule'
        self.assertEqual(row['text'].encode(), expected)
        self.assertEqual(row['text_sha256'], hashlib.sha256(expected).hexdigest())
        self.assertEqual(row['source_sha256'], p.sha(self.top))
        self.assertEqual((row['source_line_count'], row['omitted_before_lines'], row['omitted_after_lines']), (3, 1, 0))
        self.assertEqual(row['coverage'], 'PARTIAL_SOURCE_EXCERPT')

    def test_full_file_is_explicit_and_not_editable(self):
        self.prepare([str(self.top)])
        row = json.loads((self.out / 'prompt.json').read_text())['user']['read_only_rtl'][0]
        self.assertEqual(row['coverage'], 'FULL_SOURCE')
        self.assertEqual(row['source_sha256'], row['text_sha256'])
        self.assertEqual(row['text'].encode(), self.top.read_bytes())
        self.assertEqual(row['role'], 'READ_ONLY_CONTEXT_NOT_EDITABLE')

    def test_partial_large_generated_source_is_bounded(self):
        self.other.write_bytes(b'// omitted generated line\n' * 12000 + b'module other; endmodule\n')
        self.freeze()
        self.prepare([str(self.other) + ':12001:12001'])
        row = json.loads((self.out / 'prompt.json').read_text())['user']['read_only_rtl'][0]
        self.assertGreater(row['source_bytes'], p.LIMIT)
        self.assertEqual(row['omitted_before_lines'], 12000)
        self.assertEqual(row['text'], 'module other; endmodule\n')

    def test_bad_ranges_are_rejected_before_output(self):
        for suffix in (':0:1', ':1:0', ':-1:2', ':2:1', ':1:4', ':01:2', ':1', ':1:2:3', ':a:b', ':1:9999999999'):
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                self.prepare([str(self.top) + suffix])
            self.assertFalse(self.out.exists())

    def test_duplicate_overlapping_and_full_plus_partial_rejected(self):
        for specs in ([str(self.top)] * 2, [str(self.top), str(self.top) + ':2:2'],
                      [str(self.top) + ':1:2', str(self.top) + ':2:3'],
                      [str(self.top) + ':1:1', str(self.top.parent / '.' / self.top.name) + ':1:1']):
            with self.subTest(specs=specs), self.assertRaisesRegex(ValueError, 'overlapping'):
                self.prepare(specs)

    def test_adjacent_disjoint_spans_keep_explicit_order(self):
        self.prepare([str(self.top) + ':2:3', str(self.top) + ':1:1'])
        rows = json.loads((self.out / 'prompt.json').read_text())['user']['read_only_rtl']
        self.assertEqual([row['start_line'] for row in rows], [2, 1])

    def test_editable_context_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError, 'both read-only'):
            self.prepare([str(self.edit) + ':1:1'])

    def test_outside_exact_source_list_rejected(self):
        path = self.root / 'outside.v'
        path.write_text('module outside; endmodule')
        with self.assertRaisesRegex(ValueError, 'outside the exact'):
            self.prepare([str(path)])

    def test_symlink_context_and_editable_rejected(self):
        alias = self.root / 'alias.v'
        alias.symlink_to(self.top)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.prepare([str(alias)])
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.prepare(editable=[alias])

    def test_colon_path_is_explicitly_unsupported(self):
        colon = self.root / 'a:1:2'
        colon.write_text('module other; endmodule')
        with self.assertRaises(ValueError):
            self.prepare([str(colon)])

    def test_literal_colon_filename_cannot_be_confused_with_valid_range(self):
        literal = Path(str(self.top) + ':1:2')
        literal.write_text('module literal; endmodule\n')
        self.sources.append(literal)
        self.freeze()
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            self.prepare([str(literal)])

    def test_too_many_selections_and_source_scan_limit(self):
        with self.assertRaisesRegex(ValueError, '64'):
            self.prepare([str(self.top)] * 65)
        with patch.object(s, 'MAX_SOURCE_BYTES', 5), self.assertRaisesRegex(ValueError, 'scan limit'):
            self.prepare([str(self.top) + ':1:1'])
        with patch.object(s, 'MAX_CONTEXT_SOURCE_BYTES', 5), self.assertRaisesRegex(ValueError, 'scan limit'):
            self.prepare([str(self.top) + ':1:1'])

    def test_empty_and_invalid_utf8_context_rejected(self):
        for raw in (b'', b'bad\xff\n'):
            self.other.write_bytes(raw)
            self.freeze()
            with self.assertRaises(ValueError):
                self.prepare([str(self.other)])

    def test_prompt_limit_rejects_without_truncation_or_output(self):
        (self.report_root / 'timing.rpt').write_text('t' * (p.LIMIT - 1000))
        with self.assertRaisesRegex(ValueError, 'Combined prompt exceeds'):
            self.prepare([str(self.top)])
        self.assertFalse(self.out.exists())

    def test_report_snapshot_hash_matches_prompt_crlf(self):
        self.prepare([str(self.top)])
        user = json.loads((self.out / 'prompt.json').read_text())['user']
        context = json.loads((self.out / 'proposal-context.json').read_text())
        for name in p.REPORTS:
            self.assertEqual(hashlib.sha256(user['reports'][name].encode()).hexdigest(), context['input_sha256'][str(self.report_root / name)])

    def test_report_read_time_drift_rejected(self):
        original = p.read_snapshot
        def read(path, limit=p.LIMIT):
            result = original(path, limit)
            if path.name == 'timing.rpt':
                path.write_text('changed after read')
            return result
        with patch.object(p, 'read_snapshot', side_effect=read), self.assertRaisesRegex(ValueError, 'changed during'):
            self.prepare([str(self.top)])
        self.assertFalse(self.out.exists())

    def test_context_hash_mismatch_after_verified_profile_rejected(self):
        original = p.read_snapshot
        def read(path, limit=p.LIMIT):
            result = original(path, limit)
            if path == self.edit:
                self.top.write_text('transient source change')
            return result
        with patch.object(p, 'read_snapshot', side_effect=read), self.assertRaisesRegex(ValueError, 'source hash differs'):
            self.prepare([str(self.top)])

    def test_unchanged_three_editable_limit_and_legacy_invocation(self):
        with self.assertRaisesRegex(ValueError, 'one to three'):
            self.prepare(editable=self.sources)
        self.prepare()
        self.assertEqual(json.loads((self.out / 'prompt.json').read_text())['user']['read_only_rtl'], [])

    def test_canonical_profile_source_alias_rejected(self):
        profile = json.loads(self.profile.read_text())
        profile['elaboration']['sources'].append({'path': './top.v', 'sha256': p.sha(self.top)})
        profile['bundle_files_sha256']['./top.v'] = p.sha(self.top)
        profile['profile_fingerprint'] = e.fingerprint(profile)
        p.save(self.profile, profile)
        preparation = json.loads(self.preparation.read_text())
        preparation['profile_fingerprint'] = profile['profile_fingerprint']
        p.save(self.preparation, preparation)
        with self.assertRaisesRegex(ValueError, 'Duplicate canonical'):
            self.prepare()

    def test_readonly_edit_refused_and_no_rtl_changes(self):
        before = {path: path.read_bytes() for path in self.sources}
        self.prepare([str(self.top)])
        response = self.root / 'response.json'
        p.save(response, {'status': 'PROPOSED', 'experiment': {'name': 'fixture', 'files': [
            {'path': str(self.top), 'ops': [{'op': 'replace_exact', 'old': 'child C();', 'new': 'child D();', 'expect': 1}]}]}})
        with self.assertRaisesRegex(AssertionError, 'outside the caller'):
            p.review(self.out / 'proposal-context.json', response, self.out / 'review.json')
        self.assertFalse((self.out / 'review.json').exists())
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw)

    def test_editable_crlf_multiline_anchor_matches_existing_preview(self):
        original = b'module child;\r\nwire x;\r\nendmodule\r\n'
        self.edit.write_bytes(original)
        self.freeze()
        self.prepare([str(self.top)])
        user = json.loads((self.out / 'prompt.json').read_text())['user']
        self.assertEqual(user['rtl'][str(self.edit)], original.decode().replace('\r\n', '\n'))
        response = self.root / 'response.json'
        p.save(response, {'status': 'PROPOSED', 'experiment': {'name': 'fixture', 'files': [
            {'path': str(self.edit), 'ops': [{'op': 'replace_exact', 'old': 'wire x;\nendmodule',
                                            'new': 'wire y;\nendmodule', 'expect': 1}]}]}})
        result = p.review(self.out / 'proposal-context.json', response, self.out / 'review.json')
        self.assertEqual(result['status'], 'EDIT_PREVIEW_VALID_NOT_APPLIED')
        self.assertEqual(self.edit.read_bytes(), original)

    def test_outside_span_unselected_source_report_and_prompt_drift_block_review(self):
        self.prepare([str(self.top) + ':1:1'])
        response = self.root / 'response.json'
        p.save(response, {'status': 'STOP'})
        for path in [self.top, self.hidden, self.out / 'prompt.json', *(self.report_root / name for name in p.REPORTS)]:
            original = path.read_bytes()
            path.write_bytes(original + b'\nchanged outside selected span')
            with self.subTest(path=path.name), self.assertRaises(ValueError):
                p.review(self.out / 'proposal-context.json', response, self.out / 'review.json')
            self.assertFalse((self.out / 'review.json').exists())
            path.write_bytes(original)

    def test_source_drift_blocks_before_sdk_or_request_claim(self):
        self.prepare([str(self.top) + ':1:1'])
        self.top.write_bytes(self.top.read_bytes() + b'\nchanged outside span')
        with patch.dict('os.environ', {'PQC_ENABLE_LLM': '1'}), patch.object(r, 'create_client', side_effect=AssertionError('must not call SDK')):
            with self.assertRaisesRegex(ValueError, 'Inputs changed'):
                r.run(self.out / 'proposal-context.json', 'fixture', 1, 1, 1)
        self.assertFalse((self.out / '.proposal-request.lock').exists())

    def test_cli_prepare_is_offline_and_readonly(self):
        result = subprocess.run([sys.executable, str(p.ROOT / 'tools/prepare_fpga_proposal.py'), 'prepare',
                                 '--preparation', str(self.preparation), '--rtl', str(self.edit),
                                 '--context-rtl', str(self.top) + ':1:2', '--out', str(self.out)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['api_calls'], 0)
        self.assertFalse((self.out / 'proposal-run.json').exists())
        self.assertEqual(self.top.read_bytes(), b'module top;\r\nchild C();\r\nendmodule')


if __name__ == '__main__':
    unittest.main()
