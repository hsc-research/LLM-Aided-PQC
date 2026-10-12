#!/usr/bin/env python3
"""Strict selected-hierarchy SLH generic FF lowering; no technology/PPA claim."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
import export_slh_verified as ex
import slh_asic_startup as boot
import slh_asic_control as control
import slh_asic_widths as widths
import slh_asic_diagnostics as diagnostics
ROOT=Path(__file__).resolve().parents[1]

def check(variant,parameter,work,yosys):
    work=Path(work).resolve();work.mkdir(parents=True,exist_ok=True)
    rtl=work/'rtl';original,_=ex.prepare_sources(ex.VARIANTS[variant],rtl,parameter)
    boot.boot_variant(rtl);control.control_variant(rtl);widths.width_variant(rtl);diagnostics.diagnostics_variant(rtl,parameter)
    before=ex.portable.rtl_hashes(rtl)
    sources=[p for p in ex.source_order(rtl) if p.name!='tb.v']
    inc=' '.join('-I'+str(rtl/x) for x in ('sphincslet','imports/global_include','sphincslet/fsm'))
    script='read_verilog -defer '+inc+' '+' '.join(map(str,sources))+'\nhierarchy -check -top top\nproc\nopt\nmemory -nomap\nmemory_map\nopt\ntechmap\nopt\ncheck -assert\nwrite_json '+str(work/'whole-ff.json')+'\nstat\n'
    (work/'mapping.ys').write_text(script)
    v=subprocess.run([str(yosys),'-V'],capture_output=True,text=True,timeout=30)
    if v.returncode:raise RuntimeError('Yosys version check failed')
    with (work/'mapping.log').open('w') as log:
        r=subprocess.run([str(yosys),'-Q','-T','-s',str(work/'mapping.ys')],stdout=log,stderr=subprocess.STDOUT,text=True,timeout=900)
    output=(work/'mapping.log').read_text()
    if r.returncode:raise RuntimeError('strict mapping failed; '+output[-3000:])
    warnings=[line for line in output.splitlines() if line.startswith('Warning:')]
    allowed=re.compile(r'^Warning: Replacing memory \\w_mem with list of registers\. See .*/sphincslet/sha/sha(?:256|512)_w_mem\.v:\d+$')
    if any(not allowed.fullmatch(line) for line in warnings):raise RuntimeError('unexpected strict warning: '+repr(warnings))
    net=json.loads((work/'whole-ff.json').read_text());mods=net['modules']
    if any(m.get('memories') for m in mods.values()):raise RuntimeError('memory remains')
    if any('init' in v.get('attributes',{}) for m in mods.values() for v in m.get('netnames',{}).values()):raise RuntimeError('power-up init remains')
    counts={}
    for name,m in mods.items():
        cell=Counter(c['type'] for c in m.get('cells',{}).values())
        if any('latch' in k.lower() or (not k.startswith('$_') and k not in mods) for k in cell):raise RuntimeError('unmapped/non-FF cell remains: '+str(cell))
        counts[name]=dict(cell)
    def expanded(name):
        c=Counter()
        for kind,n in counts[name].items():
            if kind in mods:
                for k,v in expanded(kind).items():c[k]+=n*v
            else:c[kind]+=n
        return c
    cells=expanded('top')
    if ex.portable.rtl_hashes(rtl)!=before:raise RuntimeError('staged sources changed during mapping')
    if ex.portable.rtl_hashes(ex.VARIANTS[variant])!=original:raise RuntimeError('original sources changed during mapping')
    return {'status':'PASS','variant':variant,'parameter_set':'SHA2-'+parameter,'scope':'whole-top generic FF/logic structural lowering; no technology mapping or PPA',
      'source_sha256':original,'staged_source_sha256':before,'design_source_sha256':{n:h for n,h in before.items() if n!='sphincslet/tb.v'},'staged_sources_unchanged':True,'original_sources_unchanged':True,
      'tool_version':v.stdout.strip(),'runner_sha256':ex.sha(Path(__file__)),'command':['yosys','-Q','-T','-s','mapping.ys'],'mapping_script_sha256':ex.sha(work/'mapping.ys'),
      'exact_expected_notices':warnings,'remaining_memories':0,'remaining_latches':0,'power_up_init_attributes':0,'undriven_or_conflicting_drivers':0,
      'ff_bits':sum(n for k,n in cells.items() if 'DFF' in k),'flattened_generic_cell_counts':dict(cells),'netlist_sha256':ex.sha(work/'whole-ff.json'),'mapping_log_sha256':ex.sha(work/'mapping.log'),'work_dir':str(work)}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--variant',choices=ex.VARIANTS,required=True);p.add_argument('--parameter-set',choices=('128f','192f'),required=True);p.add_argument('--work-dir',type=Path,required=True);p.add_argument('--yosys',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    try:r=check(a.variant,a.parameter_set,a.work_dir,a.yosys)
    except Exception as e:r={'status':'FAIL','reason':str(e)}
    a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));sys.exit(r['status']!='PASS')
