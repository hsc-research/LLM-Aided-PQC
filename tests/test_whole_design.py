"""Offline protocol/controller tests. All PPA below is deliberately synthetic."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from agent import whole_design as wd


# A real subprocess fixture tests command dispatch and fresh report binding without
# invoking an EDA installation, a simulator, a network, or an LLM.
ADAPTER = r'''
import hashlib, json, pathlib, sys
request_path, response_path = map(pathlib.Path, sys.argv[1:])
r = json.loads(request_path.read_text())
mode = r['configuration']['measurement']['fixture_mode']
phase = r['phase']
files = [pathlib.Path(x) for x in r['source_hashes']]
changed = sum('flag2' in x.read_text() for x in files)
out = {'schema_version': 1, 'request_sha256': hashlib.sha256(request_path.read_bytes()).hexdigest()}
def report(name, text):
    path = response_path.parent / (name + '.rpt')
    path.write_text(text)
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
if phase == 'verify':
    out.update(status='PASS', scope='full_design', checks={'kat_all': 'PASS', 'handshake': 'PASS'},
               latency_cycles={'encrypt': 20, 'decrypt': 30}, reports={'functional': report('functional', 'FIXTURE ONLY\n')})
    if mode == 'baseline_fail' or (mode == 'candidate_fail' and changed):
        out['status'] = 'FAIL'
    if mode == 'baseline_latency' or (mode == 'missing_latency' and changed):
        del out['latency_cycles']['decrypt']
    if mode == 'latency_regression' and changed:
        out['latency_cycles']['encrypt'] += 1
    if mode == 'source_mutation' and changed:
        files[-1].write_text('CORRUPTED BY FIXTURE')
    if mode == 'config_mutation' and changed:
        pathlib.Path(next(x for x in r['configuration']['immutable_hashes'] if x.endswith('constraints.sdc'))).write_text('CORRUPTED')
elif phase == 'measure':
    slack = 1.0 + changed
    area = 100
    if mode in ('repeat', 'no_improvement'):
        slack = 1.0
    if mode == 'area_regression' and changed:
        area = 101
    if mode == 'timing_regression' and changed:
        slack = 0.5
    instance = 'top/b' if changed else 'top/a'
    out.update(status='MEASURED', scope='full_design', configuration=r['configuration'],
               metrics={'worst_setup_slack_ns': slack, 'cell_area_reported': area, 'lut': area},
               area_unit='fixture_units', reports={'timing': report('timing', 'path one\npath two\n'), 'area': report('area', 'fixture area\n')},
               critical_paths=[{'id': str(i), 'startpoint': 'reg' + str(i) + '/Q', 'endpoint': 'reg' + str(i) + '/D',
                 'instances': [instance], 'slack_ns': slack + i, 'report': 'timing', 'line_start': i+1, 'line_end': i+1} for i in range(2)])
    if mode == 'config_mismatch' and changed:
        out['configuration']['measurement']['period_ns'] += 1
    if mode == 'unmapped':
        out['critical_paths'][0]['instances'] = ['top/unknown']
    if mode == 'bad_report':
        out['reports']['timing']['sha256'] = '0' * 64
    if mode == 'few_paths':
        out['critical_paths'] = out['critical_paths'][:1]
    if mode == 'wrong_path_report':
        out['critical_paths'][0]['report'] = 'area'
    if mode == 'duplicate_path':
        out['critical_paths'][1]['startpoint'] = out['critical_paths'][0]['startpoint']
        out['critical_paths'][1]['endpoint'] = out['critical_paths'][0]['endpoint']
    if mode == 'stale':
        out['request_sha256'] = '0' * 64
elif phase == 'propose':
    path = r['allowed_files'][0]
    out.update(status='PROPOSED', strategy='offline fixture only', source_model='offline_fixture',
      experiment={'name': 'test-' + str(len(r['feedback'])), 'files': [{'path': path, 'ops': [
        {'op': 'replace_exact', 'old': 'reg flag;', 'new': 'reg flag2;', 'expect': 1}]}]})
    if mode == 'stop':
        out['status'] = 'STOP'
    if mode == 'outside_edit':
        out['experiment']['files'][0]['path'] = str(pathlib.Path(path).with_name('b.v'))
response_path.write_text(json.dumps(out))
'''


class WholeDesignTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('a.v', 'b.v'):
            (self.root / name).write_text('module top;\nreg flag;\nendmodule\n')
        (self.root / 'constraints.sdc').write_text('create_clock -period 5 [get_ports clk]\n')
        (self.root / 'adapter.py').write_text(ADAPTER)
        self.config_path = self.root / 'whole.json'
        self.raw = {'schema_version': 1, 'root': '.', 'target': 'asic', 'backend': 'genus',
                    'top': 'top', 'scope': 'full_design', 'sources': ['a.v', 'b.v'],
                    'immutable_inputs': ['constraints.sdc', 'adapter.py'], 'editable_files': ['a.v', 'b.v'],
                    'instance_to_file': {'top/a': 'a.v', 'top/b': 'b.v'},
                    'required_checks': ['kat_all', 'handshake'], 'operations': ['encrypt', 'decrypt'],
                    'area_metric': 'cell_area_reported', 'objective': {'metric': 'worst_setup_slack_ns', 'min_improvement': 0.1},
                    'candidate_budget': 1, 'critical_path_count': 2, 'max_edit_files': 1,
                    'commands': {phase: [sys.executable, str(self.root / 'adapter.py'), '{request}', '{response}']
                                 for phase in ('verify', 'measure', 'propose')},
                    'measurement': {'stage': 'post_synth', 'period_ns': 5, 'tool_version': 'fixture',
                                    'technology': 'fixture', 'corner': 'fixture', 'effort': 'fixture', 'seed': 0,
                                    'memory_model': 'flops', 'constraints': ['constraints.sdc'],
                                    'qualification': 'offline fixture ONLY', 'fixture_mode': 'good'}}

    def config(self, mode='good', **changes):
        self.raw.update(changes)
        self.raw['measurement']['fixture_mode'] = mode
        self.config_path.write_text(json.dumps(self.raw))
        return wd.load_config(self.config_path)

    def run_mode(self, mode='good', **changes):
        controller = wd.Controller(self.config(mode, **changes))
        result = controller.run()
        return controller, result

    def assert_original(self):
        for name in ('a.v', 'b.v'):
            self.assertNotIn('flag2', (self.root / name).read_text())
            self.assertIn('reg flag;', (self.root / name).read_text())

    def test_read_only_plan(self):
        self.config()
        with patch.object(wd, 'run_process', side_effect=AssertionError('must not run')):
            plan = wd.make_plan(self.config_path)
        self.assertEqual(plan['status'], 'CONFIGURED_NOT_RUN')
        self.assertFalse((self.root / '.pqc_runs').exists())

    def test_missing_functional_adapter_or_mapping_blocks_plan(self):
        for key in ('commands', 'instance_to_file'):
            raw = copy.deepcopy(self.raw)
            self.raw.pop(key)
            self.config_path.write_text(json.dumps(self.raw))
            self.assertEqual(wd.make_plan(self.config_path)['status'], 'BLOCKED')
            self.raw = raw

    def test_baseline_failure_prevents_measurement_and_proposals(self):
        controller, result = self.run_mode('baseline_fail')
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(controller.serial, 1)
        self.assertEqual(controller.events, [])
        self.assert_original()

    def test_baseline_missing_latency_blocks(self):
        controller, result = self.run_mode('baseline_latency')
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(controller.serial, 1)

    def test_accept_remeasure_and_recompute_paths(self):
        controller, result = self.run_mode(candidate_budget=2)
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertEqual(result['accepted'], 2)
        self.assertEqual(controller.serial, 8)
        self.assertEqual([row['history_state'] for row in controller.events], ['finally_accepted'] * 2)
        for name in ('a.v', 'b.v'):
            self.assertIn('flag2', (self.root / name).read_text())
        proposals = sorted(controller.directory.glob('*-propose/request.json'))
        self.assertEqual(json.loads(proposals[0].read_text())['allowed_files'], [str(self.root / 'a.v')])
        self.assertEqual(json.loads(proposals[1].read_text())['allowed_files'], [str(self.root / 'b.v')])
        self.assertTrue((controller.directory / 'outcomes.jsonl').is_file())
        from agent.experiment_history import applied_proposals, is_final_acceptance
        self.assertTrue(is_final_acceptance(controller.events[-1]))
        applied = applied_proposals('top', 'whole_design', controller.directory / 'outcomes.jsonl')
        self.assertEqual(len(applied), 1)
        (self.root / 'constraints.sdc').write_text('changed configuration')
        self.assertEqual(applied_proposals('top', 'whole_design', controller.directory / 'outcomes.jsonl'), [])
        evidence = result['final_measurement']['_evidence']
        self.assertTrue(Path(evidence['command']).is_file())
        self.assertEqual(evidence['response_sha256'], hashlib.sha256(Path(evidence['response']).read_bytes()).hexdigest())

    def test_same_controller_for_fpga(self):
        _, result = self.run_mode(target='fpga', backend='vivado', area_metric='lut')
        self.assertEqual(result['accepted'], 1)

    def test_candidate_failure_rolls_back_before_measurement(self):
        controller, result = self.run_mode('candidate_fail')
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertEqual(result['accepted'], 0)
        self.assertEqual(controller.serial, 4)
        self.assert_original()

    def test_latency_metrics_configuration_and_scope_regressions_reject(self):
        for mode in ('missing_latency', 'latency_regression', 'area_regression', 'timing_regression',
                     'config_mismatch', 'outside_edit', 'no_improvement'):
            with self.subTest(mode=mode):
                controller, result = self.run_mode(mode)
                self.assertEqual(result['accepted'], 0)
                self.assertEqual(result['status'], 'COMPLETED')
                self.assert_original()
                self.assertEqual(controller.events[0]['history_state'], 'chip_rejected')

    def test_command_input_mutations_are_restored(self):
        for mode in ('source_mutation', 'config_mutation'):
            with self.subTest(mode=mode):
                controller, result = self.run_mode(mode)
                self.assertEqual(result['accepted'], 0)
                self.assertIn('changed', controller.events[0]['error'])
                self.assert_original()
                self.assertTrue((self.root / 'constraints.sdc').read_text().startswith('create_clock'))

    def test_repeat_attempt_hash_ignores_renamed_proposal(self):
        controller, result = self.run_mode('repeat', candidate_budget=2)
        self.assertEqual(result['accepted'], 0)
        self.assertEqual(controller.serial, 6)  # no repeated functional/EDA work
        self.assertEqual(controller.events[-1]['error'], 'DUPLICATE_ATTEMPT')
        request = json.loads(sorted(controller.directory.glob('*-propose/request.json'))[-1].read_text())
        self.assertEqual(request['feedback'][0]['verdict'], 'NO_REAL_IMPROVEMENT')
        self.assert_original()

    def test_unmapped_missing_and_stale_measurements_block(self):
        for mode in ('unmapped', 'few_paths', 'bad_report', 'stale', 'wrong_path_report', 'duplicate_path'):
            with self.subTest(mode=mode):
                controller, result = self.run_mode(mode)
                self.assertEqual(result['status'], 'BLOCKED')
                self.assertEqual(controller.events, [])
                self.assert_original()

    def test_exception_and_interrupt_restore_candidate(self):
        real = wd.run_process
        for exception in (subprocess.TimeoutExpired('fixture', 1), KeyboardInterrupt()):
            def fail_measure(argv, **kwargs):
                request = json.loads(Path(argv[-2]).read_text())
                if request['phase'] == 'measure' and 'flag2' in (self.root / 'a.v').read_text():
                    raise exception
                return real(argv, **kwargs)
            with self.subTest(exception=type(exception).__name__), patch.object(wd, 'run_process', side_effect=fail_measure):
                controller = wd.Controller(self.config())
                if isinstance(exception, KeyboardInterrupt):
                    with self.assertRaises(KeyboardInterrupt):
                        controller.run()
                else:
                    self.assertEqual(controller.run()['accepted'], 0)
                self.assert_original()
                self.assertTrue((controller.directory / 'result.json').is_file())

    def test_budget_and_changed_byte_limit(self):
        controller, result = self.run_mode(max_changed_bytes=1)
        self.assertEqual(result['accepted'], 0)
        self.assertIn('changed-byte budget', controller.events[0]['error'])
        self.assert_original()
        with self.assertRaises(wd.ContractError):
            self.config(candidate_budget=0)

    def test_interrupt_after_candidate_return_restores_incumbent(self):
        controller = wd.Controller(self.config())
        original = controller.candidate
        def interrupted(*args):
            original(*args)
            raise KeyboardInterrupt()
        with patch.object(controller, 'candidate', side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):
                controller.run()
        self.assert_original()
        self.assertEqual(controller.events[-1]['history_state'], 'chip_rejected')
        self.assertEqual(controller.events[-1]['verdict'], 'INTERRUPTED')

    def test_failed_final_history_write_restores_candidate(self):
        controller = wd.Controller(self.config())
        actual_record = controller.record
        def fail_accepted(event):
            if event['history_state'] == 'finally_accepted':
                raise OSError('fixture disk error')
            return actual_record(event)
        with patch.object(controller, 'record', side_effect=fail_accepted):
            result = controller.run()
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['accepted'], 0)
        self.assert_original()
        self.assertEqual(controller.events[-1]['verdict'], 'HISTORY_WRITE_FAILED')

    def test_power_objective_is_not_accepted(self):
        with self.assertRaises(wd.ContractError):
            self.config(objective={'metric': 'power_w', 'min_improvement': 0.1})

    def test_proposer_stop_is_a_completed_bounded_run(self):
        controller, result = self.run_mode('stop', candidate_budget=10)
        self.assertEqual(result['candidates'], 1)
        self.assertEqual(controller.events[0]['verdict'], 'PROPOSER_STOP')
        self.assert_original()

    def test_asic_translation_uses_real_result_schema(self):
        cfg = self.config()
        contract = wd.configuration(cfg)
        invocation = self.root / 'invocation'
        run = invocation / 'genus-fresh'
        run.mkdir(parents=True)
        request_path, response_path = invocation / 'request.json', invocation / 'response.json'
        sources = wd.hashes(cfg['sources'])
        manifest = {'input_hashes': {**sources, **contract['immutable_hashes']},
                    'files': [{'path': x, 'language': 'verilog'} for x in cfg['sources']],
                    'tool_version_declared': 'fixture', 'library_corner_declared': 'fixture', 'effort': 'fixture', 'time_unit': 'ns', 'root': str(self.root), 'sdc': str(self.root / 'constraints.sdc')}
        contract['measurement']['asic_effective_config'] = {key: value for key, value in manifest.items() if key != 'input_hashes'}
        contract['measurement']['seed'] = 'not_applicable'
        wd.save(request_path, {'configuration': contract, 'source_hashes': sources})
        wd.save(run / 'manifest.json', manifest)
        for file in ('timing.rpt', 'area.rpt', 'constraint_audit.rpt'):
            (run / file).write_text('fixture\n')
        (run / 'constraint_audit.rpt').write_text('PQC_PERIOD_NATIVE 5\n')
        raw = {'status': 'MEASURED', 'tool': 'genus', 'stage': 'post_synth', 'top': 'top',
               'scope': 'full_design', 'period_ns': 5, 'memory_model': 'flops', 'run_dir': str(run),
               'library_time_units_verified': True,
               'metrics': {'worst_setup_slack_ns': 1.0, 'cell_area_reported': 100, 'area_unit': 'fixture_units'},
               'report_hashes': wd.hashes(run.glob('*.rpt'))}
        wd.save(run / 'result.json', raw)
        response = wd.asic_measurement_response(raw, request_path, response_path, [])
        self.assertEqual(response['metrics'], raw['metrics'])
        self.assertFalse(response['workload_power_validated'])
        self.assertIn('timing', response['reports'])
        manifest['input_hashes'][str(self.root / 'a.v')] = '0' * 64
        wd.save(run / 'manifest.json', manifest)
        with self.assertRaisesRegex(wd.ContractError, 'candidate'):
            wd.asic_measurement_response(raw, request_path, response_path, [])


if __name__ == '__main__':
    unittest.main()
