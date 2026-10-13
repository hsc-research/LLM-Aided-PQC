"""Offline fixtures only: no EDA, hardware qualification, or paid API calls."""
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
from tools import prepare_fpga_proposal as p
from tools import run_fpga_proposal as r
from agent.mldsa import exported_kat_adapter as k

class ProposalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.rtl=self.root/'a.v';self.rtl.write_text('module a; wire x; endmodule\n')
        self.prompt=self.root/'prompt.json';p.save(self.prompt,{'system':'fixture','user':{'reports':{}}})
        self.context=self.root/'proposal-context.json'
        p.save(self.context,{'schema_version':1,'status':'PROMPT_PREPARED_NO_API_CALL','profile_fingerprint':'fixture',
                            'prompt_sha256':p.sha(self.prompt),'input_sha256':{str(self.rtl):p.sha(self.rtl)},'allowed_files':[str(self.rtl)]})
    def response(self, value):
        path=self.root/'response.json';p.save(path,value);return path
    def proposal(self):
        return {'status':'PROPOSED','experiment':{'name':'fixture','files':[{'path':str(self.rtl),'ops':[{'op':'replace_exact','old':'wire x;','new':'wire y;','expect':1}]}]}}
    def test_stop_no_edit(self):
        self.assertEqual(p.review(self.context,self.response({'status':'STOP'}),self.root/'review.json')['status'],'STOP')
    def test_preview_never_edits(self):
        old=self.rtl.read_bytes();self.assertEqual(p.review(self.context,self.response(self.proposal()),self.root/'review.json')['status'],'EDIT_PREVIEW_VALID_NOT_APPLIED');self.assertEqual(self.rtl.read_bytes(),old)
    def test_source_drift(self):
        self.rtl.write_text('changed')
        with self.assertRaises(ValueError):p.review(self.context,self.response({'status':'STOP'}),self.root/'review.json')
    def test_prompt_drift(self):
        self.prompt.write_text('{}')
        with self.assertRaises(ValueError):p.review(self.context,self.response({'status':'STOP'}),self.root/'review.json')
    def test_nonexact_edit(self):
        v=self.proposal();v['experiment']['files'][0]['ops'][0]['op']='regex_swap'
        with self.assertRaises(ValueError):p.review(self.context,self.response(v),self.root/'review.json')
    def test_outside_allowlist(self):
        other=self.root/'other.v';other.write_text(self.rtl.read_text());v=self.proposal();v['experiment']['files'][0]['path']=str(other)
        with self.assertRaises(AssertionError):p.review(self.context,self.response(v),self.root/'review.json')
    def test_optin_precedes_sdk(self):
        with patch.dict(os.environ,{'PQC_ENABLE_LLM':'0'}):
            with self.assertRaises(ValueError):r.run(self.context,'fixture',1,1,1)
    def fake_client(self, stop='end_turn',fail=False):
        def create(**kwargs):
            if fail:raise TimeoutError('secret must not appear')
            return NS(usage=NS(input_tokens=10,output_tokens=10),stop_reason=stop,content=[NS(type='text',text='{"status":"STOP"}')])
        return NS(messages=NS(count_tokens=lambda **kw:NS(input_tokens=10),create=create))
    def run_fake(self,client,budget=1):
        with patch.dict(os.environ,{'PQC_ENABLE_LLM':'1'}),patch.dict('sys.modules',{'anthropic':NS(Anthropic=lambda **kw:client)}):
            return r.run(self.context,'fixture',1,1,budget)
    def test_fake_single_stop(self):
        result=self.run_fake(self.fake_client());self.assertEqual(result['status'],'STOP');self.assertEqual(result['api_calls_attempted'],1)
    def test_budget_prevents_generation(self):
        client=self.fake_client();client.messages.create=lambda **kw:self.fail('must not generate')
        self.assertEqual(self.run_fake(client,budget='0.00001')['status'],'BLOCKED_BUDGET')
    def test_timeout_unknown_no_secret(self):
        with self.assertRaises(RuntimeError):self.run_fake(self.fake_client(fail=True))
        text=(self.root/'proposal-run.json').read_text();self.assertNotIn('secret',text);self.assertEqual(json.loads(text)['status'],'FAILED_OUTCOME_UNKNOWN')
    def test_no_repeat_after_request(self):
        self.run_fake(self.fake_client())
        with self.assertRaises(ValueError):self.run_fake(self.fake_client())
    def test_exclusive_claim_blocks_duplicate(self):
        (self.root/'.proposal-request.lock').write_text('previous request')
        with self.assertRaises(ValueError):self.run_fake(self.fake_client())
    def test_missing_end_turn(self):
        with self.assertRaises(RuntimeError):self.run_fake(self.fake_client(stop='max_tokens'))
        self.assertFalse((self.root/'review.json').exists())
    def test_price_nan(self):
        with self.assertRaises(ValueError):r.positive('NaN')
    def test_complete_kat_contract(self):
        c=k.coverage_contract();self.assertEqual(len(c['operations']),210);self.assertEqual(len(set(c['operations'])),210)
        self.assertEqual(c['required_negative_controls'],['verify_mutations','verify_canonical'])

if __name__=='__main__':unittest.main()

class ExportedGateFixtureTests(unittest.TestCase):
    """Synthetic simulator output tests only; not a new RTL qualification."""
    def test_exact_source_full_coverage(self):
        import subprocess
        from agent.run_safety import hashes
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); source=root/'combined_top.v';source.write_text('module combined_top; endmodule\n')
            other=root/'aaa.v';other.write_text('module aaa; endmodule\n')
            zetas=root/'zetas.txt';zetas.write_text('0\n')
            contract=k.coverage_contract()
            elab={'parameters':{},'defines':[],'global_include_files':[], 'sources':[{'path':str(source),'language':'verilog'},{'path':str(other),'language':'verilog'}], 'include_dirs':[],'data_files':[str(zetas)]}
            cfg={'target':'fpga','top':'combined_top','source_read_order':[str(source),str(other)],**contract,
                 'target_profile':{'design':'mldsa','profile_fingerprint':'fixture','elaboration':elab}}
            req={'configuration':cfg,'source_hashes':hashes([source,other])}
            commands=[]
            def process(argv,**kw):
                commands.append(argv);log=Path(kw['log_path'])
                if '--version' in argv:text='Verilator fixture only\n'
                elif '--binary' in argv:
                    obj=Path(argv[argv.index('--Mdir')+1]);obj.mkdir();top=argv[argv.index('--top-module')+1];(obj/('V'+top)).write_text('fixture executable')
                    self.assertIn(str(source),argv);text='fixture compilation\n'
                else:
                    case=log.parent.name;operation='verify' if case.startswith('verify') else case
                    label={'keygen':'KeyGen','sign':'Sign','verify':'Verify'}[operation]
                    text=''.join(f'ML-DSA-{level}.{label}, KAT # {i} completed in 10 clock cycles\n' for level in ('II','III','V') for i in range(k.CASES[case]))+'testbench done\n'
                log.write_text(text);return subprocess.CompletedProcess(argv,0,text)
            with patch.object(k,'read_request',return_value=(req,{'schema_version':1})),patch.object(k,'require_immutable'),patch.object(k,'verify_inputs'),patch.object(k.shutil,'which',return_value='/fixture/verilator'),patch.object(k,'run_process',side_effect=process):
                result=k.verify(root/'request.json',root/'response.json')
            self.assertEqual(len(result['latency_cycles']),210);self.assertEqual(result['status'],'PASS')
            self.assertEqual(sum('--binary' in x for x in commands),5)
            self.assertEqual(source.read_text(),'module combined_top; endmodule\n')

class FeedbackFixtureTests(unittest.TestCase):
    def test_dry_feedback_is_blocked_and_flat_plus_hierarchy(self):
        from agent import fpga_feedback as f
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/'z.v';source.write_text('module top;endmodule');other=root/'a.v';other.write_text('module a;endmodule');xdc=root/'clock.xdc';xdc.write_text('')
            cfg={'target':'fpga','backend':'vivado','top':'top','source_read_order':[str(source),str(other)],
                 'immutable_hashes':{str(xdc):p.sha(xdc)},'measurement':{'stage':'post_synth','period_ns':15,'constraints':[str(xdc)],'tool_version':'2022.2','part':'xc7a200tfbg676-1'},
                 'target_profile':{'design':'mldsa','profile_fingerprint':'fixture','elaboration':{'sources':[{'path':str(source),'language':'verilog'},{'path':str(other),'language':'verilog'}],'parameters':{},'defines':[],'include_dirs':[],'data_files':[]}}}
            req={'configuration':cfg,'source_hashes':{str(other):p.sha(other),str(source):p.sha(source)}}
            with patch.object(f,'read_request',return_value=(req,{})),patch.object(f,'verify_inputs'),patch.object(f,'run_process',side_effect=AssertionError('no tool allowed')):
                result=f.collect(root/'request.json',root/'response.json')
            self.assertEqual(result['status'],'BLOCKED');self.assertFalse(result['executed']);self.assertIsNone(result['metrics'])
            t=(root/'vivado/launch.tcl').read_text();self.assertIn('report_utilization -file utilization.rpt',t);self.assertIn('report_utilization -hierarchical -file utilization_hierarchical.rpt',t);self.assertIn('-mode out_of_context',t)
