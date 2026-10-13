"""Collect exact-source Vivado OOC synthesis feedback, without target admission.

The adapter deliberately returns BLOCKED rather than MEASURED because it does
not establish mapped-memory behavior or qualify implementation warnings.
"""
import argparse
import json
import math
import os
from pathlib import Path
from agent.whole_design_adapters import read_request, verify_inputs
from agent.whole_design import require, save
from agent.run_safety import hashes, run_process
from agent.ppa_reader import parse_util, extract_wns
from tools.export_target_profiles import tcl_word, tcl_list


def collect(request_path, response_path, execute=False):
    req, response=read_request(request_path,response_path,'measure')
    cfg=req['configuration'];spec=cfg['measurement'];profile=cfg.get('target_profile',{})
    require(cfg['target']=='fpga' and cfg['backend']=='vivado' and spec['stage']=='post_synth','Only Vivado post-synthesis FPGA feedback is supported')
    require(profile.get('design')=='mldsa','Only exported ML-DSA is supported')
    elab=profile['elaboration']
    require([r['path'] for r in elab['sources']]==cfg['source_read_order'] and set(cfg['source_read_order'])==set(req['source_hashes']),'Source order mismatch')
    require(elab['parameters']=={} and elab['defines']==[] and all(r['language']=='verilog' for r in elab['sources']),'Unsupported elaboration controls')
    period=spec['period_ns'];require(type(period)in(int,float) and math.isfinite(period) and period>0,'Invalid period')
    require(len(spec['constraints'])==1,'Exactly one XDC required')
    xdc=Path(spec['constraints'][0]).resolve()
    require(str(xdc) in cfg['immutable_hashes'],'XDC must be frozen using an absolute path')
    out=Path(response_path).resolve().parent;run=out/'vivado';require(not run.exists(),'Fresh output required');run.mkdir()
    script=['if {[catch {', 'set actual_version [version -short]',
            'if {$actual_version ne '+tcl_word(spec['tool_version'])+'} {error "Vivado version mismatch"}',
            'set vf [open '+tcl_word(run/'tool-version.txt')+' w]; puts $vf $actual_version; close $vf',
            'cd '+tcl_word(run),'create_project -in_memory -part '+tcl_word(spec['part']),
            'set_property include_dirs '+tcl_list(elab['include_dirs'])+' [current_fileset]']
    for p in elab['data_files']:script.append('file copy '+tcl_word(p)+' '+tcl_word(Path(p).name))
    script+=['read_verilog '+tcl_list(cfg['source_read_order']), 'read_xdc '+tcl_word(xdc),
             'synth_design -top '+tcl_word(cfg['top'])+' -part '+tcl_word(spec['part'])+' -mode out_of_context -gated_clock_conversion off',
             'if {[llength [get_clocks]] != 1} {error "Expected exactly one clock"}',
             'if {abs([get_property PERIOD [get_clocks]] - '+str(period)+') > 1e-9} {error "Clock mismatch"}',
             'report_utilization -file utilization.rpt','report_utilization -hierarchical -file utilization_hierarchical.rpt','report_timing_summary -file timing.rpt',
             'report_timing -max_paths 5 -path_type full_clock_expanded -file paths.rpt',
             'check_timing -verbose -file check_timing.rpt','report_drc -file drc.rpt',
             'write_checkpoint synthesized.dcp','write_verilog -mode funcsim implementation.v',
             '} message]} {puts stderr $message; exit 1}','exit 0']
    tcl=run/'launch.tcl';tcl.write_text('\n'.join(script)+'\n')
    response.update(status='BLOCKED',scope='full_design',configuration=cfg,source_hashes=req['source_hashes'],
                    source_read_order=cfg['source_read_order'],target_profile_fingerprint=profile['profile_fingerprint'],
                    blockers=['Mapped-memory behavior is not verified','Structural warnings require site review','Path-to-RTL mapping requires site qualification'],
                    structural_checks_verified=False,memory_implementation_verified=False,memory_semantics_verified=False,
                    stage='post_synth',metrics=None,power=None,executed=False,reports={})
    if execute:
        env=os.environ.copy()
        # Avoid Python virtual environment libraries being loaded into Vivado.
        for key in ('PYTHONHOME','PYTHONPATH'):env.pop(key,None)
        completed=run_process(['vivado','-mode','batch','-source',str(tcl),'-log',str(run/'vivado.log'),'-journal',str(run/'vivado.jou')],cwd=run,env=env,timeout=86400,log_path=run/'console.log')
        response['executed']=True;response['tool_returncode']=completed.returncode
        verify_inputs(req)
        if completed.returncode==0:
            actual=(run/'tool-version.txt').read_text().strip();require(actual==spec['tool_version'],'Actual tool version mismatch')
            response['actual_tool_version']=actual
            response['metrics']={**parse_util(run/'utilization.rpt'),'worst_setup_slack_ns':extract_wns((run/'timing.rpt').read_text())}
            response['measurement_label']='PRELIMINARY_POST_SYNTH_NOT_ADMITTED'
        else:response['blockers'].insert(0,'Vivado failed; inspect console.log')
        for name in ('timing.rpt','utilization.rpt','utilization_hierarchical.rpt','paths.rpt','check_timing.rpt','drc.rpt','implementation.v','vivado.log','console.log'):
            path=run/name
            if path.is_file():response['reports'][name]={'path':str(path.relative_to(out)),'sha256':hashes([path])[str(path)]}
    verify_inputs(req);save(response_path,response);return response


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',required=True);p.add_argument('--response',required=True);p.add_argument('--execute',action='store_true');a=p.parse_args();print(json.dumps(collect(a.request,a.response,a.execute),indent=2))
if __name__=='__main__':main()
