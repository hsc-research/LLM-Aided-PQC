"""Adversarial target contracts; synthetic measurements only, no EDA or models."""
import copy
import json
import unittest

from agent import target_profiles as tp
from agent import whole_design as wd
from tests import test_whole_design as legacy


STRICT_ADAPTER = legacy.ADAPTER.replace("response_path.write_text(json.dumps(out))", r'''
p = r['configuration'].get('target_profile')
if p and phase != 'propose':
    out.update(configuration=r['configuration'], source_hashes=r['source_hashes'],
               source_read_order=r['configuration']['source_read_order'],
               target_profile_fingerprint=p['profile_fingerprint'])
    if phase == 'verify':
        out.update(coverage_scope='full_selected_design', covered_operations=p['required_operations'])
        if mode == 'wrong_target_gate':
            out['target_profile_fingerprint'] = '0' * 64
        if mode == 'partial_gate':
            out['covered_operations'] = ['keygen']
        if mode == 'stale_source_gate' and changed:
            out['source_hashes'] = p['baseline_source_hashes']
        if mode == 'wrong_define_gate':
            out['configuration']['target_profile']['elaboration']['defines'] = ['OTHER_TARGET']
    else:
        out.update(structural_checks_verified=True, memory_implementation_verified=True,
                   memory_semantics_verified=True, memory_semantics_scope='mapped_implementation',
                   memory_implementation=p['target']['memory_implementation'], admission_passed=True,
                   admission_policy='strict-rtl-flops-v1')
        out['reports'].update(structural=report('structural', 'FIXTURE structure\n'),
                              memory=report('memory', 'FIXTURE memory\n'),
                              memory_semantics=report('memory_semantics', 'FIXTURE equivalence\n'),
                              implementation_netlist=report('implementation_netlist', 'FIXTURE netlist\n'))
        if mode == 'unverified_memory_semantics':
            out['memory_semantics_verified'] = False
        if mode == 'rtl_only_memory_semantics':
            out['memory_semantics_scope'] = 'rtl_simulation'
        if mode == 'missing_netlist':
            del out['reports']['implementation_netlist']
        if mode == 'unverified_memory':
            out['memory_implementation_verified'] = False
        if mode == 'macro_memory':
            out['memory_implementation'] = 'macros'
        if mode == 'wrong_target_measurement':
            out['target_profile_fingerprint'] = 'f' * 64
        if mode == 'missing_memory_report':
            del out['reports']['memory']
if mode == 'edit_define' and phase == 'propose':
    out['experiment']['files'][0]['ops'][0]['new'] = '`define RV_FPGA_OPTIMIZE\nreg flag2;'
response_path.write_text(json.dumps(out))
''')


class TargetAwareTests(legacy.WholeDesignTests):
    # Inherit the fixture setup/helpers, not the legacy test methods.
    def setUp(self):
        super().setUp()
        (self.root / 'adapter.py').write_text(STRICT_ADAPTER)
        (self.root / 'qualification.json').write_text('{"kind":"offline fixture only"}')
        (self.root / 'manifest.json').write_text('{}')
        (self.root / 'bundle').mkdir()
        (self.root / 'cells.lib').write_text('library (fixture) {}')
        self.profile_path = self.root / 'profile.json'
        self.profile = {
            'schema_version': 1, 'profile_kind': 'qualified_source_target_preparation',
            'design': 'mldsa', 'variant': 'guarded-baseline', 'parameter_set': 'II_III_V',
            'target': {'kind': 'asic', 'memory_implementation': 'flops', 'memory_macros': [],
                       'technology_mapping_verified': False, 'memory_compiler_allowed': False},
            'elaboration': {'top': 'top', 'sources': [
                {'path': name, 'language': 'verilog', 'sha256': wd.hashes([self.root / name])[str(self.root / name)]}
                for name in ('a.v', 'b.v')], 'include_dirs': [], 'include_files': [],
                'defines': ['SYNTHESIS'], 'parameters': {}, 'data_files': [], 'compilation_unit': 'shared',
                'global_include_files': [], 'working_directory': 'bundle', 'language_standard': 'verilog2005'},
            'provenance': {'export_manifest': {'path': 'manifest.json', 'sha256': wd.hashes([self.root / 'manifest.json'])[str(self.root / 'manifest.json')]}},
            'boundary': {'scope': 'full_design', 'external_memories': []},
            'qualification': {'source_qualified': True,
                'report': {'path': 'qualification.json', 'sha256': wd.hashes([self.root / 'qualification.json'])[str(self.root / 'qualification.json')]},
                'required_operations': ['keygen', 'sign', 'verify']}}
        self.raw.update(target_profile='profile.json', verification_scope='full_selected_design',
                        required_negative_controls=['handshake'])
        self.raw['immutable_inputs'] += ['profile.json', 'qualification.json', 'cells.lib', 'manifest.json']
        self.raw['measurement']['asic_effective_config'] = {
            'tool': 'genus', 'period_ns': 5, 'sdc': str(self.root / 'constraints.sdc'),
            'files': [{'path': str(self.root / name), 'language': 'verilog'} for name in ('a.v', 'b.v')],
            'include_dirs': [], 'defines': ['SYNTHESIS'], 'parameters': [], 'data_files': [],
            'libraries': [str(self.root / 'cells.lib')], 'top': 'top', 'memory_model': 'flops',
            'compilation_unit': 'shared', 'language_standard': 'verilog2005', 'admission': {'policy': 'strict-rtl-flops-v1', 'waivers': []}}
        self.save_profile()

    def save_profile(self):
        self.profile.pop('profile_fingerprint', None)
        self.profile['profile_fingerprint'] = tp.fingerprint(self.profile)
        wd.save(self.profile_path, self.profile)

    def test_strict_target_baseline_and_candidate_gate(self):
        controller, result = self.run_mode()
        self.assertEqual(result['accepted'], 1)
        self.assertEqual(result['qualification_mode'], 'target_bound')
        self.assertFalse(result['hardware_learning_claim'])
        verify_requests = sorted(controller.directory.glob('*-verify/request.json'))
        self.assertEqual(len(verify_requests), 2)
        baseline, candidate = [json.loads(p.read_text()) for p in verify_requests]
        self.assertNotEqual(baseline['source_hashes'], candidate['source_hashes'])
        self.assertEqual(baseline['configuration'], candidate['configuration'])

    def test_cross_target_profile_blocks_before_command(self):
        with self.assertRaisesRegex(ValueError, 'Cross-target'):
            self.config(target='fpga', backend='vivado', area_metric='lut')

    def test_strict_negative_controls_block_before_measurement(self):
        for mode in ('wrong_target_gate', 'partial_gate', 'wrong_define_gate'):
            with self.subTest(mode=mode):
                controller, result = self.run_mode(mode)
                self.assertEqual(result['status'], 'BLOCKED')
                self.assertEqual(controller.serial, 1)
                self.assert_original()

    def test_strict_measurement_controls_reject_unqualified_target(self):
        for mode in ('unverified_memory', 'macro_memory', 'wrong_target_measurement', 'missing_memory_report',
                     'unverified_memory_semantics', 'rtl_only_memory_semantics', 'missing_netlist'):
            with self.subTest(mode=mode):
                controller, result = self.run_mode(mode)
                self.assertEqual(result['status'], 'BLOCKED')
                self.assertEqual(controller.serial, 2)
                self.assert_original()

    def test_stale_baseline_gate_cannot_qualify_candidate(self):
        controller, result = self.run_mode('stale_source_gate')
        self.assertEqual(result['accepted'], 0)
        self.assertEqual(controller.serial, 4)
        self.assertIn('selected source manifest', controller.events[0]['error'])
        self.assert_original()

    def test_compilation_directive_edits_rejected_before_candidate_gate(self):
        controller, result = self.run_mode('edit_define')
        self.assertEqual(result['accepted'], 0)
        self.assertEqual(controller.serial, 3)
        self.assertIn('frozen compilation directives', controller.events[0]['error'])
        self.assert_original()

    def test_continued_and_inline_directives_are_frozen(self):
        before = "`define MODE \\\n  1\nmodule top; endmodule\n"
        self.assertFalse(tp.unchanged_directives(before, before.replace('  1', '  2')))
        before = "wire a; `define MODE 1\n"
        self.assertFalse(tp.unchanged_directives(before, before.replace('MODE 1', 'MODE 2')))
        self.assertTrue(tp.unchanged_directives('wire a;\n', 'wire b;\n'))

    def test_mixed_profile_sources_and_fingerprints_fail(self):
        for mutation in ('hash', 'order', 'fingerprint', 'design', 'memory', 'define'):
            with self.subTest(mutation=mutation):
                old = copy.deepcopy(self.profile)
                if mutation == 'hash': self.profile['elaboration']['sources'][0]['sha256'] = '0' * 64
                if mutation == 'order': self.profile['elaboration']['sources'].reverse()
                if mutation == 'design': self.profile['design'] = 'hqc'
                if mutation == 'memory': self.profile['target']['memory_implementation'] = 'macros'
                if mutation == 'define': self.profile['elaboration']['defines'] = ['RV_FPGA_OPTIMIZE']
                self.save_profile()
                if mutation == 'fingerprint':
                    changed = dict(self.profile, profile_fingerprint='0' * 64)
                    wd.save(self.profile_path, changed)
                with self.assertRaises(ValueError): self.config()
                self.profile = old
                self.save_profile()

    def test_rehashed_profile_cannot_weaken_full_operation_coverage(self):
        for design, operations in (('mldsa', ['keygen']),
                                   ('mlkem', ['mlkem_keygen', 'mlkem_encaps', 'mlkem_decaps'])):
            with self.subTest(design=design):
                self.profile['design'] = design
                self.profile['qualification']['required_operations'] = operations
                self.save_profile()
                with self.assertRaisesRegex(ValueError, 'mandatory full-design operation'):
                    self.config()

    def test_required_coverage_and_negative_controls_cannot_be_omitted(self):
        for values in ({'verification_profile': 'mldsa_keygen_75', 'top': 'combined_top'},
                       {'verification_scope': 'keygen_only'}, {'required_negative_controls': []}):
            old = copy.deepcopy(self.raw)
            with self.subTest(values=values), self.assertRaises(ValueError): self.config(**values)
            self.raw = old

    def test_undeclared_include_dependency_and_new_file_block(self):
        headers = self.root / 'headers'; headers.mkdir()
        self.profile['elaboration']['include_dirs'] = ['headers']
        self.raw['measurement']['asic_effective_config']['include_dirs'] = [str(headers)]
        self.save_profile()
        cfg = self.config()
        controller = wd.Controller(cfg)
        (headers / 'hidden.vh').write_text('`define HIDDEN 1\n')
        with self.assertRaisesRegex(ValueError, 'changed'):
            controller.unchanged(controller.baseline_sources)
        with self.assertRaisesRegex(ValueError, 'Undeclared HDL'):
            self.config()

    def test_fpga_profile_requires_exact_part_and_inferred_memory(self):
        self.profile['target'].update(kind='fpga', memory_implementation='fpga_inferred_ram')
        self.save_profile()
        self.raw.update(target='fpga', backend='vivado', area_metric='lut')
        self.raw['measurement'].pop('asic_effective_config')
        with self.assertRaisesRegex(ValueError, 'memory_model'): self.config()
        self.raw['measurement']['memory_model'] = 'fpga_inferred_ram'
        with self.assertRaisesRegex(ValueError, 'FPGA part'): self.config()
        self.raw['measurement']['part'] = 'fixture-part-not-hardware'
        _, result = self.run_mode()
        self.assertEqual(result['accepted'], 1)

    def test_bound_history_is_not_reused_without_exact_target_configuration(self):
        from agent.experiment_history import applied_proposals, history_prompt
        controller, result = self.run_mode()
        path = controller.directory / 'outcomes.jsonl'
        self.assertEqual(applied_proposals('top', 'whole_design', path), [])
        self.assertEqual(history_prompt('top', 'whole_design', path), '')
        context = {'target_profile_fingerprint': result['target_profile_fingerprint'],
                   'configuration_sha256': wd.digest(controller.contract)}
        self.assertEqual(len(applied_proposals('top', 'whole_design', path, **context)), 1)
        self.assertIn('ACCEPT', history_prompt('top', 'whole_design', path, **context))
        context['configuration_sha256'] = '0' * 64
        self.assertEqual(applied_proposals('top', 'whole_design', path, **context), [])
        self.assertEqual(history_prompt('top', 'whole_design', path, **context), '')

    def test_cross_target_acceptance_cannot_transfer(self):
        controller, result = self.run_mode('stop')
        before = result['baseline_measurement']
        cfg = copy.deepcopy(controller.cfg)
        cfg['target'] = 'fpga'
        with self.assertRaisesRegex(ValueError, 'different target'):
            wd.acceptance(before, before, {'encrypt': 20}, {'encrypt': 20}, cfg)


# unittest inherits test methods; remove legacy tests because they intentionally
# exercise no-profile behavior and are separately run in test_whole_design.py.
for name in list(legacy.WholeDesignTests.__dict__):
    if name.startswith('test_') and name not in TargetAwareTests.__dict__:
        setattr(TargetAwareTests, name, None)


if __name__ == '__main__': unittest.main()
