"""License-free launch-contract regressions, not Vivado or FPGA qualification.

The generated launch is executed by real Tcl with explicit command stubs. There
is deliberately no catch-all unknown handler: unsupported EDA commands fail.
"""
import copy
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from agent import autonomous_fpga as controller, fpga_feedback as feedback
from tests import test_autonomous_fpga as autonomous_fixture
from tests import test_vivado_qualification as qualification_fixture
from tools.export_target_profiles import tcl_word


class LaunchContractTests(unittest.TestCase):
    def setUp(self):
        self.fixture = qualification_fixture.QualificationTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root

    def launch(self, *, version='2022.2', synthesis_failure=False, mutate=None):
        def process(argv, **options):
            script = Path(argv[argv.index('-source') + 1])
            if mutate:
                script.write_text(mutate(script.read_text()))
            wrapper = self.root / 'stub-vivado.tcl'
            wrapper.write_text('''
# This is only a tested launch API surface, never an EDA emulator.
proc version {args} {return VERSION}
proc create_project {args} {
    if {$args ne {-in_memory -part xc7a200tfbg676-1}} {error {bad project options}}
}
proc current_fileset {} {return fileset}
proc set_property {property value object} {
    if {$property ne {include_dirs} || $object ne {fileset}} {error {bad property}}
}
proc read_verilog {sources} {foreach path $sources {if {![file isfile $path]} {error {missing source}}}}
proc read_xdc {path} {
    if {![file isfile $path]} {error {missing XDC}}
    puts {WARNING: [Constraints 18-1] SYNTHETIC constraint fixture warning}
}
proc synth_design {args} {
    if {$args ne {-top combined_top -part xc7a200tfbg676-1 -mode out_of_context -gated_clock_conversion off}} {
        error {unexpected synthesis options}
    }
    puts {WARNING: [Synth 8-1234] SYNTHETIC launch fixture warning}
    SYNTHESIS_RESULT
}
proc report_utilization {args} {}
proc report_drc {args} {}
proc write_checkpoint {path} {}
proc write_verilog {args} {}
rename source original_source
proc source {path} {
    if {[file tail $path] ne {vivado_qualification.tcl}} {error {unexpected helper}}
    puts {SYNTHETIC qualification helper reached}
    puts {CRITICAL WARNING: [Timing 38-1] SYNTHETIC report fixture warning}
}
original_source SCRIPT
'''.replace('VERSION', tcl_word(version))
                  .replace('SYNTHESIS_RESULT', 'error {SYNTHETIC synthesis failure}' if synthesis_failure else '')
                  .replace('SCRIPT', tcl_word(script)))
            result = subprocess.run(['tclsh', str(wrapper)], cwd=options['cwd'],
                                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
            Path(options['log_path']).write_text(result.stdout)
            if result.returncode == 0:
                qualification_fixture.emit_reports(self.fixture.run, self.fixture.source)
            return subprocess.CompletedProcess(argv, result.returncode, result.stdout, '')
        with patch.object(feedback, 'run_process', side_effect=process):
            return feedback.collect(self.fixture.request_file, self.root / 'response.json', execute=True)

    def test_generated_launch_reaches_synthesis_and_retains_all_warnings(self):
        response = self.launch()
        self.assertEqual(response['tool_returncode'], 0)
        self.assertEqual(response['measurement_label'], 'PRELIMINARY_POST_SYNTH_NOT_ADMITTED')
        self.assertEqual(response['actual_tool_version'], '2022.2')
        self.assertIsNotNone(response['qualification'])
        self.assertEqual((self.fixture.run / 'console.log').read_bytes(),
                         (self.fixture.run / 'synthesis.log').read_bytes())
        self.assertIn('SYNTHETIC qualification helper reached', (self.fixture.run / 'console.log').read_text())
        self.assertEqual(response['qualification']['gates']['structural'], 'BLOCKED')
        self.assertEqual(len(response['warnings']), 3)
        self.assertIn('constraint fixture warning', response['warnings'][0])
        self.assertIn('report fixture warning', response['warnings'][-1])
        self.assertFalse(response['memory_semantics_verified'])

    def test_dry_run_retains_not_executed_label(self):
        with patch.object(feedback, 'run_process', side_effect=AssertionError('No tool launch allowed')):
            response = feedback.collect(self.fixture.request_file, self.root / 'response.json')
        self.assertFalse(response['executed'])
        self.assertEqual(response['measurement_label'], 'PREPARED_NOT_EXECUTED')
        self.assertIsNone(response['qualification'])
        self.assertIsNone(response['metrics'])

    def test_unknown_redirect_is_rejected_by_tcl_contract(self):
        # Deliberately recreate the reported failure. The script-integrity check
        # also blocks this mutation, but the real Tcl return code proves that
        # the launch stub is not silently accepting an unknown command.
        response = self.launch(mutate=lambda s: s.replace('synth_design -top', 'redirect -tee -file synthesis.log synth_design -top'))
        self.assertEqual(response['tool_returncode'], 1)
        self.assertIn('invalid command name "redirect"', (self.fixture.run / 'console.log').read_text())
        self.assertIsNone(response['qualification'])

    def test_synthesis_error_is_not_hidden_and_version_is_preserved(self):
        response = self.launch(synthesis_failure=True)
        self.assertTrue(response['executed'])
        self.assertEqual(response['measurement_label'], 'EXECUTED_TOOL_FAILED')
        self.assertEqual(response['status'], 'BLOCKED')
        self.assertFalse(response['memory_semantics_verified'])
        self.assertEqual(response['tool_returncode'], 1)
        self.assertEqual(response['actual_tool_version'], '2022.2')
        self.assertIn('SYNTHETIC synthesis failure', (self.fixture.run / 'synthesis.log').read_text())
        self.assertNotIn('SYNTHETIC qualification helper reached', (self.fixture.run / 'console.log').read_text())
        self.assertIsNone(response['qualification'])
        self.assertIsNone(response['metrics'])

    def test_wrong_version_records_observed_value_and_never_synthesizes(self):
        response = self.launch(version='2023.1')
        self.assertEqual(response['measurement_label'], 'EXECUTED_TOOL_FAILED')
        self.assertEqual(response['tool_returncode'], 1)
        self.assertEqual(response['actual_tool_version'], '2023.1')
        self.assertIn('Vivado version mismatch', (self.fixture.run / 'console.log').read_text())
        self.assertNotIn('[Synth 8-1234]', (self.fixture.run / 'console.log').read_text())
        self.assertIsNone(response['qualification'])


class ControllerFailureTests(unittest.TestCase):
    def setUp(self):
        self.fixture = autonomous_fixture.AutonomousTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        settings = copy.deepcopy(self.fixture.settings)
        settings['launch']['tool_version'] = '2022.2'
        settings['profile']['boundary'] = {'clock_ports': ['clk']}
        self.controller = controller.Controller(settings, self.fixture.root / 'launch-test',
                                               client_factory=lambda: self.fail('No API allowed'))
        self.controller.setup()

    def measure(self, *, returncode=0, malformed=False, launch_error=None, omit_version=False):
        c = self.controller
        def execute(argv, directory, timeout):
            def process(argv, **options):
                Path(options['log_path']).write_text('SYNTHETIC tool output\n')
                if launch_error:
                    raise launch_error
                (directory / 'vivado' / 'tool-version.txt').write_text('2022.2\n')
                if returncode == 0:
                    qualification_fixture.emit_reports(directory / 'vivado', Path(c.sources[0]))
                    if malformed:
                        (directory / 'vivado' / 'objects.tsv').write_text('invalid report\n')
                return subprocess.CompletedProcess(argv, returncode, 'SYNTHETIC tool output', '')
            with patch.object(feedback, 'run_process', side_effect=process):
                response = feedback.collect(directory / 'request.json', directory / 'response.json', execute=True)
                if omit_version:
                    response.pop('actual_tool_version')
                    (directory / 'response.json').write_text(json.dumps(response))
        c.execute = execute
        return c.stage('measure', c.baseline)

    def test_nonzero_exit_reports_tool_failure_not_version_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'Vivado failed; inspect bound vivado/console.log'):
            self.measure(returncode=1)
        self.assertEqual(self.controller.state['generation_attempts'], 0)

    def test_malformed_reports_report_collection_failure_not_version_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'evidence collection or validation failed'):
            self.measure(malformed=True)

    def test_missing_version_is_not_a_claimed_version_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'Missing actual Vivado version evidence'):
            self.measure(omit_version=True)

    def test_missing_executable_reports_collection_failure_not_version_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'evidence collection or validation failed'):
            self.measure(launch_error=FileNotFoundError('synthetic missing vivado'))


if __name__ == '__main__':
    unittest.main()
