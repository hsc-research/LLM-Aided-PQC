"""Offline whole-design history tests; no SDK or vendor executable is used."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent'))
import chip_orchestrator as chip
import experiment_history as history
import learned_rules as rules
import run_safety as safety


class FinalOutcomeHistory(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rtl = self.root / 'rtl'
        self.rtl.mkdir()
        self.source = self.rtl / 'a.v'
        self.source.write_text('original')
        self.initial_hashes = safety.hashes([self.source])
        (self.root / 'baseline.dcp').write_text('checkpoint')
        self.journal = self.root / 'history.jsonl'
        self.rule_file = self.root / 'rules.jsonl'
        self.cfg = {'scopes': ['rtl'], 'ckpt': 'baseline.dcp', 'orchestrator': 'offline-fixture',
                    'kat_gate': ['offline-gate'], 'bracket': (5, 9)}
        self.base = {'closing_fmax_mhz': 100, 'closing_period_ns': 10, 'wns_at_close': 0.1}
        self.proposal = {'block': 'a', 'strategy': 'flag_precompute',
                         'edits': [{'old': 'original', 'new': 'candidate'}]}

    def write_event(self, event):
        with self.journal.open('a') as stream:
            stream.write(json.dumps(event) + '\n')

    def exercise(self, *, gain=True, gate=True, corrupt_record=False,
                 failure=None, final_log_failure=False):
        calls, events = [], []
        def run(argv, **kwargs):
            calls.append(argv)
            if len(calls) == 1:
                self.source.write_text('candidate')
                output = io.StringIO()
                with patch.dict(os.environ, kwargs['env']), contextlib.redirect_stdout(output):
                    history.preliminary_record(self.proposal, 'fixture', 'offline-model')
                text = output.getvalue() if not corrupt_record else ''
                return subprocess.CompletedProcess(argv, 0, text + '=== ACCEPTED (filter). ===\n')
            return subprocess.CompletedProcess(argv, 0, 'GATE: ' + ('PASS' if gate else 'FAIL'))
        def log(record):
            events.append(copy.deepcopy(record))
            if final_log_failure and record.get('history_state') == 'finally_accepted':
                raise OSError('disk full after retain')
            self.write_event(record)
        def learn_after_transaction(record):
            self.assertFalse(any((self.root / '.pqc_runs/transactions').iterdir()))
        record = {'design': 'fixture'}
        after = dict(self.base, closing_fmax_mhz=101 if gain else 99)
        with patch.object(chip, 'REPO', self.root), patch.object(chip, 'run_process', run), \
             patch.object(chip, 'source_state', lambda cfg: safety.hashes([self.source])), \
             patch.object(chip, 'regen_ckpt', side_effect=failure), \
             patch.object(chip, 'closure_search', return_value=after), \
             patch.object(chip, 'log_record', side_effect=log), \
             patch.object(chip, 'learn_final_candidate', side_effect=learn_after_transaction) as learn:
            self.last_learn = learn
            accepted = chip.evaluate_candidate(self.cfg, 'rtl/a.v', self.base, 'candidate-1', record)
        if not accepted:
            self.write_event(record)  # The main driver records rejected outcomes.
        return accepted, record, events, learn

    def test_chip_rejection_restores_and_never_learns_local_win(self):
        accepted, record, _, learn = self.exercise(gain=False)
        self.assertFalse(accepted)
        self.assertEqual(self.source.read_text(), 'original')
        self.assertEqual(record['proposal']['verdict'], 'BLOCK_FILTER_PASS')
        self.assertEqual(record['history_state'], 'chip_rejected')
        self.assertEqual(history.applied_proposals('fixture', 'a', self.journal), [])
        self.assertIn('REJECT_PPA', history.history_prompt('fixture', 'a', self.journal))
        learn.assert_not_called()

    def test_gate_failure_never_learns_local_win(self):
        accepted, record, _, learn = self.exercise(gate=False)
        self.assertFalse(accepted)
        self.assertEqual(record['correctness_status'], 'FAIL')
        self.assertFalse(history.is_final_acceptance(record))
        self.assertEqual(self.source.read_text(), 'original')
        learn.assert_not_called()

    def test_final_acceptance_has_two_distinct_states_and_source_evidence(self):
        accepted, record, events, learn = self.exercise()
        self.assertTrue(accepted)
        self.assertEqual([e['history_state'] for e in events], ['accept_pending', 'finally_accepted'])
        self.assertFalse(history.is_final_acceptance(events[0]))
        self.assertTrue(history.is_final_acceptance(events[1]))
        self.assertEqual(record['baseline_sources'], self.initial_hashes)
        self.assertNotEqual(record['baseline_sources'], record['candidate_sources'])
        self.assertEqual(len(history.applied_proposals('fixture', 'a', self.journal)), 1)
        learn.assert_called_once_with(record)
        self.assertFalse(any((self.root / '.pqc_runs/transactions').iterdir()))

    def test_later_source_change_invalidates_applied_claim(self):
        self.exercise()
        self.source.write_text('different current source')
        self.assertEqual(history.applied_proposals('fixture', 'a', self.journal), [])
        self.assertIn('"currently_applied": false', history.history_prompt('fixture', 'a', self.journal))

    def test_final_log_failure_restores_without_qualifying_history_or_learning(self):
        with self.assertRaisesRegex(OSError, 'disk full after retain'):
            self.exercise(final_log_failure=True)
        self.assertEqual(self.source.read_text(), 'original')
        self.assertEqual(history.applied_proposals('fixture', 'a', self.journal), [])
        self.last_learn.assert_not_called()

    def test_missing_preliminary_record_restores_and_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'structured block-filter'):
            self.exercise(corrupt_record=True)
        self.assertEqual(self.source.read_text(), 'original')
        self.assertEqual(history.latest_records(self.journal), [])

    def test_synthesis_exception_cannot_create_final_acceptance(self):
        with self.assertRaisesRegex(RuntimeError, 'synth failed'):
            self.exercise(failure=RuntimeError('synth failed'))
        self.assertEqual(self.source.read_text(), 'original')
        self.assertEqual(history.applied_proposals('fixture', 'a', self.journal), [])

    def test_preliminary_or_legacy_records_cannot_distill_or_append_rules(self):
        client = Mock()
        for record in ({'verdict': 'ACCEPTED'},
                       {'verdict': 'BLOCK_FILTER_PASS', 'evidence_stage': 'block_filter'}):
            with self.assertRaises(ValueError):
                rules.distill_rule(client, 'offline-model', record, 'fixture')
            with self.assertRaises(ValueError):
                rules.append_rule('Never qualify a local win.', record, 'fixture', 'offline-model')
        client.messages.create.assert_not_called()

    def test_only_final_backed_rules_are_injected(self):
        _, record, _, _ = self.exercise()
        self.rule_file.write_text(json.dumps({'design': 'fixture', 'rule': 'legacy local win'}) + '\n')
        with patch.object(rules, 'RULES', str(self.rule_file)), \
             patch.object(history, 'HISTORY', self.journal):
            rules.append_rule('Qualified full-chip rule.', record, 'fixture', 'offline-model')
            text = rules.rules_prompt_block('fixture')
            self.assertIn('Qualified full-chip rule.', text)
            self.assertNotIn('legacy local win', text)
            self.write_event(dict(record, history_state='chip_rejected', verdict='REJECT_PPA'))
            self.assertEqual(rules.rules_prompt_block('fixture'), '')

    def test_legacy_success_is_not_assumed_currently_applied(self):
        self.write_event({'block': 'a', 'design': 'fixture', 'verdict': 'ACCEPTED',
                          'strategy': 'flag_precompute', 'edits': self.proposal['edits']})
        self.assertEqual(history.applied_proposals('fixture', 'a', self.journal), [])

    def test_mismatched_or_duplicate_preliminary_records_are_rejected(self):
        record = dict(self.proposal, candidate_id='other', verdict='BLOCK_FILTER_PASS',
                      evidence_stage='block_filter')
        line = history.FILTER_MARKER + json.dumps(record)
        with self.assertRaisesRegex(ValueError, 'mismatched'):
            history.parse_preliminary(line, 'candidate-1')
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            history.parse_preliminary(line + '\n' + line, 'other')

    def test_malformed_source_evidence_is_not_an_applied_claim(self):
        for invalid in ({}, {'sources': None}, {'sources': {'a': None}}, {'includes': []}):
            self.assertFalse(history.sources_match(invalid))

    def baseline_main(self, *, gate=True, mutate_at=None):
        calls, records = [], []
        def process(argv, **kwargs):
            calls.append('gate')
            if mutate_at == 'gate':
                self.source.write_text('changed during baseline verification')
            return subprocess.CompletedProcess(argv, 0, 'GATE: ' + ('PASS' if gate else 'FAIL'))
        def synth(cfg):
            calls.append('synthesis')
            if mutate_at == 'synthesis':
                self.source.write_text('changed during baseline synthesis')
        def measure(*args):
            calls.append('measurement')
            if mutate_at == 'measurement':
                self.source.write_text('changed during baseline measurement')
            return self.base
        cfg = dict(self.cfg, hier2file={})
        with patch.object(chip, 'REPO', self.root), patch.object(chip.os, 'chdir'), \
             patch.object(chip, 'DESIGNS', {'fixture': cfg}), \
             patch.object(chip, 'source_state', lambda cfg: safety.hashes([self.source])), \
             patch.object(chip, 'run_process', side_effect=process), \
             patch.object(chip, 'regen_ckpt', side_effect=synth), \
             patch.object(chip, 'closure_search', side_effect=measure), \
             patch.object(chip, 'worst_path_at_close', return_value={'source': 'a/C', 'dest': 'b/D'}), \
             patch.object(chip, 'evaluate_candidate') as dispatch, \
             patch.object(chip, 'log_record', side_effect=lambda r: records.append(copy.deepcopy(r))):
            code = chip.main(['fixture', '--dispatch'])
        return code, calls, records, dispatch

    def test_baseline_correctness_precedes_synthesis_and_measurement(self):
        code, calls, records, dispatch = self.baseline_main()
        self.assertEqual(code, 0)
        self.assertEqual(calls, ['gate', 'synthesis', 'measurement'])
        self.assertEqual(records[-1]['baseline_correctness_status'], 'PASS')
        self.assertEqual(records[-1]['baseline_sources'], self.initial_hashes)
        dispatch.assert_not_called()  # The fixture intentionally has no target mapping.

    def test_failed_baseline_prevents_measurement_and_dispatch(self):
        code, calls, records, dispatch = self.baseline_main(gate=False)
        self.assertEqual(code, 1)
        self.assertEqual(calls, ['gate'])
        self.assertEqual(records[-1]['baseline_correctness_status'], 'FAIL')
        dispatch.assert_not_called()

    def test_baseline_gate_source_change_prevents_measurement_and_dispatch(self):
        code, calls, records, dispatch = self.baseline_main(mutate_at='gate')
        self.assertEqual(code, 1)
        self.assertEqual(calls, ['gate'])
        self.assertEqual(records[-1]['baseline_correctness_status'], 'SOURCE_CHANGED')
        dispatch.assert_not_called()
        self.assertEqual(safety.hashes([self.source]), self.initial_hashes)

    def test_baseline_synthesis_source_change_prevents_measurement(self):
        code, calls, records, dispatch = self.baseline_main(mutate_at='synthesis')
        self.assertEqual(code, 1)
        self.assertEqual(calls, ['gate', 'synthesis'])
        self.assertIn('during synthesis', records[-1]['reason'])
        dispatch.assert_not_called()
        self.assertEqual(safety.hashes([self.source]), self.initial_hashes)

    def test_baseline_measurement_source_change_prevents_dispatch(self):
        code, calls, records, dispatch = self.baseline_main(mutate_at='measurement')
        self.assertEqual(code, 1)
        self.assertEqual(calls, ['gate', 'synthesis', 'measurement'])
        self.assertIn('during implementation', records[-1]['reason'])
        dispatch.assert_not_called()
        self.assertEqual(safety.hashes([self.source]), self.initial_hashes)

    def test_hqc_baseline_gate_selects_pristine_manifest(self):
        argv = chip.DESIGNS['hqc_baseline']['kat_gate']
        self.assertEqual(argv[argv.index('--source-key') + 1], 'hqc_joint_pristine')
        self.assertIn('--all', argv)

    def test_baseline_without_correctness_gate_fails_closed(self):
        with patch.object(chip, 'run_process') as run:
            with self.assertRaisesRegex(RuntimeError, 'No correctness gate'):
                chip.verify_baseline({}, {}, 10)
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
