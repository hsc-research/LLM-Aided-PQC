#!/usr/bin/env python3
"""Prepare a source-bound FPGA optimization prompt; never call an API or edit RTL.

Imported reports are user-attested preliminary synthesis observations, not a
qualified measurement. This utility cannot admit a candidate to the strict loop.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.export_target_profiles import verify_preparation, verify_profile, sha
from agent import edit_ops
from agent.whole_design_adapters import SYSTEM, TARGET_SYSTEM

REPORTS = ('timing.rpt', 'utilization.rpt', 'check_timing.rpt', 'drc.rpt')
LIMIT = 192 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def read_bounded(path, limit=LIMIT):
    require(path.is_file() and not path.is_symlink(), 'Missing or symlinked file: ' + str(path))
    require(path.stat().st_size <= limit, 'Input too large; select fewer/smaller files: ' + str(path))
    return path.read_text(encoding='utf-8')


def prepare(preparation, selected, out):
    preparation = Path(preparation).resolve()
    record = verify_preparation(preparation)
    profile_path = Path(record['profile']).resolve()
    profile = verify_profile(profile_path)
    require(profile['design'] == 'mldsa' and profile['target']['kind'] == 'fpga',
            'This preliminary route supports only exported ML-DSA FPGA sources')
    launch_path = preparation.parent / 'launch-config.json'
    require(str(launch_path) in record['input_sha256'], 'Launch configuration is not frozen')
    launch = json.loads(read_bounded(launch_path))
    require(launch.get('tool') == 'vivado', 'Expected Vivado preparation')
    report_root = Path(launch['output_root']).resolve()
    all_sources = {str((profile_path.parent / row['path']).resolve()): row['sha256']
                   for row in profile['elaboration']['sources']}
    selected = [str(Path(p).resolve()) for p in selected]
    require(1 <= len(selected) <= 3 and len(set(selected)) == len(selected), 'Select one to three distinct RTL files')
    require(set(selected) <= set(all_sources), 'Selected RTL is outside the exact exported source list')
    reports = {name: read_bounded(report_root / name) for name in REPORTS}
    source_text = {name: read_bounded(Path(name)) for name in selected}
    context = {'purpose': 'one preliminary RTL optimization proposal for human review',
               'status': 'PRELIMINARY_POST_SYNTH_REPORTS_NOT_QUALIFIED',
               'target': 'fpga', 'part': launch['part'], 'tool_version_declared': launch['tool_version'],
               'period_ns': launch['period_ns'], 'top': profile['elaboration']['top'],
               'profile_fingerprint': profile['profile_fingerprint'],
               'source_order': list(all_sources), 'allowed_files': selected,
               'rtl': source_text, 'reports': reports,
               'report_provenance': 'User-supplied files at prepared output path; hashes bind imported bytes only. Actual execution and source association are not independently proven.',
               'limitations': ['No routed timing closure', 'No power result', 'No mapped-memory verification',
                              'No full functional revalidation of a proposed edit', 'No automatic path-to-RTL ownership proof']}
    system = SYSTEM + TARGET_SYSTEM['fpga'] + '\nThis is PROPOSAL ONLY. Reports are preliminary imported observations. Nothing will be applied or accepted. Prefer STOP if the selected files cannot explain the timing path. Do not claim measured improvement.\n'
    require(len((system + json.dumps(context)).encode()) <= LIMIT, 'Combined prompt exceeds 192 KiB; reduce selected sources')
    out = Path(out).resolve()
    require(not out.exists(), 'Use a new output directory')
    # Freeze every source and dependency, not just text selected for the prompt.
    inputs = {str(preparation): sha(preparation), str(profile_path): sha(profile_path),
              **record['input_sha256'], **all_sources}
    inputs.update({str((profile_path.parent / name).resolve()): digest
                   for name, digest in profile['bundle_files_sha256'].items()})
    inputs.update({str(report_root / name): sha(report_root / name) for name in REPORTS})
    require(all(sha(p) == digest for p, digest in inputs.items()), 'Inputs changed during prompt preparation')
    out.mkdir(parents=True)
    save(out / 'prompt.json', {'system': system, 'user': context})
    result = {'schema_version': 1, 'status': 'PROMPT_PREPARED_NO_API_CALL',
              'profile_fingerprint': profile['profile_fingerprint'], 'target': 'fpga', 'tool': 'vivado',
              'part': launch['part'], 'period_ns': launch['period_ns'], 'tool_version_declared': launch['tool_version'],
              'measurement_stage': 'post_synth', 'baseline_metrics': None, 'power': None, 'input_sha256': inputs,
              'prompt_sha256': sha(out / 'prompt.json'), 'allowed_files': selected,
              'api_calls': 0, 'rtl_changed': False, 'target_tool_qualified': False,
              'automatic_acceptance': 'BLOCKED: full-operation and mapped-implementation verification adapters required'}
    save(out / 'proposal-context.json', result)
    return {'status': result['status'], 'out': str(out), 'api_calls': 0}


def review(context_path, response_path, out):
    context_path = Path(context_path).resolve()
    context = json.loads(read_bounded(context_path, 4 * 1024 * 1024))
    require(context.get('schema_version') == 1 and context.get('status') == 'PROMPT_PREPARED_NO_API_CALL', 'Wrong context record')
    require(sha(context_path.parent / 'prompt.json') == context['prompt_sha256'], 'Prompt changed')
    require(all(sha(p) == digest for p, digest in context['input_sha256'].items()), 'Source/configuration/report bytes changed; prepare again')
    proposal = json.loads(read_bounded(Path(response_path)))
    require(proposal.get('status') in ('STOP', 'PROPOSED'), 'Expected a JSON STOP or PROPOSED response')
    changed = 0
    if proposal['status'] == 'PROPOSED':
        experiment = proposal.get('experiment', {})
        require(1 <= len(experiment.get('files', [])) <= 3, 'One proposal may touch at most three selected files')
        for row in experiment['files']:
            require(1 <= len(row.get('ops', [])) <= 4, 'At most four edits per file')
            for op in row['ops']:
                require(op.get('op') == 'replace_exact', 'Only replace_exact is supported')
                require(type(op.get('expect')) is int and op['expect'] == 1, 'Each anchor must occur exactly once')
                require(isinstance(op.get('old'), str) and isinstance(op.get('new'), str), 'Text anchors required')
                changed += len(op['old'].encode()) + len(op['new'].encode())
        require(changed <= 8192, 'Proposal edit text exceeds 8192 bytes')
        edit_ops.preview_experiment(experiment, allowed_paths=context['allowed_files'])
    out = Path(out).resolve()
    require(not out.exists(), 'Do not overwrite a review result')
    result = {'schema_version': 1, 'status': 'STOP' if proposal['status'] == 'STOP' else 'EDIT_PREVIEW_VALID_NOT_APPLIED',
              'response_sha256': sha(response_path), 'context_sha256': sha(context_path),
              'profile_fingerprint': context['profile_fingerprint'], 'rtl_changed': False,
              'functional_verified': False, 'ppa_gain_verified': False,
              'automatic_acceptance': 'BLOCKED', 'edit_text_bytes': changed}
    save(out, result)
    return result


def recover_preflight(context_path, out):
    """Explicit offline re-preparation after a recorded zero-generation failure.

    Preserve the original record and claim. Never recover an uncertain generation.
    """
    context_path = Path(context_path).resolve()
    old = context_path.parent
    context = json.loads(read_bounded(context_path, 4 * 1024 * 1024))
    run = json.loads(read_bounded(old / 'proposal-run.json'))
    require(context.get('schema_version') == 1 and context.get('status') == 'PROMPT_PREPARED_NO_API_CALL', 'Wrong context')
    require(run.get('context_sha256') == sha(context_path), 'Run is not bound to this context')
    require(run.get('status') in ('FAILED', 'BLOCKED_BUDGET') and type(run.get('api_calls_attempted')) is int and run['api_calls_attempted'] == 0,
            'Recovery requires a completed, recorded failure with zero generation attempts; inspect provider usage for every uncertain outcome')
    require(run.get('input_tokens') is None and run.get('output_tokens') is None and run.get('reported_cost_usd') is None, 'Contradictory generation usage; inspect provider usage before any new request')
    require(not (old / 'proposal-response.json').exists() and not (old / 'review.json').exists(), 'Response/review exists; do not recover automatically')
    require((old / '.proposal-request.lock').is_file() and not (old / '.proposal-request.lock').is_symlink(), 'Missing or unsafe original request claim')
    prompt = read_bounded(old / 'prompt.json', 512 * 1024)
    require(sha(old / 'prompt.json') == context['prompt_sha256'], 'Prompt changed')
    require(run.get('prompt_sha256') == context['prompt_sha256'], 'Run prompt changed')
    require(all(sha(p) == digest for p, digest in context['input_sha256'].items()), 'Inputs changed; prepare a fresh prompt from the source inputs')
    out = Path(out).resolve()
    require(not out.exists(), 'Use a new output directory; historical records are never overwritten')
    context['recovery'] = {'source_context_sha256': sha(context_path), 'source_run_sha256': sha(old / 'proposal-run.json'),
                           'source_status': run['status'], 'generation_attempts': 0, 'api_calls_made_by_recovery': 0}
    out.mkdir(parents=True)
    (out / 'prompt.json').write_text(prompt, encoding='utf-8')
    save(out / 'proposal-context.json', context)
    return {'status': context['status'], 'out': str(out), 'api_calls': 0,
            'note': 'Previous record and claim preserved. Review the new context and explicitly approve any new paid request.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('prepare'); a.add_argument('--preparation', required=True); a.add_argument('--rtl', action='append', required=True); a.add_argument('--out', required=True)
    a = sub.add_parser('review'); a.add_argument('--context', required=True); a.add_argument('--response', required=True); a.add_argument('--out', required=True)
    a = sub.add_parser('recover-preflight'); a.add_argument('--context', required=True); a.add_argument('--out', required=True)
    args = p.parse_args()
    try:
        if args.command == 'prepare': result = prepare(args.preparation, args.rtl, args.out)
        elif args.command == 'recover-preflight': result = recover_preflight(args.context, args.out)
        else: result = review(args.context, args.response, args.out)
        print(json.dumps(result, indent=2)); return 0
    except (ValueError, OSError, KeyError, TypeError, AssertionError) as e:
        print('BLOCKED: ' + str(e), file=sys.stderr); return 2

if __name__ == '__main__':
    raise SystemExit(main())
