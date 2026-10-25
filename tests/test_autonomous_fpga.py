"""Synthetic controller/API tests only. No simulator, EDA, HQC or paid calls."""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from agent import autonomous_fpga as a
from agent import autonomous_design as d


class FakeClient:
    def __init__(self, replies, *, fail=False, usage=None, close_fail=False):
        self.replies = list(replies); self.fail = fail; self.calls = 0
        self.counts = 0; self.close_fail = close_fail; self.before_create = None
        self.usage = usage or types.SimpleNamespace(input_tokens=100, output_tokens=20)
        self.messages = self
    def count_tokens(self, **kwargs):
        self.counts += 1
        return types.SimpleNamespace(input_tokens=100)
    def create(self, **kwargs):
        self.calls += 1
        if self.before_create: self.before_create()
        if self.fail: raise RuntimeError('sk-never-expose-this-provider-secret')
        value = self.replies.pop(0)
        if callable(value): value = value(json.loads(kwargs['messages'][0]['content']))
        raw = value if isinstance(value, str) else json.dumps(value)
        return types.SimpleNamespace(usage=self.usage, stop_reason='end_turn', content=[types.SimpleNamespace(type='text', text=raw)])
    def close(self):
        if self.close_fail: raise RuntimeError('sk-never-expose-close-secret')


def proposal(context, old='reg flag;', new='reg flag2;'):
    return {'status': 'PROPOSED', 'experiment': {'name': 'synthetic', 'files': [
        {'path': context['allowed_files'][0], 'ops': [{'op': 'replace_exact', 'old': old, 'new': new, 'expect': 1}]}]}}


class SyntheticController(a.Controller):
    def __init__(self, *args, qualification=True, failure=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.qualification = qualification; self.failure = failure; self.stages = []; self.contexts = []
    def admission(self, measurement, sources):
        return self.qualification, [] if self.qualification else ['SYNTHETIC mapped-memory proof absent']
    def stage(self, phase, expected):
        self.unchanged(expected); self.remaining(); self.stages.append(phase)
        changed = 'reg flag;' not in Path(self.sources[0]).read_text()
        if changed and self.failure == 'compile' and phase == 'verify': raise ValueError('SYNTHETIC syntax failure')
        if changed and self.failure == 'timeout' and phase == 'verify': raise TimeoutError('SYNTHETIC timeout')
        folder = self.out / f'mock-{len(self.stages):03d}'; folder.mkdir()
        request = {'schema_version': 1, 'phase': phase, 'configuration': self.contract, 'source_hashes': expected}
        a.durable(folder / 'request.json', request)
        response = {'schema_version': 1, 'status': 'PASS' if phase == 'verify' else 'MEASURED',
                    'scope': 'full_design', 'configuration': self.contract, 'reports': {},
                    'critical_paths': [{'id': 'setup-1', 'slack_ns': 1, 'instances': ['top/cell']}],
                    'source_ownership': [{'instance': 'top/cell', 'source_path': self.sources[0], 'source_sha256': expected[self.sources[0]], 'confidence': 'direct_source_property'}],
                    'checks': {k: 'PASS' for k in a.coverage_contract()['required_checks']},
                    'latency_cycles': {k: 100 for k in a.coverage_contract()['operations']},
                    'metrics': {'worst_setup_slack_ns': 1 + int(changed), 'lut': 100}, 'area_unit': 'SYNTHETIC LUTS'}
        if changed and self.failure == 'kat' and phase == 'verify': raise ValueError('SYNTHETIC KAT mismatch')
        if changed and self.failure in ('cycle_up', 'cycle_down') and phase == 'verify':
            response['latency_cycles'][next(iter(response['latency_cycles']))] += 1 if self.failure == 'cycle_up' else -1
        if changed and self.failure == 'timing' and phase == 'measure': response['metrics']['worst_setup_slack_ns'] = -1
        a.durable(folder / 'response.json', response)
        response['_evidence'] = {'request': str(folder/'request.json'), 'request_sha256': a.hashes([folder/'request.json'])[str(folder/'request.json')],
                                 'response': str(folder/'response.json'), 'response_sha256': a.hashes([folder/'response.json'])[str(folder/'response.json')]}
        return response
    def context(self, *args):
        value = super().context(*args); self.contexts.append(value); return value


class AutonomousTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.bundle = self.root / 'profile'; (self.bundle/'rtl').mkdir(parents=True)
        self.source = self.bundle/'rtl/top.v'; self.source.write_text('module combined_top(input clk);\nreg flag;\nendmodule\n')
        self.xdc = self.root/'clock.xdc'; self.xdc.write_text('create_clock -period 15 [get_ports clk]\n')
        self.settings_file = self.root/'settings.json'; self.settings_file.write_text('{}')
        self.prep = self.root/'preparation.json'; self.prep.write_text('{}')
        self.profile_file = self.bundle/'profile.json'; self.profile_file.write_text('{}')
        self.settings = {'path': str(self.settings_file), 'preparation': str(self.prep), 'profile_path': str(self.profile_file),
                         'mode': 'strict', 'limits': {**a.DEFAULTS, 'iterations': 2, 'generation_attempts': 3, 'context_requests': 1},
                         'provider': {'model': 'synthetic-model', 'input_usd_per_million': '1', 'output_usd_per_million': '1', 'budget_usd': '1'},
                         'sources': [str(self.source)], 'editable_files': [str(self.source)],
                         'prepared': {'input_sha256': a.hashes([self.xdc])},
                         'objective': {'metric': 'worst_setup_slack_ns', 'min_improvement': 0.1}, 'minimum_slack_ns': 0,
                         'launch': {'part': 'xc7a200tfbg676-1', 'period_ns': 15, 'tool_version': 'SYNTHETIC', 'xdc': str(self.xdc)},
                         'profile': {'profile_fingerprint': 'f'*64, 'target': {'kind': 'fpga', 'memory_implementation': 'fpga_inferred_ram'},
                                     'bundle_files_sha256': {}, 'elaboration': {'top': 'combined_top', 'sources': [{'path': 'rtl/top.v', 'language': 'verilog'}],
                                      'include_files': [], 'data_files': [], 'include_dirs': ['rtl'], 'global_include_files': [], 'parameters': {}, 'defines': [], 'working_directory': 'rtl'}}}
        self.env = patch.dict(os.environ, {'PQC_ENABLE_LLM': '1'}); self.env.start(); self.addCleanup(self.env.stop)
    def controller(self, replies, **kwargs):
        client = FakeClient(replies)
        controller = SyntheticController(copy.deepcopy(self.settings), self.root/'run', client_factory=lambda: client, **kwargs)
        return controller, client
    def assert_baseline(self): self.assertIn('reg flag;', self.source.read_text())

    def test_exploratory_mode_never_promotes_even_with_qualified_fixture(self):
        self.settings['mode'] = 'exploratory'
        c, _ = self.controller([proposal, {'status': 'STOP'}], qualification=True)
        result = c.run()
        self.assertEqual(result['accepted'], 0)
        self.assertIsNone(result['best_snapshot'])
        self.assertEqual(result['status'], 'EXPLORATION_COMPLETED_UNQUALIFIED')
    def test_missing_ownership_stops_before_provider_setup(self):
        c, client = self.controller([])
        original = c.stage
        def stage(*args):
            value = original(*args); value['source_ownership'] = []; return value
        c.stage = stage
        result = c.run()
        self.assertEqual(result['status'], 'BLOCKED'); self.assertEqual(client.calls, 0)
        self.assertIsNone(c.client)
    def test_exploratory_focus_is_explicit_and_not_ownership_proof(self):
        self.settings.update(mode='exploratory', exploratory_focus=['rtl/top.v'])
        c, client = self.controller([{'status': 'STOP'}], qualification=False)
        original = c.stage
        def stage(*args):
            value = original(*args); value['source_ownership'] = []; return value
        c.stage = stage
        result = c.run()
        self.assertEqual(client.calls, 1)
        self.assertIn('unverified', c.contexts[0]['edit_scope_basis'])
    def test_malformed_response_stops_without_retry(self):
        c, client = self.controller(['not JSON'])
        result = c.run(); self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(client.calls, 1); self.assertIsNone(result['pending_request'])
    def test_count_failure_is_sanitized_without_generation(self):
        c, client = self.controller([])
        def fail(**unused): raise RuntimeError('sk-count-endpoint-secret')
        client.count_tokens = fail
        result = c.run(); self.assertEqual(client.calls, 0)
        self.assertNotIn('sk-count', json.dumps(result))
    def test_prompt_limit_stops_before_unlock(self):
        c, client = self.controller([]); c.limits['max_prompt_bytes'] = 100
        result = c.run(); self.assertEqual(result['status'], 'BLOCKED')
        self.assertIsNone(c.client); self.assertEqual(client.calls, 0)
    def test_measurement_response_tamper_is_detected(self):
        c, _ = self.controller([{'status': 'STOP'}]); c.run()
        (c.out/'mock-002/response.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Persisted record'): a.inspect_run(c.out)
    def test_dashboard_autonomous_record_is_read_only_and_provisional(self):
        from agent.current_dashboard import autonomous
        self.settings['mode'] = 'exploratory'
        c, _ = self.controller([proposal, {'status': 'STOP'}], qualification=False); c.run()
        row = autonomous(c.out)
        self.assertEqual(row['kind'], 'autonomous_fpga'); self.assertEqual(row['provisional_count'], 1)
        self.assertFalse(row['target_tool_qualified']); self.assertFalse(row['timing_signoff'])
        (c.out/'state.json').write_text('{}')
        with self.assertRaises(ValueError): autonomous(c.out)

    def test_strict_unqualified_baseline_never_unlocks_or_calls(self):
        c, client = self.controller([], qualification=False)
        result = c.run()
        self.assertEqual(result['status'], 'BASELINE_BLOCKED'); self.assertIsNone(c.client)
        self.assertEqual(client.calls, 0); self.assert_baseline()
    def test_candidate_accepted_then_feedback_reaches_next_proposal(self):
        c, client = self.controller([proposal, {'status': 'STOP'}])
        result = c.run()
        self.assertEqual(result['accepted'], 1); self.assertEqual(result['best_snapshot'], 'accepted-001')
        self.assertEqual(client.calls, 2); self.assert_baseline()
        self.assertEqual(c.contexts[1]['feedback'][-1]['verdict'], 'ACCEPT')
        self.assertIn('reg flag2;', (c.out/'accepted-001/rtl/top.v').read_text())
        self.assertTrue(a.inspect_run(c.out)['integrity_checked'])
    def test_exploration_tests_measures_then_rolls_back_without_best(self):
        self.settings['mode'] = 'exploratory'
        c, client = self.controller([proposal, {'status': 'STOP'}], qualification=False)
        result = c.run()
        self.assertEqual(result['status'], 'EXPLORATION_COMPLETED_UNQUALIFIED')
        self.assertEqual(result['accepted'], 0); self.assertIsNone(result['best_snapshot'])
        self.assertEqual(c.stages, ['verify', 'measure', 'verify', 'measure'])
        self.assertEqual(result['current_sources'], result['baseline_sources']); self.assert_baseline()
        self.assertEqual(c.contexts[1]['feedback'][-1]['verdict'], 'PROVISIONAL_NOT_ACCEPTED')
    def test_failures_feedback_and_no_measurement_on_failed_verification(self):
        for reason in ('compile', 'kat', 'cycle_up', 'cycle_down', 'timeout'):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as folder:
                c, client = self.controller([proposal, {'status': 'STOP'}], failure=reason)
                c.out = Path(folder)/'run'
                result = c.run()
                self.assertEqual(result['accepted'], 0)
                self.assertEqual(c.stages, ['verify', 'measure', 'verify'])
                self.assertEqual(c.contexts[1]['feedback'][-1]['verdict'], 'REJECTED')
                self.assertEqual(result['current_sources'], result['baseline_sources']); self.assert_baseline()
    def test_timing_regression_rolls_back(self):
        c, _ = self.controller([proposal, {'status': 'STOP'}], failure='timing')
        result = c.run(); self.assertEqual(result['accepted'], 0)
        self.assertEqual(c.history[1]['verdict'], 'TIMING_FLOOR'); self.assert_baseline()
    def test_stop_never_requests_more_context(self):
        c, client = self.controller([{'status': 'STOP', 'requests': [{'path': 'invalid'}]}])
        result = c.run(); self.assertEqual(client.calls, 1); self.assertEqual(result['context_requests'], 0)
    def test_need_context_is_bounded_and_fed_back(self):
        def context_request(ctx):
            return {'status': 'NEED_CONTEXT', 'requests': [{'path': ctx['allowed_files'][0], 'line_start': 1, 'line_end': 2}]}
        c, client = self.controller([context_request, {'status': 'STOP'}])
        result = c.run(); self.assertEqual(result['context_requests'], 1); self.assertEqual(client.calls, 2)
        self.assertEqual(c.contexts[1]['read_only_requested_context'][0]['role'], 'read_only_not_edit_permission')
    def test_context_outside_manifest_stops(self):
        c, client = self.controller([{'status': 'NEED_CONTEXT', 'requests': [{'path': '/etc/passwd', 'line_start': 1, 'line_end': 2}]}])
        result = c.run(); self.assertEqual(result['status'], 'BLOCKED'); self.assertEqual(client.calls, 1)
    def test_generation_limit_and_duplicate_candidate(self):
        self.settings['limits'].update(iterations=3, generation_attempts=2)
        self.settings['mode'] = 'exploratory'
        c, client = self.controller([proposal, proposal], qualification=False)
        result = c.run(); self.assertEqual(client.calls, 2)
        self.assertEqual(result['accepted'], 0); self.assertIn('Repeated', c.history[-1]['reason'])
    def test_cost_reservation_is_durable_before_dispatch(self):
        c, client = self.controller([{'status': 'STOP'}])
        def check():
            record = json.loads((c.out/'state.json').read_text())
            self.assertEqual(record['pending_request'], 1)
            self.assertGreater(float(record['reserved_usd']), 0)
            self.assertTrue((c.out/'proposal-001/reservation.json').is_file())
        client.before_create = check
        self.assertEqual(c.run()['spent_usd'], '0.00012')
    def test_unknown_cost_stops_with_reservation_and_no_retry(self):
        c, client = self.controller([]); client.fail = True
        result = c.run(); self.assertEqual(result['status'], 'COST_UNKNOWN_STOP')
        self.assertEqual(client.calls, 1); self.assertEqual(result['pending_request'], 1)
        self.assertNotIn('sk-never', json.dumps(result))
        with self.assertRaisesRegex(ValueError, 'Pending/uncertain'): a.inspect_run(c.out)
    def test_budget_blocks_before_generation(self):
        self.settings['provider']['budget_usd'] = '0.000001'
        c, client = self.controller([])
        self.assertEqual(c.run()['status'], 'BLOCKED'); self.assertEqual(client.calls, 0)
    def test_invalid_usage_keeps_reservation(self):
        c, client = self.controller([{'status': 'STOP'}]); client.usage = types.SimpleNamespace(input_tokens=True, output_tokens=2)
        result = c.run(); self.assertEqual(result['status'], 'COST_UNKNOWN_STOP'); self.assertEqual(client.calls, 1)
    def test_usage_over_reservation_stops(self):
        c, client = self.controller([{'status': 'STOP'}]); client.usage = types.SimpleNamespace(input_tokens=1000000, output_tokens=2)
        result = c.run(); self.assertEqual(result['status'], 'BLOCKED'); self.assertEqual(client.calls, 1)
        self.assertGreater(float(result['spent_usd']), 1)
    def test_close_failure_is_sanitized_and_state_persisted(self):
        c, client = self.controller([{'status': 'STOP'}]); client.close_fail = True
        result = c.run(); self.assertNotIn('sk-never', json.dumps(result))
        self.assertEqual(json.loads((c.out/'state.json').read_text())['status'], 'COMPLETED')
    def test_existing_run_cannot_dispatch_again(self):
        c, _ = self.controller([{'status': 'STOP'}]); c.run()
        with self.assertRaisesRegex(ValueError, 'Fresh run'): a.Controller(self.settings, c.out)
    def test_inspection_detects_source_and_journal_tampering(self):
        c, _ = self.controller([{'status': 'STOP'}]); c.run()
        path = c.out/'journal/0000.json'; text = path.read_text(); path.write_text(text.replace('BASELINE_QUALIFIED', 'FORGED'))
        with self.assertRaisesRegex(ValueError, 'Persisted record'): a.inspect_run(c.out)
    def test_environment_never_inherits_provider_credentials(self):
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'secret', 'PQC_VAULT_PASSPHRASE': 'secret', 'ANTHROPIC_WORKSPACE_ID': 'secret', 'OTHER_TOKEN': 'secret'}):
            env = a.child_environment(); self.assertNotIn('secret', env.values())
    def test_profile_lock_prevents_concurrent_run(self):
        with a.profile_lock(self.profile_file):
            with self.assertRaisesRegex(ValueError, 'Another autonomous'):
                with a.profile_lock(self.profile_file): pass
    def test_runtime_ceiling_prevents_more_work(self):
        c, client = self.controller([proposal]); c.started -= c.limits['runtime_seconds']+1
        result = c.run(); self.assertEqual(result['status'], 'BLOCKED'); self.assertEqual(client.calls, 0)


class PreparedExportTests(unittest.TestCase):
    def test_real_prepared_export_builds_isolated_contract_without_tools(self):
        from tools.export_target_profiles import export_profile, prepare, site_template
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            profile = export_profile('mldsa', 'fpga-latch-corrected-baseline', None, 'fpga', root/'profile')
            xdc = root/'clock.xdc'; xdc.write_text('create_clock -period 15 [get_ports clk]\n')
            site = site_template(profile)
            site.update(period_ns=15, constraints=str(xdc), tool_version='2022.2', part='xc7a200tfbg676-1', output_root=str(root/'unused-vivado'))
            a.durable(root/'site.json', site)
            prepare(root/'profile/profile.json', root/'site.json', root/'launch')
            config = {'schema_version': 1, 'preparation': 'launch/preparation.json', 'mode': 'strict',
                      'editable_files': ['source-bundle/rtl/gen_c.v'],
                      'provider': {'model': 'synthetic-no-call', 'input_usd_per_million': '1', 'output_usd_per_million': '1', 'budget_usd': '1'}}
            a.durable(root/'config.json', config)
            settings = a.load_settings(root/'config.json')
            c = a.Controller(settings, root/'run', client_factory=lambda: self.fail('No provider may run'))
            c.setup(); c.unchanged(c.baseline)
            self.assertEqual(len(c.sources), 35)
            self.assertEqual(len(c.cfg['operations']), 210)
            self.assertEqual(c.cfg['measurement']['effort'], 'default')
            self.assertEqual(c.cfg['measurement']['qualification'], {'io_exceptions': []})
            self.assertIn(str(a.ROOT/'tools/export_target_profiles.py'), c.immutable)
            self.assertTrue((c.out/'design-model.json').is_file())
            self.assertFalse((root/'unused-vivado').exists())


class SourceSafetyTests(unittest.TestCase):
    def test_foreign_code_and_comment_activation_rejected_without_execution(self):
        before = 'module top;\nreg flag;\nendmodule\n'
        payloads = [before.replace('reg flag;', 'import "DPI-C" function int system(input string s);'),
                    before.replace('reg flag;', 'initial $c("unsafe");'),
                    before.replace('reg flag;', 'initial $display("PASS");'),
                    before.replace('reg flag;', '/* verilator sc_bv */ reg flag;')]
        for after in payloads:
            with self.subTest(after=after), self.assertRaises(ValueError): a.unsafe_candidate(before, after)
        before = 'module top;\n/*\ninitial $system("unsafe");\n*/\nendmodule\n'
        with self.assertRaises(ValueError): a.unsafe_candidate(before, before.replace('/*\n', '').replace('*/\n', ''))
    def test_foreign_metacomment_payload_cannot_replace_existing_comment(self):
        before = 'module top;\n/* placeholder */\nreg flag;\nendmodule\n'
        for directive in ('systemc_ctor', 'systemc_header', 'systemc_imp_header'):
            after = before.replace('/* placeholder */', '/*'+directive+'\n system("synthetic only");\n*/')
            with self.subTest(directive=directive), self.assertRaisesRegex(ValueError, 'frozen comments'):
                a.unsafe_candidate(before, after)

    def test_interfaces_and_preprocessor_are_frozen(self):
        before = 'module top(input clk);\nreg flag;\nendmodule\n'
        with self.assertRaises(ValueError): a.unsafe_candidate(before, before.replace('input clk', 'input other'))
        with self.assertRaises(ValueError): a.unsafe_candidate(before, '`include "other.v"\n'+before)
    def test_pure_rtl_edit_allowed(self):
        a.unsafe_candidate('module top;\nreg flag;\nendmodule\n', 'module top;\nreg flag2;\nendmodule\n')
    def test_lexical_model_is_source_bound_and_not_training(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'top.v'; p.write_text('module top;\nchild u_child();\nendmodule\nmodule child; endmodule\n')
            result = d.model(a.hashes([p]), 'top', 'f'*64)
            self.assertFalse(result['training_performed'])
            self.assertEqual(result['instantiation_candidates'][0]['confidence'], 'lexical_candidate_not_elaborated')
            self.assertEqual(result['sources'][0]['modules'][0]['line_start'], 1)


if __name__ == '__main__': unittest.main()
