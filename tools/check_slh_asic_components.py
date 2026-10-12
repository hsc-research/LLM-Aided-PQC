#!/usr/bin/env python3
"""Focused SLH ASIC boot and postboot memory tests, plus FF mapping."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile
import sys
import hashlib

import export_slh_verified as export
import slh_asic_startup as boot
import slh_asic_control as control
import slh_asic_widths as widths
import check_asic_memory_components as mapping
ROOT=Path(__file__).resolve().parents[1]
def run(argv,cwd):
    result=subprocess.run(list(map(str,argv)),cwd=cwd,text=True,capture_output=True,timeout=180)
    return result.returncode,result.stdout+result.stderr

def check(work,tool_dir):
    work=Path(work).resolve(); work.mkdir(parents=True,exist_ok=True)
    tool_dir=Path(tool_dir)
    before={str(p.relative_to(ROOT)):boot.sha(p.read_bytes()) for p in [Path(__file__),Path(boot.__file__),Path(control.__file__),Path(widths.__file__),*boot.TEMPLATES.glob('*.v'),*(ROOT/'verification/slh_asic_startup').glob('*.sv')]}
    references = [ROOT/'agent/slh_dsa/pristine/imports'/name for name in ('mem_dual.v','mem_single.v','fifo.v','global_include/clog2.v')]
    reference_hashes = {str(p.relative_to(ROOT)):ex_hash for p in references for ex_hash in [export.sha(p)]}
    versions = {}
    for name in ('iverilog','vvp','yosys'):
        rc,out=run([tool_dir/name,'-V'],work)
        if rc or not out.strip():raise RuntimeError('tool version query failed: '+name)
        versions[name]=out.splitlines()[0]
    results=[]
    staged_records=[]
    for variant,parameter in ((v,p) for v in ('corrected-baseline','corrected-candidate') for p in ('128f','192f')):
        label=variant+'-'+parameter
        rtl=work/label/'rtl'
        export.prepare_sources(export.VARIANTS[variant],rtl,parameter)
        boot.boot_variant(rtl)
        control.control_variant(rtl)
        widths.width_variant(rtl)
        staged_before=export.portable.rtl_hashes(rtl)
        sources=[p for p in export.source_order(rtl) if p.name!='tb.v']
        binary=work/(label+'.vvp')
        cmd=[tool_dir/'iverilog','-g2005','-s','tb_startup','-o',binary]
        for inc in ('sphincslet','imports/global_include','sphincslet/fsm'):cmd += ['-I',rtl/inc]
        command=cmd+sources+[ROOT/'verification/slh_asic_startup/tb_startup.sv']
        rc,out=run(command,work)
        (work/(label+'-compile.log')).write_text(out)
        if rc:raise RuntimeError(out[-4000:])
        rc,out=run([tool_dir/'vvp',binary],work)
        (work/(label+'-simulation.log')).write_text(out)
        if rc or 'SLH_ASIC_STARTUP_PASS' not in out:raise RuntimeError(out)
        if export.portable.rtl_hashes(rtl)!=staged_before:raise RuntimeError('staged startup RTL changed during simulation')
        staged_records.append({'variant':variant,'parameter_set':parameter,'staged_source_sha256':staged_before,'compile_command':list(map(str,command)),'binary_sha256':export.sha(binary),'staged_sources_unchanged':True})
        results.append({'variant':variant,'parameter_set':parameter,'status':'PASS','test':'whole_top_boot_restart_and_normal_reset','output':out.strip()})
    refs=[]
    for name,module in [('mem_dual.v','dual'),('mem_single.v','single'),('fifo.v','fifo')]:
        source=ROOT/'agent/slh_dsa/pristine/imports'/name
        target=work/('reference_'+name)
        target.write_text(source.read_text().replace('module '+name[:-2], 'module reference_'+module))
        refs.append(target)
    binary=work/'memories.vvp'
    sources=[ROOT/'agent/slh_dsa/pristine/imports/global_include/clog2.v',boot.TEMPLATES/'mem_dual.v',boot.TEMPLATES/'mem_single.v',boot.TEMPLATES/'fifo.v',*refs,ROOT/'verification/slh_asic_startup/tb_memories.sv']
    rc,out=run([tool_dir/'iverilog','-g2005','-s','tb_memories','-o',binary,*sources],work)
    (work/'memories-compile.log').write_text(out)
    if rc:raise RuntimeError(out)
    rc,out=run([tool_dir/'vvp',binary],work)
    (work/'memories-simulation.log').write_text(out)
    if rc or 'SLH_ASIC_MEMORIES_PASS' not in out:raise RuntimeError(out)
    results.append({'status':'PASS','test':'postboot_memory_fifo_equivalence','output':out.strip()})
    # Non-power-of-two valid final word, invalid tails and X-address reads.
    binary_np=work/'memories-nonpower.vvp'
    rc,out=run([tool_dir/'iverilog','-g2005','-s','tb_memories','-Ptb_memories.DUAL_DEPTH=5','-o',binary_np,*sources],work)
    if rc:raise RuntimeError(out)
    rc,out=run([tool_dir/'vvp',binary_np],work)
    (work/'memories-nonpower-simulation.log').write_text(out)
    if rc or 'SLH_ASIC_MEMORIES_PASS' not in out:raise RuntimeError(out)
    results.append({'status':'PASS','test':'nonpower_valid_invalid_unknown_addresses','output':out.strip()})
    synthesized=[]
    for name,params in [('mem_dual','-set WIDTH 8 -set DEPTH 7 -set INIT 1'),('mem_single','-set WIDTH 8 -set DEPTH 8 -set INIT 1'),('fifo','-set BW 8 -set LGFLEN 3')]:
        synthesized.append(mapping.synthesize(str(tool_dir/'yosys'),work,name,[sources[0],boot.TEMPLATES/(name+'.v')],name,parameters=params))
    for depth,width,init in ((80,64,1),(171,64,1),(36,4,0),(52,4,0)):
        synthesized.append(mapping.synthesize(str(tool_dir/'yosys'),work,'production-dual-'+str(depth),[sources[0],boot.TEMPLATES/'mem_dual.v'],'mem_dual',parameters=f'-set WIDTH {width} -set DEPTH {depth} -set INIT {init}',expected_ff_bits=(depth+1)*width+2*width+((depth+1).bit_length()+1 if init else 0)))
    for name in ('mem_dual','mem_single'):

        rc,out=run([tool_dir/'iverilog','-g2005','-s',name,'-P'+name+'.FILE="forbidden.hex"','-o',work/'bad.vvp',sources[0],boot.TEMPLATES/(name+'.v')],work)
        if not rc:raise RuntimeError('unsupported FILE configuration compiled')
        results.append({'test':name+'_file_rejection','status':'PASS'})
    if {n:export.sha(ROOT/n) for n in reference_hashes}!=reference_hashes:raise RuntimeError('original reference memory sources changed')
    after={name:boot.sha((ROOT/name).read_bytes()) for name in before}
    if after!=before:raise RuntimeError('component inputs changed during check')
    return {'status':'PASS','scope':'focused boot/memory RTL and bounded generic FF mapping; not full functional qualification or PPA','source_sha256':before,'reference_source_sha256':reference_hashes,'tool_versions':versions,'staged_qualification':staged_records,'inputs_unchanged':True,'tests':results,'generic_mapping':synthesized}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,required=True);p.add_argument('--tool-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    try:r=check(a.work_dir,a.tool_dir)
    except Exception as e:r={'status':'FAIL','reason':str(e)}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));sys.exit(r['status']!='PASS')
