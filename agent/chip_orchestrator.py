#!/usr/bin/env python3
"""Top-down FPGA optimization with transactional candidate acceptance.

Default: measure and recommend. --dispatch runs ONE supported proposal round.
ASIC fixed-period measurement uses asic_synthesis.py. KATs are not formal proofs.
"""
import argparse
import importlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import uuid

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from run_safety import RunLock, SourceTransaction, hashes, run_process, gate_passed, proposal_accepted
from experiment_history import PARENT_ID_ENV, parse_preliminary, is_final_acceptance

DESIGNS = {
    'mldsa_baseline': {
        'key': 'combined_top_pristine',
        'ckpt': './synth_out/sweep_combined_top_pristine/post_synth_grade1.dcp',
        'bracket': (12.0, 16.0), 'hier2file': {}, 'orchestrator': None,
        'kat_gate': ['python3', 'agent/mldsa/full_kat_gate.py'],
        'scopes': ['agent/mldsa/mldsa_src'],
    },
    'mldsa': {
        'key': 'combined_top', 'ckpt': './synth_out/sweep_combined_top/post_synth_grade1.dcp',
        'bracket': (12.0, 13.5),
        'hier2file': {
            'ENCODER': 'agent/mldsa/mldsa_src/encoder.v',
            'DECODER': 'agent/mldsa/mldsa_src/decoder.v',
            'GEN_C': 'agent/mldsa/mldsa_src/gen_c.v',
            'CHALLENGE_SAMPLER': 'agent/mldsa/mldsa_src/gen_c.v',
            'MAKEHINT': 'agent/mldsa/mldsa_src/makehint.v',
            'USEHINT': 'agent/mldsa/mldsa_src/usehint.v',
            'DECOMPOSER': 'agent/mldsa/mldsa_src/coeff_decomposer.v',
            'BUTTERFLY': 'agent/mldsa/mldsa_src/butterfly.v',
            'REJ': 'agent/mldsa/mldsa_src/rejection_s.v',
        },
        'orchestrator': 'agent/mldsa/orchestrator.py',
        'orchestrator_blocks': ('rejection_a', 'rejection_s', 'rejection_y',
                                'makehint', 'gen_c', 'decoder', 'usehint'),
        'kat_gate': ['python3', 'agent/mldsa/full_kat_gate.py', 'agent/mldsa/mldsa_src'],
        'scopes': ['agent/mldsa/mldsa_src'],
    },
    'hqc_baseline': {
        'key': 'hqc_joint_pristine', 'ckpt': './synth_out/sweep_hqc_joint_pristine/post_synth_grade1.dcp',
        'bracket': (6.0, 10.0), 'hier2file': {}, 'orchestrator': None,
        'kat_gate': ['python3', 'agent/hqc/joint_kat_gate.py', '--all',
                     '--source-key', 'hqc_joint_pristine'],
        'scopes': ['build/keygen', 'build/encap', 'build/decap', 'build/joint_design'],
    },
    'hqc': {
        'key': 'hqc_joint_opt', 'ckpt': './synth_out/sweep_hqc_joint_opt/post_synth_grade1.dcp',
        'bracket': (6.0, 10.0),
        'hier2file': {
            'FIXEDWEIGHT': 'build/keygen/fixed_weight_ct.v',
            'ENCAP': 'build/encap/encap.v', 'DECAP': 'build/decap/decap.v',
            'POLY_MULT': 'build/joint_design/hqc_kem_joint_design.v',
            'V_MINUS_UY': 'build/decap/v_minus_uy.v',
            'VECTSETRAND': 'build/keygen/vect_set_random.v',
            'KECCAK': 'build/keygen/keccak_top.v', 'ENCRYPT': 'build/encap/encrypt.v',
        },
        'orchestrator': 'agent/hqc/transfer_orchestrator.py',
        # The transfer runner requires a module and an explicit parameter set.
        # Full-design admission still checks every HQC level via --all below.
        'orchestrator_args': ['hqc128'],
        # Other mapped file stems are not supported module keys for this runner.
        'orchestrator_blocks': ('encap', 'decap'),
        'joint_orchestrator': 'agent/hqc/joint_top_orchestrator.py',
        'kat_gate': ['python3', 'agent/hqc/joint_kat_gate.py', '--all'],
        'scopes': ['build/keygen', 'build/encap', 'build/decap', 'build/joint_design'],
    },
    'slh_dsa': {
        'key': 'top', 'ckpt': './synth_out/slh_dsa/post_synth.dcp',
        'bracket': (10.0, 13.0), 'regen': ['python3', 'agent/slh_dsa/regen_slh_ckpt.py'],
        'hier2file': {
            'W_MEM_INST': 'agent/slh_dsa/slh_src/sphincslet/sha/sha256_w_mem.v',
            'SHA256': 'agent/slh_dsa/slh_src/sphincslet/sha/sha256_core.v',
        },
        'orchestrator': None, 'kat_gate': ['python3', 'agent/slh_dsa/slh_kat_gate.py'],
        'scopes': ['agent/slh_dsa/slh_src'],
    },
}


def log_record(record):
    with (HERE / 'chip_orchestrator_log.jsonl').open('a') as stream:
        stream.write(json.dumps(record) + '\n')


def learn_final_candidate(record):
    """Optional learning only after durable whole-design acceptance."""
    if not is_final_acceptance(record):
        raise ValueError('Cannot learn an optimization rule from preliminary evidence')
    proposal = record['proposal']
    try:
        from learned_rules import distill_rule
        from llm_client import create_client
        distill_rule(create_client(), proposal['source_model'], record, proposal['design'])
    except Exception as error:
        print(f'Final-outcome rule distillation skipped: {error}')


def validate_closure(value):
    if isinstance(value, dict) and (value.get("measurement_valid") is False or value.get("search_complete") is False):
        raise RuntimeError("Incomplete or invalid closure measurement")
    for key in ('closing_fmax_mhz', 'closing_period_ns'):
        number = value.get(key) if isinstance(value, dict) else None
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number) or number <= 0:
            raise RuntimeError(f'Invalid closure field: {key}')
    slack = value.get('wns_at_close')
    if isinstance(slack, bool) or not isinstance(slack, (int, float)) or not math.isfinite(slack) or slack < 0:
        raise RuntimeError('Missing finite nonnegative setup slack at the reported closing point')


def closure_search(ckpt, tag, lo, hi):
    result = run_process([sys.executable, str(HERE / 'fmax_search.py'), ckpt,
                          tag, str(lo), str(hi)], cwd=REPO)
    if result.returncode or 'NO RESULT after retry' in result.stdout:
        raise RuntimeError('Closure runner failed: ' + result.stdout[-1000:])
    for line in reversed(result.stdout.splitlines()):
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict) and 'closing_period_ns' in value:
            validate_closure(value)
            return value
    raise RuntimeError('Closure runner produced no valid result')


def worst_path_at_close(tag, period, report_path=None):
    path = Path(report_path) if report_path else Path(f'/tmp/fsrch_{tag}_{period}.rpt')
    if not path.is_file():
        return None
    match = re.search(r'Slack \((?:MET|VIOLATED)\)\s*:.*?Source:\s*(\S+).*?Destination:\s*(\S+)',
                      path.read_text(), re.S)
    return {'source': match[1], 'dest': match[2]} if match else None


def map_to_file(path_rec, hier2file):
    # Preserve the established mapping precedence before inspecting deeper hierarchy.
    for endpoint in (path_rec['dest'], path_rec['source']):
        top = endpoint.split('/')[0].upper()
        for key, path in hier2file.items():
            if key in top:
                return top, path
    for endpoint in (path_rec['dest'], path_rec['source']):
        comps = [c.split('[')[0].upper() for c in endpoint.split('/')[:-1]]
        for key in sorted(hier2file, key=len, reverse=True):
            for component in reversed(comps):
                if key in component:
                    return component, hier2file[key]
    return None, None


def source_state(cfg):
    import synthesizer
    module = importlib.reload(synthesizer)
    sources = module.ordered_sources(cfg['key']) + module.VHDL_SOURCES.get(cfg['key'], [])
    include_files = []
    for directory in module.INCLUDE_DIRS.split():
        for ext in ('*.v', '*.vh', '*.svh'):
            include_files.extend(str(p) for p in Path(directory).glob(ext))
    return {'sources': hashes(sources), 'includes': hashes(include_files),
            'read_order': [str(Path(p).resolve()) for p in sources]}


def verify_baseline(cfg, record, timeout):
    """Check the exact current source state before spending on measurement."""
    if not cfg.get('kat_gate'):
        raise RuntimeError('No correctness gate configured for the baseline')
    before = source_state(cfg)
    record['baseline_sources'] = before
    checked = run_process(cfg['kat_gate'], cwd=REPO, timeout=timeout)
    if not gate_passed(checked):
        record['baseline_correctness_status'] = 'FAIL'
        raise RuntimeError('Baseline correctness gate failed; measurement and dispatch not started')
    if source_state(cfg) != before:
        record['baseline_correctness_status'] = 'SOURCE_CHANGED'
        raise RuntimeError('Baseline sources changed during verification')
    record['baseline_correctness_status'] = 'PASS'
    return before


def regen_ckpt(cfg):
    if cfg.get('regen'):
        result = run_process(cfg['regen'], cwd=REPO)
        if result.returncode:
            raise RuntimeError('Design-specific checkpoint generation failed')
        return
    import synthesizer
    module = importlib.reload(synthesizer)
    key = cfg['key']
    sources = module.ordered_sources(key)
    vhdl = module.VHDL_SOURCES.get(key, [])
    top = module.TOP_OVERRIDE.get(key, key)
    period = cfg.get('regen_period_ns', 8.600)
    checkpoint = Path(cfg['ckpt'])
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    vb = 'read_vhdl {\n' + '\n'.join(vhdl) + '\n}\n' if vhdl else ''
    tcl = (vb + 'read_verilog {\n' + '\n'.join(sources) + '\n}\n'
           + f'synth_design -top {top} -part {module.PART} -mode out_of_context{module.synth_flags(key)}\n'
           + 'set clk_port [lindex [get_ports -quiet {clk clk_i}] 0]\n'
           + 'if {$clk_port eq ""} { set clk_port [lindex [get_ports -quiet *clk*] 0] }\n'
           + 'if {$clk_port eq ""} { error "No clock port found" }\n'
           + f'create_clock -period {period:.3f} -name clk [get_ports $clk_port]\n'
           + f'write_checkpoint -force {{{checkpoint}}}\nputs {{REGEN DONE}}\n')
    with tempfile.TemporaryDirectory(prefix='pqc-regen-') as work:
        script = Path(work) / 'regen.tcl'
        script.write_text(tcl)
        result = run_process(['vivado', '-mode', 'batch', '-source', str(script),
                              '-nojournal', '-nolog'], cwd=REPO)
    if result.returncode or 'REGEN DONE' not in result.stdout or not checkpoint.is_file():
        raise RuntimeError('Checkpoint generation failed: ' + result.stdout[-1000:])


def evaluate_candidate(cfg, source_file, base, tag, record, timeout=86400):
    block = Path(source_file).stem
    command = cfg.get('orchestrator')
    arguments = [block, *cfg.get('orchestrator_args', [])]
    if block == 'hqc_kem_joint_design' and cfg.get('joint_orchestrator'):
        command, arguments = cfg['joint_orchestrator'], []
    elif cfg.get('orchestrator_blocks') is not None and block not in cfg['orchestrator_blocks']:
        record['verdict'] = f'NO_TARGET (unsupported optimizer block: {block})'
        return False
    if not command or not cfg.get('kat_gate'):
        record['verdict'] = 'NO_TARGET (no supported optimizer and checker pair)'
        return False
    scopes = [*cfg['scopes'], cfg['ckpt']]
    record.update(history_schema=1, candidate_id=tag, evidence_stage='full_design',
                  history_state='chip_rejected', baseline=base)
    with SourceTransaction(REPO, scopes) as transaction:
        original = source_state(cfg)
        record['baseline_sources'] = original
        env = dict(os.environ, **{PARENT_ID_ENV: tag})
        result = run_process([sys.executable, command, *arguments], cwd=REPO,
                             timeout=timeout, env=env)
        print(result.stdout[-2000:])
        if not proposal_accepted(result):
            record['verdict'] = 'NO_ACCEPTED_CANDIDATE (restored)'
            return False
        record['proposal'] = parse_preliminary(result.stdout, tag)
        candidate = source_state(cfg)
        if candidate == original:
            record['verdict'] = 'NO_EFFECTIVE_SOURCE_CHANGE (restored)'
            return False
        record['candidate_sources'] = candidate
        checked = run_process(cfg['kat_gate'], cwd=REPO, timeout=timeout)
        print(checked.stdout[-1000:])
        if not gate_passed(checked):
            record['correctness_status'] = 'FAIL'
            record['verdict'] = 'KAT_FAIL (restored)'
            return False
        record['correctness_status'] = 'PASS'
        if source_state(cfg) != candidate:
            raise RuntimeError('RTL changed during verification; refusing PPA comparison')
        regen_ckpt(cfg)
        post = closure_search(cfg['ckpt'], tag + '_candidate', *cfg['bracket'])
        validate_closure(post)
        if source_state(cfg) != candidate:
            raise RuntimeError('RTL changed during implementation; candidate not retained')
        record['post'] = post
        if post['closing_fmax_mhz'] <= base['closing_fmax_mhz']:
            record['verdict'] = 'REJECT_PPA (all scoped files restored)'
            return False
        record['verdict'] = 'ACCEPT'
        record['history_state'] = 'accept_pending'
        log_record(record)  # Logging failure must not retain the candidate.
        transaction.accept()
        record['history_state'] = 'finally_accepted'
        try:
            log_record(record)
        except OSError:
            # Keep the snapshot available until all required history writes
            # succeed. SourceTransaction rolls back even after accept() when
            # its body exits with an exception.
            record.update(history_state='chip_rejected', verdict='HISTORY_WRITE_FAILED (restored)')
            raise
    # No rule can be learned until the source transaction has exited cleanly.
    learn_final_candidate(record)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('design', choices=DESIGNS)
    parser.add_argument('--dispatch', action='store_true')
    parser.add_argument('--timeout', type=float, default=86400)
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('--timeout must be finite and positive')
    os.chdir(REPO)
    cfg = DESIGNS[args.design]
    tag = 'chip_' + args.design + '_' + uuid.uuid4().hex[:12]
    record = {'design': args.design, 'ts': time.strftime('%F %T'), 'tag': tag}
    try:
        with RunLock(REPO):
            with SourceTransaction(REPO, [*cfg['scopes'], cfg['ckpt']]) as baseline_transaction:
                baseline_sources = verify_baseline(cfg, record, args.timeout)
                regen_ckpt(cfg)
                if source_state(cfg) != baseline_sources:
                    raise RuntimeError('Baseline sources changed during synthesis')
                base = closure_search(cfg['ckpt'], tag, *cfg['bracket'])
                if source_state(cfg) != baseline_sources:
                    raise RuntimeError('Baseline sources changed during implementation')
                baseline_transaction.accept()
            path = worst_path_at_close(tag, base['closing_period_ns'], base.get('report_path'))
            if path is None:
                raise RuntimeError('No worst path in the closing report')
            inst, source = map_to_file(path, cfg['hier2file'])
            record.update(closure=base, worst_path=path, dispatch_instance=inst, dispatch_file=source)
            print(json.dumps(record, indent=2))
            if not args.dispatch or source is None:
                record['verdict'] = 'RECOMMENDATION' if source else 'NO_TARGET'
                log_record(record)
                return 0
            accepted = evaluate_candidate(cfg, source, base, tag, record, args.timeout)
            if not accepted:
                log_record(record)
            print('CHIP VERDICT:', record['verdict'])
            return 0
    except (Exception, KeyboardInterrupt) as error:
        record.update(verdict='ERROR (see transaction journal if recovery failed)', reason=str(error))
        log_record(record)
        print('ERROR:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
