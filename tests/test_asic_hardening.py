"""Offline report/provenance tests; fixtures never stand in for licensed runs."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent'))
import asic_synthesis as asic


class ReportValidation(unittest.TestCase):
    def metrics(self, timing='Path 1: MET (1 ps) Setup Check', area='top top 25 40.5', power='', tool='genus'):
        return asic.parse_metrics(tool, timing, area, power, 'ps', 'top', 'library_unit')

    def test_malformed_second_genus_path_is_not_skipped(self):
        for row in ('Path 2: MET (NaN ps) Setup Check', 'Path two: MET (1 ps) Setup Check',
                    'Path 2: UNKNOWN (1 ps) Setup Check', 'Path 2: VIOLATED (-1 fs) Setup Check'):
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.metrics(timing='Path 1: MET (1 ps) Setup Check\n' + row)

    def test_genus_path_sequence_and_setup_required(self):
        for timing in ('Path 2: MET (1 ps) Setup Check', 'Path 1: MET (1 ps) Hold Check',
                       'Path 1: MET (1 ps) Setup Check\nPath 1: MET (1 ps) Setup Check'):
            with self.subTest(timing=timing), self.assertRaises(ValueError):
                self.metrics(timing=timing)

    def test_overflow_timing_is_rejected(self):
        with self.assertRaises(ValueError):
            self.metrics(timing='Path 1: MET (1e999 ps) Setup Check')

    def test_rounded_violation_does_not_pass(self):
        metrics = self.metrics(timing='Path 1: VIOLATED (-0 ps) Setup Check')
        self.assertFalse(metrics['timing_met_reported'])

    def test_worst_reported_path_is_used(self):
        metrics = self.metrics(timing='Path 1: MET (3 ps) Setup Check\nPath 2: VIOLATED (-1 ps) Setup Check')
        self.assertEqual(metrics['worst_setup_slack_ns'], -0.001)
        self.assertFalse(metrics['timing_met_reported'])

    def test_unconstrained_timing_is_not_measured(self):
        with self.assertRaises(ValueError):
            self.metrics(timing='Path 1: MET (1 ps) Setup Check\nThis path is unconstrained')

    def test_missing_area_and_power_are_unknown(self):
        metrics = self.metrics(area='', power='')
        self.assertIsNone(metrics['cell_count'])
        self.assertIsNone(metrics['cell_area_reported'])
        self.assertIsNone(metrics['power_w'])

    def test_invalid_genus_area_rejected(self):
        for area in ('top top 25 -1', 'top top 25 nan', 'top top 25 1e999',
                     'top top 0 4', 'top top 25 0', 'top top 25 1\ntop top 25 2'):
            with self.subTest(area=area), self.assertRaises(ValueError):
                self.metrics(area=area)

    def test_invalid_dc_area_rejected(self):
        for area in ('Total cell area: -1', 'Total cell area: inf', 'Total cell area: 1e999',
                     'Number of cells: -3', 'Total cell area: 2\nTotal cell area: 3'):
            with self.subTest(area=area), self.assertRaises(ValueError):
                self.metrics(tool='dc', timing='Path Type: max\nslack (MET) 1', area=area)

    def test_malformed_dc_path_is_not_skipped(self):
        for timing in ('Path Type: max\nslack (MET) 1\nPath Type: max\nslack (VIOLATED) nan',
                       'Path Type: min\nslack (MET) 1', 'slack (MET) 1'):
            with self.subTest(timing=timing), self.assertRaises(ValueError):
                self.metrics(tool='dc', timing=timing)

    def test_invalid_dc_power_rejected(self):
        for value in ('-3 mW', 'nan W', '1e999 W', '2 potatoes'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.metrics(tool='dc', timing='Path Type: max\nslack (MET) 1', area='',
                             power='Total Dynamic Power = ' + value + '\nCell Leakage Power = 1 mW')

    def test_dc_power_percent_suffix(self):
        metrics = self.metrics(tool='dc', timing='Path Type: max\nslack (MET) 1', area='',
                               power='Total Dynamic Power = 2 mW (100%)\nCell Leakage Power = 3 uW')
        self.assertAlmostEqual(metrics['power_w'], .002003)

    def test_genus_power_subtotal(self):
        metrics = self.metrics(power='Power Unit: mW\nSubtotal 1 2 3 6 100.00%')
        self.assertAlmostEqual(metrics['power_w'], .006)

    def test_invalid_genus_power_rejected(self):
        for power in ('Power Unit: W\nSubtotal 1 2 3 100 100%',
                      'Power Unit: W\nSubtotal -1 2 3 4 100%',
                      'Power Unit: W\nSubtotal 1 2 3 nan 100%',
                      'Subtotal 1 2 3 6 100%',
                      'Power Unit: kW\nSubtotal 1 2 3 6 100%'):
            with self.subTest(power=power), self.assertRaises(ValueError):
                self.metrics(power=power)

    def test_real_genus_report_fixture(self):
        # Existing archived evidence is parser input only. Its results are not
        # new measurements and are not reinstated as Fmax or signoff claims.
        directory = ROOT / 'logs/asic/asap7_bf2x2_fmax_v2_base_20260812'
        text = lambda kind: (directory / ('butterfly2x2_p583_' + kind + '.rpt')).read_text()
        result = asic.parse_metrics('genus', text('timing'), text('area'), text('power'),
                                    'ps', 'butterfly2x2', 'library_unit')
        self.assertTrue(result['timing_met_reported'])
        self.assertGreater(result['cell_count'], 0)
        self.assertGreater(result['power_w'], 0)
        self.assertIsNone(result['fmax_mhz'])


class ProvenanceValidation(unittest.TestCase):
    def test_real_zero_unresolved_report(self):
        path = ROOT / 'logs/asic/hqc_portfix_20260812/hqc_unresolved.rpt'
        asic.validate_unresolved_report(path.read_text(), 'hqc_kem_joint_design')

    def test_unresolved_evidence_is_required(self):
        for text in ('', "No unresolved references in design 'top'",
                     "No unresolved references in design 'other'\nNo empty modules in design 'other'"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                asic.validate_unresolved_report(text, 'top')

    def test_contradictory_unresolved_report_rejected(self):
        text = "No unresolved references in design 'top'\nNo empty modules in design 'top'\nUnresolved instance: memory"
        with self.assertRaises(ValueError):
            asic.validate_unresolved_report(text, 'top')

    def test_liberty_units_are_checked_before_execution(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'cells.lib'
            path.write_text('library (test) { time_unit : "1ps"; }')
            asic.validate_liberty_time_units([path], 'ps')
            with self.assertRaises(ValueError):
                asic.validate_liberty_time_units([path], 'ns')
            path.write_text('/* time_unit : "1ps"; */ library (test) {}')
            with self.assertRaises(ValueError):
                asic.validate_liberty_time_units([path], 'ps')

    def test_blackbox_warning_overrides_success(self):
        for text in ('Warning : Black-boxes are represented as unresolved references [TUI-273]',
                     "A blackbox was created for instance 'REDUCER'", 'error: broken'):
            with self.subTest(text=text), self.assertRaises(RuntimeError):
                asic.validate_tool_log(text)

    def test_dc_units_are_verified(self):
        asic.validate_dc_units('Time Units : 1ns', 'ns')
        asic.validate_dc_units('Time Units : 1000ps', 'ns')
        for text in ('Time Units : 1ns', 'Time Units : nan', '', 'Time Units : 1ps\nTime Units : 1ps'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                asic.validate_dc_units(text, 'ps')

    def test_site_template_requires_explicit_constraints(self):
        environment = dict(os.environ)
        for name in asic.SITE_ENVIRONMENT:
            environment.pop(name, None)
        with tempfile.TemporaryDirectory() as root:
            script = Path(root) / 'site.tcl'
            script.write_text('set PQC_PERIOD 583\nset PQC_PERIOD_NS 0.583\nsource ' +
                              asic.word(ROOT / 'configs/asic_site.example.tcl') + '\n')
            result = subprocess.run(['tclsh', str(script)], env=environment, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            environment.update(PQC_ASIC_INPUT_TRANSITION_NS='0.01',
                               PQC_ASIC_CLOCK_UNCERTAINTY_NS='0.03', PQC_ASIC_OUTPUT_LOAD='2')
            result = subprocess.run(['tclsh', str(script)], env=environment, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            environment['PQC_ASIC_OUTPUT_LOAD'] = 'Inf'
            result = subprocess.run(['tclsh', str(script)], env=environment, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)

    def test_clock_mismatch_fails_before_tool_synthesis(self):
        script = 'set PQC_PERIOD 583\nset actual_period 600\n' + '\n'.join(asic.clock_audit_tcl())
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'test.tcl'
            source.write_text(script)
            result = subprocess.run(['tclsh', str(source)], cwd=root, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((Path(root) / 'constraint_audit.rpt').exists())


class RetiredWorkflows(unittest.TestCase):
    def test_legacy_fmax_launchers_fail_without_tool(self):
        for relative in ('asic/scripts/genus_fmax.py', 'asic/scripts/genus_fmax_arm.py',
                         'asic/asap7/scripts/asap7_fmax.py'):
            with self.subTest(relative=relative):
                result = subprocess.run([sys.executable, str(ROOT / relative)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn('disabled', result.stderr)

    def test_legacy_backend_cannot_connect(self):
        from backends.genus import GenusBackend
        with patch('subprocess.run') as process, self.assertRaises(RuntimeError):
            GenusBackend(srcdir='anything', outdir='anything')
        process.assert_not_called()

    def test_port_reorder_missing_files_fail_closed(self):
        from port.port_gate import stage1_pure_reorder
        self.assertFalse(stage1_pure_reorder('/nonexistent-before', '/nonexistent-after')[0])

    def test_port_kat_requires_structured_success_and_zero_exit(self):
        from port import port_gate
        for code, text in ((1, 'GATE: PASS'), (0, 'PASSED somewhere'), (0, 'GATE: FAIL')):
            result = subprocess.CompletedProcess([], code, text)
            with self.subTest(code=code, text=text), patch.object(port_gate, 'run_process', return_value=result):
                self.assertFalse(port_gate.stage3_kat('python3 gate.py')[0])
        result = subprocess.CompletedProcess([], 0, 'GATE: PASS')
        with patch.object(port_gate, 'run_process', return_value=result):
            self.assertTrue(port_gate.stage3_kat('python3 gate.py')[0])

    def test_remote_port_helper_has_no_effect(self):
        from port.run_port_fix import genus_accepts, run
        from port.sweep_fixes import probe
        for helper, args in ((genus_accepts, ('file.v',)), (probe, ('file.v',)),
                             (run, ('file.v', 'VLOGPT-20', 'error'))):
            with self.subTest(helper=helper), patch('subprocess.run') as process:
                with self.assertRaises(RuntimeError):
                    helper(*args)
                process.assert_not_called()


if __name__ == '__main__':
    unittest.main()
