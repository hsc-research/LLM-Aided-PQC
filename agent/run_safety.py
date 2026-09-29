"""Standard-library transaction helpers for cooperating Linux EDA workflows.

Not a security sandbox. A transaction restores its pre-run working state,
including uncommitted files, rather than checking out Git HEAD.
"""
from __future__ import annotations
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile


def hashes(paths):
    result = {}
    for path in sorted({Path(p).resolve() for p in paths}):
        if not path.is_file():
            raise RuntimeError(f"Missing input: {path}")
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1048576), b''):
                digest.update(chunk)
        result[str(path)] = digest.hexdigest()
    return result


class RunLock:
    def __init__(self, root):
        self.path = Path(root) / '.pqc-run.lock'

    def __enter__(self):
        self.stream = self.path.open('a+')
        try:
            fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.stream.close()
            raise RuntimeError('Another top-level run holds this checkout lock')
        return self

    def __exit__(self, *exc):
        self.stream.close()


class SourceTransaction:
    """Snapshot explicit checkout scopes; restore every scope unless accepted.

    New files within a scoped directory are removed on rollback. Backups
    remain under .pqc_runs/transactions if rollback fails or execution is killed.
    """
    def __init__(self, root, scopes):
        self.root = Path(root).resolve()
        self.scopes = []
        for value in scopes:
            original = self.root / value
            path = original.resolve()
            if not path.is_relative_to(self.root) or path == self.root:
                raise ValueError(f'Unsafe transaction scope: {value}')
            if any(p.is_symlink() for p in [original, *original.parents]):
                raise ValueError(f'Symlinked transaction scope: {value}')
            if any(path == p or path.is_relative_to(p) or p.is_relative_to(path) for p in self.scopes):
                raise ValueError('Transaction scopes must be disjoint')
            self.scopes.append(path)
        self.accepted = False

    def __enter__(self):
        # Validate all scopes before creating a partial backup.
        for path in self.scopes:
            if path.is_dir() and any(p.is_symlink() for p in path.rglob('*')):
                raise ValueError(f'Symlink inside scope: {path}')
        journal = self.root / '.pqc_runs/transactions'
        journal.mkdir(parents=True, exist_ok=True)
        self.backup = Path(tempfile.mkdtemp(prefix='candidate-', dir=journal))
        self.entries = []
        for i, path in enumerate(self.scopes):
            kind = 'directory' if path.is_dir() else 'file' if path.exists() else 'absent'
            if kind == 'directory':
                shutil.copytree(path, self.backup / str(i))
            elif kind == 'file':
                shutil.copy2(path, self.backup / str(i))
            self.entries.append({'path': str(path.relative_to(self.root)), 'kind': kind, 'backup': str(i)})
        (self.backup / 'manifest.json').write_text(json.dumps(self.entries, indent=2))
        return self

    def accept(self):
        self.accepted = True

    def rollback(self):
        for entry in self.entries:
            path = self.root / entry['path']
            if any(p.is_symlink() for p in path.parents):
                raise RuntimeError(f'Parent path changed; manual recovery required: {self.backup}')
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.exists():
                shutil.rmtree(path)
            if entry['kind'] != 'absent':
                path.parent.mkdir(parents=True, exist_ok=True)
                source = self.backup / entry['backup']
                if entry['kind'] == 'directory':
                    shutil.copytree(source, path)
                else:
                    shutil.copy2(source, path)

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None or not self.accepted:
            self.rollback()
        shutil.rmtree(self.backup)


def _kill_tree(pid):
    # Legacy nested runners sometimes create their own sessions. Include
    # descendants found in /proc, then kill the root process group as well.
    parents = {}
    for stat in Path('/proc').glob('[0-9]*/stat'):
        try:
            fields = stat.read_text().rsplit(')', 1)[1].split()
            parents[int(stat.parent.name)] = int(fields[1])
        except (OSError, ValueError, IndexError):
            continue
    descendants, frontier = [], [pid]
    while frontier:
        next_level = [p for p, parent in parents.items() if parent in frontier and p not in descendants]
        descendants.extend(next_level)
        frontier = next_level
    for target in reversed(descendants):
        try:
            os.kill(target, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_process(argv, *, cwd=None, timeout=86400, env=None, log_path=None):
    stream = Path(log_path).open('w') if log_path else None
    try:
        process = subprocess.Popen(argv, cwd=cwd, env=env, text=True,
                                   stdout=stream or subprocess.PIPE, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            output, _ = process.communicate(timeout=timeout)
        except BaseException:
            _kill_tree(process.pid)
            process.communicate()
            raise
    finally:
        if stream:
            stream.close()
    if log_path:
        output = Path(log_path).read_text(errors='replace')
    return subprocess.CompletedProcess(argv, process.returncode, output, '')


def gate_passed(result):
    text = result.stdout or ''
    failed = re.search(r'"status"\s*:\s*"(?:FAIL|ERROR|INCONCLUSIVE)"|GATE:\s*(?:FAIL|ERROR|INCONCLUSIVE)', text)
    passed = re.search(r'"status"\s*:\s*"PASS"|GATE:\s*PASS\b', text)
    return result.returncode == 0 and bool(passed) and not failed


def proposal_accepted(result):
    return result.returncode == 0 and bool(re.search(
        r'^\s*(?:===\s*)?ACCEPTED(?:[. (:]|$)', result.stdout or '', re.M))


def stage_sources(sources, destination):
    """Copy an explicit manifest without silently substituting pristine RTL."""
    destination = Path(destination).resolve()
    chosen = {}
    for value in sources:
        path = Path(value).resolve()
        if not path.is_file():
            raise RuntimeError(f'Missing selected source: {path}')
        if path.name in chosen and chosen[path.name] != path:
            raise ValueError(f'Ambiguous source basename: {path.name}')
        chosen[path.name] = path
    before = hashes(chosen.values())
    destination.mkdir(parents=True, exist_ok=True)
    for name, source in chosen.items():
        target = destination / name
        if target.is_symlink():
            raise ValueError(f'Symlinked staged source: {target}')
        if source != target:
            shutil.copy2(source, target)
        if hashes([target])[str(target)] != before[str(source)]:
            raise RuntimeError(f'Staging changed source bytes: {target}')
    return {name: before[str(source)] for name, source in chosen.items()}
