"""Collect exact-source Vivado OOC estimates and evidence-derived qualification.

Dry runs prepare only. --execute runs the fixed, reviewed synthesis/report path.
Observable qualification gates are computed from reports, never supplied flags.
No mapped-memory behavior or routed closure is inferred from synthesis success.
"""
import argparse
import json
import math
import os
import shutil
from pathlib import Path
from agent.whole_design_adapters import read_request, verify_inputs, require_immutable
from agent.whole_design import require, save
from agent.run_safety import hashes, run_process
from agent import vivado_qualification as qualification
from tools.export_target_profiles import tcl_word, tcl_list


def collect(request_path, response_path, execute=False):
    req, response = read_request(request_path, response_path, 'measure')
    cfg = req['configuration']; spec = cfg['measurement']; profile = cfg.get('target_profile', {})
    require(cfg['target'] == 'fpga' and cfg['backend'] == 'vivado' and spec['stage'] == 'post_synth',
            'Only Vivado post-synthesis FPGA feedback is supported')
    require(profile.get('design') == 'mldsa', 'Only exported ML-DSA is supported')
    elab = profile['elaboration']
    require([r['path'] for r in elab['sources']] == cfg['source_read_order']
            and set(cfg['source_read_order']) == set(req['source_hashes']), 'Source order mismatch')
    require(elab['parameters'] == {} and elab['defines'] == []
            and not elab.get('global_include_files', [])
            and all(r['language'] == 'verilog' for r in elab['sources']), 'Unsupported elaboration controls')
    period = spec['period_ns']
    require(type(period) in (int, float) and math.isfinite(period) and period > 0, 'Invalid period')
    require(len(spec['constraints']) == 1, 'Exactly one XDC required')
    require(spec.get('effort', 'default') == 'default' and spec.get('seed', 'not_applicable') == 'not_applicable',
            'This synthesis adapter supports default effort and no implementation seed')
    path_count = spec.get('critical_path_count', 5)
    require(type(path_count) is int and 1 <= path_count <= 100, 'Invalid path count')
    xdc = Path(spec['constraints'][0]).resolve()
    require(str(xdc) in cfg['immutable_hashes'], 'XDC must be frozen using an absolute path')
    if execute:
        for path in qualification.dependencies():
            require_immutable(path, req)
        for path in elab['data_files']:
            require_immutable(path, req)
        for path in elab.get('include_files', []):
            require_immutable(path, req)
    out = Path(response_path).resolve().parent
    run = out / 'vivado'; require(not run.exists(), 'Fresh output required'); run.mkdir()
    request_sha = response.get('request_sha256')
    # A missing request hash is permitted only in old dry-run test callers, never
    # in an executed invocation or in either qualification validator.
    if execute:
        require(isinstance(request_sha, str) and len(request_sha) == 64, 'Missing request hash')
    save(run / 'input-manifest.json', qualification.input_manifest(req, request_sha))
    script = ['if {[catch {', 'set actual_version [version -short]',
              'set vf [open ' + tcl_word(run / 'tool-version.txt') + ' w]; puts $vf $actual_version; close $vf',
              'if {$actual_version ne ' + tcl_word(spec['tool_version']) + '} {error "Vivado version mismatch"}',
              'cd ' + tcl_word(run), 'create_project -in_memory -part ' + tcl_word(spec['part']),
              'set_property include_dirs ' + tcl_list(elab['include_dirs']) + ' [current_fileset]']
    for path in elab['data_files']:
        script.append('file copy ' + tcl_word(path) + ' ' + tcl_word(Path(path).name))
    script += ['read_verilog ' + tcl_list(cfg['source_read_order']), 'read_xdc ' + tcl_word(xdc),
               'synth_design -top ' + tcl_word(cfg['top']) +
               ' -part ' + tcl_word(spec['part']) + ' -mode out_of_context -gated_clock_conversion off',
               'report_utilization -file utilization.rpt',
               'report_utilization -hierarchical -file utilization_hierarchical.rpt',
               'report_drc -file drc.rpt', 'write_checkpoint synthesized.dcp',
               'write_verilog -mode funcsim implementation.v',
               'set pqc_path_count ' + str(path_count),
               'source ' + tcl_word(Path(qualification.__file__).with_suffix('.tcl').resolve()),
               '} message]} {puts stderr $message; exit 1}', 'exit 0']
    tcl = run / 'launch.tcl'; tcl.write_text('\n'.join(script) + '\n')
    launch_sha = hashes([tcl])[str(tcl)]
    response.update(status='BLOCKED', scope='full_design', configuration=cfg, source_hashes=req['source_hashes'],
                    source_read_order=cfg['source_read_order'], target_profile_fingerprint=profile['profile_fingerprint'],
                    blockers=['Vivado has not executed', 'Exact-netlist memory semantics are not verified'],
                    structural_checks_verified=False, memory_implementation_verified=False, memory_semantics_verified=False,
                    memory_implementation='fpga_inferred_ram', memory_semantics_scope='unverified',
                    stage='post_synth', metrics=None, power=None, executed=False, reports={},
                    critical_paths=[], source_ownership=[], warnings=[], area_unit='LUTs',
                    qualification=None, measurement_label='PREPARED_NOT_EXECUTED')
    if execute:
        env = os.environ.copy()
        for key in ('PYTHONHOME', 'PYTHONPATH'):
            env.pop(key, None)
        try:
            completed = run_process(['vivado', '-mode', 'batch', '-source', str(tcl), '-log', str(run / 'vivado.log'),
                                     '-journal', str(run / 'vivado.jou')], cwd=run, env=env, timeout=86400,
                                    log_path=run / 'console.log')
            response.update(executed=True, tool_returncode=completed.returncode)
            # Vivado does not provide the redirect command used by other EDA
            # shells. Capture the real process output in Python instead. Keep
            # every byte and every warning, including elaboration/report-stage
            # messages: this is conservatively broader than synthesis alone.
            shutil.copyfile(run / 'console.log', run / 'synthesis.log')
            version_file = run / 'tool-version.txt'
            if version_file.is_file() and not version_file.is_symlink() and version_file.stat().st_size <= 1024:
                response['actual_tool_version'] = version_file.read_text().strip()
            verify_inputs(req)
            require(hashes([tcl])[str(tcl)] == launch_sha, 'Launch script changed during execution')
            if completed.returncode == 0:
                record = qualification.build_qualification(run, req, request_sha)
                observed = record['observations']
                response.update(actual_tool_version=observed['observed_tool']['tool_version'],
                                metrics=observed['metrics'], critical_paths=observed['critical_paths'],
                                source_ownership=observed['source_ownership'], qualification=observed,
                                warnings=observed['structural']['synthesis_warnings'],
                                blockers=observed['blockers'],
                                structural_checks_verified=observed['gates']['structural'] == 'PASS',
                                memory_implementation_verified=observed['gates']['mapped_memory_inventory'] == 'PASS',
                                measurement_label='PRELIMINARY_POST_SYNTH_NOT_ADMITTED')
                # No accepting branch exists without mapped-implementation
                # behavioral evidence. All individual observable gates can pass.
            else:
                response['blockers'] = ['Vivado failed; inspect console.log', 'Exact-netlist memory semantics are not verified']
        except Exception as error:
            # Preserve fresh failure evidence for the controller. Do not convert
            # incomplete/malformed reports into a partially qualified measurement.
            response.update(status='BLOCKED', measurement_label='EVIDENCE_COLLECTION_FAILED',
                            blockers=['Vivado evidence collection or validation failed'],
                            qualification_error_type=type(error).__name__)
            (run / 'qualification-error.txt').write_text(type(error).__name__ + ': ' + str(error)[:4000] + '\n')
        for name in (*qualification.RAW_REPORTS, 'qualification.json', 'qualification-error.txt', 'vivado.log', 'console.log'):
            path = run / name
            if path.is_file() and not path.is_symlink() and path.stat().st_size > 0:
                response['reports'][name] = {'path': str(path.relative_to(out)), 'sha256': hashes([path])[str(path)]}
        if response['qualification'] is not None:
            for name, filename in qualification.REPORT_KEYS.items():
                response['reports'][name] = response['reports'][filename]
    verify_inputs(req)
    save(response_path, response)
    return response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True); parser.add_argument('--response', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    print(json.dumps(collect(args.request, args.response, args.execute), indent=2))


if __name__ == '__main__':
    main()
