"""Synthetic local records test dashboard ingestion, never EDA qualification."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from agent import asic_dashboard as dash
from agent.asic_synthesis import parse_metrics


def write(path, value):
    path.write_text(json.dumps(value))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def report(path, value):
    path.write_text(value)
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


class ASICDashboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = self.root / '.pqc_runs/whole_design/fixture'
        self.phase = self.run / '002-measure'
        self.phase.mkdir(parents=True)
        self.sources = {str(self.root / 'design.v'): 'a' * 64}
        self.config = {'target': 'asic', 'backend': 'dc', 'top': 'top',
                       'measurement': {'period_ns': 5, 'stage': 'post_synth', 'technology': 'fixture',
                                       'corner': 'fixture-only', 'tool_version': 'fixture-release'}}
        self.request = {'schema_version': 1, 'phase': 'measure', 'run_id': 'fixture',
                        'source_hashes': self.sources, 'configuration': self.config}
        self.response = {'schema_version': 1, 'request_sha256': write(self.phase / 'request.json', self.request),
                         'status': 'MEASURED', 'scope': 'full_design', 'configuration': self.config,
                         'metrics': {'worst_setup_slack_ns': 1, 'cell_area_reported': 100}, 'area_unit': 'fixture_units',
                         'reports': {'timing': report(self.phase / 'timing.rpt', 'FIXTURE path\n'),
                                     'area': report(self.phase / 'area.rpt', 'FIXTURE area\n')},
                         'critical_paths': [{'id': '0', 'startpoint': 'a/Q', 'endpoint': 'b/D', 'slack_ns': 1,
                                             'report': 'timing', 'line_start': 1, 'line_end': 1}]}
        write(self.run / 'manifest.json', {'configuration': self.config, 'baseline_sources': self.sources})
        self.save()

    def save(self):
        write(self.phase / 'response.json', self.response)

    def result(self):
        return dash.collect(self.root)

    def test_bound_baseline_observations_not_qualification(self):
        result = self.result()
        self.assertEqual(result['errors'], [])
        row = result['runs'][0]
        self.assertEqual(row['measurement_role'], 'baseline')
        self.assertEqual(row['observations']['metrics']['area'], 100)
        self.assertEqual(row['observations']['metrics']['area_unit'], 'fixture_units')
        self.assertIsNone(row['observations']['metrics']['total_power_w'])
        self.assertIsNone(row['observations']['metrics']['worst_hold_slack_ns'])
        self.assertEqual(len(row['observations']['critical_paths']), 1)
        self.assertFalse(row['target_tool_qualified'])
        self.assertEqual(row['comparison']['status'], 'BLOCKED')

    def test_candidate_role_without_gains(self):
        self.request['source_hashes'] = {str(self.root / 'design.v'): 'b' * 64}
        self.response['request_sha256'] = write(self.phase / 'request.json', self.request)
        self.save()
        row = self.result()['runs'][0]
        self.assertEqual(row['measurement_role'], 'candidate')
        self.assertEqual(row['comparison']['status'], 'BLOCKED')

    def test_request_tamper_excluded(self):
        self.request['configuration']['measurement']['period_ns'] = 10
        write(self.phase / 'request.json', self.request)
        self.assertEqual(self.result()['runs'], [])

    def test_report_tamper_excluded(self):
        (self.phase / 'timing.rpt').write_text('tampered')
        self.assertEqual(self.result()['runs'], [])

    def test_configuration_mismatch_excluded(self):
        self.response['configuration'] = copy.deepcopy(self.config)
        self.response['configuration']['measurement']['corner'] = 'different'
        self.save()
        self.assertEqual(self.result()['runs'], [])

    def test_source_mismatch_excluded(self):
        self.response['source_hashes'] = {'other.v': 'c' * 64}
        self.save()
        self.assertEqual(self.result()['runs'], [])

    def test_outside_report_excluded(self):
        self.response['reports']['timing'] = report(self.root / 'private.rpt', 'unrelated')
        self.save()
        self.assertEqual(self.result()['runs'], [])

    def test_symlink_file_excluded(self):
        original = self.phase / 'timing.rpt'
        original.rename(self.phase / 'other.rpt')
        original.symlink_to(self.phase / 'other.rpt')
        self.assertEqual(self.result()['runs'], [])

    def test_symlink_ancestor_excluded(self):
        (self.root / '.pqc_runs').rename(self.root / 'elsewhere')
        (self.root / '.pqc_runs').symlink_to(self.root / 'elsewhere', target_is_directory=True)
        self.assertEqual(self.result()['runs'], [])
        self.assertTrue(self.result()['errors'])

    def test_path_traversal_excluded(self):
        self.response['reports']['timing']['path'] = str(self.phase / '../002-measure/timing.rpt')
        self.save()
        self.assertEqual(self.result()['runs'], [])

    def test_invalid_path_range_not_displayed(self):
        self.response['critical_paths'][0]['line_end'] = 2
        self.save()
        self.assertEqual(self.result()['runs'][0]['observations']['critical_paths'], [])

    def test_missing_power_and_nonfinite_metrics_stay_unknown(self):
        self.response['metrics']['power_w'] = float('nan')
        self.save()
        self.assertIsNone(self.result()['runs'][0]['observations']['metrics']['power_w'])

    def test_claimed_qualification_never_promoted(self):
        self.response.update(tool_qualification='qualified', admission_passed=True, timing_signoff=True)
        self.save()
        row = self.result()['runs'][0]
        self.assertEqual(row['recorded_qualification']['tool_qualification'], 'qualified')
        self.assertFalse(row['target_tool_qualified'])
        self.assertFalse(row['observations']['timing_signoff'])

    def test_partial_and_oversized_json_fail_closed(self):
        (self.phase / 'response.json').write_text('{')
        self.assertEqual(self.result()['runs'], [])
        (self.phase / 'response.json').write_bytes(b' ' * (dash.LIMIT + 1))
        self.assertEqual(self.result()['runs'], [])

    def test_historical_logs_not_imported(self):
        other = self.root / 'logs/asic/old'
        other.mkdir(parents=True)
        write(other / 'result.json', self.response)
        self.assertEqual(len(self.result()['runs']), 1)

    def test_standalone_dc_reparses_reports_and_components(self):
        directory = self.root / 'runs/asic/dc-fixture'
        directory.mkdir(parents=True)
        timing = 'Startpoint: a/Q (flipflop)\nEndpoint: b/D (flipflop)\nPath Type: max\nslack (MET) 1.0\n'
        area = 'Total cell area: 100\nNumber of cells: 42\n'
        power = 'Total Dynamic Power = 2 mW\nCell Leakage Power = 3 uW\n'
        manifest = {'tool': 'dc', 'top': 'top', 'scope': 'full_design', 'period_ns': 5,
                    'memory_model': 'flops', 'time_unit': 'ns', 'area_unit': 'fixture_units',
                    'input_hashes': self.sources}
        metrics = parse_metrics('dc', timing, area, power, 'ns', 'top', 'fixture_units')
        reports = [report(directory / name, value) for name, value in
                   [('timing.rpt', timing), ('area.rpt', area), ('power.rpt', power)]]
        result = {**manifest, 'status': 'MEASURED', 'stage': 'post_synth', 'metrics': metrics,
                  'report_hashes': {r['path']: r['sha256'] for r in reports}}
        write(directory / 'manifest.json', manifest)
        write(directory / 'result.json', result)
        row = self.result()['runs'][-1]
        self.assertEqual(row['measurement_role'], 'unspecified')
        self.assertEqual(row['observations']['critical_paths'][0]['endpoint'], 'b/D')
        self.assertIsNone(row['observations']['critical_paths'][0]['data_path_delay_ns'])
        self.assertEqual(row['observations']['metrics']['dynamic_power_w'], .002)
        self.assertEqual(row['observations']['metrics']['leakage_power_w'], .000003)
        result['metrics']['cell_area_reported'] = 1
        write(directory / 'result.json', result)
        self.assertEqual(len(self.result()['runs']), 1)
        self.assertTrue(self.result()['errors'])


if __name__ == '__main__':
    unittest.main()
