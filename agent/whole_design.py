"""Opt-in, fail-closed whole-design search with qualified command adapters.

No vendor report dialect or instance-to-RTL mapping is guessed here. A plan is
read-only; --execute invokes the explicitly configured, trusted commands. See
docs/WHOLE_DESIGN.md for the JSON protocol and its qualification limits.
"""
from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
import uuid

from . import edit_ops, target_profiles
from .run_safety import RunLock, SourceTransaction, hashes, run_process


class ContractError(ValueError):
    """Missing, inconsistent, or unqualified evidence; never a successful run."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def finite(value, label, positive=False):
    require(type(value) in (int, float) and math.isfinite(value)
            and (not positive or value > 0), f'Invalid {label}')
    return value


def integer(value, label, minimum=1, maximum=100):
    require(type(value) is int and minimum <= value <= maximum, f'Invalid {label}')
    return value


def save(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    os.replace(temporary, path)


def local_path(value, root):
    require(isinstance(value, str) and bool(value), 'Expected a nonempty path')
    original = root / value
    path = original.resolve()
    require(path.is_relative_to(root) and path != root, f'Path escapes design root: {value}')
    require(not any(p.is_symlink() for p in (original, *original.parents)),
            f'Symlinked input: {value}')
    require(path.is_file(), f'Missing input: {path}')
    return str(path)


def input_path(value, root):
    # Immutable site libraries may live outside the checkout. They are never
    # editable scopes; a change is detected and blocks further work.
    require(isinstance(value, str) and value, 'Expected an immutable input path')
    path = (root / value).resolve()
    require(path.is_file(), f'Missing immutable input: {path}')
    return str(path)


def strings(value, label):
    require(isinstance(value, list) and value and all(isinstance(x, str) and x for x in value),
            f'Missing {label}')
    require(len(value) == len(set(value)), f'Duplicate {label}')
    return value


def load_config(filename):
    filename = Path(filename).resolve()
    cfg = json.loads(filename.read_text())
    require(isinstance(cfg, dict), 'Configuration must be an object')
    require('_target_profile' not in cfg, 'Reserved normalized target profile field')
    require(cfg.get('schema_version') == 1, 'Expected schema_version 1')
    root = (filename.parent / cfg.get('root', '.')).resolve()
    require(root.is_dir(), 'Missing design root')
    target, backend = cfg.get('target'), cfg.get('backend')
    require((target == 'fpga' and backend == 'vivado') or
            (target == 'asic' and backend in ('genus', 'dc')), 'Unsupported target/backend')
    require(isinstance(cfg.get('top'), str) and re.fullmatch(r'[A-Za-z_]\w*', cfg['top']),
            'Missing HDL top module')
    require(cfg.get('scope') == 'full_design', 'Only explicit full_design scope is supported')
    sources = [local_path(x, root) for x in strings(cfg.get('sources'), 'ordered sources')]
    require(len(sources) == len(set(sources)), 'Duplicate resolved source')
    immutable = [input_path(x, root) for x in strings(cfg.get('immutable_inputs'), 'immutable_inputs')]
    immutable.append(str(filename))
    require(not set(sources) & set(immutable), 'Sources overlap immutable verification/configuration inputs')
    editable = [local_path(x, root) for x in strings(cfg.get('editable_files'), 'editable_files')]
    require(set(editable) <= set(sources), 'Editable RTL must belong to the measured source manifest')
    for path in editable:
        edit_ops.validate_path(path, editable)
    mapping = cfg.get('instance_to_file')
    require(isinstance(mapping, dict) and mapping, 'Missing qualified instance-to-RTL mapping')
    resolved_mapping = {}
    for instance, file in mapping.items():
        require(isinstance(instance, str) and instance and not instance.endswith('/'), 'Invalid instance prefix')
        path = local_path(file, root)
        require(path in editable, f'Mapping is outside editable RTL: {instance}')
        resolved_mapping[instance] = path
    measurement = cfg.get('measurement', {})
    require(isinstance(measurement, dict), 'Measurement configuration must be an object')
    require(measurement.get('stage') in ('post_synth', 'post_route'), 'Specify measurement stage')
    require(target != 'asic' or measurement['stage'] == 'post_synth',
            'ASIC adapters currently support logical post_synth only')
    for field in ('tool_version', 'technology', 'corner', 'effort', 'seed', 'memory_model', 'qualification'):
        require(field in measurement and measurement[field] not in ('', None, 'unspecified'),
                f'Missing measurement.{field}')
    finite(measurement.get('period_ns'), 'period_ns', True)
    require(isinstance(measurement.get('constraints'), list) and measurement['constraints'],
            'Declare measurement constraints')
    constraints = [input_path(x, root) for x in measurement['constraints']]
    require(set(constraints) <= set(immutable), 'Constraints must be immutable inputs')
    commands = cfg.get('commands', {})
    require(isinstance(commands, dict), 'Commands must be an object')
    for phase in ('verify', 'measure', 'propose'):
        argv = commands.get(phase)
        require(isinstance(argv, list) and argv and all(isinstance(x, str) and x for x in argv),
                f'Missing trusted {phase} command')
        require(any('{request}' in x for x in argv) and any('{response}' in x for x in argv),
                f'{phase} command must consume {{request}} and {{response}}')
        require(all(not re.search(r'\{[^}]*\}', x.replace('{request}', '').replace('{response}', ''))
                    for x in argv), 'Unknown command placeholder')
    if cfg.get('verification_profile') is not None:
        require(cfg['verification_profile'] == 'mldsa_keygen_75', 'Unsupported built-in verification profile')
        from .whole_design_adapters import mldsa_profile
        profile = mldsa_profile()
        require(cfg['top'] == profile['top'], 'Verification profile top mismatch')
        for key in ('required_checks', 'operations'):
            require(key not in cfg or cfg[key] == profile[key], f'Conflicting profile {key}')
            cfg[key] = profile[key]
    checks = strings(cfg.get('required_checks'), 'full-design required_checks')
    operations = strings(cfg.get('operations'), 'latency operations')
    objective = cfg.get('objective', {})
    require(isinstance(objective, dict), 'Objective must be an object')
    metric = objective.get('metric')
    area_metric = cfg.get('area_metric')
    allowed_area = ('cell_area_reported',) if target == 'asic' else ('lut', 'ff', 'dsp', 'bram')
    require(area_metric in allowed_area, 'Specify a supported primary area metric')
    require(metric in ('worst_setup_slack_ns', area_metric), 'Only fixed-period timing or area objectives are supported')
    finite(objective.get('min_improvement'), 'positive absolute min_improvement', True)
    finite(cfg.get('minimum_slack_ns', 0), 'minimum_slack_ns')
    max_area_regression = finite(cfg.get('max_area_regression_fraction', 0), 'max_area_regression_fraction')
    require(max_area_regression >= 0, 'Negative area allowance')
    integer(cfg.get('candidate_budget', 5), 'candidate_budget', maximum=100)
    integer(cfg.get('critical_path_count', 5), 'critical_path_count', minimum=2, maximum=100)
    integer(cfg.get('max_edit_files', 2), 'max_edit_files', maximum=4)
    integer(cfg.get('max_changed_bytes', 16384), 'max_changed_bytes', maximum=262144)
    integer(cfg.get('max_context_bytes', 262144), 'max_context_bytes', maximum=1048576)
    finite(cfg.get('timeout_seconds', 86400), 'timeout_seconds', True)
    if cfg.get('target_profile') is not None:
        profile_path = local_path(cfg['target_profile'], root)
        require(profile_path in immutable, 'Target profile must be an immutable input')
        require(cfg.get('verification_profile') != 'mldsa_keygen_75',
                'KeyGen-only coverage cannot qualify a full-selected-design target profile')
        require(cfg.get('verification_scope') == 'full_selected_design',
                'Target-profile optimization requires full_selected_design verification_scope')
        controls = strings(cfg.get('required_negative_controls'), 'required_negative_controls')
        require(set(controls) <= set(checks), 'Negative controls must belong to required_checks')
        cfg['_target_profile'] = target_profiles.load_profile(profile_path, root, cfg, sources, immutable)
    return {**cfg, 'root': str(root), 'config_path': str(filename), 'sources': sources,
            'immutable_inputs': sorted(set(immutable)), 'editable_files': editable,
            'instance_to_file': resolved_mapping, 'required_checks': checks, 'operations': operations}


def configuration(cfg):
    """Comparable measurement and checker contract; source bytes vary separately."""
    return {'target': cfg['target'], 'backend': cfg['backend'], 'top': cfg['top'],
            'scope': 'full_design', 'measurement': cfg['measurement'],
            'target_profile': cfg.get('_target_profile'),
            'target_include_inventory': target_profiles.include_inventory(cfg.get('_target_profile')),
            'verification_scope': cfg.get('verification_scope',
                'keygen_only' if cfg.get('verification_profile') == 'mldsa_keygen_75' else 'declared_checks_only'),
            'required_negative_controls': cfg.get('required_negative_controls', []),
            'source_read_order': cfg['sources'], 'immutable_hashes': hashes(cfg['immutable_inputs']),
            'commands': cfg['commands'], 'required_checks': cfg['required_checks'],
            'operations': cfg['operations'], 'instance_to_file': cfg['instance_to_file'],
            'admission': {'objective': cfg['objective'], 'area_metric': cfg['area_metric'],
                          'minimum_slack_ns': cfg.get('minimum_slack_ns', 0),
                          'max_area_regression_fraction': cfg.get('max_area_regression_fraction', 0),
                          'max_edit_files': cfg.get('max_edit_files', 2),
                          'max_changed_bytes': cfg.get('max_changed_bytes', 16384),
                          'critical_path_count': cfg.get('critical_path_count', 5)}}


def make_plan(filename):
    """Return blockers without launching commands or creating run files."""
    try:
        cfg = load_config(filename)
        contract = configuration(cfg)
        missing = [phase for phase, argv in cfg['commands'].items()
                   if not shutil.which(argv[0], path=os.environ.get('PATH'))
                   and not (Path(cfg['root']) / argv[0]).is_file()]
        return {'status': 'BLOCKED' if missing else 'CONFIGURED_NOT_RUN',
                'blockers': [f'Missing executable for {phase}' for phase in missing],
                'backend': cfg['backend'], 'top': cfg['top'], 'configuration': contract,
                'qualification_mode': 'target_bound' if cfg.get('_target_profile') else 'legacy_not_target_qualified',
                'candidate_budget': cfg.get('candidate_budget', 5), 'commands': cfg['commands'],
                'note': 'Adapter semantics and site qualification must be reviewed. No EDA, simulation, or LLM ran.'}
    except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
        return {'status': 'BLOCKED', 'blockers': [str(error)], 'note': 'No commands ran.'}


def validate_reports(response, directory, required):
    reports = response.get('reports')
    require(isinstance(reports, dict) and set(required) <= set(reports), 'Missing evidence reports')
    result = {}
    for name, report in reports.items():
        require(isinstance(report, dict), 'Malformed report record')
        path = Path(local_path(report.get('path'), directory))
        require(path.stat().st_size > 0, f'Empty report: {name}')
        actual = hashes([path])[str(path)]
        require(actual == report.get('sha256'), f'Report hash mismatch: {name}')
        result[name] = {'path': str(path), 'sha256': actual}
    return result


def validate_gate(response, cfg, expected=None, contract=None):
    require(response.get('status') == 'PASS' and response.get('scope') == 'full_design',
            'Full-design functional verification did not pass')
    if cfg.get('_target_profile') is not None:
        require(contract is not None and expected is not None, 'Target gate needs source/configuration binding')
        validate_target_evidence(response, expected, contract)
        require(response.get('coverage_scope') == 'full_selected_design',
                'Partial-operation gate cannot qualify the selected target design')
        require(response.get('covered_operations') == cfg['_target_profile']['required_operations'],
                'Missing full-selected-operation target coverage')
    checked = response.get('checks')
    require(isinstance(checked, dict) and all(checked.get(x) == 'PASS' for x in cfg['required_checks'])
            and all(value == 'PASS' for value in checked.values()), 'Required functional checks are missing or failed')
    cycles = response.get('latency_cycles')
    require(isinstance(cycles, dict) and set(cycles) == set(cfg['operations']),
            'Missing or mismatched operation latency evidence')
    for operation, count in cycles.items():
        integer(count, f'latency for {operation}', maximum=10**15)
    return cycles


def validate_target_evidence(response, expected, contract):
    profile = contract['target_profile']
    require(response.get('target_profile_fingerprint') == profile['profile_fingerprint'],
            'Evidence belongs to a different target profile')
    require(response.get('configuration') == contract, 'Target evidence configuration mismatch')
    require(response.get('source_hashes') == expected and
            response.get('source_read_order') == contract['source_read_order'],
            'Target evidence does not bind the full selected source manifest')


def validate_measurement(response, cfg, contract, expected=None):
    require(response.get('status') == 'MEASURED' and response.get('scope') == 'full_design',
            'Missing full-design measurement')
    require(response.get('configuration') == contract, 'Measurement configuration mismatch')
    if cfg.get('_target_profile') is not None:
        require(expected is not None, 'Target measurement needs exact source binding')
        validate_target_evidence(response, expected, contract)
        require(response.get('structural_checks_verified') is True and
                response.get('memory_implementation_verified') is True,
                'Target structural/memory implementation admission is unverified')
        require(response.get('memory_implementation') ==
                cfg['_target_profile']['target']['memory_implementation'],
                'Measured memory implementation differs from selected target')
        require({'structural', 'memory'} <= set(response.get('reports', {})),
                'Missing structural/memory target admission evidence')
        require(response.get('memory_semantics_verified') is True and
                response.get('memory_semantics_scope') == 'mapped_implementation',
                'Mapped memory startup/read/write/collision semantics are unverified')
        require({'memory_semantics', 'implementation_netlist'} <= set(response.get('reports', {})),
                'Missing mapped memory semantics report or exact implementation netlist')
        if cfg['target'] == 'asic':
            require(response.get('admission_passed') is True and
                    response.get('admission_policy') == 'strict-rtl-flops-v1',
                    'Strict ASIC admission did not pass')
    metrics = response.get('metrics', {})
    finite(metrics.get('worst_setup_slack_ns'), 'worst setup slack')
    finite(metrics.get(cfg['area_metric']), 'primary area metric', True)
    require(isinstance(response.get('area_unit'), str) and response['area_unit'], 'Missing area unit')
    paths = response.get('critical_paths')
    require(isinstance(paths, list) and len(paths) >= cfg.get('critical_path_count', 5),
            'Too few independently reported critical paths')
    seen, locations, endpoints = set(), set(), set()
    for path in paths:
        require(isinstance(path, dict) and isinstance(path.get('id'), str) and path['id'] not in seen,
                'Missing or duplicate timing-path ID')
        seen.add(path['id'])
        for field in ('startpoint', 'endpoint'):
            require(isinstance(path.get(field), str) and path[field], f'Missing path {field}')
        strings(path.get('instances'), 'timing path instance provenance')
        finite(path.get('slack_ns'), 'path slack')
        require(path.get('report') == 'timing', 'Critical paths must reference timing evidence')
        pair = (path['startpoint'], path['endpoint'])
        require(pair not in endpoints, 'Duplicate critical-path endpoint pair')
        endpoints.add(pair)
        report = response['reports'].get(path.get('report'))
        require(report is not None, 'Path lacks timing report provenance')
        begin = integer(path.get('line_start'), 'path report start line', maximum=10**8)
        end = integer(path.get('line_end'), 'path report end line', minimum=begin, maximum=10**8)
        require(end <= len(Path(report['path']).read_text().splitlines()), 'Path lines escape timing report')
        location = (report['path'], begin, end)
        require(location not in locations, 'Duplicate timing-path report range')
        locations.add(location)
    require(math.isclose(min(x['slack_ns'] for x in paths), metrics['worst_setup_slack_ns'],
                         abs_tol=1e-9, rel_tol=1e-9), 'Critical paths contradict worst setup slack')
    return response


def choose_targets(measurement, cfg):
    paths = sorted(measurement['critical_paths'], key=lambda x: (x['slack_ns'], x['id']))
    paths = paths[:cfg.get('critical_path_count', 5)]
    files, mapped = [], []
    for path in paths:
        responsible = []
        for instance in path['instances']:
            matches = [prefix for prefix in cfg['instance_to_file']
                       if instance == prefix or instance.startswith(prefix + '/')]
            if matches:
                chosen = cfg['instance_to_file'][max(matches, key=len)]
                if chosen not in responsible:
                    responsible.append(chosen)
        require(responsible, f'No qualified editable RTL mapping for critical path {path["id"]}')
        mapped.append({**path, 'responsible_files': responsible})
        for file in responsible:
            if file not in files and len(files) < cfg.get('max_edit_files', 2):
                files.append(file)
    context = {file: Path(file).read_text() for file in files}
    require(sum(len(text.encode()) for text in context.values()) <= cfg.get('max_context_bytes', 262144),
            'Responsible RTL exceeds bounded proposal context; split or refine the reviewed mapping')
    return {'critical_paths': mapped, 'allowed_files': files, 'rtl': context}


def acceptance(before, after, before_cycles, after_cycles, cfg):
    require(before['configuration'] == after['configuration'], 'Configuration changed during comparison')
    require(before['configuration'] == configuration(cfg),
            'Acceptance evidence belongs to a different target/configuration')
    require(before['area_unit'] == after['area_unit'], 'Area units changed')
    if any(after_cycles[key] > before_cycles[key] for key in before_cycles):
        return False, 'LATENCY_REGRESSION'
    old, new = before['metrics'], after['metrics']
    if new['worst_setup_slack_ns'] < cfg.get('minimum_slack_ns', 0):
        return False, 'TIMING_FLOOR'
    area = cfg['area_metric']
    if new[area] > old[area] * (1 + cfg.get('max_area_regression_fraction', 0)):
        return False, 'AREA_REGRESSION'
    metric = cfg['objective']['metric']
    if metric == area and new['worst_setup_slack_ns'] < old['worst_setup_slack_ns']:
        return False, 'TIMING_REGRESSION'
    gain = new[metric] - old[metric] if metric == 'worst_setup_slack_ns' else old[metric] - new[metric]
    return (True, 'ACCEPT') if gain >= cfg['objective']['min_improvement'] else (False, 'NO_REAL_IMPROVEMENT')


class Controller:
    def __init__(self, cfg):
        self.cfg = cfg
        self.root = Path(cfg['root'])
        self.contract = configuration(cfg)
        self.baseline_sources = hashes(cfg['sources'])
        self.directory = self.root / '.pqc_runs' / 'whole_design' / uuid.uuid4().hex
        self.events = []
        self.seen_attempts, self.seen_sources = set(), {digest(self.baseline_sources)}
        self.serial = 0
        self.pending_event = None
        self.pending_backups = None
        self.protected = sorted(set(cfg['sources']) | {
            path for path in cfg['immutable_inputs'] if Path(path).is_relative_to(self.root)})

    def unchanged(self, expected):
        require(hashes(self.cfg['sources']) == expected, 'Source manifest changed during command')
        require(configuration(self.cfg) == self.contract, 'Immutable configuration/test inputs changed')

    def command(self, phase, expected, extra=None):
        self.unchanged(expected)
        self.serial += 1
        directory = self.directory / f'{self.serial:03d}-{phase}'
        directory.mkdir()
        request = {'schema_version': 1, 'phase': phase, 'run_id': self.directory.name,
                   'source_hashes': expected, 'configuration': self.contract, **(extra or {})}
        request_path, response_path = directory / 'request.json', directory / 'response.json'
        save(request_path, request)
        request_hash = hashes([request_path])[str(request_path)]
        argv = [word.replace('{request}', str(request_path)).replace('{response}', str(response_path))
                for word in self.cfg['commands'][phase]]
        save(directory / 'command.json', {'argv': argv, 'cwd': str(self.root), 'request_sha256': request_hash})
        # Trusted adapters are read-only with respect to declared inputs. Restore
        # local inputs if an adapter unexpectedly modifies them or is interrupted.
        # External immutable libraries are hash-checked, never written by us.
        with SourceTransaction(self.root, self.protected) as transaction:
            completed = run_process(argv, cwd=self.root, timeout=self.cfg.get('timeout_seconds', 86400),
                                    log_path=directory / 'command.log')
            self.unchanged(expected)
            transaction.accept()
        require(hashes([request_path])[str(request_path)] == request_hash, 'Adapter changed its request')
        require(completed.returncode == 0, f'{phase} command failed with exit {completed.returncode}')
        require(response_path.is_file() and not response_path.is_symlink(), f'{phase} produced no fresh response')
        require(response_path.stat().st_size <= 4 * 1024 * 1024, 'Adapter response exceeds 4 MiB')
        response = json.loads(response_path.read_text())
        require(isinstance(response, dict) and response.get('schema_version') == 1 and
                response.get('request_sha256') == request_hash, f'{phase} response is stale or malformed')
        if phase != 'propose':
            response['reports'] = validate_reports(response, directory, ('functional',) if phase == 'verify' else ('timing', 'area'))
        response['_evidence'] = {'request': str(request_path), 'response': str(response_path),
                                 'response_sha256': hashes([response_path])[str(response_path)],
                                 'command': str(directory / 'command.json'), 'log': str(directory / 'command.log')}
        return response

    def record(self, event):
        with (self.directory / 'outcomes.jsonl').open('a') as stream:
            stream.write(json.dumps(event, allow_nan=False) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        self.events.append(copy.deepcopy(event))

    def verify(self, expected):
        value = self.command('verify', expected)
        validate_gate(value, self.cfg, expected, self.contract)
        return value

    def measure(self, expected):
        value = self.command('measure', expected)
        return validate_measurement(value, self.cfg, self.contract, expected)

    def candidate(self, number, current_sources, current_gate, current_measurement):
        event = {'history_schema': 1, 'candidate_id': f'{self.directory.name}-{number}',
                 'history_state': 'chip_rejected', 'evidence_stage': 'full_design',
                 'correctness_status': 'NOT_RUN', 'baseline_sources': current_sources,
                 'configuration': self.contract, 'verdict': 'ERROR',
                 'target': self.cfg['target'], 'configuration_sha256': digest(self.contract),
                 'target_profile_fingerprint': (self.contract['target_profile'] or {}).get('profile_fingerprint')}
        self.pending_event = event
        self.pending_backups = None
        backups = None
        retained = False
        try:
            targets = choose_targets(current_measurement, self.cfg)
            reply = self.command('propose', current_sources, {**targets, 'measurement': current_measurement,
                                 'feedback': [{k: row.get(k) for k in ('verdict', 'error', 'attempt_hash')}
                                              for row in self.events[-5:]]})
            event['proposal_evidence'] = reply['_evidence']
            if reply.get('status') == 'STOP':
                event['verdict'] = 'PROPOSER_STOP'
                return event, None
            require(reply.get('status') == 'PROPOSED', 'Missing typed proposal')
            experiment = copy.deepcopy(reply.get('experiment'))
            require(isinstance(experiment, dict) and isinstance(experiment.get('files'), list), 'Malformed experiment')
            require(0 < len(experiment['files']) <= self.cfg.get('max_edit_files', 2), 'Too many proposed files')
            for file in experiment['files']:
                file['path'] = local_path(file.get('path'), self.root)
            event['proposal'] = {'design': self.cfg['top'], 'block': 'whole_design',
                                 'strategy': reply.get('strategy', 'unspecified'), 'edits': experiment,
                                 'source_model': reply.get('source_model', 'configured_proposer')}
            # Experiment names and narrative cannot defeat the exact attempt filter.
            attempt_hash = digest({'sources': current_sources, 'files': sorted(experiment['files'], key=lambda x: x['path'])})
            event['attempt_hash'] = attempt_hash
            require(attempt_hash not in self.seen_attempts, 'DUPLICATE_ATTEMPT')
            self.seen_attempts.add(attempt_hash)
            preview = edit_ops.preview_experiment(experiment, allowed_paths=targets['allowed_files'])
            changed_bytes = 0
            for before, after in preview.values():
                if self.cfg.get('_target_profile') is not None:
                    require(target_profiles.unchanged_directives(before, after),
                            'Candidate changes frozen compilation directives')
                changed_bytes += sum(len(line[1:].encode()) for line in
                                     difflib.ndiff(before.splitlines(True), after.splitlines(True))
                                     if line.startswith(('+ ', '- ')))
            require(changed_bytes <= self.cfg.get('max_changed_bytes', 16384), 'Proposal exceeds changed-byte budget')
            predicted = {**current_sources, **{path: hashlib.sha256(text[1].encode()).hexdigest() for path, text in preview.items()}}
            require(digest(predicted) not in self.seen_sources, 'DUPLICATE_SOURCE_STATE')
            self.seen_sources.add(digest(predicted))
            backups = edit_ops.apply_experiment(experiment, allowed_paths=targets['allowed_files'],
                                                backup_dir=self.directory / 'backups')
            self.pending_backups = backups
            candidate_sources = hashes(self.cfg['sources'])
            event['candidate_sources'] = {'sources': candidate_sources,
                                          'includes': self.contract['immutable_hashes'],
                                          'read_order': self.cfg['sources']}
            require(candidate_sources == predicted, 'Applied source bytes differ from preview')
            gate = self.verify(candidate_sources)
            event['correctness_status'] = 'PASS'
            event['functional'] = gate
            post = self.measure(candidate_sources)
            event['before'], event['post'] = current_measurement, post
            accepted, reason = acceptance(current_measurement, post, current_gate['latency_cycles'],
                                          gate['latency_cycles'], self.cfg)
            event['verdict'] = reason
            if accepted:
                # Require next iteration to be mappable before committing this candidate.
                choose_targets(post, self.cfg)
                self.unchanged(candidate_sources)
                retained = True
                event['history_state'] = 'finally_accepted'
                return event, (candidate_sources, gate, post)
            return event, None
        except Exception as error:
            event['error'] = str(error)
            event['verdict'] = 'REJECTED'
            return event, None
        finally:
            if backups is not None and not retained:
                edit_ops.revert(backups)
            # All final records are emitted only after rollback/retention and
            # exact-source/config verification by run(). Backups remain on disk.

    def run(self):
        with RunLock(self.root):
            self.directory.mkdir(parents=True)
            save(self.directory / 'manifest.json', {'config': self.cfg, 'configuration': self.contract,
                                                   'baseline_sources': self.baseline_sources})
            result = {'status': 'BLOCKED', 'run_dir': str(self.directory), 'accepted': 0,
                      'baseline_sources': self.baseline_sources, 'timing_signoff': False,
                      'workload_power_validated': False,
                      'qualification_mode': 'target_bound' if self.cfg.get('_target_profile') else 'legacy_not_target_qualified',
                      'target_profile_fingerprint': (self.contract['target_profile'] or {}).get('profile_fingerprint'),
                      'hardware_learning_claim': False}
            try:
                self.unchanged(self.baseline_sources)
                gate = self.verify(self.baseline_sources)
                measurement = self.measure(self.baseline_sources)
                choose_targets(measurement, self.cfg)
                result['baseline_functional'], result['baseline_measurement'] = gate, measurement
                sources = self.baseline_sources
                result['final_sources'] = sources
                for number in range(1, self.cfg.get('candidate_budget', 5) + 1):
                    self.pending_event = None
                    recording = False
                    try:
                        # Keep an incumbent snapshot through outcome persistence.
                        # This closes the interruption window after candidate()
                        # returns but before the accepted outcome is durable.
                        with SourceTransaction(self.root, self.protected) as transaction:
                            event, accepted = self.candidate(number, sources, gate, measurement)
                            self.unchanged(accepted[0] if accepted else sources)
                            recording = True
                            self.record(event)
                            if accepted:
                                transaction.accept()
                    except BaseException as error:
                        self.unchanged(sources)
                        if self.pending_event is not None:
                            self.pending_event.update(history_state='chip_rejected', error=str(error),
                                verdict='HISTORY_WRITE_FAILED' if recording else 'INTERRUPTED')
                            try:
                                self.record(self.pending_event)
                            except OSError:
                                pass  # Backups/result preserve recovery context.
                        raise
                    if accepted:
                        sources, gate, measurement = accepted
                        result['accepted'] += 1
                        result['final_sources'] = sources
                    if event['verdict'] == 'PROPOSER_STOP':
                        break
                result.update(status='COMPLETED', final_sources=sources, final_functional=gate,
                              final_measurement=measurement, candidates=len(self.events))
            except BaseException as error:
                result['error'] = str(error)
                result['status'] = 'BLOCKED'
                if isinstance(error, (KeyboardInterrupt, SystemExit)):
                    raise
            finally:
                save(self.directory / 'result.json', result)
            return result


def asic_measurement_response(result, request_path, response_path, critical_paths):
    """Translate agent.asic_synthesis output; requires site-qualified path extraction.

    Keeps original evidence inside the invocation directory. It never infers
    RTL ownership from cell names, derives Fmax, or validates workload power.
    The site adapter must call this after its real run, not reuse old results.
    """
    request_path, response_path = Path(request_path).resolve(), Path(response_path).resolve()
    request = json.loads(request_path.read_text())
    contract = request['configuration']
    spec = contract['measurement']
    profile = contract.get('target_profile')
    if profile is not None:
        require(contract.get('target') == 'asic', 'ASIC result cannot qualify an FPGA target')
        target_profiles.validate_asic_plan(spec.get('asic_effective_config'), profile)
        require(result.get('admission_passed') is True and result.get('structural_checks_verified') is True
                and result.get('memory_implementation_verified') is True
                and result.get('memory_implementation') == 'flops'
                and result.get('admission_policy') == 'strict-rtl-flops-v1',
                'ASIC target implementation admission did not pass')
    require(result.get('status') == 'MEASURED' and result.get('tool') in ('genus', 'dc'),
            'ASIC measurement did not complete')
    require(result['tool'] == contract['backend'] and result.get('stage') == spec['stage']
            and result.get('top') == contract['top'] and result.get('scope') == 'full_design',
            'ASIC scope/backend/stage mismatch')
    require(result.get('period_ns') == spec['period_ns'] and result.get('memory_model') == spec['memory_model'],
            'ASIC period/memory mismatch')
    directory = Path(result['run_dir']).resolve()
    manifest = json.loads((directory / 'manifest.json').read_text())
    require(json.loads((directory / 'result.json').read_text()) == result, 'ASIC result artifact mismatch')
    effective = {key: value for key, value in manifest.items() if key not in ('output_root', 'input_hashes')}
    require(spec.get('asic_effective_config') == effective, 'ASIC effective configuration mismatch')
    require(spec.get('seed') == 'not_applicable', 'ASIC bridge has no configurable seed support')
    declared_constraints = [str((Path(manifest['root']) / path).resolve()) for path in spec['constraints']]
    require(declared_constraints == [manifest['sdc']], 'ASIC SDC differs from declared measurement constraints')
    expected = {**request['source_hashes'], **contract['immutable_hashes']}
    require(all(manifest['input_hashes'].get(path) == value for path, value in request['source_hashes'].items()),
            'ASIC source manifest does not match candidate')
    require([file['path'] for file in manifest['files']] == contract['source_read_order'], 'ASIC source order mismatch')
    require(all(expected.get(path) == value for path, value in manifest['input_hashes'].items()),
            'ASIC inputs absent from frozen source/config manifest')
    for field, manifest_field in (('tool_version', 'tool_version_declared'), ('corner', 'library_corner_declared'),
                                  ('effort', 'effort')):
        require(spec[field] == manifest.get(manifest_field), f'ASIC {field} mismatch')
    require(result.get('time_units_verified') is True or result.get('library_time_units_verified') is True,
            'ASIC time units unverified')
    # A fresh unique ASIC run must be nested in the current invocation directory.
    # This prevents translation of retained, stale report directories.
    require(directory.is_relative_to(response_path.parent), 'ASIC run must be fresh in this invocation directory')
    reports = {}
    for filename, sha in result.get('report_hashes', {}).items():
        source = Path(filename).resolve()
        require(source.is_relative_to(directory), 'ASIC report escapes its run directory')
        require(hashes([source])[str(source)] == sha, 'ASIC report hash mismatch')
        reports[source.stem] = {'path': str(source), 'sha256': sha}
    require({'timing', 'area', 'constraint_audit'} <= set(reports), 'ASIC reports are incomplete')
    from .asic_synthesis import NUMBER, TIME_NS
    audit = Path(reports['constraint_audit']['path']).read_text().strip()
    match = re.fullmatch(r'PQC_PERIOD_NATIVE (' + NUMBER + ')', audit)
    require(match is not None and manifest.get('time_unit') in TIME_NS,
            'ASIC period audit is missing or malformed')
    actual_period = float(match[1]) * TIME_NS[manifest['time_unit']]
    require(math.isclose(actual_period, spec['period_ns'], rel_tol=1e-6), 'ASIC period audit mismatch')
    response = {'schema_version': 1, 'request_sha256': hashes([request_path])[str(request_path)],
                'status': 'MEASURED', 'scope': 'full_design', 'configuration': contract,
                'metrics': result['metrics'], 'area_unit': result['metrics'].get('area_unit'),
                'critical_paths': critical_paths, 'reports': reports,
                'asic_result': str(directory / 'result.json'), 'timing_signoff': False,
                'workload_power_validated': False}
    if profile is not None:
        admission = reports.get('admission_post_synth')
        require(admission is not None, 'Missing ASIC post-synthesis admission report')
        reports['structural'] = reports['memory'] = admission
        netlist = directory / 'netlist.v'
        require(netlist.is_file() and not netlist.is_symlink(), 'Missing fresh ASIC implementation netlist')
        reports['implementation_netlist'] = {'path': str(netlist), 'sha256': hashes([netlist])[str(netlist)]}
        # FF inventory does not prove initial state, read latency, or collision
        # semantics survived synthesis. A separate qualified mapped checker is
        # needed; the built-in ASIC runner explicitly reports this as false.
        response.update(memory_semantics_verified=result.get('memory_semantics_verified', False),
                        memory_semantics_scope=result.get('memory_semantics_scope'))
        response.update(target_profile_fingerprint=profile['profile_fingerprint'],
                        source_hashes=request['source_hashes'], source_read_order=contract['source_read_order'],
                        **{key: result[key] for key in ('admission_passed', 'admission_policy',
                           'structural_checks_verified', 'memory_implementation_verified', 'memory_implementation')})
    save(response_path, response)
    return response


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--execute', action='store_true', help='Run configured trusted adapters; may consume licenses/API budget')
    args = parser.parse_args(argv)
    if not args.execute:
        result = make_plan(args.config)
    else:
        try:
            result = Controller(load_config(args.config)).run()
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
            result = {'status': 'BLOCKED', 'error': str(error)}
    print(json.dumps(result, indent=2, allow_nan=False))
    return 1 if result['status'] == 'BLOCKED' else 0


if __name__ == '__main__':
    sys.exit(main())
