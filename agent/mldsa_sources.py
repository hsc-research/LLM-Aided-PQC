"""Pinned ML-DSA input discovery and byte integrity; never invokes EDA tools."""
import hashlib
import json
import os
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
BUNDLED_ROOT = REPO / 'third_party/mldsa_osh/upstream'
COMMIT = '751009199ac081091a9059805e6921453bde0154'
MANIFEST_SHA256 = '8d06b13068061b7a5c27c7a882813da2480977b09a306d45da49b5b225b1c5d2'


def source_root():
    return Path(os.environ.get('MLDSA_ROOT') or BUNDLED_ROOT).expanduser().resolve()


def missing_inputs(root):
    root = Path(root)
    required = ['ref_combined/src/combined_top.v', 'ref_combined/src/keccak_top.vhd',
                'ref_combined/src_tb/tb_keygen_top.v', 'common/mldsa_params.v', 'common/zetas.txt']
    required += [f'KAT/KeyGen_{part}_{level}.txt'
                 for level in (44, 65, 87) for part in ('seed', 'pk', 'sk')]
    return [str(root / path) for path in required if not (root / path).is_file()]


def verify_snapshot(root=BUNDLED_ROOT):
    """Verify the pinned files and vector shape, not cryptographic correctness."""
    root = Path(root).resolve()
    raw = (root / 'SOURCE_MANIFEST.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError('ML-DSA source manifest differs from the reviewed pin')
    manifest = json.loads(raw)
    if manifest['commit'] != COMMIT or len(manifest['files']) != 106:
        raise ValueError('Unexpected ML-DSA source pin or file count')
    expected = set()
    for item in manifest['files']:
        relative = Path(item['path'])
        path = root / relative
        if relative.is_absolute() or '..' in relative.parts or relative.as_posix() in expected or path.is_symlink():
            raise ValueError('Unsafe or duplicate source-manifest path')
        expected.add(relative.as_posix())
        data = path.read_bytes()
        blob = b'blob ' + str(len(data)).encode() + b'\0' + data
        if (len(data) != item['size'] or hashlib.sha1(blob).hexdigest() != item['sha']
                or hashlib.sha256(data).hexdigest() != item['sha256']):
            raise ValueError('ML-DSA upstream blob mismatch: ' + item['path'])
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != expected | {'SOURCE_MANIFEST.json'}:
        raise ValueError('Unexpected or missing files in ML-DSA source snapshot')
    if missing_inputs(root):
        raise ValueError('Missing ML-DSA KeyGen inputs')
    for level, pk_bytes, sk_bytes in ((44, 1312, 2560), (65, 1952, 4032), (87, 2592, 4896)):
        for kind, size in (('seed', 32), ('pk', pk_bytes), ('sk', sk_bytes)):
            lines = (root / f'KAT/KeyGen_{kind}_{level}.txt').read_text().splitlines()
            if len(lines) != 25 or any(not re.fullmatch(r'[0-9A-Fa-f]{' + str(size * 2) + '}', x) for x in lines):
                raise ValueError(f'Unexpected KeyGen vector shape: {kind}/{level}')
    return {'source_integrity': 'PASS', 'commit': COMMIT, 'files': len(expected),
            'bytes': sum(item['size'] for item in manifest['files']), 'keygen_cases_present': 75,
            'qualification': 'NOT RUN: RTL compilation/simulation, Sign/Verify, FIPS certification, or PPA'}
