"""Opt-in local Claude vault. No credential reads, prompts or SDK calls on import.

Fernet authenticated encryption with a fixed, memory-hard Scrypt KDF. This is an
at-rest safeguard, not protection from a compromised account or host administrator.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
import argparse
import base64
import getpass
import json
import os
from pathlib import Path
import secrets
import stat
import sys
import warnings

APP = 'llm-aided-pqc'
FILENAME = 'claude-vault.json'
MAX_BYTES = 16384
_CACHE = None


class CredentialError(RuntimeError):
    """Safe, fixed diagnostic; never interpolate credential content."""


@dataclass(frozen=True)
class Credentials:
    api_key: str = field(repr=False)
    workspace_id: str = field(default='', repr=False)


def validate(api_key, workspace_id):
    if (not isinstance(api_key, str) or not 16 <= len(api_key) <= 4096
            or any(not 33 <= ord(c) <= 126 for c in api_key)):
        raise CredentialError('Invalid API key format; use the hidden setup prompt.')
    if (not isinstance(workspace_id, str) or len(workspace_id) > 128
            or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in workspace_id)):
        raise CredentialError('Invalid workspace ID; copy the ID from Console Settings > Workspaces.')
    return Credentials(api_key, workspace_id)


def vault_directory():
    base = os.environ.get('XDG_CONFIG_HOME') or str(Path.home() / '.config')
    path = Path(base) / APP
    if not path.is_absolute() or '..' in path.parts:
        raise CredentialError('XDG_CONFIG_HOME must be an absolute path without parent traversal.')
    repo = Path(__file__).resolve().parents[1]
    if path == repo or repo in path.parents or any((p / '.git').is_file() or (p / '.git' / 'HEAD').is_file() for p in (path, *path.parents)):
        raise CredentialError('Credential storage must be outside every Git checkout.')
    return path


@contextmanager
def private_directory(create=False):
    """Hold directory FDs while walking; never follow a symlink component."""
    if os.name != 'posix' or not hasattr(os, 'O_NOFOLLOW'):
        raise CredentialError('The local vault requires POSIX no-follow file permissions.')
    path = vault_directory()
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for index, name in enumerate(path.parts[1:]):
            final = index == len(path.parts) - 2
            if create:
                try:
                    os.mkdir(name, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
            info = os.fstat(fd)
            mode = stat.S_IMODE(info.st_mode)
            if final:
                if info.st_uid != os.getuid() or mode != 0o700:
                    raise CredentialError('Vault directory must be owned by you with mode 0700.')
            elif info.st_uid not in (0, os.getuid()) or (mode & 0o022 and not (info.st_uid == 0 and mode & stat.S_ISVTX)):
                raise CredentialError('Unsafe owner or writable parent directory in vault path.')
        yield fd
    except OSError:
        raise CredentialError('Vault unavailable or unsafe; check its path, ownership and permissions.') from None
    finally:
        os.close(fd)


def _read(fd):
    file_fd = os.open(FILENAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    with os.fdopen(file_fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1 or info.st_size > MAX_BYTES):
            raise CredentialError('Vault must be a private, single-link, owner-only regular file (0600).')
        data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise CredentialError('Vault is too large.')
        return data


def _fernet(passphrase, salt):
    # Parameters are fixed, never trusted from a file (no attacker-controlled KDF work).
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    key = Scrypt(salt=salt, length=32, n=2**17, r=8, p=1).derive(passphrase.encode('utf-8'))
    return Fernet(base64.urlsafe_b64encode(key))


def _decrypt(data, passphrase):
    from cryptography.fernet import InvalidToken
    try:
        envelope = json.loads(data)
        if envelope.get('version') != 1 or envelope.get('kdf') != 'scrypt-n131072-r8-p1':
            raise ValueError()
        salt = base64.b64decode(envelope['salt'], validate=True)
        if len(salt) != 16 or not isinstance(envelope['token'], str):
            raise ValueError()
        payload = json.loads(_fernet(passphrase, salt).decrypt(envelope['token'].encode('ascii')))
        return validate(payload['api_key'], payload['workspace_id'])
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError, InvalidToken):
        raise CredentialError('Cannot unlock vault: incorrect passphrase or damaged/unsupported vault.') from None


def hidden_input(prompt):
    # getpass normally falls back to echoing stdin on some hosts. Never allow it.
    try:
        with open('/dev/tty', 'w') as tty, warnings.catch_warnings():
            if not tty.isatty():
                raise CredentialError('An interactive terminal is required; secrets cannot come from stdin.')
            warnings.simplefilter('error', getpass.GetPassWarning)
            return getpass.getpass(prompt, stream=tty)
    except (OSError, EOFError, getpass.GetPassWarning):
        raise CredentialError('An echo-free interactive terminal is required; use SSH with a terminal.') from None


def setup(replace=False):
    """Only an explicit user CLI invocation calls this. Never transmits credentials."""
    global _CACHE
    with private_directory(create=True) as fd:
        try:
            existing = _read(fd)
        except FileNotFoundError:
            existing = None
        if existing is not None:
            if not replace:
                raise CredentialError('Vault already exists; use setup --replace to unlock and replace it.')
            _decrypt(existing, hidden_input('Current vault passphrase: '))
        elif replace:
            raise CredentialError('No existing vault to replace; use setup without --replace.')
        credentials = validate(hidden_input('Claude API key (hidden): '),
                               hidden_input('Workspace ID (hidden; blank only for a workspace-scoped key): '))
        passphrase = hidden_input('New vault passphrase (at least 14 characters): ')
        if len(passphrase) < 14 or len(passphrase) > 1024:
            raise CredentialError('Use a strong unique vault passphrase of 14 to 1024 characters.')
        if passphrase != hidden_input('Confirm vault passphrase: '):
            raise CredentialError('Passphrases do not match; nothing was saved.')
        salt = secrets.token_bytes(16)
        payload = json.dumps({'api_key': credentials.api_key, 'workspace_id': credentials.workspace_id}).encode()
        token = _fernet(passphrase, salt).encrypt(payload).decode('ascii')
        data = json.dumps({'version': 1, 'kdf': 'scrypt-n131072-r8-p1',
                           'salt': base64.b64encode(salt).decode('ascii'), 'token': token}).encode() + b'\n'
        name = '.claude-vault-' + secrets.token_hex(16)
        temp_fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
        os.fchmod(temp_fd, 0o600)
        try:
            with os.fdopen(temp_fd, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if existing is None:
                # Atomic no-clobber installation, including racing setup processes.
                os.link(name, FILENAME, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
            else:
                if _read(fd) != existing:
                    raise CredentialError('Vault changed while prompting; replacement refused.')
                os.replace(name, FILENAME, src_dir_fd=fd, dst_dir_fd=fd)
            os.fsync(fd)
        finally:
            try:
                os.unlink(name, dir_fd=fd)
            except FileNotFoundError:
                pass
        _CACHE = None


def load_credentials():
    """Unlock once in this Python process; never export secrets to child environments."""
    global _CACHE
    source = os.environ.get('PQC_CLAUDE_AUTH', 'vault')
    if source == 'env':
        return validate(os.environ.get('ANTHROPIC_API_KEY', ''), os.environ.get('ANTHROPIC_WORKSPACE_ID', ''))
    if source != 'vault':
        raise CredentialError('PQC_CLAUDE_AUTH must be vault or env.')
    if os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_WORKSPACE_ID'):
        raise CredentialError('Unset legacy key/workspace environment variables before using the vault, or explicitly select PQC_CLAUDE_AUTH=env.')
    path = vault_directory()
    if _CACHE is not None and _CACHE[0] == path and _CACHE[1] == os.getpid():
        return _CACHE[2]
    with private_directory() as fd:
        data = _read(fd)
    result = _decrypt(data, hidden_input('Unlock Claude vault: '))
    _CACHE = (path, os.getpid(), result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description='Store Claude credentials encrypted outside the checkout; no API calls.')
    sub = parser.add_subparsers(dest='command', required=True)
    command = sub.add_parser('setup', help='Hidden interactive prompts; encrypt and save locally.')
    command.add_argument('--replace', action='store_true', help='Unlock the existing vault before replacing it.')
    sub.add_parser('status', help='Check file safety only; does not unlock or validate with Claude.')
    args = parser.parse_args(argv)
    try:
        if args.command == 'setup':
            setup(replace=args.replace)
            print('Encrypted Claude vault saved locally. No API request was made.')
        else:
            with private_directory() as fd:
                _read(fd)
            print('Private vault file present. Unlock and API validity have not been checked.')
        return 0
    except CredentialError as exc:
        print('BLOCKED: ' + str(exc), file=sys.stderr)
        return 2
    except (OSError, ImportError, KeyboardInterrupt):
        # No traceback, arbitrary exception payload, path or secret is printed.
        print('BLOCKED: credential setup/status failed. Check terminal access, passphrase, optional llm dependencies, and private vault permissions; see docs/CLAUDE_CREDENTIALS.md.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
