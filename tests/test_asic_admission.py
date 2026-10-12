"""Offline admission contract controls; no vendor tool/RTL is being qualified.

Every qualification document below is deliberately synthetic, temporary test
input. Passing this suite validates fail-closed software/Tcl plumbing only.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent import asic_synthesis as asic


class Admission(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name, text in {'top.v': '// plumbing fixture, not synthesizable RTL',
                           'timing.lib': 'library (fixture) { time_unit : "1ps"; }',
                           'timing.db': 'not a compiled library',
                           'constraints.sdc': '# fixture only'}.items():
            (self.root / name).write_text(text)
        self.cfg = {'schema_version': 1, 'root': '.', 'top': 'top', 'scope': 'test',
                    'period_ns': 1, 'memory_model': 'flops', 'sdc': 'constraints.sdc',
                    'compilation_unit': 'single_ordered_compilation_unit_with_persistent_preprocessor_state',
                    'language_standard': 'verilog2005',
                    'files': [{'path': 'top.v', 'language': 'verilog'}],
                    'admission': {'policy': asic.ADMISSION_POLICY, 'waivers': []},
                    'tools': {tool: {'executable': sys.executable, 'version': 'fixture-version',
                                    'time_unit': 'ps', 'target_libraries': ['timing.' + ext]}
                              for tool, ext in (('genus', 'lib'), ('dc', 'db'))}}
        self.path = self.root / 'config.json'

    def plan(self, tool='genus'):
        self.path.write_text(json.dumps(self.cfg))
        return asic.load_config(self.path, tool)

    def qualify_fixture(self, tool='genus', bad_check=None, bad_phase='pre_synth', memory=None, version=None):
        checks = dict.fromkeys(asic.ADMISSION_CHECKS, 0)
        memories = dict.fromkeys(asic.MEMORY_FIELDS, 0)
        memories.update(memory_inventory_complete=1, mapped_memory_bits=8, flip_flop_memory_bits=8)
        checks_tcl = ' '.join(f'{key} {value}' for key, value in checks.items())
        mem_tcl = ' '.join(f'{key} {value}' for key, value in memories.items())
        code = ('# SYNTHETIC TCL CONTRACT TEST; NOT VENDOR QUALIFICATION\n'
                'proc pqc_admission_snapshot {phase native_report} {\n'
                ' set file [open $native_report w]; puts $file "synthetic raw evidence"; close $file\n'
                f' set checks [dict create {checks_tcl}]\n'
                f' set memory [dict create {mem_tcl}]\n')
        if bad_check:
            code += f' if {{$phase eq "{bad_phase}"}} {{dict set checks {bad_check} 1}}\n'
        for key, value in (memory or {}).items():
            code += f' if {{$phase eq "{bad_phase}"}} {{dict set memory {key} {value}}}\n'
        code += (' return [dict create tool_version ' + asic.word(version or 'fixture-version') +
                 ' checks $checks memory $memory]\n}\n')
        adapter = self.root / 'adapter.tcl'
        adapter.write_text(code)
        self.qualification = {'schema_version': 1, 'policy': asic.ADMISSION_POLICY, 'tool': tool,
                              'tool_version': 'fixture-version', 'reviewed_by': 'synthetic fixture',
                              'reviewed_at': '2000-01-01', 'diagnostic_policy_review': 'synthetic only',
                              'compilation_unit': self.cfg['compilation_unit'],
                              'language_standard': self.cfg['language_standard'],
                              'adapter_hashes': {'adapter.tcl': self.digest(adapter)},
                              'diagnostics': [], 'controls': {}}
        for name in asic.ADMISSION_CONTROLS:
            evidence = self.root / (name + '.txt')
            evidence.write_text('SYNTHETIC control fixture: ' + name)
            self.qualification['controls'][name] = {
                'observed': 'PASS' if name in asic.ADMISSION_POSITIVE_CONTROLS else 'REJECT',
                'evidence': evidence.name, 'sha256': self.digest(evidence)}
        self.save_qualification()
        self.cfg['tools'][tool]['admission_adapter'] = {
            'tcl': 'adapter.tcl', 'qualification': 'qualification.json', 'inputs': []}
        return self.plan(tool)

    def save_qualification(self):
        (self.root / 'qualification.json').write_text(json.dumps(self.qualification))

    @staticmethod
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def report(plan, phase='post_synth', **overrides):
        fields = {'PQC_ADMISSION_SCHEMA': '1', 'PHASE': phase, 'TOOL': plan['tool'],
                  'VERSION': plan['tool_version_declared'], 'TOP': plan['top'],
                  **dict.fromkeys(asic.ADMISSION_CHECKS, 0), **dict.fromkeys(asic.MEMORY_FIELDS, 0)}
        fields.update(memory_inventory_complete=1, mapped_memory_bits=8, flip_flop_memory_bits=8)
        fields.update(overrides)
        return ''.join(f'{key} {value}\n' for key, value in fields.items())

    def run_tcl(self, plan):
        # Stubs validate our control flow, not any DC/Genus command or design.
        stub = ('set search_path {}\n'
                'proc get_db {args} {if {[lindex $args end] eq ".period"} {return 1000}; return 1}\n'
                'proc get_attribute {args} {return 1000}\n'
                'proc syn_generic {args} {set f [open mapping_started w]; close $f}\n'
                'proc compile_ultra {args} {set f [open mapping_started w]; close $f}\n'
                'proc unknown {args} {return 1}\n')
        work = self.root / 'tcl'
        work.mkdir(exist_ok=True)
        (work / 'mapping_started').unlink(missing_ok=True)
        output = subprocess.run(['tclsh'], input=stub + asic.render_tcl(plan), cwd=work,
                                capture_output=True, text=True)
        return output, (work / 'mapping_started').exists()

    def fake_process(self, plan, *, missing=None, overrides=None):
        def run(command, cwd, **kwargs):
            cwd = Path(cwd)
            reports = {'constraint_audit.rpt': 'PQC_PERIOD_NATIVE 1000', 'power.rpt': 'fixture',
                       'netlist.v': 'fixture', 'constraints.sdc': 'fixture'}
            if plan['tool'] == 'genus':
                reports.update({'timing.rpt': 'Path 1: MET (1 ps) Setup Check',
                                'area.rpt': 'top top 25 40.5', 'design.db': 'fixture',
                                'unresolved.rpt': "No unresolved references in design 'top'\nNo empty modules in design 'top'"})
            else:
                reports.update({'timing.rpt': 'Path Type: max\nslack (MET) 1',
                                'area.rpt': 'Number of cells: 25\nTotal cell area: 40.5',
                                'design.ddc': 'fixture', 'units.rpt': 'Time Units : 1ps',
                                'hold.rpt': 'fixture', 'check_timing.rpt': 'fixture'})
            for phase in ('pre_synth', 'post_synth'):
                reports[f'admission_{phase}.rpt'] = self.report(plan, phase, **(overrides or {}))
                reports[f'admission_{phase}_native.rpt'] = 'SYNTHETIC raw evidence'
            for name, value in reports.items():
                if name != missing:
                    (cwd / name).write_text(value)
            return subprocess.CompletedProcess(command, 0, 'PQC_SYNTHESIS_DONE\n')
        return run

    def test_no_adapter_dry_run_cannot_claim_or_launch(self):
        plan = self.plan()
        with patch.object(asic, 'run_process') as process:
            result = asic.run(plan, dry_run=True)
            self.assertEqual(result['admission_qualification'], 'site_qualification_required')
            self.assertFalse(result['admission_passed'])
            self.assertFalse(result['memory_implementation_verified'])
            with self.assertRaisesRegex(ValueError, 'no tool launched'):
                asic.run(plan)
            process.assert_not_called()
        output, mapped = self.run_tcl(plan)
        self.assertNotEqual(output.returncode, 0)
        self.assertFalse(mapped)

    def test_legacy_measurement_explicitly_unverified(self):
        del self.cfg['admission']
        plan = self.plan()
        with patch.object(asic, 'run_process', self.fake_process(plan)):
            result = asic.run(plan)
        self.assertEqual(result['status'], 'MEASURED')
        self.assertFalse(result['structural_checks_verified'])
        self.assertFalse(result['memory_implementation_verified'])
        self.assertIsNone(result['memory_implementation'])

    def test_valid_fixture_pipeline_both_tools_retains_all_evidence(self):
        for tool in ('genus', 'dc'):
            with self.subTest(tool=tool):
                plan = self.qualify_fixture(tool)
                with patch.object(asic, 'run_process', self.fake_process(plan)):
                    result = asic.run(plan)
                self.assertTrue(result['admission_passed'])
                self.assertTrue(result['structural_checks_verified'])
                self.assertTrue(result['memory_implementation_verified'])
                self.assertEqual(result['memory_implementation'], 'flops')
                self.assertFalse(result['memory_semantics_verified'])
                self.assertFalse(result['automatic_acceptance'])
                self.assertEqual(result['qualification_evidence_origin'], 'site_supplied_not_independently_reproduced')
                for phase in ('pre_synth', 'post_synth'):
                    for suffix in ('', '_native'):
                        name = str(Path(result['run_dir']) / f'admission_{phase}{suffix}.rpt')
                        self.assertIn(name, result['report_hashes'])

    def test_required_admission_artifacts_cannot_be_omitted(self):
        plan = self.qualify_fixture()
        for phase in ('pre_synth', 'post_synth'):
            for suffix in ('', '_native'):
                with self.subTest(phase=phase, suffix=suffix), patch.object(
                        asic, 'run_process', self.fake_process(plan, missing=f'admission_{phase}{suffix}.rpt')):
                    with self.assertRaisesRegex(RuntimeError, 'Missing or empty artifact'):
                        asic.run(plan)

    def test_each_structural_fault_rejected_by_python_and_before_mapping(self):
        for key in asic.ADMISSION_CHECKS:
            with self.subTest(check=key):
                plan = self.qualify_fixture(bad_check=key)
                with self.assertRaisesRegex(ValueError, key):
                    asic.validate_admission_report(self.report(plan, **{key: 1}), plan, 'post_synth')
                output, mapped = self.run_tcl(plan)
                self.assertNotEqual(output.returncode, 0, output.stderr)
                self.assertFalse(mapped)

    def test_post_mapping_fault_rejected(self):
        plan = self.qualify_fixture(bad_check='multiple_drivers', bad_phase='post_synth')
        output, mapped = self.run_tcl(plan)
        self.assertTrue(mapped)
        self.assertNotEqual(output.returncode, 0)
        self.assertNotIn('PQC_SYNTHESIS_DONE', output.stdout)

    def test_no_macro_or_blackbox_memory_can_be_waived(self):
        for key in ('memory_macro_cells', 'memory_blackboxes'):
            with self.subTest(key=key):
                plan = self.qualify_fixture(memory={key: 1})
                output, mapped = self.run_tcl(plan)
                self.assertNotEqual(output.returncode, 0)
                self.assertFalse(mapped)
                with self.assertRaisesRegex(ValueError, 'macro-free'):
                    asic.validate_admission_report(self.report(plan, **{key: 1}), plan, 'post_synth')

    def test_post_mapping_ff_bit_accounting_required(self):
        for override in ({'memory_inventory_complete': 0}, {'unmapped_memory_bits': 1},
                         {'mapped_memory_bits': 8, 'flip_flop_memory_bits': 7}):
            with self.subTest(override=override):
                plan = self.qualify_fixture(memory=override, bad_phase='post_synth')
                output, mapped = self.run_tcl(plan)
                self.assertNotEqual(output.returncode, 0)
                with self.assertRaises(ValueError):
                    asic.validate_admission_report(self.report(plan, **override), plan, 'post_synth')

    def test_tcl_valid_fixture_and_live_version_mismatch(self):
        for tool in ('genus', 'dc'):
            plan = self.qualify_fixture(tool)
            output, mapped = self.run_tcl(plan)
            self.assertEqual(output.returncode, 0, output.stderr)
            self.assertTrue(mapped)
            for phase in ('pre_synth', 'post_synth'):
                asic.validate_admission_report((self.root / 'tcl' / f'admission_{phase}.rpt').read_text(), plan, phase)
            plan = self.qualify_fixture(tool, version='different-live-release')
            output, mapped = self.run_tcl(plan)
            self.assertNotEqual(output.returncode, 0)
            self.assertFalse(mapped)

    def test_unknown_duplicate_negative_or_missing_evidence_is_rejected(self):
        plan = self.qualify_fixture()
        good = self.report(plan)
        for text in (good + 'unknown 0\n', good + 'latches 0\n', good.replace('latches 0\n', ''),
                     good.replace('latches 0', 'latches -1'), good.replace('latches 0', 'latches true'),
                     good.replace('VERSION fixture-version', 'VERSION unqualified'),
                     good.replace('PHASE post_synth', 'PHASE pre_synth')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                asic.validate_admission_report(text, plan, 'post_synth')

    def test_qualification_hashes_version_compilation_and_controls_fail_closed(self):
        self.qualify_fixture()
        original = copy.deepcopy(self.qualification)
        mutations = [lambda q: q.update(tool_version='other'),
                     lambda q: q.update(compilation_unit='separate_files'),
                     lambda q: q.update(language_standard='systemverilog2017'),
                     lambda q: q['adapter_hashes'].update({'adapter.tcl': '0' * 64}),
                     lambda q: q['controls'].pop('latches'),
                     lambda q: q['controls']['latches'].update(observed='PASS'),
                     lambda q: q['controls']['known_good_flop_memory'].update(observed='REJECT'),
                     lambda q: q['controls']['memory_macro'].update(sha256='0' * 64)]
        for mutate in mutations:
            self.qualification = copy.deepcopy(original)
            mutate(self.qualification)
            self.save_qualification()
            with self.assertRaises(ValueError):
                self.plan()

    def test_qualified_dependencies_and_controls_in_input_fingerprint(self):
        plan = self.qualify_fixture()
        for name in ('adapter.tcl', 'qualification.json', *[c + '.txt' for c in asic.ADMISSION_CONTROLS]):
            self.assertIn(str(self.root / name), plan['input_hashes'])
        (self.root / 'known_good.txt').write_text('changed after qualification loading')
        with patch.object(asic, 'run_process') as process, self.assertRaisesRegex(ValueError, 'Inputs changed'):
            asic.run(plan)
        process.assert_not_called()

    def test_duplicate_configuration_keys_rejected(self):
        self.path.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            asic.load_config(self.path)

    def test_benign_warning_is_not_blanket_rejected(self):
        asic.validate_tool_log('Warning: vectorless activity uses default toggle rate [POWER-FIXTURE]')
        asic.validate_tool_log('No inferred latches; multiple drivers: 0')
        for warning in ('port width mismatch', 'multiple drivers', 'inferred latch'):
            with self.subTest(warning=warning), self.assertRaises(RuntimeError):
                asic.validate_tool_log('Warning: ' + warning)

    def test_exact_review_waiver_and_fatal_policy(self):
        self.qualify_fixture()
        line = 'Warning: Fixture review diagnostic [FIXTURE-1]'
        self.qualification['diagnostics'] = [
            {'id': 'fixture-review', 'pattern': r'\[FIXTURE-1\]', 'category': 'other',
             'disposition': 'review', 'reason': 'synthetic review-only policy control'},
            {'id': 'fixture-benign', 'pattern': r'\[BENIGN-1\]', 'category': 'other',
             'disposition': 'benign', 'reason': 'synthetic benign warning control'}]
        self.save_qualification()
        with self.assertRaisesRegex(RuntimeError, 'Unwaived'):
            asic.validate_tool_log(line, self.plan()['admission'])
        self.cfg['admission']['waivers'] = [{'diagnostic_id': 'fixture-review',
            'line_sha256': hashlib.sha256(line.encode()).hexdigest(), 'reason': 'reviewed exact instance',
            'approved_by': 'synthetic fixture reviewer'}]
        admission = self.plan()['admission']
        self.assertEqual(len(asic.validate_tool_log(line, admission)['waived']), 1)
        asic.validate_tool_log('Warning: benign [BENIGN-1]', admission)
        with self.assertRaisesRegex(RuntimeError, 'Unwaived'):
            asic.validate_tool_log(line + ' changed instance', admission)
        self.qualification['diagnostics'][0]['disposition'] = 'fatal'
        self.save_qualification()
        with self.assertRaisesRegex(ValueError, 'cannot be waived'):
            self.plan()
        self.qualification['diagnostics'][0].update(disposition='benign', category='latches')
        self.save_qualification()
        with self.assertRaisesRegex(ValueError, 'Invalid reviewed'):
            self.plan()

    def test_strict_macros_configuration_rejected(self):
        self.cfg['memory_model'] = 'macros'
        with self.assertRaisesRegex(ValueError, 'memory_model=flops'):
            self.plan()


if __name__ == '__main__':
    unittest.main()
