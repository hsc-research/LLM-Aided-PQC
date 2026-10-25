"""Separate block-filter observations from durable, whole-design acceptance.

The chip driver owns final outcomes. A block runner may report a preliminary
win, but cannot turn it into an applied-edit claim or a qualified learned rule.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

try:
    from .run_safety import hashes
except ImportError:
    from run_safety import hashes

HISTORY = Path(__file__).resolve().parent / 'chip_orchestrator_log.jsonl'
PARENT_ID_ENV = 'PQC_PARENT_RUN_ID'
FILTER_MARKER = 'PQC_BLOCK_FILTER_PASS '


def preliminary_record(record, design, model):
    """Tag a local win and emit a parent-readable record, without learning."""
    value = dict(record, verdict='BLOCK_FILTER_PASS', evidence_stage='block_filter',
                 design=design, source_model=model,
                 candidate_id=os.environ.get(PARENT_ID_ENV))
    if value['candidate_id']:
        print(FILTER_MARKER + json.dumps(value, allow_nan=False))
    return value


def parse_preliminary(output, candidate_id):
    rows = [line[len(FILTER_MARKER):] for line in output.splitlines()
            if line.startswith(FILTER_MARKER)]
    if len(rows) != 1:
        raise ValueError('Expected exactly one structured block-filter record')
    value = json.loads(rows[0])
    if (not isinstance(value, dict) or value.get('candidate_id') != candidate_id
            or value.get('verdict') != 'BLOCK_FILTER_PASS'
            or value.get('evidence_stage') != 'block_filter'
            or not isinstance(value.get('strategy'), str)
            or not isinstance(value.get('edits'), list) or not value['edits']):
        raise ValueError('Invalid or mismatched block-filter record')
    return value


def is_final_acceptance(record):
    return (isinstance(record, dict) and record.get('history_schema') == 1
            and record.get('history_state') == 'finally_accepted'
            and record.get('evidence_stage') == 'full_design'
            and record.get('correctness_status') == 'PASS'
            and record.get('verdict') == 'ACCEPT'
            and isinstance(record.get('candidate_id'), str)
            and bool(record.get('candidate_id'))
            and isinstance(record.get('candidate_sources'), dict)
            and bool(record.get('candidate_sources'))
            and isinstance(record.get('proposal'), dict))


def latest_records(path=None):
    """Last event per candidate wins; legacy rows never imply final acceptance."""
    path = Path(path) if path is not None else HISTORY
    if not path.is_file():
        return []
    latest = {}
    for line in path.read_text().splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue  # An interrupted trailing write cannot become evidence.
        if (isinstance(record, dict) and record.get('history_schema') == 1
                and isinstance(record.get('candidate_id'), str)):
            latest[record['candidate_id']] = record
    return list(latest.values())


def sources_match(state):
    """Require current bytes for every captured source and include file."""
    if not isinstance(state, dict) or not state:
        return False
    source_values, include_values = state.get('sources', state), state.get('includes', {})
    if not isinstance(source_values, dict) or not isinstance(include_values, dict):
        return False
    values = dict(source_values)
    values.update(include_values)
    if not values or any(not isinstance(value, str) for value in values.values()):
        return False
    try:
        return hashes(values) == values
    except (OSError, RuntimeError):
        return False


def target_context_matches(record, target_profile_fingerprint=None, configuration_sha256=None):
    """Target-bound outcomes are never reusable without their exact context."""
    bound = record.get('target_profile_fingerprint')
    if bound is None:
        return target_profile_fingerprint is None and configuration_sha256 is None
    return (bound == target_profile_fingerprint and
            isinstance(configuration_sha256, str) and
            record.get('configuration_sha256') == configuration_sha256)


def applied_proposals(design, block, path=None, *, target_profile_fingerprint=None, configuration_sha256=None):
    result = []
    for record in latest_records(path):
        proposal = record.get('proposal', {})
        if (target_context_matches(record, target_profile_fingerprint, configuration_sha256)
                and is_final_acceptance(record) and proposal.get('design') == design
                and proposal.get('block', proposal.get('module')) == block
                and sources_match(record['candidate_sources'])):
            result.append(proposal)
    return result


def history_prompt(design, block, path=None, limit=5, *, target_profile_fingerprint=None, configuration_sha256=None):
    """Final outcomes are diagnostic context, never a blanket strategy ban."""
    rows = []
    for record in latest_records(path):
        proposal = record.get('proposal', {})
        if (not target_context_matches(record, target_profile_fingerprint, configuration_sha256)
                or not isinstance(proposal, dict) or proposal.get('design') != design
                or proposal.get('block', proposal.get('module')) != block
                or record.get('history_state') not in ('finally_accepted', 'chip_rejected')):
            continue
        rows.append({'candidate_id': record['candidate_id'],
                     'outcome': record.get('verdict'),
                     'strategy': proposal.get('strategy'),
                     'currently_applied': is_final_acceptance(record)
                     and sources_match(record.get('candidate_sources'))})
    if not rows:
        return ''
    return ('\nWHOLE-DESIGN OUTCOMES (diagnostic evidence; a local filter pass is '
            'not final acceptance, and a failed edit does not ban its strategy):\n'
            + json.dumps(rows[-limit:]))
