# Local encrypted Claude credentials

[Project home](../README.md) · [FPGA proposal workflow](FPGA_AGENT_FEEDBACK.md) · [Security limits](../SECURITY.md)

## Save the key once, unlock when you run

The foreground FPGA proposal runner can load a locally encrypted API key and
workspace ID. Enter the key once at setup; later Python processes ask for your
vault passphrase. Within one Python process the unlocked credentials are cached
in memory. This is not passwordless access or a background unlock agent.

Run setup **yourself in a trusted interactive terminal**, including an SSH session
with a terminal. Do not send the key or passphrase in chat, paste them into a
command, put them in `.env`, or add them to scripts. Installation and setup do not
contact Claude, test authentication, generate a proposal, or incur API charges:

```sh
python3 -m pip install -e '.[llm]'
python3 -m agent.claude_credentials setup
```

The hidden prompts ask for:

1. Your Claude API key.
2. Your workspace ID, from Claude Console **Settings > Workspaces**. Supply this
   for a key that is not scoped to a workspace. Only leave it blank if you know
   the key is already workspace-scoped. The key type is not inferred from its text.
3. A strong, unique vault passphrase, then confirmation. Prefer several randomly
   selected words; at least 14 characters are required. Keep it in a trusted
   password manager. There is no passphrase recovery feature.

The stored workspace ID is sent as `anthropic-workspace-id` on **both** the
count-tokens request and the generation request. See the provider's
[authentication and workspace documentation](https://platform.claude.com/docs/en/manage-claude/authentication).
A workspace ID does not grant access: the key must already be authorized for it.
Expired keys, incorrect IDs, access restrictions and billing limits still require
resolution in the Console.

Check local file presence and permissions without unlocking or contacting Claude:

```sh
python3 -m agent.claude_credentials status
```

To change the key, workspace ID or passphrase, unlock the existing vault and
explicitly replace it:

```sh
python3 -m agent.claude_credentials setup --replace
```

Replacement is atomic. Failures before atomic replacement leave the old vault
intact; a failure after replacement (such as a directory-sync error) can mean the
new file is already installed. Check local status and unlock before repeating. Restart any previously unlocked process to use the new credentials. This
command does not create, revoke, rotate or alter an API key at the provider.

## Run one approved foreground proposal

The vault is the default source. If you previously exported a key or workspace
ID, remove those variables from this shell before using the vault:

```sh
unset ANTHROPIC_API_KEY ANTHROPIC_WORKSPACE_ID ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL ANTHROPIC_LOG ANTHROPIC_CUSTOM_HEADERS
unset PQC_CLAUDE_AUTH
```

Then use the [single-proposal command](FPGA_AGENT_FEEDBACK.md#optional-single-claude-request)
with your explicitly approved model, input/output prices and budget. It will
prompt `Unlock Claude vault:` with echo disabled. No secret appears in the
command line or is exported from the vault into child-process environment
variables. Setup does not authorize a paid run: `PQC_ENABLE_LLM=1` and the runner's
other explicit cost/data checks remain required.

The client uses the official HTTPS endpoint, a 120-second timeout, no SDK retry,
no redirects, and no environment-proxy/custom certificate configuration.
`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_CUSTOM_HEADERS` and
`ANTHROPIC_LOG` are rejected, rather
than silently redirecting credentials or enabling verbose logs. Sites requiring
a corporate proxy/custom CA need a separately reviewed integration. Provider and
HTTP-client logging are suppressed; supported synchronous SDK errors are converted
to bounded categories before callers can log them. Streaming is unsupported.
This does not prevent arbitrary code or debuggers in your process from accessing
secrets.

### Scope and unattended jobs

This vault supports a **direct foreground Python process with a controlling
terminal**. It refuses non-interactive input and never falls back to echoing a
secret on stdin. Detached jobs, cron and the whole-design controller's detached
proposer subprocess have no terminal and cannot unlock this vault. Each separate
Python process needs its own unlock. Do not export the decrypted key to make these
flows work. A managed secret service or separately designed credential broker
would be needed for unattended use.

All maintained model callers share the workspace-header and retry-safe client
factory, but their scheduling differs. Older optimization loops can intentionally
request several proposals; the one-generation limit applies specifically to
`tools/run_fpga_proposal.py`, not to every program in this repository.

For an existing site-managed environment integration only, `PQC_CLAUDE_AUTH=env`
explicitly selects the user's existing `ANTHROPIC_API_KEY` and optional
`ANTHROPIC_WORKSPACE_ID`. The program does not save those values or create an
`.env` file. Environment variables are plaintext process state and may be inherited
by children; this mode is **not** the encrypted-vault workflow. Vault loading never
silently falls back to environment credentials or an insecure keyring backend.

## Recover a confirmed preflight failure without erasing history

A recorded `FAILED` run with `api_calls_attempted: 0` means the runner recorded
no generation attempt. For a workspace-header error during token counting, fix
local credentials first, then explicitly create a new prompt context:

```sh
python3 tools/prepare_fpga_proposal.py recover-preflight \
  --context .pqc_runs/fpga-proposals/mldsa-review-001/proposal-context.json \
  --out .pqc_runs/fpga-proposals/mldsa-review-002
```

This is **offline preparation only**, not an API retry. It checks the original
record/context/prompt binding and source hashes, copies the unchanged prompt into
a new directory and adds hash-linked recovery provenance. The original run record
and `.proposal-request.lock` remain unchanged. Existing output directories,
changed inputs, response/review files and uncertain generation outcomes are
refused. A zero-generation `BLOCKED_BUDGET` record can also be re-prepared after
you review the pricing/budget. Review the new context before separately running
any new paid request. Never delete a lock or failed record to bypass the guard.

If `api_calls_attempted` is 1, or the status is `RUNNING` or
`FAILED_OUTCOME_UNKNOWN`, **check provider usage before considering another
request**. This helper refuses those outcomes. No failure triggers an automatic
retry. SDK initialization/unlock failures now also leave a bound failure record.

New records contain a bounded `failure_stage`, `error_category` and optional
numeric `provider_http_status`. For example, `token_count`, `workspace_required`,
`400` identifies a missing workspace header without saving the provider response
body. Token-count attempts are recorded separately from generation attempts.
Neither local status nor a token count establishes successful paid generation or
proves a billing cap. Historical records are not rewritten to add these fields.

## What protects the file, and what does not

- Default location: `~/.config/llm-aided-pqc/claude-vault.json`, or
  `$XDG_CONFIG_HOME/llm-aided-pqc/claude-vault.json`. An overridden base must be
  absolute. The vault cannot be inside a Git checkout. Do not sync it publicly.
- Encryption uses the maintained `cryptography` package's
  [Fernet authenticated encryption](https://cryptography.io/en/latest/fernet/)
  and Scrypt password-based key derivation with a fresh 16-byte salt, `n=131072`,
  `r=8`, `p=1`. The KDF requires roughly 128 MiB. Its fixed parameters cannot be
  increased by a malicious file. No custom cipher or unencrypted fallback exists.
- The API key and workspace ID are encrypted together. Version, KDF identifier,
  salt, approximate ciphertext size and Fernet creation timestamp are public.
- The app directory must be owned by you and mode `0700`; the file must be owned
  by you and mode `0600`, regular, single-link and bounded in size. Symlink path
  components and unsafe writable parents are refused. Files are opened with
  no-follow checks and encrypted writes use private temporary files plus atomic
  installation/replacement. Permissions are checked; existing unsafe permissions
  are not silently changed.
- This POSIX workflow is intended for Linux/SSH. It is not a Windows credential
  manager integration. Use a private, local filesystem with reliable POSIX
  permissions and atomic rename/link behavior; unusual network filesystems may
  refuse the operations and are not validated here.
- At-rest encryption helps if someone obtains only the encrypted file or backup.
  It does **not** protect against root/host administrators, another process using
  your OS account, malware, injected dependencies, terminal recording or a
  compromised program while unlocked. Python cannot guarantee memory zeroization;
  swap, crash dumps and debugger snapshots can contain plaintext. Prefer a
  dedicated trusted account/host, encrypted storage and suitable dump/swap policy.
- Backups remain offline password-guessing targets, so use a strong unique
  passphrase. File deletion is not secure erasure and does not revoke the remote
  key. If a key was exposed in history, logs or chat, revoke it in the Console and
  create a replacement yourself; saving it encrypted afterward does not undo the
  exposure.

Tests use dummy credentials, synthetic provider replies and a local pseudo-terminal.
No real API credentials, authentication test, paid generation, EDA run or hardware
qualification is performed by these tests.
