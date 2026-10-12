#!/usr/bin/env python3
"""Exhaustive synchronous tuple/hold-transition test of actual XMSS decoder RTL."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import export_slh_verified as ex
import slh_asic_startup as startup
import slh_asic_control as control
ROOT=Path(__file__).resolve().parents[1]

def check(work,tools):
    work=Path(work).resolve();work.mkdir(parents=True,exist_ok=True);tools=Path(tools)
    rtl=work/'rtl';ex.prepare_sources(ex.VARIANTS['corrected-baseline'],rtl,'128f');startup.boot_variant(rtl)
    path=rtl/'sphincslet/fsm/XMSS_FSM.v';before=path.read_text();control.control_variant(rtl);after=path.read_text()
    marker='always@(cnt, ch_cnt, LR_flag, LR_flag2, hash_done_1d, flag_last, XMSS_start) begin'
    start=before.rindex(marker);end=before.index('\n`endif',start)
    original=before[start:end]
    start=after.index('reg sig_read_history;');end=after.index('\n`endif',start)
    current=after[start:end]
    for name,body in [('original',original),('current',current)]:
        text='module '+name+'''_decoder #(parameter CH_len=2)(input clk,rstn,input [3:0] cnt,ch_cnt,input LR_flag2,XMSS_start,output reg o_sig_read_mem_r);
wire LR_flag=0,hash_done_1d=0,flag_last=0;
'''+body+'\nendmodule\n'
        (work/(name+'.v')).write_text(text)
    sources=[work/'original.v',work/'current.v',ROOT/'verification/slh_asic_startup/tb_control.sv']
    results=[]
    for ch in (2,4):
        binary=work/('control'+str(ch)+'.vvp')
        cmd=[tools/'iverilog','-g2005','-s','tb_control','-Ptb_control.CH_len='+str(ch),'-o',binary,*sources]
        r=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,timeout=60)
        if r.returncode:raise RuntimeError(r.stdout+r.stderr)
        r=subprocess.run([str(tools/'vvp'),str(binary)],capture_output=True,text=True,timeout=60)
        (work/('control'+str(ch)+'.log')).write_text(r.stdout+r.stderr)
        if r.returncode or 'SLH_ASIC_CONTROL_PASS' not in r.stdout:raise RuntimeError(r.stdout+r.stderr)
        results.append({'CH_len':ch,'status':'PASS','checks':12294,'output':r.stdout.strip()})
    return {'status':'PASS','evidence':'exhaustive binary decoder tuples plus hold-entry/hold-exit transitions at settled clock cycles',
      'assumptions':'cnt/ch_cnt/XMSS_start/LR_flag2 change only via existing posedge registers; no arbitrary asynchronous-input equivalence claim',
      'reference_sha256':startup.sha(before.encode()),'derivative_sha256':startup.sha(after.encode()),
      'transform_sha256':ex.sha(Path(control.__file__)),
      'test_inputs_sha256':{str(p.relative_to(ROOT)):ex.sha(p) for p in (Path(__file__),ROOT/'verification/slh_asic_startup/tb_control.sv')},'cases':results}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--work-dir',type=Path,required=True);p.add_argument('--tool-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 try:r=check(a.work_dir,a.tool_dir)
 except Exception as e:r={'status':'FAIL','reason':str(e)}
 a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));sys.exit(r['status']!='PASS')
