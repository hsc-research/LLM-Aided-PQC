#!/usr/bin/env python3
"""Additional exact-netlist checks, separate from the frozen synthesis runner."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import shutil
ROOT=Path(__file__).resolve().parents[1]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def audit(report_path, artifact_dir):
    report_path=Path(report_path).resolve();before=report_path.read_bytes();r=json.loads(before)
    if r.get('status')!='PASS':raise ValueError('structural run did not pass')
    netpath=Path(r['work_dir'])/'whole-ff.json'
    digest=sha(netpath)
    if digest!=r['netlist_sha256']:raise ValueError('netlist differs from structural record')
    artifact_dir=Path(artifact_dir).resolve();artifact_dir.mkdir(parents=True,exist_ok=True)
    artifacts={}
    for name,key in (('mapping.ys','mapping_script_sha256'),('mapping.log','mapping_log_sha256')):
        source=netpath.parent/name;target=artifact_dir/name
        if sha(source)!=r[key]:raise ValueError('mapping artifact differs from structural record')
        shutil.copyfile(source,target)
        if sha(target)!=r[key]:raise ValueError('mapping artifact changed during copy')
        artifacts[str(target.relative_to(ROOT))]=r[key]
    data=json.loads(netpath.read_text());modules=data['modules']
    boxes=[];tribufs=[];unmapped=[];inits=[];memories=[];latches=[]
    for name,module in modules.items():
        for key in ('blackbox','whitebox','lib_whitebox'):
            if key in module.get('attributes',{}):boxes.append(name+':'+key)
        if module.get('memories'):memories.append(name)
        for net,details in module.get('netnames',{}).items():
            if 'init' in details.get('attributes',{}):inits.append(name+'.'+net)
        for cell,details in module.get('cells',{}).items():
            kind=details['type'];location=name+'.'+cell
            if 'TBUF' in kind.upper() or 'TRIBUF' in kind.upper():tribufs.append(location)
            if 'LATCH' in kind.upper():latches.append(location)
            if not kind.startswith('$_') and kind not in modules:unmapped.append(location+':'+kind)
    if any((boxes,tribufs,unmapped,inits,memories,latches)):
        raise ValueError('netlist contains unsupported structures: '+repr({'boxes':boxes,'tribufs':tribufs,'unmapped':unmapped,'inits':inits,'memories':memories,'latches':latches}))
    if report_path.read_bytes()!=before or sha(netpath)!=digest:raise ValueError('audit input changed during validation')
    return {'status':'PASS','variant':r['variant'],'parameter_set':r['parameter_set'],
            'portable_artifacts_sha256':artifacts,'structural_report_sha256':hashlib.sha256(before).hexdigest(),'netlist_sha256':digest,'auditor_sha256':sha(__file__),
            'blackbox_or_whitebox_modules':0,'tri_state_cells':0,'unmapped_cells':0,'remaining_memories':0,'remaining_latches':0,'power_up_init_attributes':0,
            'scope':'exact generic netlist structural audit only; no standard-cell mapping, timing, PPA or undefined-address hardware claim'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--structure-report',type=Path,required=True);p.add_argument('--artifact-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    try:r=audit(a.structure_report,a.artifact_dir)
    except Exception as e:r={'status':'FAIL','reason':str(e)}
    a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));sys.exit(r['status']!='PASS')
