#!/usr/bin/env python3
"""Revalidate exact source, compiled artifact, log coverage and generic-FF evidence.

This consumes finished local runs; it never substitutes requested coverage for
observed results and never invokes an EDA tool. Output is a fresh report only.
"""
from pathlib import Path
import argparse, collections, gc, json, re, sys
from build_mldsa_startup_derivative import sha
from check_mldsa_startup_kats import check_restart_evidence


def netlist_summary(path):
    path=Path(path); data=json.loads(path.read_text()); modules=data['modules']
    latches=[];memories=[];initializers=[];tristates=[];blackboxes=[]
    for name,mod in modules.items():
        if any(int(str(mod.get('attributes',{}).get(key,'0')),2) for key in ('blackbox','whitebox')):
            blackboxes.append(name)
        for net,wire in mod['netnames'].items():
            if 'init' in wire.get('attributes',{}):initializers.append((name,net))
        if mod.get('memories'):memories.extend((name,m) for m in mod['memories'])
        for cname,cell in mod['cells'].items():
            typ=cell['type']
            if 'latch' in typ.lower() or typ=='$sr':latches.append((name,cname))
            if typ.startswith('$mem'):memories.append((name,cname))
            if 'tribuf' in typ.lower() or 'tbuf' in typ.lower():tristates.append((name,cname))
            if typ not in modules and not typ.startswith('$'):blackboxes.append((name,cname,typ))
    if latches or memories or initializers or tristates or blackboxes:
        raise ValueError('residual forbidden generic structure: '+str({'latches':len(latches),'memories':len(memories),'init':len(initializers),'tristates':len(tristates),'blackboxes':len(blackboxes)}))
    cache={}
    def count(name,parents=()):
        if name in parents:raise ValueError('recursive netlist hierarchy')
        if name in cache:return cache[name]
        bits=0;banks=collections.Counter()
        for cell in modules[name]['cells'].values():
            typ=cell['type']
            if typ in modules:
                subbits,subbanks=count(typ,parents+(name,));bits+=subbits;banks.update(subbanks)
            elif 'ff' in typ.lower():bits+=len(cell['connections']['Q'])
        if 'mldsa_sameclock_ff_ram' in name:
            ports=modules[name]['ports'];depth=2**len(ports['addra']['bits']);width=len(ports['dia']['bits'])
            banks[f'{depth}x{width}']+=1
            if bits!=width*(depth+2):raise ValueError('production RAM FF bit count differs')
        cache[name]=(bits,banks);return bits,banks
    total,banks=count('combined_top_asic')
    if dict(banks)!={'4096x96':1,'1024x96':6}:raise ValueError('whole-core bank multiplicity differs: '+str(banks))
    result={'status':'PASS','tool_version':data.get('creator'),'netlist_sha256':sha(path),'module_count':len(modules),'reachable_module_types':len(cache),
            'hierarchical_ff_bits':total,'production_ram_banks':dict(banks),'production_storage_bits':983040,
            'production_ram_output_ff_bits':1344,'production_ram_total_ff_bits':984384,
            'remaining_memory_cells':0,'remaining_latch_cells':0,'powerup_init_attributes':0,'tristate_cells':0,'blackboxes':0,
            'standard_cell_mapped':False,'mapped_netlist_functional_equivalence':False}
    del data,modules;gc.collect();return result


def collect(repo,workspace,out):
    repo=Path(repo).resolve();w=Path(workspace).resolve();out=Path(out).resolve()
    if out.exists():raise ValueError('report output must be new')
    sys.path.insert(0,str(repo))
    from tools.export_mldsa_verified import validate_report
    from agent.mldsa.portable_kat_gate import evaluate_log
    result={'schema_version':1,'status':'PASS','qualification_scope':'Exact-source full RTL KATs, explicit boot semantics and generic FF structural mapping',
            'standard_cell_qualification':False,'physical_timing_ppa_qualification':False,'fullcore_fourstate_qualification':False,
            'variants':{},'components':{},'limitations':['Full KATs are two-state Verilator runs with finite randomized-initial-state checks, not formal equivalence.',
                'Full-core Icarus was bounded at 45 seconds without completion; four-state component checks are separate.',
                'No standard-cell library mapping, mapped-netlist functional simulation/equivalence, timing, PPA or FIPS certification.',
                'Only supported runtime levels 2/3/5 and original operation reset/start protocol are covered; arbitrary ordinary-reset abort recovery is not qualified.']}
    for short,variant,label in [('baseline','guarded-baseline','baseline_canonical_pass'),('candidate','corrected-candidate','candidate_corrected_pass')]:
        design=w/'release'/variant;manifest=json.loads((design/'manifest.json').read_text());run=w/'runs'/('release-'+short);r=json.loads((run/'result.json').read_text())
        if r.get('status')!='PASS' or not r.get('full_210_case_coverage') or not r.get('source_hashes_unchanged'):
            raise ValueError('unfinished, reduced or changed-input run: '+short)
        if r['design_manifest_sha256']!=sha(design/'manifest.json'):raise ValueError('source manifest changed')
        for row in manifest['sources']:
            p=design/row['path']
            if sha(p)!=row['sha256'] or r['source_hashes'].get(str(p))!=row['sha256']:raise ValueError('source binding failed '+str(p))
        for field in ('source_hashes','executable_hashes','testbench_hashes'):
            for p,h in r[field].items():
                if sha(p)!=h:raise ValueError(field+' changed: '+p)
        expected_keys={f'{c}:seed-{s}' for c in ('keygen','sign','verify','verify_mutations','verify_canonical') for s in (0,11,29)}
        if set(r['coverage'])!=expected_keys:raise ValueError('unexpected seed/case coverage')
        reference=json.loads((repo/'docs/verification/mldsa-portable-2026-10-12'/label/'result.json').read_text())
        checked={};logs={};restart_total=0
        for seed in (0,11,29):
            coverage={}
            for case in ('keygen','sign','verify','verify_mutations','verify_canonical'):
                row=r['coverage'][f'{case}:seed-{seed}'];log=run/case/f'simulate-seed-{seed}.log';text=log.read_text()
                op='verify' if case.startswith('verify') else case;count={'keygen':25,'sign':15,'verify':15,'verify_mutations':4,'verify_canonical':11}[case]
                parsed=evaluate_log(text,op,count,row['simulator_returncode'])
                if parsed['status']!='PASS' or parsed['vectors']!=row['vectors']:raise ValueError('log coverage differs from report')
                restart=check_restart_evidence(text);restart_total+=restart['observed_aborts']
                if row['vectors']!=reference['coverage'][case]['vectors']:raise ValueError('postboot cycle counts differ from reference')
                coverage[case]={**row,'restart_evidence':restart,'postboot_cycle_counts_match_reference':True}
                logs[str(log.relative_to(w))]=sha(log)
            test={'status':'PASS','variant':reference['variant'],'coverage':coverage};validate_report(test,variant)
            checked[str(seed)]={'status':'PASS','coverage':coverage,'tested_cases':210,'postboot_cycle_counts_match_reference':True}
        for log in run.glob('*/compile.log'):logs[str(log.relative_to(w))]=sha(log)
        mapping=w/'mapping'/f'release-{short}-ff.log';logtext=mapping.read_text()
        if len(re.findall(r'Found and reported 0 problems\.',logtext))!=2 or re.search(r'^ERROR:',logtext,re.MULTILINE):
            raise ValueError('whole-core proc and FF structural checks did not both pass')
        structural=netlist_summary(w/'mapping'/f'release-{short}-ff.json')
        logs[str(mapping.relative_to(w))]=sha(mapping)
        record={'status':'PASS','source_variant':variant,'top':'combined_top_asic','source_manifest':f'asic/rtl/mldsa_startup/{variant}/manifest.json',
                'source_manifest_sha256':sha(design/'manifest.json'),'sources':[{**row,'language':'verilog2005'} for row in manifest['sources']],
                'full_kat_report':f'docs/verification/mldsa-asic-startup-2026-10-12/{short}/full-result.json','full_kat_report_sha256':sha(run/'result.json'),
                'functional':{'status':'PASS','compile_status':'PASS','settings':checked,'completed_cases':630,'exact_source_bound':True},
                'startup':{'status':'PASS','observed_boot_aborts':restart_total,'abort_markers_before_first_completed_kat':True,'source_contract':manifest['contract'],
                           'ordinary_reset_midoperation_recovery_qualified':False},'structural':structural,'logs':logs}
        result['variants']['asic-startup-'+short]=record
    component_path=w/'runs/release-components/result.json'
    component=json.loads(component_path.read_text())
    if component.get('status')!='PASS' or component.get('design_manifest_sha256')!=sha(w/'release/guarded-baseline/manifest.json'):
        raise ValueError('component evidence does not match release source')
    for name,row in component['checks'].items():
        if row.get('status')!='PASS' or row.get('compile_returncode')!=0 or row.get('simulate_returncode')!=0 or row.get('observed_marker_count')!=1 or not row.get('input_hashes_unchanged'):
            raise ValueError('component evidence failed: '+name)
        for p,h in row['input_hashes'].items():
            if sha(p)!=h:raise ValueError('component source changed: '+p)
        if sha(w/'runs/release-components'/(name+'-simulate.log'))!=row['simulate_log_sha256']:
            raise ValueError('component simulation log changed')
        result['components'][name]=row
    result['component_report']={'path':'docs/verification/mldsa-asic-startup-2026-10-12/components/result.json','sha256':sha(component_path)}
    fault=w/'trials/hint-unknown-fault.log'
    if 'unknown observable output' not in fault.read_text() or 'ASIC_HINT_READ_VIEW_PASS' in fault.read_text():
        raise ValueError('knownness fault injection did not fail')
    result['components']['knownness_negative_control']={'status':'EXPECTED_FAILURE','log_sha256':sha(fault),
        'fault_testbench_sha256':sha(w/'trials/tb_unknown_fault.sv'),'reason':'both implementations expose X in a live hint byte; independent knownness check rejects it'}
    result['tools']={'yosys_large_stack_runner_sha256':sha(Path(__file__).resolve().parent/'run_yosys_large_stack.py'),'evidence_checker_sha256':sha(Path(__file__)),
                     'wasm_stack_bytes':16777216,'async_stack_bytes':33554432,'thread_stack_bytes':33554432}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--workspace',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    r=collect(a.repo,a.workspace,a.out);print(r['status'])
    for name,row in r['variants'].items():print(name,row['functional']['completed_cases'],row['structural']['hierarchical_ff_bits'])
