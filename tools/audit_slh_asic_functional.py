#!/usr/bin/env python3
"""Recheck immutable functional artifacts and create portable log provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import check_slh_portable as portable
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit(path,log_dir):
    import export_slh_asic_verified as exporter
    path=Path(path).resolve();raw=path.read_bytes();r=json.loads(raw)
    if r.get('status')!='PASS' or r.get('evidence_kind')!='asic_boot_vendor_rtl_differential':raise ValueError('functional derivative did not pass')
    parameter=r['parameter_set'].removeprefix('SHA2-')
    if parameter not in ('128f','192f'):raise ValueError('unsupported parameter')
    w=Path(r['run_dir']);staged=w/'rtl';binary=w/'tb.vvp'
    if portable.rtl_hashes(staged)!=r['staged_source_sha256'] or sha(binary)!=r['executable_sha256']:raise ValueError('executed RTL/binary identity changed')
    if sha(ROOT/'tools/check_slh_portable.py')!=r['runner_sha256']:raise ValueError('functional runner identity changed')
    log_dir=Path(log_dir).resolve();log_dir.mkdir(parents=True,exist_ok=True)
    _,golden=portable.gate.load_reference(parameter)
    cases=[];files={}
    def retain(src,name):
        dst=log_dir/name;shutil.copyfile(src,dst)
        if sha(src)!=sha(dst):raise ValueError('artifact changed during copy')
        files[str(dst.relative_to(ROOT))]=sha(dst)
    retain(w/'compile.log','compile.log');retain(w/'compile-command.json','compile-command.json')
    report_cases={c['case']:c for c in r['cases']}
    if set(report_cases)!={'baseline','signature-memory-bitflip'} or len(r['cases'])!=2:raise ValueError('wrong functional case inventory')
    for name in ('baseline','signature-memory-bitflip'):
        case=report_cases[name];log=w/name/'sim.log';output=log.read_text()
        produced=w/name/'TECS_v8.srcs/sources_1/imports/data_sha2'/('SIG_file0_'+parameter+'_w.hex')
        checked=portable.check_case(golden,produced,output,case['simulator_returncode'],parameter,name!='baseline')
        if checked['status']!='PASS' or checked['output_sha256']!=case['output_sha256'] or checked['rtl_verification_flag']!=case['rtl_verification_flag']:raise ValueError('saved simulation artifacts do not satisfy exact signature/verify controls')
        lines=[line for line in output.splitlines() if line.startswith('SLH_ASIC_ADDRESS_REPORT ')]
        if output.count('SLH_ASIC_BOOT_READY')!=1 or lines!=case['consumed_address_reports']:raise ValueError('boot/address report differs from raw log')
        exporter.validate_address_reports({'consumed_address_reports':lines},parameter)
        retain(log,name+'.log');retain(w/name/'command.json',name+'-command.json');retain(produced,name+'-produced.hex')
        cases.append({'case':name,'status':'PASS','log_sha256':sha(log),'produced_sha256':sha(produced),'rtl_verification_flag':checked['rtl_verification_flag'],'address_reports':lines})
    if path.read_bytes()!=raw:raise ValueError('functional report changed during audit')
    return {'status':'PASS','parameter_set':r['parameter_set'],'functional_report_sha256':hashlib.sha256(raw).hexdigest(),'executed_binary_sha256':r['executable_sha256'],
        'auditor_sha256':sha(__file__),'checker_sha256':sha(ROOT/'tools/check_slh_portable.py'),'portable_files_sha256':files,'cases':cases,
        'scope':'raw artifact recheck and portable provenance; historical vendor differential, not independent algorithm validation'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--functional-report',type=Path,required=True);p.add_argument('--log-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    try:r=audit(a.functional_report,a.log_dir)
    except Exception as e:r={'status':'FAIL','reason':str(e)}
    a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));sys.exit(r['status']!='PASS')
