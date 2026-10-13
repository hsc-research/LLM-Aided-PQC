import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from agent.current_dashboard import collect, report_summary


def write(path, value):
    path.write_text(json.dumps(value))
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CurrentDashboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run = self.root / '.pqc_runs/fpga-proposals/test'
        self.run.mkdir(parents=True)
        prompt_hash = write(self.run / 'prompt.json', {'user': {
            'profile_fingerprint': 'a' * 64, 'target': 'fpga', 'part': 'xc7a200tfbg676-1',
            'period_ns': 15, 'tool_version_declared': '2022.2',
            'reports': {'check_timing.rpt': '1. checking no_clock (198)\n4. checking unconstrained_internal_endpoints (66)'}}})
        self.context_hash = write(self.run / 'proposal-context.json', {'schema_version': 1,
            'status': 'PROMPT_PREPARED_NO_API_CALL', 'profile_fingerprint': 'a' * 64,
            'prompt_sha256': prompt_hash})

    def tearDown(self):
        self.tmp.cleanup()

    def test_prepared_is_not_pass(self):
        run = collect(self.root)['runs'][0]
        self.assertEqual(run['automatic_acceptance'], 'BLOCKED')
        self.assertEqual(run['functional_verification'], 'NOT_RUN')
        self.assertEqual(run['observations']['warnings']['no_clock'], 198)
        self.assertIsNone(run['reported_cost_usd'])
        self.assertFalse(run['target_tool_qualified'])

    def test_bound_api_usage_and_unknown_cost(self):
        write(self.run / 'proposal-run.json', {'context_sha256': self.context_hash,
            'status': 'FAILED_OUTCOME_UNKNOWN', 'api_calls_attempted': 1,
            'estimated_max_cost_usd': '1.2', 'reported_cost_usd': None})
        run = collect(self.root)['runs'][0]
        self.assertEqual(run['status'], 'FAILED_OUTCOME_UNKNOWN')
        self.assertEqual(run['api_calls_attempted'], 1)
        self.assertEqual(run['estimated_max_cost_usd'], 1.2)
        self.assertIsNone(run['reported_cost_usd'])

    def test_stale_review_not_used(self):
        write(self.run / 'review.json', {'context_sha256': 'wrong', 'status': 'PASS'})
        run = collect(self.root)['runs'][0]
        self.assertEqual(run['status'], 'PROMPT_PREPARED_NO_API_CALL')
        self.assertIn('stale', run['notes'][-1])

    def test_preview_is_never_acceptance(self):
        write(self.run / 'review.json', {'context_sha256': self.context_hash,
            'status': 'EDIT_PREVIEW_VALID_NOT_APPLIED', 'functional_verified': True,
            'ppa_gain_verified': True, 'automatic_acceptance': 'PASS'})
        run = collect(self.root)['runs'][0]
        self.assertEqual(run['automatic_acceptance'], 'BLOCKED')
        self.assertEqual(run['candidate_measurement'], 'NOT_RUN')

    def test_corrupt_and_partial_file(self):
        (self.run / 'prompt.json').write_text('{')
        data = collect(self.root)
        self.assertEqual(data['runs'], [])
        self.assertEqual(data['errors'][0]['status'], 'INCOMPLETE_OR_INVALID')

    def test_prompt_tamper(self):
        write(self.run / 'prompt.json', {'user': {}})
        self.assertIn('hash mismatch', collect(self.root)['errors'][0]['reason'])

    def test_symlink_ignored(self):
        (self.run / 'prompt.json').unlink()
        outside = self.root / 'secret.json'
        outside.write_text('{"secret":"private"}')
        (self.run / 'prompt.json').symlink_to(outside)
        self.assertEqual(collect(self.root)['runs'], [])
        self.assertNotIn('private', json.dumps(collect(self.root)))

    def test_no_paths_followed(self):
        context = json.loads((self.run / 'proposal-context.json').read_text())
        context['input_sha256'] = {'/not/a/real/path': 'bad'}
        write(self.run / 'proposal-context.json', context)
        self.assertEqual(len(collect(self.root)['runs']), 1)

    def test_missing_reports_are_unknown(self):
        result = report_summary({})
        self.assertIsNone(result['warnings']['no_clock'])
        self.assertIsNone(result['metrics']['worst_setup_slack_ns'])

    def test_report_parser(self):
        result = report_summary({'timing.rpt': ' WNS(ns) TNS(ns)\n ------- -----\n 0.293 0.000\n',
          'utilization.rpt': '| Instance | Module | Total LUTs | FFs | RAMB36 | RAMB18 | DSP Blocks |\n| top | (top) | 73664 | 29542 | 29 | 0 | 16 |'})
        self.assertEqual(result['metrics']['worst_setup_slack_ns'], .293)
        self.assertEqual(result['metrics']['luts'], 73664)
        self.assertEqual(result['metrics']['ramb36'], 29)
        self.assertFalse(result['timing_signoff'])

    def test_flat_utilization_report(self):
        result = report_summary({'utilization.rpt': """
| Site Type | Used | Fixed | Available | Util% |
| Slice LUTs* | 73,664 | 0 | 134600 | 54.73 |
| Slice Registers | 29542 | 0 | 269200 | 10.97 |
| Block RAM Tile | 29.5 | 0 | 365 | 8.08 |
| RAMB36/FIFO* | 29 | 0 | 365 | 7.95 |
| RAMB18 | 1 | 0 | 730 | 0.14 |
| DSPs | 16 | 0 | 740 | 2.16 |
"""})
        self.assertEqual(result['metrics']['luts'], 73664)
        self.assertEqual(result['metrics']['ffs'], 29542)
        self.assertEqual(result['metrics']['bram_tiles'], 29.5)
        self.assertEqual(result['metrics']['ramb36'], 29)
        self.assertEqual(result['metrics']['ramb18'], 1)
        self.assertEqual(result['metrics']['dsp'], 16)
        self.assertIsNone(result['metrics']['power_w'])

    def test_missing_flat_resources_stay_unknown(self):
        result = report_summary({'utilization.rpt': '| CLB LUTs | NaN | 0 | 100 | 0 |'})
        self.assertIsNone(result['metrics']['luts'])
        self.assertIsNone(result['metrics']['bram_tiles'])

    def test_endpoints_and_ui_are_read_only(self):
        try:
            from agent.dashboard import app
        except ImportError:
            self.skipTest('Install dashboard extra for endpoint tests')
        app.config['PQC_REPO_ROOT'] = str(self.root)
        client = app.test_client()
        self.assertEqual(client.get('/api/current').status_code, 200)
        self.assertEqual(client.post('/api/current').status_code, 405)
        self.assertEqual(client.post('/').status_code, 405)
        with client.get('/') as response:
            html = response.get_data(as_text=True)
        self.assertIn('PQC current runs', html)
        self.assertIn('Historical dashboard', html)
        with client.get('/static/current.js') as response:
            js = response.get_data(as_text=True)
        self.assertIn('textContent', js)
        self.assertNotIn('innerHTML', js)
        self.assertNotIn('method:', js)
        with client.get('/legacy') as response:
            self.assertIn('Historical records only', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
