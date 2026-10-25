#!/usr/bin/env python3
"""Pinned whole-core KAT checks for the FPGA selector-default derivative."""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, sys, time
from export_mldsa_fpga_latch_corrected import sha


def run(repo,design,out,tool_dir,jobs,selected,vector_count,seeds):
    repo=Path(repo).resolve();design=Path(design).resolve();out=Path(out).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('work directory must be new/empty')
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0,str(repo))
    from agent.mldsa.portable_kat_gate import prepare_testbench,evaluate_log,stage_verify_mutations,stage_canonical_cases
    from agent.mldsa_sources import verify_snapshot
    verify_snapshot()
    upstream=repo/'third_party/mldsa_osh/upstream'; manifest=json.loads((design/'manifest.json').read_text())
    sources=[design/r['path'] for r in manifest['sources']]
    for p,r in zip(sources,manifest['sources']):
        if sha(p)!=r['sha256']:raise ValueError('derivative hash mismatch')
    inputs={str(p):sha(p) for p in sources}
    inputs[str(design/'zetas.txt')]=sha(design/'zetas.txt')
    fixture_inputs=list((upstream/'KAT').glob('*'))+list((upstream/'ref_combined/src_tb').glob('*'))+[upstream/'common/mldsa_params.v']
    inputs.update({str(p):sha(p) for p in fixture_inputs})
    env=os.environ.copy();env['PATH']=str(Path(tool_dir).resolve())+os.pathsep+env['PATH'];env['MAKEFLAGS']='CFG_CXXFLAGS_PCH_I=-include'
    exe=shutil.which('verilator',path=env['PATH'])
    if not exe:raise ValueError('installed Verilator required')
    version=subprocess.run([exe,'--version'],env=env,text=True,capture_output=True,check=True).stdout.strip()
    result={'schema_version':1,'status':'RUNNING','design_manifest_sha256':sha(design/'manifest.json'),'variant':manifest['source_variant']+'+fpga-selector-defaults','tool':version,'source_hashes':inputs,'coverage':{},'commands':[],'collision_assertions':False,'two_state_simulation':True,'four_state_fullcore_qualified':False,'normal_reset_contract':'Original per-operation reset semantics retained; arbitrary abort/reset recovery is not claimed.'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    try:
        for case in selected:
            operation='verify' if case.startswith('verify') else case
            count={'keygen':25,'sign':15,'verify':15,'verify_mutations':4,'verify_canonical':11}[case]
            if vector_count is not None and not case.startswith('verify_'):count=vector_count
            work=out/case;tbdir=work/'ref_combined/src_tb';tbdir.mkdir(parents=True)
            shutil.copytree(upstream/'common',work/'common')
            shutil.copy2(design/'zetas.txt',tbdir/'zetas.txt')
            if case=='verify_mutations':stage_verify_mutations(upstream/'KAT',tbdir)
            elif case=='verify_canonical':stage_canonical_cases(upstream/'KAT',tbdir)
            else:
                for p in (upstream/'KAT').glob('*.txt'):
                    data=p.read_text()
                    if vector_count is not None:
                        prefix={'keygen':'KeyGen','sign':'SigGen','verify':'SigVer'}[operation]
                        if p.name.startswith(prefix+'_'):data='\n'.join(data.split()[:count])+'\n'
                    (tbdir/p.name).write_text(data)
            source=upstream/'ref_combined/src_tb'/f'tb_{operation}_top.v'
            text=prepare_testbench(source.read_text(),operation,count,20000000)
            tb=tbdir/source.name;tb.write_text(text);top=tb.stem;obj=work/'obj'
            command=[exe,'--binary','--timing','--top-module',top,'--Mdir',str(obj),'-j',str(jobs),'-Wno-fatal','--x-initial','unique','--x-assign','unique',*map(str,sources),str(tb)]
            result['commands'].append({'compile':command,'cwd':str(tbdir)})
            with (work/'compile.log').open('w') as log:
                subprocess.run(command,cwd=tbdir,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900,check=True)
            result.setdefault('testbench_hashes',{})[str(tb)]=sha(tb)
            executable=obj/('V'+top);result.setdefault('executable_hashes',{})[str(executable)]=sha(executable)
            for seed in seeds:
                command=[str(executable)] if seed==0 else [str(executable),'+verilator+rand+reset+2',f'+verilator+seed+{seed}']
                result['commands'].append({'simulate':command,'cwd':str(tbdir)})
                started=time.monotonic()
                with (work/f'simulate-seed-{seed}.log').open('w') as log:
                    process=subprocess.run(command,cwd=tbdir,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=900)
                text=(work/f'simulate-seed-{seed}.log').read_text(errors='replace')
                row=evaluate_log(text,operation,count,process.returncode)
                row.update(seed=seed,runtime_s=round(time.monotonic()-started,2))
                if operation=='verify':
                    expected=[(tbdir/f'SigVer_result_{level}.txt').read_text().split()[:count] for level in (44,65,87)]
                    row['known_valid']=sum(v.count('0') for v in expected);row['known_invalid']=sum(v.count('1') for v in expected)
                result['coverage'][case+':seed-'+str(seed)]=row
                (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
                print(case,seed,row['status'],row['completed'],flush=True)
                if row['status']!='PASS':raise RuntimeError(row.get('reason','KAT failed'))
        result['status']='PASS'
    except (OSError,RuntimeError,subprocess.SubprocessError) as exc:
        result['status']='FAIL';result['reason']=str(exc)
    finally:
        changed=[p for p,h in inputs.items() if sha(p)!=h]
        result['source_hashes_unchanged']=not changed
        if changed: result.update(status='FAIL',changed_inputs=changed)
        result['full_210_case_coverage']=set(selected)=={'keygen','sign','verify','verify_mutations','verify_canonical'} and vector_count is None
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--design',required=True);p.add_argument('--out',required=True);p.add_argument('--tool-dir',required=True);p.add_argument('--jobs',type=int,default=2);p.add_argument('--cases',nargs='+',choices=['keygen','sign','verify','verify_mutations','verify_canonical'],default=['keygen','sign','verify','verify_mutations','verify_canonical']);p.add_argument('--vectors',type=int);p.add_argument('--seeds',type=int,nargs='+',default=[0])
    a=p.parse_args();r=run(a.repo,a.design,a.out,a.tool_dir,a.jobs,a.cases,a.vectors,a.seeds);print(r['status'],a.out);sys.exit(0 if r['status']=='PASS' else 1)
