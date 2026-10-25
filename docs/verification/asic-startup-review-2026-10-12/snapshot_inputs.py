import hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path('/workspace/scratch/8c6eb979d526/pqc-project/integrated');OUT=pathlib.Path(__file__).resolve().parent
files=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().split('\0');values={}
for name in sorted(set(files)-{''}):
 p=ROOT/name
 if p.is_file():values[name]=hashlib.sha256(p.read_bytes()).hexdigest()
output={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'file_count':len(values),'files_sha256':values}
if len(sys.argv)>1 and sys.argv[1]=='before':
 dest=OUT/'frozen-inputs-before.json'
 if dest.exists():raise RuntimeError('refusing to overwrite freeze record')
 dest.write_text(json.dumps(output,sort_keys=True,indent=2)+'\n');print(output['file_count'],'files frozen')
else:
 prior=json.loads((OUT/'frozen-inputs-before.json').read_text());changes={n:{'before':prior['files_sha256'].get(n),'after':values.get(n)} for n in set(values)|set(prior['files_sha256']) if values.get(n)!=prior['files_sha256'].get(n)}
 result={'status':'PASS' if not changes and prior['head']==output['head'] else 'FAIL','before_head':prior['head'],'after_head':output['head'],'file_count':len(values),'changes':changes}
 (OUT/'frozen-inputs-after.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,indent=2));sys.exit(result['status']!='PASS')
