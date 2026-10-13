"""Independent synthetic fault-injection regressions; no external tools or API."""
import copy
import json
from pathlib import Path
import subprocess
import types
import unittest
from unittest.mock import patch

from tests import test_autonomous_fpga as fixture_module
from tests.test_autonomous_fpga import proposal
from tests.test_vivado_qualification import emit_reports
from agent import autonomous_fpga as a, fpga_feedback as f


class IndependentReview(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture_module.AutonomousTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_snapshot_failure_rolls_back(self):
        c, client = self.fixture.controller([proposal, {'status': 'STOP'}])
        original = c.snapshot
        def snapshot(name, expected):
            if name.startswith('accepted-'):
                raise OSError('synthetic disk failure')
            return original(name, expected)
        c.snapshot = snapshot
        result = c.run()
        self.assertEqual(result['accepted'], 0)
        self.assertIn('reg flag;', Path(c.sources[0]).read_text())
        self.assertEqual(result['current_sources'], result['baseline_sources'])

    def test_journal_failure_rolls_back_and_cannot_claim_integrity(self):
        c, client = self.fixture.controller([proposal, {'status': 'STOP'}])
        original = c.record
        def record(event):
            if event.get('verdict') == 'ACCEPT':
                raise OSError('synthetic journal failure')
            return original(event)
        c.record = record
        result = c.run()
        self.assertEqual(result['accepted'], 0)
        self.assertEqual(result['status'], 'PERSISTENCE_FAILED')
        self.assertIn('reg flag;', Path(c.sources[0]).read_text())
        with self.assertRaises(ValueError):
            a.inspect_run(c.out)

    def test_accepted_rtl_tamper_is_detected(self):
        c, _ = self.fixture.controller([proposal, {'status': 'STOP'}])
        c.run()
        (c.out/'accepted-001/rtl/top.v').write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'Snapshot source changed'):
            a.inspect_run(c.out)

    def test_provisional_rtl_tamper_is_detected(self):
        self.fixture.settings['mode'] = 'exploratory'
        c, _ = self.fixture.controller([proposal, {'status': 'STOP'}], qualification=False)
        c.run()
        (c.out/'provisional-001/rtl/top.v').write_text('tampered')
        with self.assertRaisesRegex(ValueError, 'Snapshot source changed'):
            a.inspect_run(c.out)

    def test_usage_evidence_tamper_is_detected(self):
        c, _ = self.fixture.controller([{'status': 'STOP'}])
        c.run()
        (c.out/'proposal-001/usage.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Persisted record changed'):
            a.inspect_run(c.out)

    def test_postspawn_deadline_kills_child(self):
        c, _ = self.fixture.controller([])
        folder=self.fixture.root/'command';folder.mkdir()
        process=types.SimpleNamespace(pid=123456, wait=lambda: None)
        with patch.object(c, 'remaining', side_effect=[10, ValueError('expired')]), \
             patch.object(a.subprocess, 'Popen', return_value=process), \
             patch.object(a, '_kill_tree') as kill:
            with self.assertRaises(ValueError):
                c.execute(['synthetic'], folder, 10)
            kill.assert_called_once_with(123456)

    def test_fast_child_cannot_bypass_artifact_limit(self):
        c, _ = self.fixture.controller([])
        c.limits['max_artifact_bytes']=1
        folder=self.fixture.root/'command';folder.mkdir()
        (folder/'artifact').write_bytes(b'too large')
        process=types.SimpleNamespace(pid=123456, poll=lambda: 0, returncode=0)
        with patch.object(a.subprocess, 'Popen', return_value=process):
            with self.assertRaisesRegex(ValueError, 'artifact byte limit'):
                c.execute(['synthetic'], folder, 10)

    def test_real_feedback_parser_integrates_with_controller(self):
        settings=copy.deepcopy(self.fixture.settings)
        settings['launch']['tool_version']='2022.2'
        settings['profile']['boundary']={'clock_ports':['clk']}
        c=a.Controller(settings,self.fixture.root/'integration',client_factory=lambda: self.fail('No API'))
        c.setup()
        def execute(argv,directory,timeout):
            def process(argv,**options):
                emit_reports(directory/'vivado',Path(c.sources[0]))
                Path(options['log_path']).write_text('SYNTHETIC only\n')
                return subprocess.CompletedProcess(argv,0,'SYNTHETIC only','')
            with patch.object(f,'run_process',side_effect=process):
                f.collect(directory/'request.json',directory/'response.json',execute=True)
        c.execute=execute
        response=c.stage('measure',c.baseline)
        self.assertEqual(response['metrics']['lut'],100)
        self.assertFalse(c.admission(response,c.baseline)[0])

    def test_relocated_comments_cannot_activate_system_tasks(self):
        before='module top;\n/*\ninitial $finish;\n*/\nwire x;\nendmodule\n'
        after='module top;\ninitial $finish;\n/*\nwire x;\n*/\nendmodule\n'
        with self.assertRaises(ValueError):
            a.unsafe_candidate(before,after)


if __name__=='__main__':
    unittest.main()
