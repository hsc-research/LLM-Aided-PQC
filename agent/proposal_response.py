"""Bounded, deterministic decoding of one review-only model proposal.

Presentation wrappers never authorize edits. Rationale prose is retained only in
raw response evidence; it is not a measured result or a source of instructions.
"""
import hashlib
import json
import re

LIMIT = 192 * 1024
RATIONALE_LIMIT = 32 * 1024
MAX_DEPTH = 64
PARSER_VERSION = 'single-proposal-v1'


class ResponseFormatError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__('Response format rejected: ' + code + '; original response preserved.')


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ResponseFormatError('duplicate_json_key')
        result[key] = value
    return result


def _constant(_value):
    raise ResponseFormatError('non_finite_json_number')


def _check_depth(text):
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '{[':
            depth += 1
            if depth > MAX_DEPTH:
                raise ResponseFormatError('json_too_deep')
        elif char in '}]':
            depth -= 1


def decode_response(raw):
    """Accept one object, optionally one JSON fence with labeled plain rationale.

    No substring hunting, first-object selection or malformed-JSON repair. Numeric identifier-attached RTL selectors in rationale are allowed. Other
    structural braces/brackets or fences are refused rather than silently
    discarding a competing answer or code payload.
    """
    if not isinstance(raw, str):
        raise ResponseFormatError('response_too_large_or_not_text')
    try:
        size = len(raw.encode('utf-8'))
    except UnicodeError:
        raise ResponseFormatError('invalid_unicode') from None
    if size > LIMIT:
        raise ResponseFormatError('response_too_large_or_not_text')
    text = raw.strip()
    envelope = 'plain_json'
    rationale = ''
    if text.startswith('```'):
        match = re.fullmatch(r'```(?:json)?[ \t]*\r?\n(.*?)\r?\n```[ \t]*(.*)', text, flags=re.DOTALL)
        if not match:
            raise ResponseFormatError('invalid_json_fence')
        text, trailer = match.groups()
        if '```' in trailer or '~~~' in trailer:
            raise ResponseFormatError('multiple_or_ambiguous_fences')
        trailer = trailer.strip()
        if trailer:
            heading = re.fullmatch(r'(?:\*\*Rationale:\*\*|Rationale:)[ \t]*(.*)', trailer, flags=re.DOTALL)
            if not heading:
                raise ResponseFormatError('unlabeled_trailing_content')
            rationale = heading.group(1).strip()
            # Preserve technical prose such as `PISO[102]/D` and
            # `genblk1[2].KECCAK`; do not mask arbitrary inline code or arrays.
            prose = re.sub(r'(?<![A-Za-z0-9_$])([A-Za-z_$][A-Za-z0-9_$]*)(?:\[[0-9]+(?::[0-9]+)?\])+', r'\1', rationale)
            if (not rationale or len(rationale.encode('utf-8')) > RATIONALE_LIMIT
                    or any(char in prose for char in '{}[]')):
                raise ResponseFormatError('ambiguous_or_oversized_rationale')
            for line in rationale.splitlines():
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except (ValueError, RecursionError):
                    pass
                else:
                    raise ResponseFormatError('ambiguous_rationale_value')
        envelope = 'fenced_json'
    _check_depth(text)
    try:
        proposal = json.loads(text, object_pairs_hook=_object, parse_constant=_constant)
    except ResponseFormatError:
        raise
    except (ValueError, TypeError, RecursionError):
        raise ResponseFormatError('invalid_or_multiple_json_values') from None
    if not isinstance(proposal, dict):
        raise ResponseFormatError('json_root_must_be_object')
    try:
        canonical = json.dumps(proposal, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, UnicodeError, RecursionError):
        raise ResponseFormatError('invalid_json_value') from None
    return proposal, {
        'parser_version': PARSER_VERSION, 'envelope': envelope,
        'proposal_sha256': hashlib.sha256(canonical).hexdigest(),
        'untrusted_rationale_present': bool(rationale),
        'untrusted_rationale_bytes': len(rationale.encode('utf-8')),
        'untrusted_rationale_sha256': hashlib.sha256(rationale.encode('utf-8')).hexdigest() if rationale else None,
        'rationale_note': 'Model-authored rationale is unverified commentary, never measured evidence or edit authorization.',
    }
