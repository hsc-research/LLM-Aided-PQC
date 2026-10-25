"""Foreground, bounded ML-DSA FPGA experimentation with exact-source feedback.

Never launches model commands. Baseline RTL is copied, never edited. Explicit
exploration can collect provisional candidates; strict admission remains separate.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import copy
from decimal import Decimal, InvalidOperation
import hashlib
import fcntl
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

from . import autonomous_design, edit_ops, llm_client, target_profiles
from .proposal_response import decode_response
from .run_safety import RunLock, SourceTransaction, hashes, _kill_tree
from .whole_design import (ContractError, acceptance, configuration, digest, finite,
                           integer, require, validate_gate, validate_measurement,
                           validate_reports, validate_target_evidence)
from .whole_design_adapters import SYSTEM, TARGET_SYSTEM
from .mldsa.exported_kat_adapter import coverage_contract, dependencies

ROOT = Path(__file__).resolve().parents[1]
LIMITS = {'iterations': (1, 100), 'generation_attempts': (1, 100),
          'context_requests': (0, 16), 'max_output_tokens': (1, 8192),
          'max_prompt_bytes': (4096, 196608), 'max_changed_bytes': (1, 16384),
          'max_edit_files': (1, 3), 'jobs': (1, 32),
          'runtime_seconds': (1, 604800), 'stage_timeout_seconds': (1, 86400),
          'api_timeout_seconds': (1, 120), 'max_log_bytes': (1024, 16777216),
          'max_artifact_bytes': (1048576, 17179869184)}
DEFAULTS = dict(iterations=5, generation_attempts=5, context_requests=2,
                max_output_tokens=4096, max_prompt_bytes=196608, max_changed_bytes=8192,
                max_edit_files=2, jobs=2, runtime_seconds=21600, stage_timeout_seconds=7200,
                api_timeout_seconds=120, max_log_bytes=8388608, max_artifact_bytes=4294967296)


def durable(path, value):
    """Atomic replacement, fsync bytes and directory before an external action."""
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    require(not path.is_symlink() and not temporary.is_symlink(), 'Symlinked state path')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def positive(value):
    try: result = Decimal(str(value))
    except InvalidOperation: raise ContractError('Explicit positive finite USD pricing and budget required') from None
    require(result.is_finite() and result > 0, 'Explicit positive finite USD pricing and budget required')
    return result


def load_settings(path):
    path = Path(path).resolve()
    value = json.loads(path.read_text())
    require(value.get('schema_version') == 1, 'Expected autonomous schema_version 1')
    require(value.get('mode', 'strict') in ('strict', 'exploratory'), 'Mode must be strict or exploratory')
    limits = {**DEFAULTS, **value.get('limits', {})}
    require(set(limits) == set(LIMITS), 'Unknown run limit')
    for key, (low, high) in LIMITS.items(): integer(limits[key], key, low, high)
    require(limits['context_requests'] < limits['generation_attempts'], 'Context requests must leave a bounded proposal attempt')
    provider = value.get('provider', {})
    require(isinstance(provider, dict) and set(provider) == {'model', 'input_usd_per_million', 'output_usd_per_million', 'budget_usd'}, 'Provider configuration contains unknown fields; never place credentials here')
    require(isinstance(provider.get('model'), str) and re.fullmatch(r'[A-Za-z0-9_.:-]{1,160}', provider['model']), 'Explicit approved model required')
    for name in ('input_usd_per_million', 'output_usd_per_million', 'budget_usd'): positive(provider.get(name))
    prep = (path.parent / value['preparation']).resolve()
    from tools.export_target_profiles import verify_preparation, verify_profile
    prepared = verify_preparation(prep)
    profile_path = Path(prepared['profile']).resolve()
    profile = verify_profile(profile_path)
    require(profile['design'] == 'mldsa' and profile['target']['kind'] == 'fpga', 'Only exported ML-DSA FPGA is implemented; HQC is disabled')
    launch_path = prep.parent / 'launch-config.json'
    require(str(launch_path) in prepared['input_sha256'], 'Unbound launch configuration')
    launch = json.loads(launch_path.read_text())
    require(launch['tool'] == 'vivado', 'Only Vivado is supported')
    sources = [str((profile_path.parent / row['path']).resolve()) for row in profile['elaboration']['sources']]
    chosen = value.get('editable_files', [])
    require(isinstance(chosen, list) and 1 <= len(chosen) <= 32, 'Explicit editable file allowlist required')
    chosen = [str((profile_path.parent / p).resolve()) for p in chosen]
    require(len(set(chosen)) == len(chosen) and set(chosen) <= set(sources), 'Editable source outside exact profile')
    require(all(not Path(p).is_symlink() for p in sources), 'Symlinked source')
    objective = value.get('objective', {'metric': 'worst_setup_slack_ns', 'min_improvement': 0.05})
    require(objective.get('metric') in ('worst_setup_slack_ns', 'lut'), 'Supported objectives are setup slack or LUT count')
    finite(objective.get('min_improvement'), 'minimum improvement', True)
    minimum_slack = finite(value.get('minimum_slack_ns', 0), 'minimum slack')
    return {**value, 'path': str(path), 'mode': value.get('mode', 'strict'), 'limits': limits,
            'profile': profile, 'profile_path': str(profile_path), 'prepared': prepared,
            'preparation': str(prep), 'launch': launch, 'sources': sources,
            'editable_files': chosen, 'objective': objective, 'minimum_slack_ns': minimum_slack}


def child_environment():
    # An allowlist prevents API keys, vault passphrases, provider IDs and ambient
    # auth/proxy variables from reaching compiler/EDA descendants.
    allowed = ('PATH', 'HOME', 'USER', 'LANG', 'LC_ALL', 'TMPDIR', 'XILINX_VIVADO',
               'XILINXD_LICENSE_FILE', 'LM_LICENSE_FILE', 'LD_LIBRARY_PATH')
    return {name: os.environ[name] for name in allowed if name in os.environ}


@contextmanager
def deadline(seconds):
    require(seconds > 0, 'Runtime budget exhausted')
    def expired(*unused): raise TimeoutError('Run deadline exceeded')
    previous = signal.signal(signal.SIGALRM, expired)
    old = signal.setitimer(signal.ITIMER_REAL, seconds)
    try: yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, *old)
        signal.signal(signal.SIGALRM, previous)


def unsafe_candidate(before, after):
    """Conservative full resulting-file gate before any HDL compiler sees it.

    No DPI, foreign-language hooks, simulator commands, new attributes/directives
    or changes to comment delimiters. False rejects are preferable to execution.
    Trusted preexisting ROM read tasks cannot be introduced or activated by edits.
    """
    require(target_profiles.unchanged_directives(before, after), 'Frozen compilation directives changed')
    forbidden = r'(?i)(\bDPI\b|DPI-C|\b(?:verilator|verilator_config|cver|vpi|pli)\b|\$system\b|\$fopen\b|\$fwrite\b|\$fdisplay\b|\$swrite\b|\$sformat\b|\$readmem[bh]\b|\$writemem[bh]\b|\$value\$plusargs\b|\$test\$plusargs\b)'
    # Existing ROM initialization is valid baseline code. Any change in a file
    # containing such hooks is refused, avoiding comment-context activation.
    require(not re.search(forbidden, before) and not re.search(forbidden, after),
            'Candidate touches foreign-code, file-I/O, simulator or tool hooks')
    pure_tasks = {'clog2', 'signed', 'unsigned', 'bits', 'size', 'high', 'low', 'left', 'right', 'rtoi', 'itor', 'bitstoreal', 'realtobits', 'countones', 'onehot', 'onehot0', 'isunknown'}
    require(set(re.findall(r'\$([A-Za-z_]\w*)', after)) <= pure_tasks, 'Candidate contains unsupported simulator/system tasks')
    require(re.findall(r'/\*|\*/|//', before) == re.findall(r'/\*|\*/|//', after), 'Candidate changes comment boundaries')
    comments = lambda text: re.findall(r'/\*.*?\*/|//[^\n]*', text, re.S)
    require(comments(before) == comments(after), 'Candidate changes frozen comments or foreign-code metacomments')
    require(re.findall(r'\(\*.*?\*\)', before, re.S) == re.findall(r'\(\*.*?\*\)', after, re.S), 'Candidate changes tool attributes')
    require(re.findall(r'`[^\n]*', before) == re.findall(r'`[^\n]*', after), 'Candidate changes preprocessor context')
    # Keep literal module headers plus all input/output declarations byte-stable.
    interface = lambda s: re.findall(r'\bmodule\b.*?;|\b(?:input|output|inout)\b[^;]*;', s, re.S)
    require(interface(before) == interface(after), 'Candidate changes a module interface')


@contextmanager
def profile_lock(path):
    # Cooperating runs sharing an export cannot charge concurrently, even with
    # different output directories. The immutable profile is opened read-only.
    with Path(path).open('r') as stream:
        try: fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise ContractError('Another autonomous run holds this source-profile lock') from None
        yield


class Controller:
    def __init__(self, settings, out, client_factory=None):
        self.settings = settings
        self.limits = settings['limits']
        self.out = Path(out).resolve()
        require(not self.out.exists(), 'Fresh run directory required; existing runs are never dispatched again')
        self.client_factory = client_factory or llm_client.create_client
        self.client = None
        self.started = time.monotonic()
        self.state = {'schema_version': 1, 'status': 'INITIALIZING', 'mode': settings['mode'],
                      'generation_attempts': 0, 'context_requests': 0, 'iterations': 0,
                      'accepted': 0, 'spent_usd': '0', 'reserved_usd': '0', 'pending_request': None,
                      'journal_head': None, 'best_snapshot': None, 'provisional_candidates': [],
                      'timing_signoff': False, 'hardware_learning_claim': False,
                      'power_validated': False, 'baseline_unchanged': True}
        self.history = []
        self.seen = set()
        self.serial = 0
        self.cfg = None

    def remaining(self):
        value = self.limits['runtime_seconds'] - (time.monotonic() - self.started)
        require(value > 0, 'Runtime budget exhausted')
        return value

    def persist(self):
        self.state['elapsed_seconds'] = round(time.monotonic() - self.started, 3)
        durable(self.out / 'state.json', self.state)

    def record(self, event):
        row = {**event, 'sequence': len(self.history), 'previous': self.state['journal_head']}
        row['sha256'] = digest(row)
        # One atomic file per event; state points to the committed journal head.
        durable(self.out / 'journal' / f'{len(self.history):04d}.json', row)
        self.history.append(row); self.state['journal_head'] = row['sha256']; self.persist()

    def setup(self):
        self.out.mkdir(parents=True); (self.out / 'journal').mkdir(); (self.out / 'working').mkdir()
        s = self.settings; profile = s['profile']; base = Path(s['profile_path']).parent
        originals = {str(Path(s['path'])): hashes([s['path']])[str(Path(s['path']))],
                     str(Path(s['preparation'])): hashes([s['preparation']])[str(Path(s['preparation']))],
                     s['profile_path']: hashes([s['profile_path']])[s['profile_path']],
                     **s['prepared']['input_sha256'], **hashes(s['sources'])}
        originals.update({str((base / name).resolve()): value for name, value in profile['bundle_files_sha256'].items()})
        # All imported Python modules and the exact fixture closure are frozen.
        code = [str(p) for p in (ROOT / 'agent').rglob('*.py') if '__pycache__' not in p.parts]
        code += [str(p) for p in (ROOT / 'agent').glob('*.tcl')]
        code.append(str(ROOT / 'tools' / 'export_target_profiles.py'))  # trusted Tcl quoting imported by Vivado child
        originals.update(hashes([*dependencies(), *code]))
        normalized_originals = {}
        for name, expected in originals.items():
            canonical = str(Path(name).resolve())
            require(canonical not in normalized_originals or normalized_originals[canonical] == expected, 'Conflicting immutable aliases')
            normalized_originals[canonical] = expected
        originals = normalized_originals
        self.originals = originals
        require(hashes(originals) == originals, 'Original input binding changed')
        mapping = {}
        for name in s['sources'] + [str((base / r['path']).resolve()) for kind in ('include_files', 'data_files') for r in profile['elaboration'][kind]]:
            source = Path(name); target = self.out / 'working' / source.relative_to(base)
            require(not source.is_symlink(), 'Symlinked profile input')
            target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
            mapping[name] = str(target)
        elab = copy.deepcopy(profile['elaboration'])
        elab['sources'] = [{'path': mapping[str((base / r['path']).resolve())], 'language': r['language']} for r in elab['sources']]
        for kind in ('include_files', 'data_files'):
            elab[kind] = [mapping[str((base / r['path']).resolve())] for r in elab[kind]]
        for kind in ('include_dirs', 'global_include_files'):
            elab[kind] = [str(self.out / 'working' / Path(p)) for p in elab[kind]]
        elab['working_directory'] = str(self.out / 'working' / elab['working_directory'])
        Path(elab['working_directory']).mkdir(parents=True, exist_ok=True)
        self.sources = [mapping[p] for p in s['sources']]
        self.editable = [mapping[p] for p in s['editable_files']]
        self.source_origins = {mapping[p]: p for p in s['sources']}
        self.baseline = hashes(self.sources)
        self.immutable = {**originals, **hashes([p for p in mapping.values() if p not in self.sources])}
        normalized = {'profile_path': s['profile_path'], 'profile_fingerprint': profile['profile_fingerprint'],
                      'design': 'mldsa', 'variant': profile.get('variant'), 'target': profile['target'],
                      'elaboration': elab, 'baseline_source_hashes': self.baseline,
                      'required_operations': ['keygen', 'sign', 'verify'], 'boundary': profile.get('boundary')}
        coverage = coverage_contract(); launch = s['launch']
        self.cfg = {'root': str(self.out), 'target': 'fpga', 'backend': 'vivado', 'top': elab['top'],
                    'scope': 'full_design', 'sources': self.sources, 'immutable_inputs': list(self.immutable),
                    '_target_profile': normalized, 'verification_scope': 'full_selected_design',
                    'required_checks': coverage['required_checks'], 'operations': coverage['operations'],
                    'required_negative_controls': coverage['required_negative_controls'],
                    'editable_files': self.editable, 'instance_to_file': {},
                    'area_metric': 'lut', 'objective': s['objective'], 'minimum_slack_ns': s['minimum_slack_ns'],
                    'max_area_regression_fraction': 0, 'max_edit_files': self.limits['max_edit_files'],
                    'max_changed_bytes': self.limits['max_changed_bytes'], 'critical_path_count': 5,
                    'commands': {'verify': [sys.executable, '-m', 'agent.mldsa.exported_kat_adapter'],
                                 'measure': [sys.executable, '-m', 'agent.fpga_feedback']},
                    'measurement': {'stage': 'post_synth', 'period_ns': launch['period_ns'],
                                    'tool_version': launch['tool_version'], 'part': launch['part'],
                                    'technology': launch['part'], 'corner': 'vivado_default',
                                    'effort': 'default', 'seed': 'not_applicable',
                                    'memory_model': 'fpga_inferred_ram', 'constraints': [launch['xdc']],
                                    'qualification': {'io_exceptions': s.get('io_exceptions', [])}}}
        self.contract = configuration(self.cfg)
        self.contract['autonomous_policy'] = {'mode': s['mode'], 'latency': 'exactly_unchanged',
                                             'limits': self.limits, 'source_origins': self.source_origins}
        self.state.update(configuration_sha256=digest(self.contract), model=s['provider']['model'], original_hashes=self.originals,
                          baseline_sources=self.baseline, current_sources=self.baseline,
                          profile_fingerprint=profile['profile_fingerprint'], source_origins=self.source_origins)
        durable(self.out / 'configuration.json', self.contract)
        self.snapshot('baseline', self.baseline)
        durable(self.out / 'design-model.json', autonomous_design.model(self.baseline, self.cfg['top'], self.state['profile_fingerprint']))
        self.persist()

    def unchanged(self, expected):
        require(hashes(self.sources) == expected, 'Candidate source manifest changed unexpectedly')
        require(hashes(self.immutable) == self.immutable, 'Frozen baseline/configuration/fixture input changed')
        require(target_profiles.include_inventory(self.cfg['_target_profile']) == self.contract['target_include_inventory'], 'Include inventory changed')

    def snapshot(self, name, expected):
        folder = self.out / name; require(not folder.exists(), 'Snapshot already exists'); folder.mkdir()
        content = {}
        for source in self.sources:
            relative = Path(source).relative_to(self.out / 'working')
            target = folder / relative; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
            content[str(relative)] = expected[source]
        durable(folder / 'manifest.json', {'source_hashes': content, 'original_source_hashes': expected,
                                          'configuration_sha256': digest(self.contract),
                                          'qualification': 'PROVISIONAL_NOT_ACCEPTED' if name.startswith('provisional') else 'SEE_BOUND_JOURNAL'})
        return name

    def execute(self, argv, directory, timeout):
        log = directory / 'command.log'
        allotted = min(timeout, self.remaining())
        with log.open('w') as stream:
            process = subprocess.Popen(argv, cwd=ROOT, env=child_environment(), stdout=stream,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                end = time.monotonic() + min(allotted, self.remaining())
                while process.poll() is None:
                    if time.monotonic() >= end: raise TimeoutError('Tool stage timed out')
                    require(log.stat().st_size <= self.limits['max_log_bytes'], 'Tool log byte limit exceeded')
                    size = sum(p.stat().st_size for p in directory.rglob('*') if p.is_file() and not p.is_symlink())
                    require(size <= self.limits['max_artifact_bytes'], 'Tool artifact byte limit exceeded')
                    time.sleep(0.1)
            except BaseException:
                _kill_tree(process.pid); process.wait(); raise
        require(log.stat().st_size <= self.limits['max_log_bytes'], 'Tool log byte limit exceeded')
        size = sum(p.stat().st_size for p in directory.rglob('*') if p.is_file() and not p.is_symlink())
        require(size <= self.limits['max_artifact_bytes'], 'Tool artifact byte limit exceeded')
        require(process.returncode == 0, 'Tool adapter failed; inspect bound command.log')

    def stage(self, phase, expected):
        self.unchanged(expected); self.remaining(); self.serial += 1
        self.state['active_stage'] = phase; self.persist()
        directory = self.out / f'{self.serial:03d}-{phase}'; directory.mkdir()
        req = {'schema_version': 1, 'phase': phase, 'run_id': self.out.name,
               'source_hashes': expected, 'configuration': self.contract}
        request = directory / 'request.json'; response = directory / 'response.json'; durable(request, req)
        request_hash = hashes([request])[str(request)]
        argv = self.cfg['commands'][phase] + ['--request', str(request), '--response', str(response)]
        if phase == 'verify': argv += ['--jobs', str(self.limits['jobs']), '--timeout', str(self.limits['stage_timeout_seconds'])]
        else: argv += ['--execute']
        durable(directory / 'command.json', {'argv': argv, 'request_sha256': request_hash,
                                             'credential_environment': 'allowlisted_non_provider_variables'})
        with SourceTransaction(self.out, self.sources) as transaction:
            try:
                self.execute(argv, directory, self.limits['stage_timeout_seconds'])
            except Exception:
                log = directory / 'command.log'
                text = log.read_text(errors='replace')[-4000:] if log.is_file() else ''
                self.last_stage_failure = {'phase': phase, 'log': str(log), 'tail': text}
                raise
            self.unchanged(expected); transaction.accept()
        require(hashes([request])[str(request)] == request_hash, 'Tool changed request')
        require(response.is_file() and not response.is_symlink() and response.stat().st_size <= 4194304, 'Missing or oversized fresh adapter response')
        value = json.loads(response.read_text())
        require(value.get('schema_version') == 1 and value.get('request_sha256') == request_hash, 'Stale adapter response')
        value['reports'] = validate_reports(value, directory, ('functional',) if phase == 'verify' else ())
        validate_target_evidence(value, expected, self.contract)
        value['_evidence'] = {'response': str(response), 'response_sha256': hashes([response])[str(response)],
                              'request': str(request), 'request_sha256': request_hash}
        if phase == 'verify': validate_gate(value, self.cfg, expected, self.contract)
        else:
            # A failed launch or report parser must not masquerade as a tool
            # version mismatch merely because qualified metadata is absent.
            require(not value.get('qualification_error_type'),
                    'Vivado evidence collection or validation failed; inspect bound vivado/qualification-error.txt')
            require(value.get('executed') is True, 'Vivado did not execute; inspect bound vivado/console.log')
            require(type(value.get('tool_returncode')) is int and value['tool_returncode'] == 0,
                    'Vivado failed; inspect bound vivado/console.log')
            require(isinstance(value.get('actual_tool_version'), str) and bool(value['actual_tool_version']),
                    'Missing actual Vivado version evidence')
            require(value.get('actual_tool_version') == self.cfg['measurement']['tool_version'], 'Vivado actual version mismatch')
            require(isinstance(value.get('metrics'), dict), 'No actual Vivado measurement')
            finite(value['metrics'].get('worst_setup_slack_ns'), 'measured setup slack')
            finite(value['metrics'].get('lut'), 'measured LUT count', True)
            require(bool(value['reports']), 'Missing measured evidence reports')
            from .vivado_qualification import validate_feedback
            validate_feedback(value, req, directory)
        return value

    def admission(self, measurement, sources):
        try:
            validate_measurement(measurement, self.cfg, self.contract, sources)
            # Beyond the legacy boolean contract, the producer must prove timing
            # coverage, zero structural hazards and source ownership explicitly.
            from .vivado_qualification import validate_admission
            request = json.loads(Path(measurement['_evidence']['request']).read_text())
            validate_admission(measurement, request, Path(measurement['_evidence']['response']).parent)
            return True, []
        except (ValueError, KeyError, TypeError, ImportError, OSError) as error:
            return False, [str(error), *[str(x) for x in measurement.get('blockers', [])]]

    def select_targets(self, measurement, sources):
        owners = {row.get('instance'): row for row in measurement.get('source_ownership', [])}
        ordered = []
        for path in sorted(measurement.get('critical_paths', []), key=lambda p: (p['slack_ns'], p['id'])):
            for instance in path.get('instances', []):
                row = owners.get(instance, {})
                source = row.get('source_path')
                if (row.get('confidence') == 'direct_source_property' and source in self.editable
                        and row.get('source_sha256') == sources[source]
                        and source not in ordered):
                    ordered.append(source)
        basis = 'Vivado direct source properties on measured critical paths; exact allowlist intersection'
        if not ordered and self.settings['mode'] == 'exploratory':
            focus = self.settings.get('exploratory_focus', [])
            inverse = {original: working for working, original in self.source_origins.items()}
            base = Path(self.settings['profile_path']).parent
            for entry in focus:
                original = str((base / entry).resolve())
                require(original in inverse and inverse[original] in self.editable, 'Exploratory focus outside reviewed allowlist')
                if inverse[original] not in ordered: ordered.append(inverse[original])
            basis = 'Explicit user-nominated exploratory focus; ownership is unverified, candidates cannot be accepted'
        require(ordered, 'No measured editable source ownership. Review direct source properties or explicitly nominate exploratory_focus; no paid request was made.')
        return ordered[:self.limits['max_edit_files']], basis

    def context(self, sources, gate, measurement, requested):
        facts = autonomous_design.model(sources, self.cfg['top'], self.state['profile_fingerprint'])
        durable(self.out / 'design-model.json', facts)
        # Persist the complete lexical graph; send bounded summary plus the exact
        # allowlist text. Top interfaces precede local candidate source text.
        summary = copy.deepcopy(facts)
        for source in summary['sources']:
            for module in source['modules']:
                if module['name'] != self.cfg['top']: module.pop('header')
        path_instances = {i for path in measurement.get('critical_paths', []) for i in path.get('instances', [])}
        ownership = [row for row in measurement.get('source_ownership', []) if row.get('instance') in path_instances]
        allowed, selection_basis = self.select_targets(measurement, sources)
        # Never promote a model's ownership guess into an edit permission.
        return {'target': 'fpga', 'scope': 'exact_selected_mldsa', 'design_model': summary,
                'measurement_configuration': self.cfg['measurement'], 'allowed_files': allowed,
                'rtl': {p: Path(p).read_text() for p in allowed},
                'read_only_requested_context': requested,
                'measurement': {k: measurement.get(k) for k in ('status', 'metrics', 'warnings', 'critical_paths', 'blockers')},
                'source_ownership': ownership, 'edit_scope_basis': selection_basis, 'coverage': {'checks': gate['checks'], 'latency_cases': len(gate['latency_cycles'])},
                'feedback': [{k: r.get(k) for k in ('iteration', 'verdict', 'reason', 'metrics_before', 'metrics_after', 'attempt_sha256', 'model_hypotheses', 'diagnostics')} for r in self.history[-8:]],
                'mode': self.settings['mode'], 'training_performed': False,
                'remaining': {'iterations': self.limits['iterations'] - self.state['iterations'],
                              'generation_attempts': self.limits['generation_attempts'] - self.state['generation_attempts']}}

    def ask(self, context):
        require(self.state['pending_request'] is None, 'Uncertain prior paid request; inspect billing before any new run')
        require(self.state['generation_attempts'] < self.limits['generation_attempts'], 'Generation-attempt limit reached')
        system = SYSTEM + TARGET_SYSTEM['fpga'] + '''\nUse the source-linked design model top-down before suggesting edits. Its lexical graph is not elaborated hierarchy. Separate source facts from hypotheses. Feedback is from the exact prior candidate and is not model training. Every edit must preserve exactly all 210 measured cycle counts and leave all comments unchanged. You may return {"status":"NEED_CONTEXT","requests":[{"path":"exact manifest path","line_start":1,"line_end":20}],"reason":"missing evidence"}, or {"status":"STOP","reason":"no defensible edit"}. Context requests consume a generation attempt and never authorize an edit or a command. Optional model_hypotheses is commentary, not qualification evidence.'''
        user = json.dumps(context, allow_nan=False)
        require(len((system + user).encode()) <= self.limits['max_prompt_bytes'], 'Prompt exceeds byte budget; narrow reviewed edit scope')
        provider = self.settings['provider']
        params = {'model': provider['model'], 'system': system, 'messages': [{'role': 'user', 'content': user}]}
        if self.client is None:
            require(os.environ.get('PQC_ENABLE_LLM') == '1', 'Paid generation disabled; fresh explicit authorization and PQC_ENABLE_LLM=1 required')
            try:
                with deadline(min(self.remaining(), self.limits['api_timeout_seconds'])): self.client = self.client_factory()
            except Exception:
                raise ContractError('Foreground provider credential setup failed; no generation dispatched') from None
        number = self.state['generation_attempts'] + 1
        folder = self.out / f'proposal-{number:03d}'; require(not folder.exists(), 'Proposal directory already claimed'); folder.mkdir()
        durable(folder / 'prompt.json', {'system': system, 'user': context})
        self.state['status'] = 'TOKEN_COUNT_PENDING'; self.persist()
        try:
            with deadline(min(self.remaining(), self.limits['api_timeout_seconds'])):
                counted = self.client.messages.count_tokens(**params).input_tokens
        except Exception:
            raise ContractError('Provider token-count preflight failed; no generation dispatched and no automatic retry') from None
        require(type(counted) is int and counted >= 0, 'Invalid token count')
        reserved_tokens = counted + (counted + 9) // 10 + 1024
        ip, op = positive(provider['input_usd_per_million']), positive(provider['output_usd_per_million'])
        reserved = (Decimal(reserved_tokens) * ip + Decimal(self.limits['max_output_tokens']) * op) / 1000000
        spent = Decimal(self.state['spent_usd']); budget = positive(provider['budget_usd'])
        require(spent + reserved <= budget, 'Cumulative estimated budget exhausted; no generation dispatched')
        self.state.update(pending_request=number, reserved_usd=str(reserved), generation_attempts=number, status='GENERATION_PENDING')
        self.persist()  # durable reservation BEFORE any generation dispatch
        durable(folder / 'reservation.json', {'request': number, 'estimated_max_usd': str(reserved),
                                               'input_reserved_tokens': reserved_tokens, 'max_output_tokens': self.limits['max_output_tokens'],
                                               'budget_usd': str(budget), 'pricing': provider})
        try:
            with deadline(min(self.remaining(), self.limits['api_timeout_seconds'])):
                reply = self.client.messages.create(**params, max_tokens=self.limits['max_output_tokens'])
            usage = reply.usage
            it, ot = usage.input_tokens, usage.output_tokens
            require(type(it) is int and it >= 0 and type(ot) is int and 0 <= ot <= self.limits['max_output_tokens'], 'Missing or invalid returned usage')
            require(not getattr(usage, 'cache_creation_input_tokens', 0) and not getattr(usage, 'cache_read_input_tokens', 0), 'Unexpected cache billing; cost must be reconciled')
            cost = (Decimal(it) * ip + Decimal(ot) * op) / 1000000
            durable(folder / 'usage.json', {'input_tokens': it, 'output_tokens': ot, 'cost_usd_at_declared_prices': str(cost),
                                           'billing_note': 'Provider billing is authoritative; this is not an account-side hard spending cap.'})
            self.state.update(spent_usd=str(spent + cost), reserved_usd='0', pending_request=None, status='RESPONSE_RECEIVED')
            self.persist()
            require(cost <= reserved and spent + cost <= budget, 'Returned usage exceeded cost reservation; stop and reconcile billing')
            require(reply.stop_reason == 'end_turn' and reply.content and all(b.type == 'text' for b in reply.content), 'Incomplete or tool-directed response')
            raw = ''.join(b.text for b in reply.content)
            require(len(raw.encode()) <= 196608, 'Model response exceeds byte bound')
            durable(folder / 'raw-response.json', {'text': raw})
            proposal, formatting = decode_response(raw)
            durable(folder / 'response.json', {'proposal': proposal, 'response_format': formatting})
            return proposal
        except BaseException:
            if self.state['pending_request'] is not None:
                self.state['status'] = 'COST_UNKNOWN_STOP'; self.persist()
            # Never retain provider exception strings or automatically retry.
            raise ContractError('Generation failed or could not be reviewed; inspect local usage/reservation. No automatic retry.') from None

    def proposal(self, reply, context, sources):
        require(reply.get('status') == 'PROPOSED', 'Expected PROPOSED, NEED_CONTEXT or STOP')
        experiment = copy.deepcopy(reply.get('experiment'))
        require(isinstance(experiment, dict) and isinstance(experiment.get('files'), list), 'Missing typed experiment')
        require(1 <= len(experiment['files']) <= self.limits['max_edit_files'], 'Edit file bound exceeded')
        changed = 0
        for row in experiment['files']:
            require(row.get('path') in context['allowed_files'], 'Edit outside narrowed allowlist')
            require(isinstance(row.get('ops'), list) and 1 <= len(row['ops']) <= 4, 'At most four edit operations per file')
            for op in row['ops']:
                require(op.get('op') == 'replace_exact' and type(op.get('expect')) is int and op['expect'] == 1, 'Only unique exact-anchor replacements accepted')
                require(isinstance(op.get('old'), str) and isinstance(op.get('new'), str), 'Invalid edit anchors')
                changed += len(op['old'].encode()) + len(op['new'].encode())
        require(changed <= self.limits['max_changed_bytes'], 'Edit byte limit exceeded')
        preview = edit_ops.preview_experiment(experiment, allowed_paths=context['allowed_files'])
        for before, after in preview.values(): unsafe_candidate(before, after)
        expected = {**sources, **{p: hashlib.sha256(after.encode()).hexdigest() for p, (_, after) in preview.items()}}
        key = digest(expected)
        require(key not in self.seen and expected != sources, 'Repeated or no-op candidate source state')
        self.seen.add(key)
        return experiment, expected, key

    def run(self):
        try:
            self.setup()
            with profile_lock(self.settings['profile_path']), RunLock(self.out):
                self.state['status'] = 'BASELINE_VERIFY'; self.persist()
                sources = self.baseline
                gate = self.stage('verify', sources)
                self.state['status'] = 'BASELINE_MEASURE'; self.persist()
                measurement = self.stage('measure', sources)
                qualified, blockers = self.admission(measurement, sources)
                self.state.update(baseline_qualified=qualified, qualification_blockers=blockers,
                                  baseline_functional=gate['_evidence'], baseline_measurement=measurement['_evidence'])
                self.record({'verdict': 'BASELINE_QUALIFIED' if qualified else 'BASELINE_PROVISIONAL', 'blockers': blockers})
                if not qualified and self.settings['mode'] == 'strict':
                    self.state['status'] = 'BASELINE_BLOCKED'; return self.state
                if qualified and self.settings['mode'] == 'strict': self.state['best_snapshot'] = 'baseline'
                requested = []
                self.seen.add(digest(sources))
                while self.state['iterations'] < self.limits['iterations'] and self.state['generation_attempts'] < self.limits['generation_attempts']:
                    self.remaining(); self.unchanged(sources)
                    context = self.context(sources, gate, measurement, requested)
                    reply = self.ask(context)
                    if reply.get('status') in ('NEED_CONTEXT', 'STOP'):
                        wants = reply.get('requests')
                        if reply['status'] == 'NEED_CONTEXT' and wants and self.state['context_requests'] < self.limits['context_requests']:
                            requested = autonomous_design.excerpts(wants, sources, self.limits['max_prompt_bytes'] // 3)
                            self.state['context_requests'] += 1
                            self.record({'verdict': 'CONTEXT_ADDED', 'reason': str(reply.get('reason', ''))[:2000]})
                            continue
                        self.record({'verdict': 'PROPOSER_STOP', 'reason': str(reply.get('reason', ''))[:2000]})
                        break
                    self.state['iterations'] += 1
                    event = {'iteration': self.state['iterations'], 'verdict': 'REJECTED', 'metrics_before': measurement['metrics'],
                             'model_hypotheses': str(reply.get('model_hypotheses', ''))[:4000], 'hypotheses_are_verified': False}
                    accepted = False
                    expected = sources
                    self.last_stage_failure = None
                    prior_state = copy.deepcopy(self.state)
                    with SourceTransaction(self.out, self.sources) as transaction:
                        try:
                            experiment, expected, key = self.proposal(reply, context, sources)
                            event['attempt_sha256'] = key
                            edit_ops.apply_experiment(experiment, allowed_paths=context['allowed_files'], backup_dir=self.out/'edit-backups')
                            self.unchanged(expected)
                            after_gate = self.stage('verify', expected)
                            require(after_gate['latency_cycles'] == gate['latency_cycles'], 'LATENCY_CHANGED: exact 210-case cycle equality is required')
                            after = self.stage('measure', expected)
                            require(after.get('qualification', {}).get('observed_tool', {}).get('tool_build') == measurement.get('qualification', {}).get('observed_tool', {}).get('tool_build'), 'TOOL_BUILD_CHANGED: matched vendor build is required')
                            event['metrics_after'] = after['metrics']; event['functional'] = after_gate['_evidence']; event['measurement'] = after['_evidence']
                            candidate_qualified, reasons = self.admission(after, expected)
                            if self.settings['mode'] == 'strict' and qualified and candidate_qualified:
                                accepted, reason = acceptance(measurement, after, gate['latency_cycles'], after_gate['latency_cycles'], self.cfg, contract=self.contract)
                                event['verdict'] = reason
                            else:
                                event['verdict'] = 'PROVISIONAL_NOT_ACCEPTED'; event['reason'] = reasons or blockers
                                name = self.snapshot(f'provisional-{self.state["iterations"]:03d}', expected)
                                self.state['provisional_candidates'].append(name)
                            if accepted:
                                name = self.snapshot(f'accepted-{self.state["iterations"]:03d}', expected)
                                event['snapshot'] = name
                        except Exception as error:
                            accepted = False
                            event.update(verdict='REJECTED', reason=str(error)[:2000], diagnostics=self.last_stage_failure)
                        self.unchanged(expected if hashes(self.sources) == expected else sources)
                        if accepted:
                            # Keep the rollback snapshot alive until promotion
                            # provenance AND current-state persistence succeed.
                            self.state.update(accepted=self.state['accepted']+1, best_snapshot=name, current_sources=expected)
                            event['retention'] = 'ACCEPTED_WORKSPACE'
                            try:
                                self.record(event)
                                transaction.accept()
                            except BaseException:
                                self.state = prior_state
                                self.state['status'] = 'PERSISTENCE_FAILED'
                                raise
                    if accepted:
                        sources, gate, measurement = expected, after_gate, after
                    else:
                        event['retention'] = 'ROLLED_BACK_TO_INCUMBENT'
                        self.record(event)
                    self.unchanged(sources)
                self.state['status'] = 'COMPLETED' if self.settings['mode'] == 'strict' else 'EXPLORATION_COMPLETED_UNQUALIFIED'
                return self.state
        except BaseException as error:
            if self.state['status'] not in ('COST_UNKNOWN_STOP', 'PERSISTENCE_FAILED'): self.state['status'] = 'BLOCKED'
            self.state['error'] = str(error)[:2000]
            if isinstance(error, (KeyboardInterrupt, SystemExit)): raise
            return self.state
        finally:
            if self.client is not None:
                try: self.client.close()
                except Exception: self.state['client_close_error'] = 'Provider client close failed; details withheld'
            if self.out.exists():
                if hasattr(self, 'originals'):
                    try: self.state['baseline_unchanged'] = hashes(self.originals) == self.originals
                    except (OSError, RuntimeError): self.state['baseline_unchanged'] = False
                # Bind all persisted control/response/evidence records after the
                # final state is written. Large tool artifacts are already bound
                # by adapter report hashes, and source snapshots by manifests.
                self.persist()
                records = [p for p in self.out.rglob('*.json') if not any(x in p.relative_to(self.out).parts for x in ('kat-work', 'edit-backups', '.pqc_runs')) and p.name != 'integrity.json']
                durable(self.out / 'integrity.json', {'records': {str(p.relative_to(self.out)): h for p, h in ((p, hashes([p])[str(p)]) for p in records)}})


def inspect_run(directory):
    """Read-only integrity inspection. Never resumes or redispatches an API call."""
    folder = Path(directory).resolve()
    integrity_path = folder / 'integrity.json'
    require(integrity_path.is_file() and not integrity_path.is_symlink(), 'Run finalization is incomplete; no redispatch is allowed')
    integrity = json.loads(integrity_path.read_text())
    for relative, expected in integrity['records'].items():
        path = folder / relative
        require(path.resolve().is_relative_to(folder) and not path.is_symlink(), 'Integrity record escapes run')
        require(hashes([path])[str(path.resolve())] == expected, 'Persisted record changed: ' + relative)
    state = json.loads((folder / 'state.json').read_text())
    require(state.get('schema_version') == 1, 'Unsupported run state')
    config = json.loads((folder / 'configuration.json').read_text())
    require(digest(config) == state['configuration_sha256'], 'Configuration record changed')
    require(state['status'] != 'PERSISTENCE_FAILED', 'Interrupted promotion persistence; no successful integrity claim')
    head = None
    accepted = []
    for index, path in enumerate(sorted((folder / 'journal').glob('*.json'))):
        row = json.loads(path.read_text()); claimed = row.pop('sha256')
        require(row['sequence'] == index and row['previous'] == head and digest(row) == claimed, 'Journal chain changed')
        head = claimed
        if row.get('verdict') == 'ACCEPT':
            require(row.get('retention') == 'ACCEPTED_WORKSPACE', 'Acceptance lacks retention evidence')
            accepted.append(row)
    require(len(accepted) == state['accepted'], 'Acceptance count disagrees with journal')
    if accepted:
        require(accepted[-1]['snapshot'] == state['best_snapshot'], 'Best snapshot disagrees with accepted journal')
        manifest = json.loads((folder/state['best_snapshot']/'manifest.json').read_text())
        require(manifest['original_source_hashes'] == state['current_sources'], 'Accepted snapshot does not match current source hashes')
    require(head == state['journal_head'], 'Journal/state mismatch; interrupted persistence requires review')
    require(hashes(state['original_hashes']) == state['original_hashes'], 'Original sources or immutable inputs changed')
    require(hashes(state['current_sources']) == state['current_sources'], 'Working source state changed')
    for name in dict.fromkeys(['baseline', *state['provisional_candidates'], *[row['snapshot'] for row in accepted]]):
        snapshot = folder / name
        require(snapshot.resolve().is_relative_to(folder) and not snapshot.is_symlink(), 'Snapshot escapes run')
        manifest = json.loads((snapshot / 'manifest.json').read_text())
        require(manifest['configuration_sha256'] == state['configuration_sha256'], 'Snapshot configuration mismatch')
        for relative, expected in manifest['source_hashes'].items():
            path = snapshot / relative
            require(path.resolve().is_relative_to(snapshot) and not path.is_symlink(), 'Snapshot source escapes run')
            require(hashes([path])[str(path.resolve())] == expected, 'Snapshot source changed')
    for relative in integrity['records']:
        if relative.endswith('/response.json') and not relative.startswith('proposal-'):
            path = folder / relative
            response = json.loads(path.read_text())
            validate_reports(response, path.parent, ())
    require(state['pending_request'] is None, 'Pending/uncertain paid request; do not resume or redispatch, reconcile provider usage')
    return {**state, 'integrity_checked': True, 'resumed': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config'); parser.add_argument('--out'); parser.add_argument('--execute', action='store_true')
    parser.add_argument('--inspect')
    args = parser.parse_args(argv)
    try:
        if args.inspect: result = inspect_run(args.inspect)
        else:
            require(args.config and args.out, '--config and --out are required')
            settings = load_settings(args.config)
            if not args.execute:
                result = {'status': 'CONFIGURED_NOT_RUN', 'mode': settings['mode'], 'sources': len(settings['sources']),
                          'limits': settings['limits'], 'paid_calls': 0, 'tools_ran': False,
                          'note': 'Execute first checks the exact baseline. Paid work requires a newly approved model/data/budget and PQC_ENABLE_LLM=1.'}
            else: result = Controller(settings, args.out).run()
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if result['status'] in ('CONFIGURED_NOT_RUN', 'COMPLETED', 'EXPLORATION_COMPLETED_UNQUALIFIED') else 2
    except (ValueError, KeyError, TypeError, OSError) as error:
        print('BLOCKED: ' + str(error), file=sys.stderr); return 2


if __name__ == '__main__': raise SystemExit(main())
