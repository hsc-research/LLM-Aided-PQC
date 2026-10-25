#!/usr/bin/env python3
"""Full pinned KAT checks for the explicit ML-DSA ASIC startup derivative."""
from pathlib import Path
import argparse, hashlib, json, os, re, shutil, subprocess, sys, time
from build_mldsa_startup_derivative import Scan, sha


def add_boot(text, boot_restarts=False):
    old='combined_top DUT ('
    if text.count(old)!=1: raise ValueError('DUT anchor differs')
    text=text.replace(old,'combined_top_asic DUT (')
    text,n=re.subn(r'(\s+data_o\s*)(\n\s*\);)',r'\1, boot_rst, boot_ready\2',text,count=1)
    if n!=1: raise ValueError('DUT ports differ')
    # Existing fixture initialization is unchanged. Pause its transaction FSM
    # until startup completes, rather than shifting any operation-level latency.
    sc=Scan(text); edits=[]
    for i,t in enumerate(sc.t):
        if t[0]!='always':continue
        a=i+1
        if sc.word(a)!='@':continue
        end=sc.balanced(a+1); prefix=text[t.start():sc.t[end].start()]
        if 'posedge clk' not in prefix:continue
        b=sc.stmt(end); l,r=sc.span(end,b)
        if 'portable_cycles' in text[l:r]: continue
        edits.append((l,r,'begin if (boot_ready && !boot_rst) '+text[l:r]+' end'))
    if len(edits)!=1:raise ValueError('expected one testbench transaction FSM')
    for l,r,new in sorted(edits,reverse=True):text=text[:l]+new+text[r:]
    text = text.replace('\nendmodule','''
    reg boot_rst = 1;
    wire boot_ready;
    initial begin
        repeat (3) @(negedge clk);
        boot_rst = 0;
    end
    always @(negedge clk) begin
        if (!boot_ready && (ready_i !== 0 || valid_o !== 0 || data_o !== 0))
            $fatal(1, "ASIC boot leaked handshake or data");
    end
endmodule''')
    monitor = "\n"
    for bank in range(7):
        monitor += f"""
    always @(posedge clk) begin
        if (boot_ready && !boot_rst && DUT.CORE.en_ram{bank} &&
            DUT.CORE.wea_ram{bank} && DUT.CORE.web_ram{bank} &&
            DUT.CORE.addra_ram{bank} == DUT.CORE.addrb_ram{bank})
            $fatal(1, "undefined dual-write collision in RAM {bank}");
    end
"""
    if boot_restarts:
        monitor += """
    integer restart_count = 0;
    initial begin
        wait (boot_rst == 0);
        repeat (2) begin
            wait (boot_ready == 1);
            wait (start == 1);
            repeat (restart_count == 0 ? 250 : 2000) @(negedge clk);
            boot_rst = 1;
            repeat (3) @(negedge clk);
            // Reset this test's host transaction FSM, as required by a cold boot.
            state = S_INIT; sec_lvl = 2; c = 0; ctr = 0; average = 0;
            valid_i = 0; ready_o = 0; data_i = 0; start = 0; rst = 1;
            restart_count = restart_count + 1;
            boot_rst = 0;
        end
        $display("ASIC_RESTARTS_PASS count=%0d", restart_count);
    end
"""
    return text.replace('\nendmodule', monitor+'\nendmodule')


def check_restart_evidence(text):
    markers=list(re.finditer(r'^ASIC_RESTARTS_PASS count=(\d+)\s*$',text,re.MULTILINE))
    first=re.search(r'ML-DSA-(?:II|III|V)\.\w+, KAT #\s*\d+ completed in',text)
    if len(markers)!=1 or int(markers[0][1])!=2:
        raise ValueError('missing, duplicate or incorrect completed restart marker')
    if first is None or first.start() < markers[0].end():
        raise ValueError('a KAT completed before the two intended boot aborts')
    return {'observed_aborts':2,'marker_count':1,'marker_precedes_completed_kats':True,
            'last_boot_completed_before_kats':'transaction FSM cannot progress until boot_ready'}


def run(repo,design,out,tool_dir,jobs,selected,vector_count,seeds,boot_restarts=False):
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
    fixture_inputs=list((upstream/'KAT').glob('*'))+list((upstream/'ref_combined/src_tb').glob('*'))+[upstream/'common/mldsa_params.v']
    inputs.update({str(p):sha(p) for p in fixture_inputs})
    env=os.environ.copy();env['PATH']=str(Path(tool_dir).resolve())+os.pathsep+env['PATH'];env['MAKEFLAGS']='CFG_CXXFLAGS_PCH_I=-include'
    exe=shutil.which('verilator',path=env['PATH'])
    if not exe:raise ValueError('installed Verilator required')
    version=subprocess.run([exe,'--version'],env=env,text=True,capture_output=True,check=True).stdout.strip()
    result={'schema_version':1,'status':'RUNNING','design_manifest_sha256':sha(design/'manifest.json'),'variant':manifest['source_variant']+'+explicit-asic-startup','tool':version,'source_hashes':inputs,'coverage':{},'commands':[],'boot_restarts_per_process':2 if boot_restarts else 0,'collision_assertions':True,'two_state_simulation':True,'four_state_fullcore_qualified':False,'normal_reset_contract':'Original per-operation reset semantics retained; arbitrary abort/reset recovery is not claimed.'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    try:
        for case in selected:
            operation='verify' if case.startswith('verify') else case
            count={'keygen':25,'sign':15,'verify':15,'verify_mutations':4,'verify_canonical':11}[case]
            if vector_count is not None and not case.startswith('verify_'):count=vector_count
            work=out/case;tbdir=work/'ref_combined/src_tb';tbdir.mkdir(parents=True)
            shutil.copytree(upstream/'common',work/'common')
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
            tb=tbdir/source.name;tb.write_text(add_boot(text,boot_restarts));top=tb.stem;obj=work/'obj'
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
                if boot_restarts:
                    try: row['restart_evidence']=check_restart_evidence(text)
                    except ValueError as exc: row.update(status='FAIL',reason=str(exc))
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
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--design',required=True);p.add_argument('--out',required=True);p.add_argument('--tool-dir',required=True);p.add_argument('--jobs',type=int,default=2);p.add_argument('--cases',nargs='+',choices=['keygen','sign','verify','verify_mutations','verify_canonical'],default=['keygen','sign','verify','verify_mutations','verify_canonical']);p.add_argument('--vectors',type=int);p.add_argument('--seeds',type=int,nargs='+',default=[0]);p.add_argument('--boot-restarts',action='store_true')
    a=p.parse_args();r=run(a.repo,a.design,a.out,a.tool_dir,a.jobs,a.cases,a.vectors,a.seeds,a.boot_restarts);print(r['status'],a.out);sys.exit(0 if r['status']=='PASS' else 1)
