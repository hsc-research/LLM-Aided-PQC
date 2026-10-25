"""Selected-mode gate regressions. Mock simulator output is not an RTL PASS."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent'))
from slh_dsa import slh_kat_gate as gate

DONE = 'sig gen done\nsig verification done\nThe signature is matched!\n'


class SelectedSLHGate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rtl = self.root / 'candidate'
        shutil.copytree(gate.HERE / 'pristine', self.rtl)
        env = patch.dict(os.environ, {'PQC_RUN_DIR': str(self.root / 'runs')})
        env.start()
        self.addCleanup(env.stop)
        self.saved_data_root = os.environ.pop('SLH_DATA_ROOT', None)
        if self.saved_data_root is not None:
            self.addCleanup(os.environ.__setitem__, 'SLH_DATA_ROOT', self.saved_data_root)
        self.setting = self.rtl / 'sphincslet/setting.v'
        self.template = self.setting.read_text()

    def select(self, parameter):
        # Change only this disposable unit-test fixture, never repository RTL.
        text = re.sub(r'^`define PARAM_128F$', '//`define PARAM_128F', self.template, flags=re.M)
        text = text.replace(f'//`define PARAM_{parameter.upper()}\n', f'`define PARAM_{parameter.upper()}\n')
        self.setting.write_text(text)

    def simulator(self, *, output_parameter=None, filename_parameter=None, transform=None,
                  output=DONE, mutate=None, omit_output=False):
        def run(argv, **kwargs):
            sim = Path(kwargs['cwd'])
            work = sim.parents[3]
            parameter = gate.check_configuration(work / 'rtl/sphincslet/setting.v')
            stdout = ''
            if argv[0] == 'xsim':
                data = work / 'TECS_v8.srcs/sources_1/imports/data_sha2'
                produced = data / f'SIG_file0_{filename_parameter or parameter}_w.hex'
                self.assertFalse(produced.exists(), 'stale signature leaked into this run')
                if not omit_output:
                    raw = gate.load_reference(output_parameter or parameter)[1]
                    produced.write_bytes(transform(raw) if transform else raw)
                if mutate:
                    mutate()
                stdout = output
            Path(kwargs['log_path']).write_text(stdout)
            return subprocess.CompletedProcess(argv, 0, stdout)
        return run

    def mocked_run(self, **kwargs):
        with patch.object(gate, 'run_process', side_effect=self.simulator(**kwargs)):
            return gate.run_equiv(self.rtl)

    def test_all_six_selections_bind_correct_reference_filename_and_full_length(self):
        for parameter in gate.REFERENCES:
            with self.subTest(parameter=parameter):
                self.select(parameter)
                before = {str(p): p.read_bytes() for p in self.rtl.rglob('*') if p.is_file()}
                result = self.mocked_run()
                self.assertEqual(result['status'], 'PASS', result)
                self.assertEqual(result['parameter_set'], f'SHA2-{parameter}')
                self.assertEqual(Path(result['golden']).name, f'SIG_{parameter}.hex')
                self.assertEqual(result['produced_filename'], f'SIG_file0_{parameter}_w.hex')
                self.assertEqual(result['signature_words'], gate.REFERENCES[parameter][1])
                self.assertEqual(result['evidence_kind'], 'vendor_rtl_differential')
                self.assertIs(result['independent_fips_205_validation'], False)
                run_dir = Path(result['run_dir'])
                self.assertEqual(len(json.loads((run_dir / 'inputs.json').read_text())), 4)
                self.assertEqual(json.loads((run_dir / 'reference.json').read_text())['parameter_set'],
                                 f'SHA2-{parameter}')
                self.assertEqual(before, {str(p): p.read_bytes() for p in self.rtl.rglob('*') if p.is_file()})

    def test_192f_never_accepts_128f_bytes_even_with_correct_192f_filename(self):
        self.select('192f')
        result = self.mocked_run(output_parameter='128f')
        self.assertEqual(result['status'], 'FAIL', result)
        self.assertIn('differs from golden', result['reason'])

    def test_192f_does_not_read_128f_output_filename(self):
        self.select('192f')
        result = self.mocked_run(filename_parameter='128f')
        self.assertEqual(result['status'], 'FAIL', result)
        self.assertEqual(result['reason'], 'no signature produced')

    def test_every_byte_including_framing_and_final_newline_is_compared(self):
        self.select('192f')
        for transform in (lambda b: b[:-1], lambda b: b[:-17], lambda b: b[17:],
                          lambda b: b + b'0000000000000000\n',
                          lambda b: (b'0' if b[:1] != b'0' else b'1') + b[1:],
                          lambda b: b[:-17] + b'0000000000000000\n'):
            with self.subTest(transform=transform):
                self.assertEqual(self.mocked_run(transform=transform)['status'], 'FAIL')

    def test_no_signature_and_incomplete_or_contradictory_logs_fail(self):
        self.select('192f')
        self.assertEqual(self.mocked_run(omit_output=True)['status'], 'FAIL')
        for output in ('The signature is matched!', 'sig gen done\nThe signature is matched!',
                       DONE + 'The signature is not matched!\n', DONE + 'ERROR: failure\n',
                       DONE.replace('The signature is matched!', 'prefix The signature is matched! suffix')):
            self.assertEqual(self.mocked_run(output=output)['status'], 'FAIL', output)

    def test_unknown_ambiguous_shake_or_redefined_config_fails_before_tools(self):
        for suffix in ('\n`define SHAKE\n', '\n`define PARAM_192F\n', '\n`undef PARAM_128F\n',
                       '\n`define PARAM_SET "192f"\n', '\n`define PARAM_512F\n'):
            self.setting.write_text(self.template + suffix)
            with patch.object(gate, 'run_process') as tool:
                self.assertEqual(gate.run_equiv(self.rtl)['status'], 'ERROR')
            tool.assert_not_called()
        for text in ('', self.template.replace('`define PARAM_128F\n', '//`define PARAM_128F\n'),
                     self.template.replace('`define PARAM_SET "128f"', '`define PARAM_SET "192f"'),
                     self.template.replace('`define PARAM_128\n', '`define\n PARAM_128\n')):
            self.setting.write_text(text)
            with patch.object(gate, 'run_process') as tool:
                self.assertEqual(gate.run_equiv(self.rtl)['status'], 'ERROR')
            tool.assert_not_called()

    def test_input_bitflip_or_missing_input_fails_before_tools(self):
        self.select('192f')
        for name in ('SLH_192f_SK.hex', 'SLH_192f_PK.hex', '192_optrand.hex', 'SLH_msg_33B.hex'):
            path = self.rtl / 'imports/data_sha2' / name
            original = path.read_bytes()
            path.write_bytes(b'0' + original[1:] if original[:1] != b'0' else b'1' + original[1:])
            with patch.object(gate, 'run_process') as tool:
                self.assertEqual(gate.run_equiv(self.rtl)['status'], 'ERROR')
            tool.assert_not_called()
            path.unlink()
            with patch.object(gate, 'run_process') as tool:
                self.assertEqual(gate.run_equiv(self.rtl)['status'], 'ERROR')
            tool.assert_not_called()
            path.write_bytes(original)

    def test_modified_vendor_testbench_is_rejected(self):
        tb = self.rtl / 'sphincslet/tb.v'
        tb.write_text(tb.read_text().replace('SIG_file0_', 'wrong_'))
        with patch.object(gate, 'run_process') as tool:
            self.assertEqual(gate.run_equiv(self.rtl)['status'], 'ERROR')
        tool.assert_not_called()

    def test_new_sidecar_cannot_authorize_replaced_golden(self):
        self.select('192f')
        references = self.root / 'references'
        shutil.copytree(gate.GOLDEN_DIR, references)
        path = references / 'SIG_192f.hex'
        path.write_bytes((references / 'SIG_128f.hex').read_bytes())
        path.with_suffix('.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest())
        with patch.object(gate, 'GOLDEN_DIR', references), patch.object(gate, 'run_process') as tool:
            result = gate.run_equiv(self.rtl)
        self.assertEqual(result['status'], 'ERROR', result)
        self.assertIn('checksum mismatch', result['reason'])
        tool.assert_not_called()

    def test_stale_external_signatures_are_preserved_and_ignored(self):
        self.select('192f')
        external = self.rtl / 'imports/data_sha2/SIG_file0_192f_w.hex'
        external.write_bytes(gate.load_reference('192f')[1])
        before = external.read_bytes()
        self.assertEqual(self.mocked_run(omit_output=True)['status'], 'FAIL')
        self.assertEqual(external.read_bytes(), before)

    def test_changed_source_or_input_during_run_is_rejected(self):
        for path in (self.rtl / 'sphincslet/top.v', self.rtl / 'imports/data_sha2/SLH_msg_33B.hex'):
            original = path.read_bytes()
            result = self.mocked_run(mutate=lambda: path.write_bytes(original + b'\n'))
            self.assertEqual(result['status'], 'ERROR', result)
            self.assertIn('changed during verification', result['reason'])
            path.write_bytes(original)

    def test_missing_tool_is_error_with_selected_parameter_and_no_pass(self):
        self.select('192f')
        with patch.object(gate, 'run_process', side_effect=FileNotFoundError('xvlog unavailable')):
            result = gate.run_equiv(self.rtl)
        self.assertEqual(result['status'], 'ERROR', result)
        self.assertEqual(result['stage'], 'xvlog')
        self.assertEqual(result['parameter_set'], 'SHA2-192f')

    def test_relocated_identical_data_root_is_accepted_but_changed_data_is_not(self):
        self.select('192f')
        data_root = self.root / 'inputs'
        shutil.copytree(self.rtl / 'imports/data_sha2', data_root / 'data_sha2')
        with patch.dict(os.environ, {'SLH_DATA_ROOT': str(data_root)}):
            self.assertEqual(self.mocked_run()['status'], 'PASS')
            (data_root / 'data_sha2/192_optrand.hex').write_text('bad')
            with patch.object(gate, 'run_process') as tool:
                self.assertEqual(gate.run_equiv(self.rtl)['status'], 'ERROR')
            tool.assert_not_called()

    def test_historical_128f_alias_is_unchanged(self):
        self.assertEqual((gate.HERE / 'gate/SIG_file0_128f_w.hex').read_bytes(),
                         gate.load_reference('128f')[1])


if __name__ == '__main__':
    unittest.main()
