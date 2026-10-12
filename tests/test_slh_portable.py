"""Unit checks for the explicit portability harness; these are not RTL runs."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import check_slh_portable as portable

DONE = 'sig gen done\nsig verification done\nSLH_VERIFY_FLAG=0\nThe signature is matched!\n'
REJECTED = ('sig gen done\n' + portable.TAMPER_MARKER + '\nsig verification done\n'
            'SLH_VERIFY_FLAG=1\nThe signature is not matched!\n')


class PortableSLH(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rtl = self.root / 'rtl'
        shutil.copytree(portable.gate.HERE / 'pristine', self.rtl)
        self.produced = self.root / 'signature.hex'
        self.expected = portable.gate.load_reference('128f')[1]
        self.produced.write_bytes(self.expected)

    def check(self, *, text=DONE, code=0, tamper=False):
        return portable.check_case(self.expected, self.produced, text, code, '128f', tamper)

    def test_only_three_reviewed_files_change(self):
        before = portable.rtl_hashes(self.rtl)
        changes = portable.portability_variant(self.rtl)
        after = portable.rtl_hashes(self.rtl)
        self.assertEqual({p for p in before if before[p] != after[p]}, set(portable.PORTABILITY_INPUTS))
        self.assertEqual({c['path'] for c in changes}, set(portable.PORTABILITY_INPUTS))
        tb = (self.rtl / 'sphincslet/tb.v').read_text()
        self.assertEqual(tb.count('portability_fscanf_result = $fscanf('), 23)
        self.assertEqual(tb.count('SIG_MEM.mem[0] = SIG_MEM.mem[0] ^ 64\'h1;'), 1)
        self.assertIn('$test$plusargs("SLH_TAMPER")', tb)
        self.assertIn('SLH_VERIFY_FLAG=%b', tb)
        self.assertEqual(portable.gate.check_configuration(self.rtl / 'sphincslet/setting.v'), '128f')

    def test_unreviewed_portability_input_fails_closed(self):
        for name in portable.PORTABILITY_INPUTS:
            original = (self.rtl / name).read_bytes()
            (self.rtl / name).write_bytes(original + b'\n')
            with self.assertRaisesRegex(ValueError, 'differs from reviewed'):
                portable.portability_variant(self.rtl)
            shutil.rmtree(self.rtl)
            shutil.copytree(portable.gate.HERE / 'pristine', self.rtl)

    def test_pristine_and_candidate_unchanged_by_transform(self):
        for path in (portable.gate.HERE / 'pristine', portable.gate.DEFAULT_RTL):
            before = portable.rtl_hashes(path)
            copy = self.root / path.name
            shutil.copytree(path, copy)
            portable.portability_variant(copy)
            self.assertEqual(portable.rtl_hashes(path), before)

    def test_optional_auth_sensitivity_fix_is_exact_and_pinned(self):
        path = self.rtl / 'sphincslet/fsm/XMSS_FSM.v'
        before = path.read_text()
        change = portable.auth_sensitivity_variant(self.rtl)
        self.assertEqual(path.read_text(), before.replace('always@(h_cnt2) begin',
                                                        'always@(h_cnt2, leaf_idx) begin'))
        self.assertEqual(change['before_sha256'], hashlib.sha256(before.encode()).hexdigest())
        with self.assertRaisesRegex(ValueError, 'differs from reviewed'):
            portable.auth_sensitivity_variant(self.rtl)

    def test_good_baseline_and_real_rejection_contracts(self):
        self.assertEqual(self.check()['status'], 'PASS')
        negative = self.check(text=REJECTED, tamper=True)
        self.assertEqual(negative['status'], 'PASS')
        self.assertEqual(negative['gate_result']['status'], 'FAIL')
        self.assertTrue(negative['full_vendor_dump_matches'])

    def test_negative_rejection_cannot_qualify_a_failed_baseline(self):
        baseline = self.check(text=DONE.replace('SLH_VERIFY_FLAG=0', 'SLH_VERIFY_FLAG=1'))
        negative = self.check(text=REJECTED, tamper=True)
        cases = portable.qualify_cases([baseline, negative])
        self.assertEqual(cases[0]['status'], 'FAIL')
        self.assertEqual(cases[1]['status'], 'UNQUALIFIED')
        self.assertTrue(cases[1]['observed_rejection'])
        self.assertFalse(cases[1]['negative_control_qualified'])
        self.assertEqual(portable.qualify_cases(cases)[1]['status'], 'UNQUALIFIED')
        cases = portable.qualify_cases([self.check(), self.check(text=REJECTED, tamper=True)])
        self.assertEqual(cases[1]['status'], 'PASS')
        self.assertTrue(cases[1]['negative_control_qualified'])

    def test_unknown_missing_or_wrong_verification_flag_fails(self):
        for bad in ('x', 'X', 'z', 'Z', '1', ''):
            self.assertEqual(self.check(text=DONE.replace('SLH_VERIFY_FLAG=0', 'SLH_VERIFY_FLAG=' + bad))['status'], 'FAIL')
        self.assertEqual(self.check(text=DONE + 'SLH_VERIFY_FLAG=0\n')['status'], 'FAIL')

    def test_negative_control_needs_all_signals_and_exact_generated_dump(self):
        for output in (DONE, REJECTED.replace(portable.TAMPER_MARKER, ''),
                       REJECTED.replace('SLH_VERIFY_FLAG=1', 'SLH_VERIFY_FLAG=x'),
                       REJECTED.replace('sig verification done', ''),
                       REJECTED + 'ERROR: stopped\n', REJECTED + 'The signature is matched!\n'):
            self.assertEqual(self.check(text=output, tamper=True)['status'], 'FAIL')
        self.assertEqual(self.check(text=REJECTED, code=1, tamper=True)['status'], 'FAIL')
        self.produced.write_bytes(b'0' + self.expected[1:])
        self.assertEqual(self.check(text=REJECTED, tamper=True)['status'], 'FAIL')
        self.produced.unlink()
        self.assertEqual(self.check(text=REJECTED, tamper=True)['status'], 'FAIL')

    def test_baseline_cannot_accept_tamper_marker_or_incomplete_signature(self):
        self.assertEqual(self.check(text=DONE + portable.TAMPER_MARKER)['status'], 'FAIL')
        self.produced.write_bytes(self.expected[:-1])
        self.assertEqual(self.check()['status'], 'FAIL')
        self.produced.unlink()
        self.assertEqual(self.check()['status'], 'FAIL')

    def test_missing_tools_are_not_pass(self):
        with patch.object(portable.shutil, 'which', return_value=None):
            result, code = portable.run_check(self.rtl)
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'UNAVAILABLE')

    def test_simulator_timeout_returns_nonzero_error(self):
        def fake_run(argv, **kwargs):
            if '-g2005' in argv:
                Path(argv[argv.index('-o') + 1]).write_bytes(b'unit-test executable stub')
                return subprocess.CompletedProcess(argv, 0, '')
            raise subprocess.TimeoutExpired(argv, 0.01)
        with patch.object(portable.shutil, 'which', side_effect=lambda name: name), \
             patch.object(portable.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'test version', '')), \
             patch.object(portable, 'run_process', side_effect=fake_run), \
             patch.dict(portable.os.environ, {'PQC_RUN_DIR': str(self.root / 'runs')}):
            result, code = portable.run_check(self.rtl, timeout=0.01)
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'ERROR')
        self.assertEqual(result['stage'], 'simulation')
        self.assertTrue(result['tracked_sources_unchanged'])
        self.assertEqual(result['selected_rtl_root'], str(self.rtl))

    def test_timeout_and_jobs_are_validated_before_execution(self):
        for timeout in (0, -1, float('inf'), float('nan'), True):
            with patch.object(portable, 'run_process') as run:
                result, code = portable.run_check(self.rtl, timeout=timeout)
            self.assertEqual(code, 2)
            run.assert_not_called()
        self.assertEqual(portable.run_check(self.rtl, jobs=3)[1], 2)


if __name__ == '__main__':
    unittest.main()
