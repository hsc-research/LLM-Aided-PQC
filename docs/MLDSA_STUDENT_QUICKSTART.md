# ML-DSA: baseline, agent run, and student handoff

## Next step: reproduce the passing baseline on the server

Verilator 5.048 and historical development runtime 5.49 now pass all 210 cases on the final checker, with every vector cycle count and all 35 RTL hashes matching. This was verified in the test environment; the user's server still needs its own replay. Verilator 5.022 produces incorrect KeyGen bytes and is blocked.

Ask server IT to install/build the official [Verilator v5.048 release](https://github.com/verilator/verilator/releases/tag/v5.048) alongside the old version and provide its activation/PATH instructions. Do not copy the tested Debian binary onto EL9. Keep existing runs `mldsa-001` / `mldsa-002`; both stopped before paid generation.

## 1. Freeze the working server setup

Run on the licensed server, in the existing Python 3.11.10 virtual environment:

```sh
cd /home/zabideen/ASIC_Projects/LLM-Aided-PQC
source .venv/bin/activate
python3 --version
command -v python3
verilator --version
command -v verilator
vivado -version
git rev-parse HEAD
git status --short
python3 -m pip freeze
```

Activate the actual existing venv and site Vivado setup before these commands; their paths are site-specific. Select the verified simulator through PATH and recheck its version. Freeze Python, Verilator's exact build, C++ compiler/make, package versions, repository commit plus local diff, and Vivado 2022.2 build identity. A floating minimum simulator version is not a reproducibility pin.

Baseline configuration:
- Variant: `fpga-latch-corrected-baseline`
- Part: `xc7a200tfbg676-1`; clock: 15 ns
- Profile: `build/profiles/mldsa-latch-corrected-baseline-fpga/profile.json`
- Preparation: `build/launch/mldsa-latch-corrected-fpga/preparation.json`
- Local controller config: `configs/autonomous_fpga.local.json`

Validate existing inputs without regenerating them:

```sh
python3 tools/export_target_profiles.py --verify build/profiles/mldsa-latch-corrected-baseline-fpga/profile.json
python3 tools/export_target_profiles.py --verify-preparation build/launch/mldsa-latch-corrected-fpga/preparation.json
```

If validation fails, stop and fix the setup. Never edit a frozen manifest to make it pass. A changed interpreter/checker or moved checkout may require fresh preparation in a new launch directory, using the reviewed site file, and a corresponding local-config path change. Preserve old preparations and reports. Preparation binds absolute paths and hashes; simply copying an old preparation to a student's checkout is insufficient.

## 2. Replay KATs, then measure the baseline without model calls

From the repository root, with the selected simulator on PATH, run the dedicated replay. It exports the latch-corrected baseline, checks the historical source hashes and runs all 210 cases. It needs no API key or Vivado:

```sh
python3 docs/verification/mldsa-verilator-compat-2026-10-14/replay.py --out "$PWD/.pqc_runs/mldsa-kat-$(date -u +%Y%m%dT%H%M%SZ)"
```

Require the full pass: 75 KeyGen, 45 Sign, 45 Verify, 12 mutation and 33 canonical-hint cases. Preserve the response, raw logs and per-vector cycles. Compilation or equal cycle counts alone is insufficient. Stop if any case fails.

Then use the controller to re-verify and measure the prepared source profile with paid generation disabled. Set `mode: "strict"` in the reviewed local config. Its model/pricing fields must remain valid even for this no-paid-call run because the config parser requires them.

```sh
RUN=".pqc_runs/autonomous-fpga/mldsa-baseline-$(date -u +%Y%m%dT%H%M%SZ)"
python3 -m agent.autonomous_fpga --config configs/autonomous_fpga.local.json --out "$RUN"
env -u PQC_ENABLE_LLM python3 -m agent.autonomous_fpga --config configs/autonomous_fpga.local.json --out "$RUN" --execute
python3 -m agent.autonomous_fpga --inspect "$RUN"
```

The first command is configuration validation only. Review `001-verify/`, `002-measure/`, `state.json`, configuration/journal and the `baseline/` snapshot. Vivado evidence must include setup/hold slack, LUT/FF/memory, latch inventory, DRC, constraints and warnings.

A terminal `BASELINE_BLOCKED` after successful KAT and measurement means qualification is incomplete, **not that KATs failed**. Mapped-memory behavioral qualification is currently missing; other measured blockers may remain. Exploratory mode can instead finish baseline work and later report `BLOCKED` / `Paid generation disabled...`. Always read stage evidence and the error. Never waive a failing KAT or invent timing exceptions to proceed.

## 3. Run the approved bounded LLM experiment

Start only after the baseline evidence is reviewed. The current flow can run **exploratory** experiments, retaining provisional results; it cannot claim strict accepted optimization while qualification gaps remain.

Review `configs/autonomous_fpga.local.json` before a new run:
- `mode`: `"exploratory"`, explicitly approved as provisional experimentation.
- `provider.model` and input/output prices: the approved model and verified prices.
- `provider.budget_usd`: `"5.00"` maximum for this approved run.
- `limits.generation_attempts`: `3`; `limits.iterations`: at most `3`.
- `limits.context_requests`: `1` for the current approved configuration, and less than generation attempts. Context continuations consume the same generation-attempt allowance.
- Keep reviewed `editable_files`, narrow scope and existing resource/time bounds. If source ownership is missing, only use an explicitly reviewed `exploratory_focus` within that allowlist.

The current owner-approved experiment covers sending the selected RTL/report excerpts to the configured provider, up to $5 and three generation requests. Its two failed verification attempts made no paid calls. Separate student experiments require their own approved scope and budget. The software cost reservation is an estimate; use provider-side spending controls too.

The owner enters their own credentials only in the trusted interactive server terminal:

```sh
python3 -m agent.claude_credentials status
# Only if their own vault is not already configured:
python3 -m agent.claude_credentials setup
```

Never share the key, vault file or passphrase. Keep the paid process in the foreground so it can unlock the vault. After approval:

```sh
RUN=".pqc_runs/autonomous-fpga/mldsa-agent-$(date -u +%Y%m%dT%H%M%SZ)"
PQC_ENABLE_LLM=1 python3 -m agent.autonomous_fpga --config configs/autonomous_fpga.local.json --out "$RUN" --execute
python3 -m agent.autonomous_fpga --inspect "$RUN"
```

Each new run rechecks/re-measures its baseline; the current controller does not resume/reuse the earlier baseline run. Do not reuse run directories. Review usage/reservations before retrying an uncertain provider outcome. Candidate acceptance requires unchanged per-vector cycles as well as functional checks; exploratory candidates remain provisional and are rolled back.

## 4. Student takes over on the same server

Use the student's own Unix account, own writable checkout/worktree, own Python environment and own encrypted credential vault. An administrator can give appropriate access to the existing licensed tools and approved read-only baseline evidence. Do not give the student the owner's login or credentials. These account/access changes are setup work requiring owner/admin approval.

Give the student:
1. The exact tested commit and any patch, tool/version record and package lock/freeze.
2. Reviewed source profile, site/XDC settings and instructions to create fresh preparation for their paths/interpreter.
3. Baseline 210-case evidence and Vivado reports, plus the first bounded agent run, inspection result, cost and rejection/provisional reasons.
4. The approved editable-source scope, objective, stopping rules and this command sequence.

Have the student reproduce the no-paid baseline first. Their first paid experiment needs its own model/data/budget approval and their own vault. Run one hardware experiment at a time on the same profile; do not launch competing jobs against a shared workspace. Separate checkouts can still compete for server RAM/CPU and Vivado licenses, so coordinate execution.

## Dashboard: server process, laptop browser

On the server, from the checkout whose runs should be displayed, activate that checkout's environment:

```sh
# One-time optional UI installation, if Flask is missing:
python3 -m pip install -e '.[dashboard]'
python3 -m agent.dashboard
```

On the student's **laptop**, using their real server username and hostname:

```sh
ssh -N -L 8080:127.0.0.1:8080 STUDENT@SERVER
```

Open `http://127.0.0.1:8080` in the laptop browser. Keep the server process and tunnel running. If laptop port 8080 is busy, use `-L 8081:127.0.0.1:8080` and open local port 8081. The server app itself uses fixed port 8080, so coordinate one dashboard process per host. Do not expose it publicly: it has no login. It displays records; it cannot launch runs or independently qualify hardware.

## Further reading

- [Autonomous loop](AUTONOMOUS_FPGA.md)
- [Reproduction guide](REPRODUCE.md)
- [Latch-corrected baseline](fpga/MLDSA_LATCH_CORRECTION.md)
- [Vivado qualification](fpga/VIVADO_QUALIFICATION.md)
- [Credential setup](CLAUDE_CREDENTIALS.md)
- [Dashboard](CURRENT_DASHBOARD.md)
