"""License-free fail-closed regressions for cryptographic correctness gates.

These tests validate harness behavior with mocked simulator outcomes. They do
not constitute RTL KAT execution or replace FPGA/ASIC tool validation.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent'))
from hqc import kat_gate as hqc
from hqc import joint_kat_gate as joint
from mldsa import full_kat_gate as mldsa
from mldsa import timing_equiv_gate as timing
from slh_dsa import slh_kat_gate as slh


def completed_log(count=25):
    return '\n'.join(f'ML-DSA-{level}.KeyGen, KAT #{index} completed in {100 + index} clock cycles'
                     for level in mldsa.LEVELS for index in range(count)) + '\nML-DSA.KeyGen testbench done.\n'


class TemporaryGateTree(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.environment = patch.dict(os.environ, {'PQC_RUN_DIR': str(self.root / 'runs')})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()


class HQCSecrets(TemporaryGateTree):
    def compare(self, left, right):
        enc, dec = self.root / 'enc', self.root / 'dec'
        enc.write_text(left)
        dec.write_text(right)
        return hqc.compare_secrets(enc, dec)

    def test_empty_outputs_fail(self):
        for invalid in ('', '\n  ', '0', 'a' * 127, 'a' * 129, 'x' * 128, 'z' * 128):
            with self.subTest(invalid=invalid):
                self.assertEqual(self.compare(invalid, invalid), 'INVALID')

    def test_valid_secrets_match(self):
        self.assertEqual(self.compare('a' * 128 + '\n', 'A' * 128), 'MATCH')

    def test_mismatched_secrets_fail(self):
        self.assertEqual(self.compare('a' * 128, 'b' * 128), 'MISMATCH')

    def test_missing_secret_fails(self):
        self.assertEqual(hqc.compare_secrets(self.root / 'missing', self.root / 'other'), 'MISSING')

    def test_missing_or_invalid_stimulus_fails(self):
        source, dest = self.root / 'input', self.root / 'output'
        source.mkdir()
        with self.assertRaises(FileNotFoundError):
            hqc.copy_inputs(source, dest, ('s',), ('128',))
        for invalid in ('', 'x', '012'):
            (source / 's_128.in').write_text(invalid)
            with self.assertRaises(ValueError):
                hqc.copy_inputs(source, dest, ('s',), ('128',))

    def build(self):
        for operation in ('keygen', 'encap', 'decap'):
            folder = self.root / 'build' / operation / 'tb'
            folder.mkdir(parents=True)
            (folder / f'{operation}.tcl').write_text('test fixture')
            (folder.parent / 'candidate.v').write_text('uncommitted candidate')

    def simulator(self, empty_secret=False, invalid_stimulus=False):
        def run(script, stage, work):
            folder = work / {'keygen': hqc.KEYGEN_SIM, 'encap': hqc.ENCAP_SIM, 'decap': hqc.DECAP_SIM}[stage]
            folder.mkdir(parents=True)
            for level in hqc.PARAM_SETS:
                for kind in ('s', 'h', 'x', 'y', 'u', 'v', 'd'):
                    (folder / f'{kind}_{level}.in').write_text('' if invalid_stimulus else '0101\n')
                (folder / f'ss_output_{level}.out').write_text('' if empty_secret else 'a' * 128)
            return True, ''
        return run

    def test_run_snapshots_candidate_and_preserves_old_artifacts(self):
        self.build()
        old = self.root / hqc.ENCAP_SIM / 'ss_output_128.out'
        old.parent.mkdir(parents=True)
        old.write_text('old scientific evidence')
        with patch.object(hqc, '_run_tcl', side_effect=self.simulator()):
            first = hqc.run_kat(self.root)
            second = hqc.run_kat(self.root)
        self.assertEqual(first['status'], 'PASS')
        self.assertNotEqual(first['run_dir'], second['run_dir'])
        self.assertEqual(old.read_text(), 'old scientific evidence')
        self.assertEqual((Path(first['run_dir']) / 'build/decap/candidate.v').read_text(), 'uncommitted candidate')

    def test_candidate_change_during_run_is_rejected(self):
        self.build()
        simulator = self.simulator()
        def mutate(script, stage, work):
            result = simulator(script, stage, work)
            if stage == 'decap':
                (self.root / 'build/decap/candidate.v').write_text('different candidate')
            return result
        with patch.object(hqc, '_run_tcl', side_effect=mutate):
            outcome = hqc.run_kat(self.root)
        self.assertEqual(outcome['status'], 'FAIL')
        self.assertIn('changed during verification', outcome['reason'])

    def test_binary_memory_comments_are_accepted_but_not_empty_comments(self):
        source = self.root / 'stimuli'
        source.mkdir()
        path = source / 's_128.in'
        path.write_text('// memory data\n@0000 0101\n/* comment */ 1010\n')
        hqc.copy_inputs(source, self.root / 'copied', ('s',), ('128',))
        path.write_text('// no actual data\n@0000\n')
        with self.assertRaises(ValueError):
            hqc.copy_inputs(source, self.root / 'copied', ('s',), ('128',))

    def test_run_rejects_empty_secret_even_with_successful_simulator(self):
        self.build()
        with patch.object(hqc, '_run_tcl', side_effect=self.simulator(empty_secret=True)):
            self.assertEqual(hqc.run_kat(self.root)['status'], 'FAIL')

    def test_run_stops_on_incomplete_generated_stimuli(self):
        self.build()
        with patch.object(hqc, '_run_tcl', side_effect=self.simulator(invalid_stimulus=True)) as simulate:
            result = hqc.run_kat(self.root)
        self.assertEqual(result['status'], 'FAIL')
        self.assertEqual(simulate.call_count, 1)

    def test_vivado_error_text_and_nonzero_exit_fail(self):
        for ok, output in ((False, 'PASS'), (True, 'ERROR: failed'), (True, 'FATAL: failed')):
            with patch.object(hqc, 'run_command', return_value=(ok, output)):
                self.assertFalse(hqc._run_tcl('test.tcl', 'test', self.root)[0])


class MLDSAResults(unittest.TestCase):
    def evaluate(self, text=None, code=0, count=25):
        return mldsa.evaluate_simulation(completed_log(count) if text is None else text, code, count)[0]

    def test_complete_security_level_coverage_passes(self):
        outcome, records = mldsa.evaluate_simulation(completed_log(), 0, 25)
        self.assertEqual(outcome['status'], 'PASS')
        self.assertEqual(len(records), 75)
        self.assertEqual(outcome['kats_completed'], 75)

    def test_archived_trace_has_75_distinct_vectors(self):
        text = (ROOT / 'agent/mldsa/fullkat_run.log').read_text()
        self.assertEqual(self.evaluate(text)['status'], 'PASS')
        self.assertEqual(len(mldsa.parse_per_vector(text)), 75)

    def test_nonzero_exit_never_passes(self):
        self.assertEqual(self.evaluate(code=1)['status'], 'FAIL')

    def test_done_marker_alone_fails(self):
        self.assertEqual(self.evaluate('testbench done')['status'], 'FAIL')

    def test_missing_vector_or_security_level_fails(self):
        lines = completed_log().splitlines()
        for text in ('\n'.join(lines[1:]), '\n'.join(line for line in lines if 'ML-DSA-V.' not in line)):
            self.assertEqual(self.evaluate(text)['status'], 'FAIL')

    def test_repeated_vector_completion_fails(self):
        text = completed_log() + completed_log().splitlines()[0]
        self.assertEqual(self.evaluate(text)['status'], 'FAIL')

    def test_incomplete_or_malformed_cycles_fail(self):
        for replacement in ('KAT #0 started', 'KAT #0 completed in 0 clock cycles', 'KAT #0 completed in x clock cycles'):
            text = completed_log().replace('KAT #0 completed in 100 clock cycles', replacement, 1)
            self.assertEqual(self.evaluate(text)['status'], 'FAIL')

    def test_wrong_and_error_lines_fail(self):
        for error in ('WRONG before any vector', 'ERROR: xsim failed', 'FATAL: xsim failed'):
            self.assertEqual(self.evaluate(error + '\n' + completed_log())['status'], 'FAIL')

    def test_missing_done_or_timeout_fails(self):
        self.assertEqual(self.evaluate(completed_log().replace('testbench done', 'stopped'))['status'], 'FAIL')
        self.assertEqual(mldsa.evaluate_simulation(completed_log(), 0, 25, timed_out=True)[0]['status'], 'FAIL')

    def test_subset_requires_three_times_requested_count(self):
        self.assertEqual(self.evaluate(count=2)['kats_expected'], 6)
        self.assertEqual(self.evaluate(completed_log(1), count=2)['status'], 'FAIL')


class MLDSARuns(TemporaryGateTree):
    def setUp(self):
        super().setUp()
        self.vendor = self.root / 'vendor'
        for directory in ('ref_combined/src', 'ref_combined/src_tb', 'common', 'KAT'):
            (self.vendor / directory).mkdir(parents=True)
        (self.vendor / 'ref_combined/src/top.v').write_text('module top; endmodule\n')
        (self.vendor / 'ref_combined/src_tb/tb_keygen_top.v').write_text('localparam  NUM_TV = 25;\n')

    def tool(self, argv, **kwargs):
        output = completed_log() if argv[0] == 'xsim' else ''
        Path(kwargs['log_path']).write_text(output)
        return subprocess.CompletedProcess(argv, 0, output)

    def test_runs_write_unique_artifacts_and_do_not_touch_archive(self):
        archive = ROOT / 'agent/mldsa/fullkat_run.log'
        original = archive.read_bytes()
        with patch.object(mldsa, 'run_process', side_effect=self.tool):
            first = mldsa.run_full_kat(root=self.vendor)
            second = mldsa.run_full_kat(root=self.vendor)
        self.assertEqual(first['status'], 'PASS', first)
        self.assertNotEqual(first['run_dir'], second['run_dir'])
        self.assertEqual(len(json.loads(Path(first['per_vector_file']).read_text())), 75)
        self.assertEqual(archive.read_bytes(), original)

    def test_simulator_nonzero_rc_with_complete_log_fails(self):
        def tool(argv, **kwargs):
            result = self.tool(argv, **kwargs)
            if argv[0] == 'xsim':
                result.returncode = 9
            return result
        with patch.object(mldsa, 'run_process', side_effect=tool):
            self.assertEqual(mldsa.run_full_kat(root=self.vendor)['status'], 'FAIL')

    def test_timeout_with_complete_log_fails(self):
        def tool(argv, **kwargs):
            result = self.tool(argv, **kwargs)
            if argv[0] == 'xsim':
                raise subprocess.TimeoutExpired(argv, 1)
            return result
        with patch.object(mldsa, 'run_process', side_effect=tool):
            self.assertEqual(mldsa.run_full_kat(root=self.vendor)['status'], 'FAIL')

    def test_invalid_arguments_never_launch_tools(self):
        with patch.object(mldsa, 'run_process') as tool:
            for count in (0, -1, 26, True, 1.2):
                self.assertEqual(mldsa.run_full_kat(vectors=count)['status'], 'FAIL')
            for timeout in (0, -1, True, float('inf'), float('nan')):
                self.assertEqual(mldsa.run_full_kat(timeout=timeout)['status'], 'FAIL')
        tool.assert_not_called()

    def test_missing_or_unknown_override_fails(self):
        override = self.root / 'override'
        override.mkdir()
        (override / 'misspelled.v').write_text('candidate')
        with patch.object(mldsa, 'run_process') as tool:
            for path in (override, self.root / 'missing'):
                self.assertEqual(mldsa.run_full_kat(path, root=self.vendor)['status'], 'FAIL')
        tool.assert_not_called()

    def test_lowered_testbench_vector_capacity_fails(self):
        (self.vendor / 'ref_combined/src_tb/tb_keygen_top.v').write_text('localparam NUM_TV = 0;')
        with patch.object(mldsa, 'run_process') as tool:
            self.assertEqual(mldsa.run_full_kat(root=self.vendor)['status'], 'FAIL')
        tool.assert_not_called()

    def test_failed_cli_exits_nonzero(self):
        result = subprocess.run([sys.executable, str(ROOT / 'agent/mldsa/full_kat_gate.py'), '--vectors', '0'],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['status'], 'FAIL')


class SLHSignatures(TemporaryGateTree):
    def setUp(self):
        super().setUp()
        self.golden = self.root / 'golden.hex'
        self.produced = self.root / 'produced.hex'
        self.golden.write_text('aabbccdd\n')
        self.produced.write_text('aabbccdd\n')

    def check(self, code=0, output='The signature is matched'):
        return slh.check_signature(self.golden, self.produced, output, code)

    def test_successful_signature_check(self):
        self.assertEqual(self.check()['status'], 'PASS')

    def test_nonzero_simulator_exit_overrides_success_text(self):
        self.assertEqual(self.check(code=1)['status'], 'FAIL')

    def test_empty_matching_signatures_fail(self):
        self.golden.write_text(' \n')
        self.produced.write_text(' \n')
        self.assertEqual(self.check()['status'], 'FAIL')

    def test_missing_mismatched_and_contradictory_outputs_fail(self):
        self.assertEqual(self.check(output='The signature is matched\nThe signature is not matched')['status'], 'FAIL')
        self.assertEqual(self.check(output='ERROR: tool failed\nThe signature is matched')['status'], 'FAIL')
        self.assertEqual(self.check(output='stopped')['status'], 'FAIL')
        self.produced.write_text('different')
        self.assertEqual(self.check()['status'], 'FAIL')
        self.produced.unlink()
        self.assertEqual(self.check()['status'], 'FAIL')

    def test_unsupported_configuration_is_explicit(self):
        setting = self.root / 'setting.v'
        for text in ('`define PARAM_192F\n', '`define PARAM_128F\n`define SHAKE\n', '`define PARAM_128F\n`define PARAM_128S\n'):
            setting.write_text(text)
            with self.assertRaisesRegex(ValueError, 'supports SHA2 PARAM_128F only'):
                slh.check_configuration(setting)
        setting.write_text('// `define SHAKE\n// `define PARAM_192F\n`define PARAM_128F\n')
        slh.check_configuration(setting)

    def fixture(self):
        rtl = self.root / 'rtl'
        for name in ('imports/global_include/clog2.v', 'imports/fifo.v', 'sphincslet/tb.v', 'sphincslet/setting.v'):
            path = rtl / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('`define PARAM_128F\n' if path.name == 'setting.v' else '// fixture\n')
        data = rtl / 'imports/data_sha2'
        data.mkdir()
        (data / 'SIG_file0_128f_w.hex').write_text('old evidence must survive')
        self.golden.with_suffix('.sha256').write_text(hashlib.sha256(self.golden.read_bytes()).hexdigest())
        return rtl

    def tool(self, argv, **kwargs):
        output = ''
        if argv[0] == 'xsim':
            output = 'The signature is matched'
            data = Path(kwargs['cwd']).parents[3] / 'TECS_v8.srcs/sources_1/imports/data_sha2'
            (data / 'SIG_file0_128f_w.hex').write_bytes(self.golden.read_bytes())
        Path(kwargs['log_path']).write_text(output)
        return subprocess.CompletedProcess(argv, 0, output)

    def test_run_isolated_and_preserves_external_signature(self):
        rtl = self.fixture()
        with patch.object(slh, 'DEFAULT_RTL', rtl), patch.object(slh, 'GOLDEN', self.golden), \
             patch.object(slh, 'run_process', side_effect=self.tool):
            result = slh.run_equiv(rtl)
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual((rtl / 'imports/data_sha2/SIG_file0_128f_w.hex').read_text(), 'old evidence must survive')

    def test_run_rejects_process_failure_and_timeout(self):
        rtl = self.fixture()
        for failure in (subprocess.CompletedProcess([], 1, 'The signature is matched'), subprocess.TimeoutExpired('xsim', 1)):
            with patch.object(slh, 'DEFAULT_RTL', rtl), patch.object(slh, 'GOLDEN', self.golden), \
                 patch.object(slh, 'run_process', side_effect=failure if isinstance(failure, Exception) else None,
                              return_value=failure):
                self.assertEqual(slh.run_equiv(rtl)['status'], 'FAIL')

    def test_corrupted_golden_checksum_blocks_before_simulation(self):
        rtl = self.fixture()
        self.golden.write_text('corrupted')
        with patch.object(slh, 'GOLDEN', self.golden), patch.object(slh, 'run_process') as tool:
            self.assertEqual(slh.run_equiv(rtl)['status'], 'ERROR')
        tool.assert_not_called()


class TimingResults(unittest.TestCase):
    def vectors(self):
        return mldsa.parse_per_vector(completed_log(1))

    def test_exact_equivalence_passes_independent_of_record_order(self):
        records = self.vectors()
        self.assertEqual(timing.compare_vectors(records, list(reversed(records)))['status'], 'PASS')

    def test_constant_offset_is_not_latency_preserving(self):
        baseline = self.vectors()
        optimized = [dict(v, cycles=v['cycles'] + 1) for v in baseline]
        self.assertEqual(timing.compare_vectors(baseline, optimized)['status'], 'FAIL')

    def test_empty_incomplete_duplicate_and_invalid_vectors_fail(self):
        valid = self.vectors()
        for invalid in ([], valid[:-1], valid + valid[:1], [dict(v, cycles=0) for v in valid],
                        [dict(v, **{'pass': False}) for v in valid]):
            with self.assertRaises(ValueError):
                timing.compare_vectors(valid, invalid)

    def test_failed_child_status_never_reads_stale_files(self):
        with patch.object(timing.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, '{"status":"PASS"}', '')):
            with self.assertRaises(RuntimeError):
                timing.run('candidate')


class BlockResults(TemporaryGateTree):
    def test_lockstep_rejects_nonzero_zero_missing_and_contradictory_results(self):
        from mldsa.gate_result import lockstep_result
        for code, text, err in (
                (1, 'EQUIV RESULT: PASS checked 200', 'fatal'),
                (0, 'EQUIV RESULT: PASS checked 0', ''),
                (0, 'EQUIV RESULT: PASS', ''),
                (0, 'NOT EQUIV RESULT: PASS checked 200', ''),
                (0, 'EQUIV RESULT: PASS checked 200\nEQUIV RESULT: FAIL', ''),
                (0, 'EQUIV RESULT: PASS checked 200', 'FATAL: failed'),
                (0, 'EQUIV RESULT: PASS checked 200 outputs 1 errors', '')):
            with self.subTest(code=code, text=text):
                result = subprocess.CompletedProcess([], code, text, err)
                self.assertEqual(lockstep_result(result)['status'], 'FAIL')
        for text in ('EQUIV RESULT: PASS checked 200', 'EQUIV RESULT: PASS checked 200 outputs 0 errors'):
            self.assertEqual(lockstep_result(subprocess.CompletedProcess([], 0, text, ''))['status'], 'PASS')

    def test_each_lockstep_wrapper_uses_fail_closed_parser(self):
        import importlib
        for name in ('decoder', 'gen_c', 'makehint', 'usehint', 'rejection_a', 'rejection_s', 'rejection_y'):
            module = importlib.import_module('mldsa.' + name + '_equiv_gate')
            pristine = self.root / (name + '.v')
            pristine.write_text('module ' + name + '; endmodule\n')
            for code, checked in ((1, 200), (0, 0), (0, 200)):
                compile_result = subprocess.CompletedProcess([], 0, '', '')
                sim_result = subprocess.CompletedProcess([], code, f'EQUIV RESULT: PASS checked {checked}', '')
                with patch.object(module, 'PRISTINE', str(pristine)), \
                     patch.object(module.subprocess, 'run', side_effect=[compile_result, sim_result]):
                    outcome = module.run_equiv()
                self.assertEqual(outcome['status'], 'PASS' if code == 0 and checked > 0 else 'FAIL', name)

    def test_block_gate_rejects_false_positive_and_incomplete_counts(self):
        from mldsa import mldsa_block_gate as block
        for code, count in ((1, 200), (0, 0), (0, 199), (0, 200)):
            output = f'==== checked {count} outputs, 0 errors ====\nBLOCK-KAT RESULT: PASS ({count}/{count})'
            with patch.object(block, '_run', side_effect=[(0, '', ''), (0, '', ''), (code, output, '')]):
                ok, reason, checked = block._one_level(self.root, '2')
            self.assertEqual(ok, code == 0 and count == 200, reason)
        with patch.object(block, '_run', side_effect=[(0, '', ''), (0, '', ''),
                          (1, 'checked 0 outputs, 0 errors\nBLOCK-KAT RESULT: PASS', 'fatal')]):
            self.assertFalse(block._one_level(self.root, '2')[0])

    def encoder_log(self):
        text = '\n'.join(f'CFG sl={level} em={mode} done: 10 words' for level in (2, 3, 5) for mode in range(6))
        return text + '\nSWITCHSEQ sl=3 done: 20 words\nSWITCHSEQ sl=5 done: 20 words\nGATE RESULT: PASS'

    def test_encoder_requires_all_positive_configuration_counts(self):
        from mldsa.gate_result import encoder_result
        valid = self.encoder_log()
        self.assertEqual(encoder_result(subprocess.CompletedProcess([], 0, valid, ''))['status'], 'PASS')
        for text, code in ((valid, 1), ('GATE RESULT: PASS', 0), (valid.replace('10 words', '0 words', 1), 0),
                           (valid.replace('SWITCHSEQ sl=3 done: 20 words', ''), 0),
                           (valid + '\nCFG sl=2 em=0 done: 10 words', 0),
                           (valid + '\nGATE RESULT: FAIL', 0)):
            self.assertEqual(encoder_result(subprocess.CompletedProcess([], code, text, ''))['status'], 'FAIL')

    def test_encoder_wrapper_rejects_success_text_after_simulator_failure(self):
        from mldsa import encoder_equiv_gate as encoder
        for name in encoder.FILES:
            (self.root / name).write_text('module ' + name.removesuffix('.v') + '; endmodule\n')
        results = [subprocess.CompletedProcess([], 0, '', ''),
                   subprocess.CompletedProcess([], 1, self.encoder_log(), 'fatal')]
        with patch.object(encoder, 'PRISTINE', str(self.root)), patch.object(encoder.subprocess, 'run', side_effect=results):
            self.assertEqual(encoder.run_equiv(str(self.root))['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
