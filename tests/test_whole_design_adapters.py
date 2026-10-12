"""Built-in adapter tests with no paid calls, simulator, or licensed EDA."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from agent import asic_synthesis
from agent import whole_design as wd
from agent import whole_design_adapters as adapters


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'top.v'
        self.source.write_text('module top;\nreg flag;\nendmodule\n')
        self.run = self.root / 'invocation'
        self.run.mkdir()
        self.request_path, self.response_path = self.run / 'request.json', self.run / 'response.json'
        self.config = {'target': 'asic', 'backend': 'genus', 'top': 'top', 'scope': 'full_design',
                       'source_read_order': [str(self.source)], 'immutable_hashes': {},
                       'measurement': {'stage': 'post_synth', 'period_ns': 5, 'memory_model': 'flops',
                                       'effort': {'generic': 'high', 'map': 'high', 'opt': 'high'},
                                       'tool_version': 'fixture', 'corner': 'fixture', 'seed': 'not_applicable',
                                       'constraints': ['constraints.sdc']}}
        self.request = {'schema_version': 1, 'phase': 'propose', 'configuration': self.config,
                        'source_hashes': wd.hashes([self.source]), 'allowed_files': [str(self.source)],
                        'rtl': {str(self.source): self.source.read_text()}, 'critical_paths': [],
                        'measurement': {'metrics': {'worst_setup_slack_ns': 1}}, 'feedback': []}
        self.proposal = {'status': 'PROPOSED', 'strategy': 'fixture', 'experiment': {'name': 'fixture', 'files': [
            {'path': str(self.source), 'ops': [{'op': 'replace_exact', 'old': 'reg flag;', 'new': 'reg flag2;', 'expect': 1}]}]}}

    def save_request(self):
        wd.save(self.request_path, self.request)

    def mock_model(self, proposal=None, stop_reason='end_turn'):
        reply = SimpleNamespace(stop_reason=stop_reason,
                                content=[SimpleNamespace(type='text', text=json.dumps(proposal or self.proposal))])
        return SimpleNamespace(messages=SimpleNamespace(create=lambda **kwargs: reply))

    def test_proposer_uses_existing_cost_opt_in(self):
        self.save_request()
        with patch.dict(os.environ, {'PQC_ENABLE_LLM': '0'}):
            with self.assertRaisesRegex(RuntimeError, 'disabled'):
                adapters.propose_llm(self.request_path, self.response_path, 'fixture-model')
        self.assertFalse(self.response_path.exists())

    def test_proposer_returns_typed_proposal_without_writing_rtl(self):
        self.save_request()
        with patch.object(adapters.llm_client, 'create_client', return_value=self.mock_model()):
            result = adapters.propose_llm(self.request_path, self.response_path, 'fixture-model')
        self.assertEqual(result['source_model'], 'fixture-model')
        self.assertEqual(result['status'], 'PROPOSED')
        self.assertNotIn('flag2', self.source.read_text())
        self.assertTrue((self.run / 'llm_request.json').is_file())

    def test_proposer_rejects_truncation_outside_paths_and_command_ops(self):
        for mutation in ('truncation', 'path', 'operation'):
            with self.subTest(mutation=mutation):
                proposal = copy.deepcopy(self.proposal)
                stop = 'max_tokens' if mutation == 'truncation' else 'end_turn'
                if mutation == 'path':
                    proposal['experiment']['files'][0]['path'] = str(self.root / 'missing.v')
                if mutation == 'operation':
                    proposal['experiment']['files'][0]['ops'][0]['op'] = 'run_command'
                self.save_request()
                with patch.object(adapters.llm_client, 'create_client', return_value=self.mock_model(proposal, stop)):
                    with self.assertRaises((wd.ContractError, edit_error())):
                        adapters.propose_llm(self.request_path, self.response_path, 'fixture-model')
                self.assertFalse(self.response_path.exists())
                self.assertNotIn('flag2', self.source.read_text())

    def prepare_asic(self):
        library = self.root / 'cells.lib'
        library.write_text('library (fixture) { time_unit : "1ns"; }\n')
        (self.root / 'constraints.sdc').write_text('create_clock -period 5 [get_ports clk]\n')
        site = self.root / 'asic.json'
        wd.save(site, {'schema_version': 1, 'root': '.', 'top': 'top', 'scope': 'full_design',
                       'synthesis_tool': 'genus', 'period_ns': 5, 'memory_model': 'flops',
                       'files': [{'path': 'top.v', 'language': 'verilog'}], 'sdc': 'constraints.sdc',
                       'tools': {'genus': {'target_libraries': ['cells.lib'], 'time_unit': 'ns',
                                           'version': 'fixture', 'corner': 'fixture'}}})
        extractor = self.root / 'extract.py'
        extractor.write_text("import json,pathlib,sys\npathlib.Path(sys.argv[2]).write_text(json.dumps(["
                             "{'id':str(i),'startpoint':'reg'+str(i)+'/Q','endpoint':'out'+str(i)+'/D',"
                             "'instances':['top/u'],'slack_ns':1+i,'report':'timing','line_start':i+1,'line_end':i+1} for i in range(2)]))\n")
        extractor_config = self.root / 'extract.json'
        wd.save(extractor_config, {'argv': [sys.executable, str(extractor), '{timing_report}', '{paths_json}'],
                                   'inputs': [str(extractor)]})
        described = adapters.describe_asic(site)
        self.config['measurement']['asic_effective_config'] = described['asic_effective_config']
        immutable = set(described['required_frozen_inputs']) - {str(self.source)}
        immutable.update([str(extractor), str(extractor_config)])
        self.config['immutable_hashes'] = wd.hashes(immutable)
        self.request['phase'] = 'measure'
        self.save_request()
        return site, extractor_config

    def fake_asic_run(self, plan):
        run = Path(plan['output_root']) / 'genus-fixture'
        run.mkdir()
        wd.save(run / 'manifest.json', plan)
        (run / 'timing.rpt').write_text('Path 1: MET (1 ns) Setup Check\nPath 2: MET (2 ns) Setup Check\n')
        (run / 'area.rpt').write_text('top fixture 10 100\n')
        (run / 'constraint_audit.rpt').write_text('PQC_PERIOD_NATIVE 5\n')
        result = {'status': 'MEASURED', 'tool': 'genus', 'stage': 'post_synth', 'top': 'top',
                  'scope': 'full_design', 'period_ns': 5, 'memory_model': 'flops', 'run_dir': str(run),
                  'library_time_units_verified': True,
                  'metrics': {'worst_setup_slack_ns': 1, 'cell_area_reported': 100, 'area_unit': 'library_unit'},
                  'report_hashes': wd.hashes(run.glob('*.rpt'))}
        wd.save(run / 'result.json', result)
        return result

    def test_asic_cli_adapter_uses_existing_plan_and_fresh_extractor(self):
        site, extractor = self.prepare_asic()
        with patch.object(asic_synthesis, 'run', side_effect=self.fake_asic_run) as run:
            result = adapters.measure_asic(self.request_path, self.response_path, site, extractor)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(result['status'], 'MEASURED')
        self.assertEqual(len(result['critical_paths']), 2)
        self.assertEqual(result['metrics']['cell_area_reported'], 100)

    def test_asic_effective_config_mismatch_blocks_before_tool(self):
        site, extractor = self.prepare_asic()
        self.config['measurement']['asic_effective_config']['compile'] = 'different'
        self.save_request()
        with patch.object(asic_synthesis, 'run', side_effect=AssertionError('must not run')):
            with self.assertRaisesRegex(wd.ContractError, 'effective configuration'):
                adapters.measure_asic(self.request_path, self.response_path, site, extractor)

    def test_mldsa_adapter_refuses_broader_coverage(self):
        self.request['phase'] = 'verify'
        self.config.update(top='combined_top', required_checks=['sign'], operations=['sign'])
        self.save_request()
        from agent.mldsa import full_kat_gate
        with patch.object(full_kat_gate, 'run_full_kat', side_effect=AssertionError('must not run')):
            with self.assertRaisesRegex(wd.ContractError, 'KeyGen-only'):
                adapters.verify_mldsa_keygen(self.request_path, self.response_path, self.root, self.root)
        profile = adapters.mldsa_profile()
        self.assertEqual(len(profile['operations']), 75)
        self.assertEqual(len(profile['required_checks']), 3)

    def test_mldsa_adapter_binds_every_candidate_and_each_vector_latency(self):
        reference = self.root / 'reference'
        immutable = []
        for folder in ('ref_combined/src', 'ref_combined/src_tb', 'common', 'KAT'):
            path = reference / folder
            path.mkdir(parents=True)
            file = path / 'fixture.txt'
            file.write_text('fixture')
            immutable.append(file)
        profile = adapters.mldsa_profile()
        self.config.update({key: profile[key] for key in ('top', 'required_checks', 'operations')})
        self.config['immutable_hashes'] = wd.hashes(immutable)
        self.request['phase'] = 'verify'
        self.save_request()
        def fake_gate(*args, **kwargs):
            work = Path(os.environ['PQC_RUN_DIR']) / 'gate'
            work.mkdir()
            log = work / 'run.log'
            log.write_text('\n'.join(f'ML-DSA-{level}.KeyGen KAT #{i} completed in {100+i} clock cycles'
                                      for level in ('II', 'III', 'V') for i in range(25)) + '\ntestbench done\n')
            wd.save(work / 'sources.json', self.request['source_hashes'])
            wd.save(work / 'vectors.json', [])
            return {'status': 'PASS', 'run_dir': str(work), 'log_file': str(log),
                    'per_vector_file': str(work / 'vectors.json')}
        from agent.mldsa import full_kat_gate
        with patch.object(full_kat_gate, 'run_full_kat', side_effect=fake_gate):
            result = adapters.verify_mldsa_keygen(self.request_path, self.response_path, self.root, reference)
        self.assertEqual(len(result['latency_cycles']), 75)
        self.assertEqual(result['latency_cycles']['mldsa_keygen_II_kat_24'], 124)
        self.assertEqual(result['checks'], dict.fromkeys(profile['required_checks'], 'PASS'))


def edit_error():
    from agent.edit_ops import EditError
    return EditError


if __name__ == '__main__':
    unittest.main()
