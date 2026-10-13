import hashlib, json, os, ast, inspect, subprocess, time
from pathlib import Path
import sys, unittest
ROOT=Path('/workspace/scratch/8c6eb979d526/pqc-fpga-agent-loop')
OUT=Path(__file__).resolve().parent
start=time.monotonic()
prior=json.loads((ROOT/'docs/verification/dual-target-review-2026-10-12.json').read_text())
prior_excluded={r['test']:r['reason'] for r in prior['software_tests']['excluded']}
prior_ids=set()
for file in sorted((ROOT/'tests').glob('test_*.py')):
    old=subprocess.run(['git','show','HEAD:'+str(file.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True)
    if old.returncode:continue
    tree=ast.parse(old.stdout)
    for cls in tree.body:
        if isinstance(cls,ast.ClassDef):
            for method in cls.body:
                if isinstance(method,(ast.FunctionDef,ast.AsyncFunctionDef)) and method.name.startswith('test'):
                    prior_ids.add(file.stem+'.'+cls.name+'.'+method.name)
os.chdir(ROOT)
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests'))
EXCLUDE={
    'test_core_runtime.OfflineRuntime.test_imports_without_sdk_or_key': 'Includes HQC orchestrator imports; omitted conservatively under HQC execution restriction',
    'test_safety_and_backends.ChipAcceptance.test_unsupported_mapped_blocks_do_not_launch_optimizer': 'Mixed HQC/MLDSA dispatcher test; omitted conservatively under HQC execution restriction',
    'test_safety_and_backends.ChipAcceptance.test_supported_blocks_match_runner_registries': 'Mixed HQC/MLDSA registry test; omitted conservatively under HQC execution restriction',
}
def flatten(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite): yield from flatten(item)
        else: yield item
all_tests=list(flatten(unittest.defaultTestLoader.discover(str(ROOT/'tests'))))
selected=[]; excluded=[]
for test in all_tests:
    name=test.id()
    reason=prior_excluded.get(name) or EXCLUDE.get(name)
    if name not in prior_ids:
        method=getattr(test,test._testMethodName)
        if 'hqc' in (name+' '+inspect.getsource(method)).lower():
            reason='New HQC-related test conservatively omitted under HQC execution restriction'
    if '.HQCSecrets.' in name or '.HQCPrivateWorkspace.' in name or name in ('test_safety_and_backends.ChipAcceptance.test_hqc_block_dispatch_supplies_parameter_set', 'test_safety_and_backends.ChipAcceptance.test_hqc_joint_dispatch_has_no_block_or_parameter_argument', 'test_experiment_history.FinalOutcomeHistory.test_hqc_baseline_gate_selects_pristine_manifest'):
        reason='HQC-specific test omitted under prior HQC execution restriction (including mocked gate and staging paths)'
    if reason: excluded.append({'test':name,'reason':reason})
    else: selected.append(test)
missing=set(prior_excluded)-{t.id() for t in all_tests}
if missing:raise RuntimeError('Prior excluded test inventory changed: '+repr(missing))
print('EXCLUDED TESTS:',json.dumps(excluded,indent=2),flush=True)
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(selected))
summary={'optimization':sys.flags.optimize,'discovered':len(all_tests),'selected':len(selected),'ran':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':[{'test':test.id(),'reason':reason} for test,reason in result.skipped],'successful':result.wasSuccessful(),'excluded':excluded,'scope':'Permitted non-HQC subset; not a full suite pass, RTL algorithm requalification, or licensed EDA validation'}
summary['elapsed_seconds']=round(time.monotonic()-start,3)
summary['runner_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
summary['prior_exclusion_count']=len(prior_excluded)
summary['new_hqc_exclusions']=[r for r in excluded if r['test'] not in prior_excluded]
output=OUT/f'unittest-O{sys.flags.optimize}.json'
output.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2),flush=True)
sys.exit(not result.wasSuccessful())
