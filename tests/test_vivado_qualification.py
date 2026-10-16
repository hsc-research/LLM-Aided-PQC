"""Synthetic license-free report fixtures; these do not qualify Vivado or RTL."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from agent import fpga_feedback as feedback
from agent import vivado_qualification as q
from agent.run_safety import hashes
from agent.whole_design import save


def encoded(*values):
    return '\t'.join(str(value).encode().hex() for value in values) + '\n'


def check_timing(changes=None):
    changes = changes or {}
    return '\n'.join(f'{i}. checking {name} ({changes.get(name, 0)})' for i, name in enumerate(q.CHECKS, 1)) + '\n'


def timing_summary(setup='0.100', hold='0.050'):
    return ('Enable Multi Corner Analysis : Yes\nIgnore I/O Paths : No\nSlow Yes Yes\nFast Yes Yes\n'
            'WNS(ns) TNS(ns) TNS Failing Endpoints TNS Total Endpoints WHS(ns) THS(ns) THS Failing Endpoints THS Total Endpoints\n'
            '------- ------- ------- ------- ------- ------- ------- -------\n'
            f'{setup} 0.000 0 100 {hold} 0.000 0 100\n')


def emit_reports(run, source, latch=False, ownership=True, no_clock=0, io_missing=False):
    rows = [('meta', 'schema', q.SCHEMA), ('meta', 'tool_version', '2022.2'),
            ('meta', 'tool_build', 'Vivado 2022.2 SYNTHETIC FIXTURE ONLY'),
            ('meta', 'part', 'xc7a200tfbg676-1'), ('meta', 'top', 'combined_top'),
            ('meta', 'stage', 'post_synth'), ('meta', 'mode', 'out_of_context'),
            ('meta', 'effort', 'default'), ('meta', 'seed', 'not_applicable'),
            ('meta', 'primitive_count', '7' if latch else '6'),
            ('meta', 'latch_inventory_count', '1' if latch else '0'),
            ('meta', 'blackbox_count', '0'),
            ('clock', 'clk', '15.0', '0', 'clk'),
            ('port', 'clk', 'IN', '1'), ('port', 'din', 'IN', '0'), ('port', 'dout', 'OUT', '0')]
    for i in range(5):
        rows.append(('cell', f'u/r{i}', 'FDRE', 'REGISTER.FLOP.FDRE', 'FLOP', 'FLOP', str(source) if ownership else '', '1'))
    rows += [('cell', 'u/ram', 'RAMB36E1', 'BLOCKRAM.BRAM.RAMB36E1', '', 'BRAM', str(source), '1'),
             ('memory_property', 'u/ram', 'WRITE_MODE_A', 'READ_FIRST'),
             ('memory_property', 'u/ram', 'INIT_00', "256'h0")]
    if latch:
        rows += [('cell', 'u/latch', 'LDCE', 'REGISTER.LATCH.LDCE', 'LATCH', 'LATCH', str(source), '1'),
                 ('latch', 'u/latch')]
    for port in ('din', 'dout'):
        for delay in ('max', 'min'):
            rows.append(('port_timing', port, delay, '1', 'INFINITY' if io_missing else '0.1', '0'))
    for name in sorted(q.DRC_CHECKS):
        rows.append(('drc_check', name, '1'))
    details = []
    for kind in ('setup', 'hold'):
        for i in range(5):
            name = f'{kind}-{i+1}'; slack = '0.100' if kind == 'setup' else '0.050'
            rows += [('path', name, kind, f'u/r{i}/Q', f'u/r{i}/D', slack), ('path_cell', name, f'u/r{i}')]
            details += [f'PQC_PATH_BEGIN {name}', f'Slack (MET) : {slack}ns (required time - arrival time)',
                        f'  Source: u/r{i}/Q', f'  Destination: u/r{i}/D',
                        f'  Path Type: {kind.title()} (fixture only)', f'PQC_PATH_END {name}']
    rows.append(('meta', 'complete', '1'))
    (run / 'objects.tsv').write_text(''.join(encoded(*r) for r in rows))
    (run / 'paths.rpt').write_text('\n'.join(details) + '\n')
    (run / 'check_timing.rpt').write_text(check_timing({'no_clock': no_clock, 'no_input_delay': 1 if io_missing else 0}))
    (run / 'timing.rpt').write_text(timing_summary())
    (run / 'tool-version.txt').write_text('2022.2\n')
    (run / 'utilization.rpt').write_text('| Slice LUTs | 100 | 0 | 10000 |\n| Slice Registers | 5 | 0 | 10000 |\n| Block RAM Tile | 1 | 0 | 100 |\n| DSPs | 0 | 0 | 100 |\n')
    (run / 'effective.xdc').write_text('create_clock -period 15 [get_ports clk]\nset_input_delay -clock clk 1 [get_ports din]\nset_output_delay -clock clk 1 [get_ports dout]\n')
    for name in q.RAW_REPORTS:
        if not (run / name).exists():
            (run / name).write_text('SYNTHETIC FIXTURE ONLY, not actual EDA evidence\n')


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'top.v'; self.source.write_text('module combined_top; endmodule\n')
        self.xdc = self.root / 'constraints.xdc'; self.xdc.write_text('create_clock -period 15 [get_ports clk]\n')
        self.cfg = {'target': 'fpga', 'backend': 'vivado', 'top': 'combined_top',
                    'source_read_order': [str(self.source)], 'immutable_hashes': hashes([self.xdc, *q.dependencies()]),
                    'measurement': {'stage': 'post_synth', 'period_ns': 15, 'constraints': [str(self.xdc)],
                                    'tool_version': '2022.2', 'part': 'xc7a200tfbg676-1'},
                    'target_profile': {'design': 'mldsa', 'profile_fingerprint': 'synthetic-fixture',
                                       'boundary': {'clock_ports': ['clk']},
                                       'elaboration': {'sources': [{'path': str(self.source), 'language': 'verilog'}],
                                                       'parameters': {}, 'defines': [], 'include_dirs': [], 'data_files': []}}}
        self.request = {'schema_version': 1, 'phase': 'measure', 'configuration': self.cfg,
                        'source_hashes': hashes([self.source])}
        self.request_file = self.root / 'request.json'; save(self.request_file, self.request)
        self.run = self.root / 'vivado'

    def fixture(self, **kwargs):
        self.run.mkdir()
        emit_reports(self.run, self.source, **kwargs)
        return q.evaluate(self.run, self.request)

    def execute_fixture(self, **kwargs):
        def process(argv, **options):
            emit_reports(self.run, self.source, **kwargs)
            Path(options['log_path']).write_text('SYNTHETIC process fixture\n')
            return subprocess.CompletedProcess(argv, 0, 'SYNTHETIC process fixture', '')
        with patch.object(feedback, 'run_process', side_effect=process):
            return feedback.collect(self.request_file, self.root / 'response.json', execute=True)

    def test_clean_observable_checks_pass_but_memory_behavior_does_not(self):
        result = self.fixture()
        self.assertEqual(result['gates'], {'setup_timing': 'PASS', 'hold_timing': 'PASS', 'structural': 'PASS', 'constraint_coverage': 'PASS',
                         'path_ownership': 'PASS', 'mapped_memory_inventory': 'PASS', 'mapped_memory_semantics': 'UNVERIFIED'})
        self.assertEqual(result['metrics']['worst_hold_slack_ns'], 0.05)
        self.assertEqual(result['source_ownership'][0]['confidence'], 'direct_source_property')

    def test_known_bad_baseline_remains_blocked(self):
        result = self.fixture(latch=True, no_clock=198, io_missing=True)
        self.assertEqual(result['gates']['structural'], 'BLOCKED')
        self.assertEqual(result['gates']['constraint_coverage'], 'BLOCKED')
        self.assertEqual(result['structural']['counts']['latches'], 1)
        self.assertEqual(result['constraints']['check_timing']['no_clock'], 198)

    def test_archived_actual_bad_report_is_rejected(self):
        archived = Path(__file__).resolve().parents[1] / 'logs/closure/mldsa_ooc_20260803/fsrch_chipv2_mldsa_baseline_1244_15.0.rpt'
        counts = q.parse_check_timing(archived.read_text())
        self.assertEqual(counts['no_clock'], 198)
        self.assertEqual(counts['unconstrained_internal_endpoints'], 66)
        self.assertEqual(counts['latch_loops'], 0)  # Not evidence of zero latches.

    def test_execute_collect_and_recompute_feedback(self):
        response = self.execute_fixture()
        self.assertEqual(response['status'], 'BLOCKED')
        self.assertTrue(response['structural_checks_verified'])
        self.assertFalse(response['memory_semantics_verified'])
        self.assertEqual(q.validate_feedback(response, self.request, self.root), response['qualification'])
        with self.assertRaisesRegex(ValueError, 'mapped_memory_semantics'):
            q.validate_admission(response, self.request, self.root)

    def test_user_booleans_cannot_admit_a_netlist(self):
        response = self.execute_fixture()
        response.update(status='MEASURED', memory_semantics_verified=True, structural_checks_verified=True)
        with self.assertRaisesRegex(ValueError, 'mapped_memory_semantics'):
            q.validate_admission(response, self.request, self.root)

    def test_changed_checkpoint_is_not_reusable(self):
        response = self.execute_fixture()
        (self.run / 'synthesized.dcp').write_text('different checkpoint')
        with self.assertRaisesRegex(ValueError, 'Changed qualification'):
            q.validate_feedback(response, self.request, self.root)

    def test_changed_netlist_is_not_reusable(self):
        response = self.execute_fixture()
        (self.run / 'implementation.v').write_text('different netlist')
        with self.assertRaisesRegex(ValueError, 'Changed qualification'):
            q.validate_feedback(response, self.request, self.root)

    def test_changed_source_is_not_reusable(self):
        response = self.execute_fixture()
        self.source.write_text('module changed; endmodule\n')
        with self.assertRaisesRegex(ValueError, 'Frozen inputs'):
            q.validate_feedback(response, self.request, self.root)

    def test_response_metric_cannot_override_objects(self):
        response = self.execute_fixture()
        response['metrics']['luts'] = 1
        with self.assertRaisesRegex(ValueError, 'metrics'):
            q.validate_feedback(response, self.request, self.root)

    def test_missing_or_conflicting_timing_checks_rejected(self):
        for text in ('', check_timing().replace('1. checking no_clock (0)', ''), check_timing() + '1. checking no_clock (9)\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                q.parse_check_timing(text)

    def test_missing_hold_or_nan_is_rejected(self):
        for text in (timing_summary().replace('WHS(ns)', 'UNKNOWN'), timing_summary(hold='NaN'),
                     timing_summary().replace('0 100 0.050', '0 0 0.050')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                q.parse_timing_summary(text)

    def test_unknown_ownership_does_not_use_instance_names(self):
        result = self.fixture(ownership=False)
        self.assertEqual(result['gates']['path_ownership'], 'BLOCKED')
        self.assertEqual(result['critical_paths'][0]['responsible_files'], [])

    def test_relative_source_location_is_not_guessed(self):
        self.fixture()
        text = (self.run / 'objects.tsv').read_text().replace(str(self.source).encode().hex(), self.source.name.encode().hex())
        (self.run / 'objects.tsv').write_text(text)
        self.assertEqual(q.evaluate(self.run, self.request)['gates']['path_ownership'], 'BLOCKED')

    def test_warning_needs_review_even_with_zero_latches(self):
        self.fixture()
        (self.run / 'synthesis.log').write_text('WARNING: [Synth 8-1234] fixture\n')
        result = q.evaluate(self.run, self.request)
        self.assertEqual(result['gates']['structural'], 'BLOCKED')
        self.assertEqual(result['structural']['counts']['unreviewed_synthesis_warnings'], 1)

    def test_wrong_part_clock_tool_or_stage_rejected(self):
        self.fixture()
        original = (self.run / 'objects.tsv').read_text()
        for before, after in [('2022.2', '2023.1'), ('xc7a200tfbg676-1', 'wrong'), ('post_synth', 'routed')]:
            (self.run / 'objects.tsv').write_text(original.replace(before.encode().hex(), after.encode().hex()))
            with self.subTest(after=after), self.assertRaises(ValueError):
                q.evaluate(self.run, self.request)
        (self.run / 'objects.tsv').write_text(original.replace('15.0'.encode().hex(), '10.0'.encode().hex()))
        self.assertEqual(q.evaluate(self.run, self.request)['gates']['constraint_coverage'], 'BLOCKED')

    def test_internal_false_path_is_not_a_coverage_fix(self):
        self.fixture()
        with (self.run / 'effective.xdc').open('a') as stream:
            stream.write('set_false_path -to [get_pins u/r0/D]\n')
        result = q.evaluate(self.run, self.request)
        self.assertEqual(result['gates']['constraint_coverage'], 'BLOCKED')

    def test_exact_justified_io_exception(self):
        self.xdc.write_text('set_false_path -from [get_ports din]\n')
        self.cfg['immutable_hashes'] = hashes([self.xdc, *q.dependencies()])
        self.cfg['measurement']['qualification'] = {'io_exceptions': [{'port': 'din', 'direction': 'IN',
                             'reason': 'User-defined asynchronous reset boundary', 'xdc': str(self.xdc), 'line': 1}]}
        self.fixture()
        with (self.run / 'effective.xdc').open('a') as stream:
            stream.write(self.xdc.read_text())
        text = (self.run / 'objects.tsv').read_text()
        for delay in ('max', 'min'):
            text = text.replace(encoded('port_timing', 'din', delay, '1', '0.1', '0'),
                                encoded('port_timing', 'din', delay, '1', 'INFINITY', '1'))
        (self.run / 'objects.tsv').write_text(text)
        result = q.evaluate(self.run, self.request)
        self.assertEqual(result['gates']['constraint_coverage'], 'PASS')
        self.assertEqual(result['constraints']['qualified_io_exceptions'][0]['port'], 'din')

    def test_exception_never_subtracts_positive_missing_delay_count(self):
        self.test_exact_justified_io_exception()
        (self.run / 'check_timing.rpt').write_text(check_timing({'no_input_delay': 1}))
        self.assertEqual(q.evaluate(self.run, self.request)['gates']['constraint_coverage'], 'BLOCKED')

    def test_model_cannot_supply_exception_without_xdc_command(self):
        self.cfg['measurement']['qualification'] = {'io_exceptions': [{'port': 'din', 'direction': 'IN',
                              'reason': 'arbitrary model suggestion', 'xdc': str(self.xdc), 'line': 1}]}
        with self.assertRaisesRegex(ValueError, 'exact all-path'):
            self.fixture()

    def test_incomplete_object_report_is_rejected(self):
        self.fixture()
        text = (self.run / 'objects.tsv').read_text().replace(encoded('meta', 'complete', '1'), '')
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            q.parse_objects(text)

    def test_literal_bus_cell_round_trip(self):
        self.fixture()
        text = (self.run / 'objects.tsv').read_text()
        text = text.replace('u/r0'.encode().hex(), 'u/gen[0]/r{one}'.encode().hex())
        self.assertIn('u/gen[0]/r{one}', [r[0] for r in q.parse_objects(text)['cell']])

    def test_negative_hold_is_measured_but_not_qualified(self):
        self.fixture()
        path = self.run / 'timing.rpt'
        path.write_text(path.read_text().replace('0.050 0.000 0 100', '-0.050 -0.250 5 100'))
        path = self.run / 'objects.tsv'
        path.write_text(path.read_text().replace('0.050'.encode().hex(), '-0.050'.encode().hex()))
        path = self.run / 'paths.rpt'
        path.write_text(path.read_text().replace('Slack (MET) : 0.050', 'Slack (VIOLATED) : -0.050'))
        result = q.evaluate(self.run, self.request)
        self.assertEqual(result['gates']['hold_timing'], 'BLOCKED')
        self.assertTrue(any('hold slack=-0.05' in message for message in result['blockers']))

    def test_setup_floor_is_not_silently_weakened(self):
        self.cfg['admission'] = {'minimum_slack_ns': 0.2}
        result = self.fixture()
        self.assertEqual(result['gates']['setup_timing'], 'BLOCKED')

    def test_disabled_drc_cannot_claim_clean_structure(self):
        self.fixture()
        path = self.run / 'objects.tsv'
        path.write_text(path.read_text().replace(encoded('drc_check', 'MDRV-1', '1'),
                                                 encoded('drc_check', 'MDRV-1', '0')))
        result = q.evaluate(self.run, self.request)
        self.assertEqual(result['gates']['structural'], 'BLOCKED')
        self.assertEqual(result['structural']['counts']['disabled_structural_checks'], 1)

    def test_reduced_corner_or_io_coverage_is_not_complete(self):
        self.fixture()
        path = self.run / 'timing.rpt'; original = path.read_text()
        for before, after in [('Fast Yes Yes', 'Fast Yes No'), ('Ignore I/O Paths : No', 'Ignore I/O Paths : Yes')]:
            path.write_text(original.replace(before, after))
            self.assertEqual(q.evaluate(self.run, self.request)['gates']['constraint_coverage'], 'BLOCKED')

    def test_missing_empty_or_oversized_tool_build_is_rejected(self):
        self.fixture()
        path = self.run / 'objects.tsv'; original = path.read_text()
        build_row = encoded('meta', 'tool_build', 'Vivado 2022.2 SYNTHETIC FIXTURE ONLY')
        for replacement in ('', encoded('meta', 'tool_build', ''),
                            encoded('meta', 'tool_build', '   '),
                            encoded('meta', 'tool_build', 'x' * 16385)):
            path.write_text(original.replace(build_row, replacement))
            with self.subTest(length=len(replacement)), self.assertRaisesRegex(ValueError, 'tool build identity'):
                q.evaluate(self.run, self.request)

    def test_missing_primary_clock_profile_blocks_coverage(self):
        self.fixture()
        self.cfg['target_profile']['boundary'] = None
        self.assertEqual(q.evaluate(self.run, self.request)['gates']['constraint_coverage'], 'BLOCKED')

    def test_tcl_is_complete_and_uses_real_objects(self):
        script = Path(q.__file__).with_suffix('.tcl')
        code = 'set f [open {' + str(script) + '} r]; set s [read $f]; close $f; puts [info complete $s]\n'
        result = subprocess.run(['tclsh'], input=code, text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout.strip(), '1')
        text = script.read_text()
        for required in ('PRIMITIVE_SUBGROUP == LATCH', 'REF_NAME =~ LD*', 'FILE_NAME', 'LINE_NUMBER',
                         '-no_waivers', 'get_cells -of_objects $path', 'get_property SLACK'):
            self.assertIn(required, text)


if __name__ == '__main__':
    unittest.main()
