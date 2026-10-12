#!/usr/bin/env python3
"""Run the three bounded four-state ASIC-startup component tests, without downloads."""
from pathlib import Path
import argparse,json,os,re,shutil,subprocess,sys
from build_mldsa_startup_derivative import sha


def run(repo,design,out,tool_dir):
    repo=Path(repo).resolve();design=Path(design).resolve();out=Path(out).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('output must be new/empty')
    out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((design/'manifest.json').read_text())
    for row in manifest['sources']:
        if sha(design/row['path'])!=row['sha256']:raise ValueError('changed derivative source')
    base=repo/'third_party/mldsa_osh/upstream/ref_combined/src';tests=Path(__file__).resolve().parents[1]/'verification/mldsa_startup';rtl=design/'rtl'
    original=base/'makehint.v';reference=out/'makehint_reference.v'
    text,n=re.subn(r'\bmodule makehint\b','module makehint_reference',original.read_text())
    if n!=1:raise ValueError('reference module anchor changed')
    reference.write_text(text)
    env=os.environ.copy();env['PATH']=str(Path(tool_dir).resolve())+os.pathsep+env['PATH']
    binaries={n:shutil.which(n,path=env['PATH']) for n in ('iverilog','vvp')}
    if not all(binaries.values()):raise ValueError('installed Icarus and vvp required')
    result={'schema_version':1,'status':'PASS','design_manifest_sha256':sha(design/'manifest.json'),'tools':{},'checks':{}}
    for name,exe in binaries.items():
        v=subprocess.run([exe,'-V'],capture_output=True,text=True,env=env,timeout=10)
        result['tools'][name]={'launcher_sha256':sha(exe),'version':(v.stdout+v.stderr).splitlines()[:4]}
    cases=[('ram','tb_sameclock_ff_ram',[rtl/'mldsa_sameclock_ff_ram.v',base/'dual_port_ram.v'],'ASIC_RAM_PASS checked_cycles=10096'),
           ('shell','tb_boot_shell',[rtl/'combined_top_asic.v'],'ASIC_BOOT_SHELL_PASS complete_boots=3'),
           ('hint_read','tb_makehint_read_view',[rtl/'makehint.v',reference],'ASIC_HINT_READ_VIEW_PASS exhaustive_control_cases=12288')]
    for name,top,files,marker in cases:
        tb=tests/(top+'.sv');sources=[tb,*files];before={str(p):sha(p) for p in sources};executable=out/(name+'.vvp')
        command=[binaries['iverilog'],'-g2012','-s',top,'-o',str(executable),*map(str,sources)]
        with (out/(name+'-compile.log')).open('w') as log:
            compile_result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=env,timeout=60)
        row={'status':'FAIL','compile_command':command,'input_hashes':before,'compile_returncode':compile_result.returncode}
        result['checks'][name]=row
        if compile_result.returncode==0:
            row['executable_sha256']=sha(executable);command=[binaries['vvp'],str(executable)]
            with (out/(name+'-simulate.log')).open('w') as log:
                sim=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=env,timeout=60)
            text=(out/(name+'-simulate.log')).read_text();row.update(simulate_command=command,simulate_returncode=sim.returncode,observed_marker_count=text.count(marker),simulate_log_sha256=sha(out/(name+'-simulate.log')))
            if sim.returncode==0 and text.count(marker)==1 and 'FATAL' not in text:row['status']='PASS'
        row['input_hashes_unchanged']=all(sha(p)==h for p,h in before.items())
        if not row['input_hashes_unchanged']:row['status']='FAIL'
        if row['status']!='PASS':result['status']='FAIL'
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--design',required=True);p.add_argument('--out',required=True);p.add_argument('--tool-dir',required=True);a=p.parse_args()
    r=run(a.repo,a.design,a.out,a.tool_dir);print(r['status']);sys.exit(0 if r['status']=='PASS' else 1)
