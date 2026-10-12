"""Coverage labels for legacy ML-DSA acceptance; no simulator or paid API calls."""
import subprocess
import unittest
from unittest.mock import patch

from agent import chip_orchestrator as chip


class ChipGateCoverageTests(unittest.TestCase):
    def assert_keygen_only(self, record, prefix=''):
        self.assertEqual(record[prefix + 'verification_profile'], 'mldsa_keygen_75')
        coverage = record[prefix + 'verification_coverage']
        self.assertIn('75 total', coverage)
        self.assertIn('Sign and Verify are not checked', coverage)

    def test_both_mldsa_configurations_retain_keygen_gate(self):
        for name in ('mldsa', 'mldsa_baseline'):
            cfg = chip.DESIGNS[name]
            self.assert_keygen_only(cfg)
            self.assertIn('agent/mldsa/full_kat_gate.py', cfg['kat_gate'])
            self.assertNotIn('agent/mldsa/portable_kat_gate.py', cfg['kat_gate'])

    def test_baseline_pass_and_failure_keep_bounded_coverage(self):
        for passed in (True, False):
            for name in ('mldsa', 'mldsa_baseline'):
                record = {}
                result = subprocess.CompletedProcess([], 0, 'GATE: ' + ('PASS' if passed else 'FAIL'))
                with patch.object(chip, 'source_state', return_value={'source': 'hash'}), \
                     patch.object(chip, 'run_process', return_value=result):
                    if passed:
                        chip.verify_baseline(chip.DESIGNS[name], record, 10)
                    else:
                        with self.assertRaisesRegex(RuntimeError, 'correctness gate failed'):
                            chip.verify_baseline(chip.DESIGNS[name], record, 10)
                self.assert_keygen_only(record, 'baseline_')
                self.assertEqual(record['baseline_correctness_status'], 'PASS' if passed else 'FAIL')

    def test_candidate_accept_and_gate_failure_keep_bounded_coverage(self):
        cfg = chip.DESIGNS['mldsa']
        base = {'closing_fmax_mhz': 100, 'closing_period_ns': 10, 'wns_at_close': 0.1}
        post = dict(base, closing_fmax_mhz=101)
        for passed in (True, False):
            record = {}
            responses = [subprocess.CompletedProcess([], 0, '=== ACCEPTED. ==='),
                         subprocess.CompletedProcess([], 0, 'GATE: ' + ('PASS' if passed else 'FAIL'))]
            with patch.object(chip, 'SourceTransaction'), \
                 patch.object(chip, 'run_process', side_effect=responses), \
                 patch.object(chip, 'parse_preliminary', return_value={}), \
                 patch.object(chip, 'source_state', side_effect=[{'old': 'hash'}, *[{'new': 'hash'}] * 3]), \
                 patch.object(chip, 'regen_ckpt') as regen, \
                 patch.object(chip, 'closure_search', return_value=post), \
                 patch.object(chip, 'log_record'), patch.object(chip, 'learn_final_candidate'):
                accepted = chip.evaluate_candidate(cfg, 'agent/mldsa/mldsa_src/usehint.v',
                                                   base, 'coverage-test', record)
            self.assertEqual(accepted, passed)
            self.assert_keygen_only(record)
            self.assertEqual(record['correctness_status'], 'PASS' if passed else 'FAIL')
            if not passed:
                regen.assert_not_called()

    def test_unconfigured_design_is_not_given_mldsa_coverage(self):
        record = {}
        chip.record_verification_coverage({}, record)
        self.assertEqual(record, {})


if __name__ == '__main__':
    unittest.main()
