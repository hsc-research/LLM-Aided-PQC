"""License-free regressions. Tool executables and generated Tcl use test stubs."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'agent'))
import run_safety as safety
import chip_orchestrator as chip
import experiment_history as history
import asic_synthesis as asic
from hqc import joint_kat_gate as hqc


class TemporaryTree(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.src = self.root / 'rtl'
        self.src.mkdir()
        (self.src / 'a.v').write_text('uncommitted original')
        (self.src / 'b.v').write_text('paired original')
    def tearDown(self):
        self.tmp.cleanup()


class Transactions(TemporaryTree):
    def test_rollback_all_files(self):
        with safety.SourceTransaction(self.root, ['rtl', 'missing.v']):
            (self.src / 'a.v').write_text('changed')
            (self.src / 'b.v').unlink()
            (self.src / 'new.v').write_text('new')
            (self.root / 'missing.v').write_text('new')
        self.assertEqual((self.src / 'a.v').read_text(), 'uncommitted original')
        self.assertEqual((self.src / 'b.v').read_text(), 'paired original')
        self.assertFalse((self.src / 'new.v').exists())
        self.assertFalse((self.root / 'missing.v').exists())
    def test_exception_restores(self):
        with self.assertRaises(RuntimeError):
            with safety.SourceTransaction(self.root, ['rtl']):
                (self.src / 'a.v').write_text('bad')
                raise RuntimeError('tool failure')
        self.assertEqual((self.src / 'a.v').read_text(), 'uncommitted original')
    def test_accept_retains(self):
        with safety.SourceTransaction(self.root, ['rtl']) as transaction:
            (self.src / 'a.v').write_text('accepted')
            transaction.accept()
        self.assertEqual((self.src / 'a.v').read_text(), 'accepted')
    def test_escape_rejected(self):
        with self.assertRaises(ValueError):
            safety.SourceTransaction(self.root, ['../outside'])
    def test_overlap_rejected(self):
        with self.assertRaises(ValueError):
            safety.SourceTransaction(self.root, ['rtl', 'rtl/a.v'])
    def test_symlink_rejected(self):
        (self.root / 'alias').symlink_to(self.src, target_is_directory=True)
        with self.assertRaises(ValueError):
            safety.SourceTransaction(self.root, ['alias'])
    def test_lock(self):
        with safety.RunLock(self.root):
            with self.assertRaises(RuntimeError):
                with safety.RunLock(self.root):
                    pass
    def test_stage_preserves_candidate(self):
        manifest = safety.stage_sources(self.src.glob('*.v'), self.root / 'scratch')
        self.assertEqual((self.root / 'scratch/a.v').read_text(), 'uncommitted original')
        self.assertEqual(len(manifest), 2)
    def test_duplicate_basename_rejected(self):
        (self.root / 'a.v').write_text('different')
        with self.assertRaises(ValueError):
            safety.stage_sources([self.root / 'a.v', self.src / 'a.v'], self.root / 'scratch')
    def test_verdicts_fail_closed(self):
        result = lambda code, text: subprocess.CompletedProcess([], code, text)
        self.assertTrue(safety.gate_passed(result(0, 'GATE: PASS')))
        self.assertFalse(safety.gate_passed(result(1, 'GATE: PASS')))
        self.assertFalse(safety.gate_passed(result(0, 'GATE: PASS\nGATE: FAIL')))
        self.assertFalse(safety.gate_passed(result(0, 'no errors')))
        self.assertTrue(safety.proposal_accepted(result(0, '=== ACCEPTED. ===')))
        self.assertFalse(safety.proposal_accepted(result(0, 'NOT_ACCEPTED')))
    def test_timeout_retains_log(self):
        log = self.root / 'tool.log'
        with self.assertRaises(subprocess.TimeoutExpired):
            safety.run_process(['/bin/sh', '-c', 'echo started; sleep 9'],
                               timeout=0.3, log_path=log)
        self.assertIn('started', log.read_text())


class ChipAcceptance(TemporaryTree):
    def setUp(self):
        super().setUp()
        (self.root / 'baseline.dcp').write_text('baseline checkpoint')
        self.cfg = {'scopes': ['rtl'], 'ckpt': 'baseline.dcp', 'orchestrator': 'fake.py',
                    'kat_gate': ['fake-gate'], 'bracket': (5, 9)}
        self.base = {'closing_fmax_mhz': 100, 'closing_period_ns': 10, 'wns_at_close': 0.1}
    def exercise(self, gate=True, gain=False, mutation=False, failure=None, no_edit=False, log_failure=False):
        calls = []
        def process(argv, **kwargs):
            calls.append(argv)
            if len(calls) == 1:
                if not no_edit:
                    (self.src / 'a.v').write_text('candidate')
                    (self.src / 'b.v').write_text('paired update')
                proposal = {'candidate_id': kwargs['env'][history.PARENT_ID_ENV],
                            'verdict': 'BLOCK_FILTER_PASS', 'evidence_stage': 'block_filter',
                            'design': 'fixture', 'block': 'a', 'strategy': 'fixture',
                            'source_model': 'offline-fixture', 'edits': [{'old': 'a', 'new': 'b'}]}
                return subprocess.CompletedProcess(argv, 0, '=== ACCEPTED. ===\n'
                    + history.FILTER_MARKER + json.dumps(proposal))
            if mutation:
                (self.src / 'a.v').write_text('silently replaced')
            return subprocess.CompletedProcess(argv, 0, 'GATE: ' + ('PASS' if gate else 'FAIL'))
        record = {}
        after = dict(self.base, closing_fmax_mhz=101 if gain else 99)
        with patch.object(chip, 'REPO', self.root), patch.object(chip, 'run_process', process), \
             patch.object(chip, 'source_state', lambda cfg: safety.hashes(self.src.glob('*.v'))), \
             patch.object(chip, 'regen_ckpt', side_effect=failure), \
             patch.object(chip, 'closure_search', return_value=after), \
             patch.object(chip, 'learn_final_candidate'), \
             patch.object(chip, 'log_record', side_effect=OSError('disk full') if log_failure else None):
            accepted = chip.evaluate_candidate(self.cfg, 'rtl/a.v', self.base, 'test', record)
        return accepted, record
    def test_ppa_rejection_restores_pair(self):
        accepted, rec = self.exercise()
        self.assertFalse(accepted)
        self.assertEqual((self.src / 'b.v').read_text(), 'paired original')
        self.assertIn('REJECT_PPA', rec['verdict'])
    def test_failed_gate_restores(self):
        self.assertFalse(self.exercise(gate=False)[0])
        self.assertEqual((self.src / 'a.v').read_text(), 'uncommitted original')
    def test_changed_candidate_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'changed during verification'):
            self.exercise(gain=True, mutation=True)
        self.assertEqual((self.src / 'b.v').read_text(), 'paired original')
    def test_failed_synthesis_restores(self):
        with self.assertRaises(RuntimeError):
            self.exercise(failure=RuntimeError('synth failed'))
        self.assertEqual((self.src / 'a.v').read_text(), 'uncommitted original')
    def test_no_effective_edit_rejected(self):
        accepted, rec = self.exercise(no_edit=True)
        self.assertFalse(accepted)
        self.assertIn('NO_EFFECTIVE', rec['verdict'])
    def test_logging_failure_restores(self):
        with self.assertRaises(OSError):
            self.exercise(gain=True, log_failure=True)
        self.assertEqual((self.src / 'a.v').read_text(), 'uncommitted original')
    def test_success_keeps_pair(self):
        self.assertTrue(self.exercise(gain=True)[0])
        self.assertEqual((self.src / 'b.v').read_text(), 'paired update')
    def test_missing_or_negative_slack_rejected(self):
        for invalid in (None, -0.1, float('nan'), True):
            with self.assertRaises(RuntimeError):
                chip.validate_closure(dict(self.base, wns_at_close=invalid))

    def dispatched_command(self, design, source_file):
        cfg = dict(chip.DESIGNS[design], scopes=['rtl'], ckpt='baseline.dcp')
        record = {}
        with patch.object(chip, 'REPO', self.root), \
             patch.object(chip, 'source_state', return_value={}), \
             patch.object(chip, 'run_process', return_value=subprocess.CompletedProcess(
                 [], 0, 'no_action')) as process:
            self.assertFalse(chip.evaluate_candidate(cfg, source_file, self.base, 'test', record))
        process.assert_called_once()
        return process.call_args.args[0]

    def test_hqc_block_dispatch_supplies_parameter_set(self):
        for block in ('encap', 'decap'):
            with self.subTest(block=block):
                self.assertEqual(self.dispatched_command('hqc', f'build/{block}/{block}.v'),
                                 [sys.executable, 'agent/hqc/transfer_orchestrator.py',
                                  block, 'hqc128'])
        self.assertIn('--all', chip.DESIGNS['hqc']['kat_gate'])

    def test_hqc_joint_dispatch_has_no_block_or_parameter_argument(self):
        self.assertEqual(self.dispatched_command('hqc', 'build/joint_design/hqc_kem_joint_design.v'),
                         [sys.executable, 'agent/hqc/joint_top_orchestrator.py'])

    def test_mldsa_dispatch_does_not_receive_hqc_parameter_set(self):
        self.assertEqual(self.dispatched_command('mldsa', 'agent/mldsa/mldsa_src/rejection_s.v'),
                         [sys.executable, 'agent/mldsa/orchestrator.py', 'rejection_s'])

    def test_unsupported_mapped_blocks_do_not_launch_optimizer(self):
        unsupported = {
            'hqc': ('fixed_weight_ct', 'v_minus_uy', 'vect_set_random', 'keccak_top', 'encrypt'),
            'mldsa': ('encoder', 'coeff_decomposer', 'butterfly'),
        }
        for design, blocks in unsupported.items():
            for block in blocks:
                with self.subTest(design=design, block=block), \
                     patch.object(chip, 'run_process') as process, \
                     patch.object(chip, 'SourceTransaction') as transaction:
                    record = {}
                    self.assertFalse(chip.evaluate_candidate(
                        chip.DESIGNS[design], f'rtl/{block}.v', self.base, 'test', record))
                    self.assertEqual(record['verdict'],
                                     f'NO_TARGET (unsupported optimizer block: {block})')
                    process.assert_not_called()
                    transaction.assert_not_called()

    def test_supported_blocks_match_runner_registries(self):
        from mldsa.orchestrator import BLOCKS
        from synthesizer import MODULE_SOURCES
        self.assertEqual(set(chip.DESIGNS['mldsa']['orchestrator_blocks']), set(BLOCKS))
        self.assertTrue(set(chip.DESIGNS['hqc']['orchestrator_blocks']) <= set(MODULE_SOURCES))


class HQCPrivateWorkspace(TemporaryTree):
    def test_stage_leaves_live_candidate_untouched(self):
        for directory in ('build/keygen/tb', 'build/encap/tb', 'hardware/joint_design/tb',
                          'hardware/common/fixed_weight', 'hardware/common/memory',
                          'hardware/common/shake256/rtl', 'hardware/common/adders',
                          'hardware/common/barrett_reduction', 'hardware/encap/memory_files', 'record'):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        for op in ('keygen', 'encap'):
            (self.root / f'build/{op}/tb/{op}.tcl').write_text('# fixture')
        (self.root / 'hardware/encap/memory_files/seed_align.py').write_text('# fixture')
        (self.root / 'hardware/joint_design/tb/tb.v').write_text('module tb; endmodule')
        fake = types.ModuleType('synthesizer')
        selected = []
        fake.ordered_sources = lambda key: selected.append(key) or [str(self.src / 'a.v'), str(self.src / 'b.v')]
        def seed(argv, **kwargs):
            (Path(kwargs['cwd']) / argv[-2]).write_text('seed')
            return subprocess.CompletedProcess(argv, 0, '')
        work = self.root / 'private'
        work.mkdir()
        with patch.dict(sys.modules, {'synthesizer': fake}), \
             patch.object(hqc.importlib, 'reload', lambda value: value), \
             patch.object(hqc, 'REPO', self.root), patch.object(hqc, 'HERE', self.root / 'record'), \
             patch.object(hqc, 'run_process', seed):
            manifest, original = hqc.stage(work)
            hqc.verify_sources(manifest, original, work)
            pristine_work = self.root / 'pristine-private'
            pristine_work.mkdir()
            hqc.stage(pristine_work, 'hqc_joint_pristine')
        self.assertEqual(selected, ['hqc_joint_opt', 'hqc_joint_pristine'])
        self.assertEqual((self.src / 'a.v').read_text(), 'uncommitted original')
        self.assertEqual((work / 'build/joint_design/a.v').read_text(), 'uncommitted original')
        (work / 'build/joint_design/a.v').write_text('corrupted')
        with self.assertRaises(RuntimeError):
            hqc.verify_sources(manifest, original, work)
    def test_joint_defines_are_set_together(self):
        text = hqc.joint_tcl('tb', 'hqc128', [], {'a.v': 'hash'})
        self.assertEqual(text.count('verilog_define {SHARED=1 SHARED_ENCAP=1}'), 2)
        self.assertIn('parameter_set=\\"hqc128\\"', text)
        self.assertNotIn('git checkout', text)


class ASIC(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for name in ('top.v', 'timing.lib', 'timing.db'):
            (self.root / name).write_text('test fixture only')
        (self.root / 'timing.lib').write_text('library (fixture) { time_unit : "1ps"; }')
        (self.root / 'constraints.sdc').write_text('set fixture_constraint 1')
        self.cfg = {'schema_version': 1, 'root': '.', 'top': 'top', 'scope': 'test',
                    'period_ns': 1, 'memory_model': 'flops', 'sdc': 'constraints.sdc',
                    'files': [{'path': 'top.v', 'language': 'verilog'}],
                    'tools': {name: {'time_unit': 'ps', 'target_libraries': ['timing.' + ext]}
                              for name, ext in (('genus', 'lib'), ('dc', 'db'))}}
        self.path = self.root / 'config.json'
    def tearDown(self):
        self.tmp.cleanup()
    def plan(self, tool='genus'):
        self.path.write_text(json.dumps(self.cfg))
        return asic.load_config(self.path, tool)
    def test_tool_choice(self):
        self.assertEqual(self.plan('dc')['tool'], 'dc')
        self.assertEqual(self.plan()['tool'], 'genus')
    def test_invalid_tool(self):
        with self.assertRaises(ValueError): self.plan('unknown')
    def test_dc_requires_compiled_libraries(self):
        self.cfg['tools']['dc']['target_libraries'] = ['timing.lib']
        with self.assertRaisesRegex(ValueError, '.db'): self.plan('dc')
    def test_missing_inputs(self):
        (self.root / 'top.v').unlink()
        with self.assertRaises(RuntimeError): self.plan()
    def test_invalid_units(self):
        self.cfg['tools']['genus']['time_unit'] = 'guess'
        with self.assertRaises(ValueError): self.plan()
    def test_nonfinite_period(self):
        self.cfg['period_ns'] = float('nan')
        with self.assertRaises(ValueError): self.plan()
    def test_no_wildcard_sources(self):
        self.cfg['files'][0]['path'] = '*.v'
        with self.assertRaises(RuntimeError): self.plan()
    def test_scripts_are_vendor_specific(self):
        genus = asic.render_tcl(self.plan())
        dc = asic.render_tcl(self.plan('dc'))
        self.assertIn('syn_generic\nsyn_map\nsyn_opt', genus)
        self.assertIn('set PQC_PERIOD 1000', genus)
        self.assertIn('hdl_error_on_blackbox true', genus)
        self.assertIn('compile_ultra -no_autoungroup', dc)
        self.assertNotIn('compile_ultra', genus)
    def test_dry_run_does_not_launch(self):
        self.assertEqual(asic.run(self.plan(), dry_run=True)['status'], 'DRY_RUN')
        self.assertFalse((self.root / 'runs').exists())
    def test_no_fallback(self):
        self.cfg['tools']['genus']['executable'] = 'missing-pqc-tool'
        with self.assertRaises(ValueError): asic.run(self.plan())
    def test_explicit_timing_units(self):
        metrics = asic.parse_metrics('genus', 'Path 1: MET (1 ps) Setup Check', 'top top 25 40.5', '', 'ps', 'top', 'library_unit')
        self.assertAlmostEqual(metrics['worst_setup_slack_ns'], 0.001)
        self.assertIsNone(metrics['power_w'])
        self.assertIsNone(metrics['fmax_mhz'])
    def test_dc_power_units(self):
        metrics = asic.parse_metrics('dc', 'Path Type: max\nslack (MET) 1', 'Number of cells: 25\nTotal cell area: 40.5',
            'Total Dynamic Power = 2 mW\nCell Leakage Power = 3 uW', 'ps', 'top', 'library_unit')
        self.assertAlmostEqual(metrics['power_w'], 0.002003)
    def test_missing_slack_fails(self):
        with self.assertRaises(ValueError): asic.parse_metrics('dc', '', '', '', 'ns', 'top', 'library_unit')
    def test_contradictory_slack_fails(self):
        with self.assertRaises(ValueError):
            asic.parse_metrics('genus', 'Path 1: MET (-1 ps) Setup Check', '', '', 'ps', 'top', 'library_unit')
    def mock_tool(self, tool='genus', marker=True, missing=False, error=False):
        exe = self.root / 'fake-tool'
        checkpoint = 'design.db' if tool == 'genus' else 'design.ddc'
        timing = 'Path 1: MET (1 ps) Setup Check' if tool == 'genus' else 'Path Type: max\nslack (MET) 1'
        code = '#!/usr/bin/env python3\nfrom pathlib import Path\n'
        code += f"Path('timing.rpt').write_text({timing!r})\n"
        area = 'top top 25 40.5' if tool == 'genus' else 'Number of cells: 25\nTotal cell area: 40.5'
        code += f"Path('area.rpt').write_text({area!r})\n"
        code += "Path('constraint_audit.rpt').write_text('PQC_PERIOD_NATIVE 1000')\n"
        if tool == 'genus':
            unresolved = "No unresolved references in design 'top'\nNo empty modules in design 'top'\n"
            code += f"Path('unresolved.rpt').write_text({unresolved!r})\n"
        else:
            code += "Path('units.rpt').write_text('Time Units : 1ps')\n"
            code += "Path('check_timing.rpt').write_text('fixture')\n"
            code += "Path('hold.rpt').write_text('fixture')\n"
        for name in ('power.rpt', 'netlist.v', 'constraints.sdc', checkpoint):
            if not (missing and name == 'netlist.v'): code += f"Path({name!r}).write_text('fixture')\n"
        if marker: code += "print('PQC_SYNTHESIS_DONE')\n"
        if error: code += "print('Error: deliberate tool error')\n"
        exe.write_text(code)
        exe.chmod(0o755)
        self.cfg['tools'][tool]['executable'] = str(exe)
        return self.plan(tool)
    def test_mock_genus_run(self):
        result = asic.run(self.mock_tool())
        self.assertEqual(result['status'], 'MEASURED')
        self.assertFalse(result['automatic_acceptance'])
        self.assertTrue(Path(result['run_dir'], 'manifest.json').is_file())
    def test_mock_dc_run(self):
        self.assertEqual(asic.run(self.mock_tool('dc'))['status'], 'MEASURED')
    def test_completion_marker_required(self):
        with self.assertRaises(RuntimeError): asic.run(self.mock_tool(marker=False))
    def test_missing_artifact_fails(self):
        with self.assertRaises(RuntimeError): asic.run(self.mock_tool(missing=True))
    def test_log_error_overrides_exit_zero(self):
        with self.assertRaises(RuntimeError): asic.run(self.mock_tool(error=True))
    def test_input_changes_rejected(self):
        plan = self.mock_tool()
        (self.root / 'top.v').write_text('changed after plan')
        with self.assertRaises(ValueError): asic.run(plan)
    def test_runs_are_separate(self):
        plan = self.mock_tool()
        self.assertNotEqual(asic.run(plan)['run_dir'], asic.run(plan)['run_dir'])
    def test_tcl_quoting(self):
        value = 'a {b} $x [exit] "hello" \\ end'
        done = subprocess.run(['tclsh'], input='puts ' + asic.word(value) + '\n', text=True, capture_output=True)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(done.stdout.strip(), value)
    def test_generated_tcl_syntax_with_stubs(self):
        stub = ('set search_path {}\n'
                'proc get_db {args} {if {[lindex $args end] eq ".period"} {return 1000}; return 1}\n'
                'proc get_attribute {args} {return 1000}\n'
                'proc unknown {args} {return 1}\n')
        for tool in ('genus', 'dc'):
            with tempfile.TemporaryDirectory() as work:
                result = subprocess.run(['tclsh'], input=stub + asic.render_tcl(self.plan(tool)),
                                        cwd=work, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('PQC_SYNTHESIS_DONE', result.stdout)


if __name__ == '__main__':
    unittest.main()
