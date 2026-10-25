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

    def test_only_allowlisted_failure_fields_reach_dashboard(self):
        value={'context_sha256':self.context_hash,'status':'FAILED','api_calls_attempted':0,
               'token_count_requests_attempted':1,'failure_stage':'token_count',
               'error_category':'workspace_required','provider_http_status':400,
               'error_type':'SECRET','error_note':'SECRET','api_key':'SECRET','workspace_id':'SECRET'}
        write(self.run/'proposal-run.json',value)
        result=collect(self.root)['runs'][0]
        self.assertEqual(result['failure_stage'],'token_count')
        self.assertEqual(result['error_category'],'workspace_required')
        self.assertEqual(result['provider_http_status'],400)
        self.assertEqual(result['token_count_requests_attempted'],1)
        self.assertNotIn('SECRET',json.dumps(result))
        value.update(failure_stage='SECRET',error_category='SECRET',provider_http_status='SECRET')
        write(self.run/'proposal-run.json',value)
        self.assertNotIn('SECRET',json.dumps(collect(self.root)))

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

    def test_hierarchical_instances_are_ranked_not_summed(self):
        result = report_summary({'utilization.rpt': """
| Instance | Module | Total LUTs | FFs | RAMB36 | RAMB18 | DSP Blocks |
| top | (top) | 100 | 50 | 2 | 0 | 1 |
| A | block_a | 70 | 30 | 1 | 0 | 1 |
| nested | block_n | 60 | 20 | 0 | 0 | 1 |
| B | block_b | 30 | 20 | 1 | 0 | 0 |
"""})
        self.assertEqual(result['metrics']['luts'], 100)
        self.assertEqual([r['instance'] for r in result['resource_instances']], ['A','nested','B'])
        self.assertEqual(report_summary({})['resource_instances'], [])

    def test_setup_and_hold_path_details(self):
        result = report_summary({'timing.rpt': """Slack (MET) : 0.293ns
 Source: DECODER/encode_mode_reg[0]/C
 Destination: ENCODER/PISO_reg[102]/D
 Path Group: clk
 Path Type: Setup (Max at Slow Process Corner)
 Data Path Delay: 14.652ns (logic 4.263ns (29.095%) route 10.389ns (70.905%))
 Logic Levels: 20 (LUT6=10)
Slack (VIOLATED) : -0.201ns
 Source: GEN_Y/OFFSET_reg[0]/C
 Destination: GEN_Y/OFFSET_reg[1]/D
 Path Type: Hold (Min at Fast Process Corner)
"""})
        paths = result['critical_paths']
        self.assertEqual(len(paths), 2)
        self.assertEqual(paths[0]['data_path_delay_ns'], 14.652)
        self.assertEqual(paths[0]['net_delay_ns'], 10.389)
        self.assertEqual(paths[0]['logic_levels'], 20)
        self.assertTrue(paths[1]['path_type'].startswith('Hold'))
        self.assertEqual(paths[1]['slack_ns'], -.201)
        self.assertIsNone(paths[1]['net_delay_ns'])

    def test_hold_summary_kept_separate_from_setup(self):
        result = report_summary({'timing.rpt': ' WNS(ns) TNS(ns) TNS Failing Endpoints TNS Total Endpoints WHS(ns) THS(ns) THS Failing Endpoints THS Total Endpoints\n --- --- --- --- --- --- --- ---\n 0.293 0.000 0 68434 0.201 0.000 0 68434\n'})
        self.assertEqual(result['metrics']['worst_setup_slack_ns'], .293)
        self.assertEqual(result['metrics']['worst_hold_slack_ns'], .201)
        self.assertIsNone(result['metrics']['latency_cycles'])

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

    def test_brand_and_accessibility_markup(self):
        from html.parser import HTMLParser
        class Inspector(HTMLParser):
            def __init__(self):
                super().__init__(); self.ids = []; self.main = 0; self.h1 = 0
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if 'id' in attrs: self.ids.append(attrs['id'])
                if tag == 'main': self.main += 1
                if tag == 'h1': self.h1 += 1
        static = Path(__file__).resolve().parents[1] / 'agent/dashboard_static'
        for filename in ('current.html', 'index.html'):
            text = (static / filename).read_text()
            parser = Inspector(); parser.feed(text)
            self.assertEqual(parser.main, 1)
            self.assertEqual(parser.h1, 1)
            self.assertEqual(len(parser.ids), len(set(parser.ids)))
            self.assertIn('Skip to results', text)
            self.assertIn('hsc-logo.png', text)
            self.assertIn('University_of_Idaho_logo.png', text)
            self.assertIn('aria-current="page"', text)
        css = (static / 'hsc-dashboard.css').read_text()
        self.assertIn('focus-visible', css)
        self.assertIn('prefers-reduced-motion', css)
        def luminance(hex_color):
            channels = [int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4)]
            linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
            return sum(a*b for a,b in zip(linear, (.2126,.7152,.0722)))
        for foreground, background in [('191919','f1b300'),('545454','ffffff'),('735400','ffffff'),('ffffff','191919')]:
            a,b = sorted((luminance(foreground),luminance(background)))
            self.assertGreaterEqual((b+.05)/(a+.05),4.5)

    def test_asic_records_are_included_without_relabeling(self):
        from unittest.mock import patch
        with patch('agent.current_dashboard.collect_asic', return_value={'runs': [{'id':'asic-record','target':'asic'}], 'errors': []}):
            data = collect(self.root)
        self.assertEqual(len(data['runs']), 2)
        self.assertEqual(data['runs'][-1]['target'], 'asic')

    def test_direct_script_import_preserves_package_imports(self):
        try:
            import flask
        except ImportError:
            self.skipTest('Install dashboard extra for entry-point test')
        import runpy
        module = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'agent/dashboard.py'), run_name='dashboard_import_test')
        module['app'].config['PQC_REPO_ROOT'] = str(self.root)
        self.assertEqual(module['app'].test_client().get('/api/current').status_code, 200)

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
        self.assertIn('Run tracking &amp; results', html)
        self.assertIn('Historical experiments', html)
        with client.get('/static/current.js') as response:
            js = response.get_data(as_text=True)
        self.assertIn('textContent', js)
        self.assertNotIn('innerHTML', js)
        self.assertNotIn('method:', js)
        with client.get('/legacy') as response:
            self.assertIn('Historical records only', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
