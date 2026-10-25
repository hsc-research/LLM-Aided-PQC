import hashlib,json,pathlib,shutil,subprocess,sys,tempfile,time
ROOT=pathlib.Path('/workspace/scratch/8c6eb979d526/pqc-project/asic-startup-independent-review/index-only-tree');OUT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));from tools.export_target_profiles import export_profile,verify_profile

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
combos=[('mlkem','baseline',None)]+[('mldsa',v,None) for v in ('guarded-baseline','corrected-candidate')]+[('slh',v,p) for v in ('corrected-baseline','corrected-candidate') for p in ('128f','192f')]
configs=[(*c,t) for c in combos for t in ('fpga','asic')]+[('mldsa',v,None,'asic') for v in ('asic-startup-baseline','asic-startup-candidate')]+[('slh',v,p,'asic') for v in ('asic-startup-baseline','asic-startup-candidate') for p in ('128f','192f')]
assert len(configs)==20
rows=[];start=time.monotonic();(OUT/'profiles').mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='final-independent-profile-rebuild-',dir=OUT) as tmp:
 for n,(design,variant,param,target) in enumerate(configs):
  key='-'.join(x for x in (design,variant,param,target) if x);a=pathlib.Path(tmp)/f'{n}-a';b=pathlib.Path(tmp)/f'{n}-b'
  x=export_profile(design,variant,param,target,a);y=export_profile(design,variant,param,target,b)
  assert x==verify_profile(a/'profile.json') and y==verify_profile(b/'profile.json')
  aa,bb=files(a),files(b);assert aa==bb,(key,'nondeterministic')
  man=json.loads((a/'source-bundle/manifest.json').read_text())
  assert [(z['path'].removeprefix('source-bundle/'),z['sha256']) for z in x['elaboration']['sources']]==[(z['path'],z['sha256']) for z in man['sources']]
  assert not x['qualification']['target_tool_qualified'] and not x['target']['technology_mapping_verified']
  if variant.startswith('asic-startup-'):
   assert not x['qualification']['whole_algorithm_qualified'] and x['qualification']['startup_rtl_tested']
   assert x['elaboration']['data_files']==[] and x['boundary']['ready_ports']
  moved=pathlib.Path(tmp)/f'{n}-relocated';a.rename(moved)
  result=subprocess.run([sys.executable,'-I',str(moved/'verify_profile.py'),'--verify',str(moved/'profile.json')],cwd='/tmp',capture_output=True,text=True,timeout=60)
  assert result.returncode==0,(key,result.stderr)
  (OUT/'profiles'/f'{key}.json').write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
  rows.append({'design':design,'variant':variant,'parameter_set':param,'target':target,'status':'PASS','file_count':len(aa),'exact_two_build_hashes_match':True,'ordered_source_hashes_match':True,'standalone_relocated_verify_returncode':result.returncode,'profile_fingerprint':x['profile_fingerprint'],'source_count':len(x['elaboration']['sources']),'qualification_report_sha256':x['qualification']['report']['sha256']})
  shutil.rmtree(b);shutil.rmtree(moved);print(key,'PASS',flush=True)
r={'status':'PASS','scope':'Independent source-only deterministic rebuild, relocation and hash binding; no HDL or EDA process invoked','profiles':rows,'count':len(rows),'elapsed_seconds':round(time.monotonic()-start,3),'runner_sha256':sha(pathlib.Path(__file__))}
(OUT/'profile-rebuild-review.json').write_text(json.dumps(r,indent=2)+'\n')
