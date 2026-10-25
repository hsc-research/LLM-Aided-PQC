"""Bounded, read-only source excerpts for a proposal, never an edit allowlist.

These are literal source bytes and profile metadata, not an HDL elaborator or a
proof that a reported timing cell belongs to a source line.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import re

MAX_CONTEXT_SELECTIONS = 64
MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_CONTEXT_SOURCE_BYTES = 16 * 1024 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read_only_sources(selections, source_hashes, editable):
    """PATH or PATH:START:END; line numbers are one-based and inclusive.

    Parse from the right and reject colons in the remaining path to avoid
    ambiguously treating a malformed range as a filename. All file bytes are
    hash-checked, including bytes outside the selected spans. No truncation.
    """
    require(len(selections) <= MAX_CONTEXT_SELECTIONS, 'At most 64 read-only source selections')
    cache, spans, result = {}, {}, []
    total = 0
    for spec in selections:
        require(isinstance(spec, str) and bool(spec), 'Read-only source selection must be a path')
        if ':' in spec:
            require(not Path(spec).exists() and not Path(spec).is_symlink(),
                    'Colon-containing source paths are unsupported and ambiguous with line ranges')
        match = re.fullmatch(r'(.+):([1-9][0-9]{0,8}):([1-9][0-9]{0,8})', spec)
        name = match[1] if match else spec
        require(':' not in name, 'Use an unambiguous PATH or PATH:START:END with positive line numbers')
        path = Path(name)
        require(not path.is_symlink(), 'Read-only source must not be a symlink')
        name = str(path.resolve())
        require(name in source_hashes, 'Read-only RTL is outside the exact exported source list')
        require(name not in editable, 'A source cannot be both read-only context and editable RTL')
        if name not in cache:
            with Path(name).open('rb') as stream:
                data = stream.read(MAX_SOURCE_BYTES + 1)
            require(len(data) <= MAX_SOURCE_BYTES, 'Read-only source exceeds the 4 MiB scan limit')
            total += len(data)
            require(total <= MAX_CONTEXT_SOURCE_BYTES, 'Read-only sources exceed the 16 MiB scan limit')
            require(hashlib.sha256(data).hexdigest() == source_hashes[name], 'Read-only source hash differs from the exact profile')
            # readlines splits on LF only, preserving exact CRLF/LF source bytes.
            lines = io.BytesIO(data).readlines()
            require(bool(lines), 'Read-only source is empty')
            data.decode('utf-8')  # Fail rather than repair undecodable source.
            cache[name] = (data, lines)
        data, lines = cache[name]
        start, end = (int(match[2]), int(match[3])) if match else (1, len(lines))
        require(1 <= start <= end <= len(lines), 'Read-only source range is reversed or outside the file')
        require(all(end < a or start > b for a, b in spans.get(name, [])), 'Duplicate or overlapping read-only source ranges')
        spans.setdefault(name, []).append((start, end))
        raw = b''.join(lines[start - 1:end])
        partial = start != 1 or end != len(lines)
        result.append({'path': name, 'role': 'READ_ONLY_CONTEXT_NOT_EDITABLE',
                       'source_sha256': source_hashes[name], 'source_bytes': len(data),
                       'source_line_count': len(lines), 'start_line': start, 'end_line': end,
                       'text_sha256': hashlib.sha256(raw).hexdigest(), 'text_bytes': len(raw),
                       'coverage': 'PARTIAL_SOURCE_EXCERPT' if partial else 'FULL_SOURCE',
                       'omitted_before_lines': start - 1, 'omitted_after_lines': len(lines) - end,
                       'omission_note': 'Lines outside this span are omitted, not assumed irrelevant.' if partial else 'No lines omitted.',
                       'text': raw.decode('utf-8')})
    return result


def design_overview(profile, source_hashes, editable, context_rows):
    """Keep source order and roles explicit; do not infer a hierarchy graph."""
    elab = profile['elaboration']
    context_files = {row['path'] for row in context_rows}
    return {
        'evidence': 'Frozen exported profile and hash-bound literal source text; not elaborated hierarchy or timing-path ownership proof.',
        'top': elab['top'], 'profile_fingerprint': profile['profile_fingerprint'],
        'parameters': elab.get('parameters', {}), 'defines': elab.get('defines', []),
        'global_include_files': elab.get('global_include_files', []),
        'include_dirs': elab.get('include_dirs', []),
        'ordered_sources': [
            {'path': path, 'sha256': digest,
             'text_role': ('EDITABLE_FULL_SOURCE' if path in editable else
                           'READ_ONLY_SELECTED_CONTEXT' if path in context_files else 'TEXT_NOT_INCLUDED')}
            for path, digest in source_hashes.items()],
        'hierarchy_scope': 'Use provided top-level interfaces/instantiations as partial source evidence. Unprovided source text and unelaborated generate branches remain unknown.',
        'analysis_order': [
            'Start at the declared top and provided top-level interface/instantiation context; identify cross-module control, data and handshake dependencies.',
            'Then trace the reported worst whole-design paths through the provided source context; do not infer source ownership from similar names alone.',
            'Only then consider an exact edit in allowed_files. Context visibility never grants edit permission; prefer STOP when essential evidence is missing.'],
        'measurement_scope': 'Imported post-synthesis reports, not routed timing or placement evidence. Model commentary cannot set timing requirements or override the frozen period and constraints.'}
