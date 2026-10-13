"""Source-linked working knowledge, not an elaborator or model training.

Facts here are lexical source observations. Synthesized ownership can only come
from independently bound implementation evidence. LLM statements stay hypotheses.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import re

from .whole_design import require, digest

MAX_SOURCE = 4 * 1024 * 1024
MAX_TOTAL = 16 * 1024 * 1024


def model(sources, top, profile_fingerprint):
    rows, total, declarations = [], 0, {}
    for name, expected in sources.items():
        path = Path(name)
        require(not path.is_symlink(), 'Symlinked design source')
        raw = path.read_bytes()
        total += len(raw)
        require(len(raw) <= MAX_SOURCE and total <= MAX_TOTAL, 'Design scan byte limit exceeded')
        require(hashlib.sha256(raw).hexdigest() == expected, 'Design source changed during scan')
        text = raw.decode('utf-8')
        # Blank comments while preserving offsets/lines. Strings remain unknown.
        clean = re.sub(r'/\*.*?\*/|//[^\n]*', lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), text, flags=re.S)
        modules = []
        for match in re.finditer(r'\bmodule\s+([A-Za-z_]\w*)\b', clean):
            end = clean.find('endmodule', match.end())
            require(end >= 0, 'Unterminated module declaration')
            header_end = clean.find(';', match.end(), end)
            require(header_end >= 0, 'Missing module header')
            begin_line = text.count('\n', 0, match.start()) + 1
            stop_line = text.count('\n', 0, end) + 1
            header = text[match.start():header_end + 1]
            require(len(header.encode()) <= 16384, 'Module interface excerpt too large')
            item = {'name': match[1], 'line_start': begin_line, 'line_end': stop_line,
                    'header': header, 'confidence': 'literal_source_declaration',
                    'sha256': expected, 'path': name}
            modules.append(item)
            declarations.setdefault(match[1], []).append({'path': name, 'line': begin_line, 'sha256': expected})
        rows.append({'path': name, 'sha256': expected, 'bytes': len(raw),
                     'lines': text.count('\n') + bool(text and not text.endswith('\n')),
                     'modules': modules, '_clean': clean, '_text': text})
    edges = []
    # Conservative lexical candidates only: parameters/generate/conditionals are
    # not elaborated. Every candidate includes its literal source line.
    for row in rows:
        for match in re.finditer(r'^\s*([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*\(', row['_clean'], re.M):
            if match[1] not in declarations:
                continue
            line = row['_text'].count('\n', 0, match.start(1)) + 1
            edges.append({'module_type': match[1], 'instance': match[2], 'path': row['path'],
                          'line': line, 'sha256': row['sha256'],
                          'confidence': 'lexical_candidate_not_elaborated',
                          'possible_definitions': declarations[match[1]]})
        del row['_clean'], row['_text']
    return {'schema_version': 1, 'profile_fingerprint': profile_fingerprint,
            'source_state_sha256': digest(sources), 'top': top, 'sources': rows,
            'instantiation_candidates': edges,
            'unknowns': ['Parameterized/generate hierarchy is not elaborated by this lexical scan.',
                         'Timing-cell ownership requires synthesis provenance, not similar names.',
                         'PQC algorithm roles and handshake semantics require cited source analysis.'],
            'training_performed': False, 'model_claims_are_evidence': False}


def excerpts(selections, sources, max_bytes):
    result, total = [], 0
    require(isinstance(selections, list) and len(selections) <= 16, 'At most 16 requested source excerpts')
    seen = set()
    for selection in selections:
        require(isinstance(selection, dict) and set(selection) == {'path', 'line_start', 'line_end'}, 'Invalid context request')
        name = selection['path']
        require(name in sources, 'Requested context outside frozen source manifest')
        a, b = selection['line_start'], selection['line_end']
        require(type(a) is int and type(b) is int and 1 <= a <= b and b - a < 400,
                'Context span must contain 1..400 lines')
        require((name, a, b) not in seen, 'Duplicate context request')
        seen.add((name, a, b))
        raw = Path(name).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == sources[name], 'Context source changed')
        lines = raw.splitlines(keepends=True)
        require(b <= len(lines), 'Context span escapes source')
        content = b''.join(lines[a-1:b])
        total += len(content)
        require(total <= max_bytes, 'Requested context exceeds byte budget')
        result.append({**selection, 'source_sha256': sources[name], 'text_sha256': hashlib.sha256(content).hexdigest(),
                       'text': content.decode('utf-8'), 'role': 'read_only_not_edit_permission'})
    return result
