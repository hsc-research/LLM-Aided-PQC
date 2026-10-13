# Bounded autonomous FPGA experimentation

[Project home](../README.md) · [Vivado qualification](fpga/VIVADO_QUALIFICATION.md) · [Exact-source verification](FPGA_AGENT_FEEDBACK.md#exact-source-verification-adapter)

`python3 -m agent.autonomous_fpga` connects the source context, model proposal,
exact-source 210-case verification, fresh Vivado measurement and feedback into one
foreground process. It can run several distinct experiments without manually
copying a proposal into RTL. This implementation supports exported ML-DSA FPGA
sources and Vivado OOC synthesis. It does not execute HQC or qualify Genus/DC.

## What is automatic, and what is qualified

Every run copies the selected export into an isolated working tree. It runs the
baseline compile/full KAT gate, invokes Vivado on those exact bytes under the
prepared part/clock/XDC/tool settings, and derives observable qualification gates
from raw tool objects and reports. It does not ask the user to write PASS flags.

- `strict` (default): missing baseline qualification stops before loading API
  credentials or making a model request. Acceptance requires qualified baseline
  and candidate evidence, unchanged latency for all 210 cases, timing/resource
  limits and a real objective improvement. The original export is never changed.
- `exploratory`: explicitly permits a bounded experiment/verification/measurement
  feedback loop even when implementation qualification is incomplete. Candidate
  RTL is compiled, all 210 cases must pass with exactly unchanged cycles, and
  Vivado is rerun before a provisional snapshot is retained. Every candidate is
  then rolled back to the incumbent. Provisional results never replace a best
  snapshot or become accepted optimization gains.

The current Vivado producer can establish structural counts, clock/constraint
coverage, source ownership and primitive inventory. **Mapped-memory behavioral
qualification remains missing.** Therefore a real run currently cannot reach
strict acceptance; observable checks passing does not bypass that final gate.
Exploratory mode nevertheless runs actual repeated candidate experiments, rather
than stopping at a proposal preview. Its measurements are post-synthesis estimates,
not routed timing closure. No power or physical side-channel result is produced.

The older reported baseline had 66 latches, 198 no-clock pins and incomplete I/O
constraints. Those defects are blockers, not zeroes or waivers. Start from the
[separate latch-corrected export](fpga/MLDSA_LATCH_CORRECTION.md), preserve the old
profile/reports, and run the exact new baseline again. The correction alone does
not establish clock coverage or mapped-memory behavior.

## Prepare and run

1. Export/verify the explicitly selected ML-DSA FPGA variant and create a site
   preparation using `tools/export_target_profiles.py`, as described in the
   [latch-correction workflow](fpga/MLDSA_LATCH_CORRECTION.md#start-a-fresh-fpga-run).
   Freeze the actual part, Vivado version, reviewed XDC and clock period. Do not
   copy observations from a different source fingerprint.
2. Copy `configs/autonomous_fpga.example.json` to a local configuration. Set
   `preparation` relative to that configuration file. `editable_files` is a
   reviewed global allowlist of exact source paths relative to the export's
   profile directory. It can contain up to 32 files; a proposal gets at most three
   of them (two by default), selected from measured critical-path source ownership.
3. Fill in a newly approved model, current input/output prices and total budget.
   The previously authorized single proposal budget is not continuing permission
   for this loop. Never put credentials or workspace IDs in this configuration.
4. Inspect the configuration without running tools or a provider:

   ```sh
   python3 -m agent.autonomous_fpga \
     --config configs/autonomous_fpga.local.json \
     --out .pqc_runs/autonomous-fpga/mldsa-001
   ```

5. On the licensed server, after approving the local tool run, add `--execute`.
   With `PQC_ENABLE_LLM` unset, baseline tool checks may run but generation remains
   disabled. For a newly approved paid experiment loop, use the foreground shell:

   ```sh
   PQC_ENABLE_LLM=1 python3 -m agent.autonomous_fpga \
     --config configs/autonomous_fpga.local.json \
     --out .pqc_runs/autonomous-fpga/mldsa-001 --execute
   ```

The API client is created in this foreground process after baseline checks and
context selection. The encrypted vault unlocks once per process; the key stays
in process memory. Do not detach the process before a required vault prompt.
Tool children receive an allowlisted environment without provider credentials,
workspace IDs, vault passphrases or ambient proxy/auth variables. There is no
background credential broker and no proposer subprocess requiring another TTY.
Trusted compiler/EDA software still runs with the invoking user's OS privileges;
this is not an OS security sandbox.

If Vivado cannot attribute a measured path to an exact source file/line, similar
instance names do not establish ownership. Strict mode stops. In explicitly
exploratory mode, a human can supply `exploratory_focus` using the same source-path
syntax, restricted to `editable_files`. The prompt labels it user-nominated,
unverified ownership. It is never an acceptance waiver or a widening of edit
permission. Review complete I/O constraints separately; exact, user-justified
per-port false-path entries are described in the qualification document.

## Iteration and retained understanding

For each candidate the controller:

1. Hashes the whole selected source closure, profile, constraints, fixture files,
   adapter code and compile inputs; restores/checks them around trusted stages.
2. Scans module declarations/interfaces and literal instantiation candidates into
   `design-model.json`, with source SHA-256 and line references. This is a lexical
   observation, not elaborated hierarchy. Unknown generate branches, algorithm
   semantics and cell ownership remain explicit.
3. Selects a narrow measured ownership scope, supplies top-down interfaces,
   source context, metrics, blockers and recent source-bound failure feedback.
   The provider may request bounded read-only line spans through `NEED_CONTEXT`.
4. Accepts only typed unique-anchor replacements in the allowlist. It freezes
   module interfaces/directives/attributes and complete comment contents, rejects foreign code/DPI/Verilator
   hooks and non-pure simulator tasks in edited files, and enforces byte limits.
5. Runs the exact export adapter, which compiles selected RTL without regenerating
   it and checks 75 KeyGen, 45 Sign, 45 Verify, 12 modified-input and 33 canonical-
   hint cases. Every returned cycle count must equal the incumbent's count before
   synthesis is attempted. A faster trace is also a changed trace and is rejected.
6. Runs matched Vivado OOC synthesis, checks full tool build identity as well as
   configured version/part/period, and rehashes/reparses the raw measurements.
7. Persists the result and feeds the distinct failure or measurement back into
   the next attempt. Syntax/KAT failures, timeouts, no improvement and duplicate
   source states do not become accepted candidates.

The persistent source model and experiment journal are working context. No model
training occurs, and model hypotheses do not become proven architectural facts.
Finite KATs are not formal equivalence, exhaustive functional proof or a guarantee
against physical side channels. There is currently no formal-equivalence adapter
in this entrypoint; an independently qualified one is a future additional gate.

## Bounds, stopping and recovery

Iterations, total generation attempts, read-only context requests, prompt/output
size, edited files/bytes, compiler jobs, API timeout and total runtime are bounded.
Generation is serial, SDK retries are disabled, and cooperating runs sharing the
same export profile cannot execute concurrently. `STOP` is terminal;
`NEED_CONTEXT` alone may request a bounded continuation. Malformed responses and
provider failures stop instead of silently purchasing a retry.

Before each generation, token counting is followed by a durable cost reservation
for counted input + 10% + 1024 tokens and the full output allowance, at explicitly
supplied prices. Returned usage is reconciled before the next request. An uncertain
request retains its reservation and stops. Unexpected cache usage or invalid usage
also stops for billing review. **This is an estimated cost bound, not an account-
side billing cap**; use provider spending controls for a guaranteed account limit.

Tool process trees are killed on timeout, interruption or sampled output-limit
violations. Logs and artifacts are checked during execution and again at exit.
The filesystem can grow between checks; use an OS filesystem quota when a strict
storage cap is required. Model prompt/response and adapter-response sizes are explicitly bounded.
Local configuration and controller records are trusted files, not untrusted upload parsers. Kill -9 or machine failure may leave an interrupted workspace; the
original source export is unchanged, and evidence is retained for inspection.

`state.json`, the hash-chained journal, request/response/usage records, immutable
baseline snapshot and provisional/accepted snapshots remain under the chosen run
folder. No existing run folder is reused or automatically resumed:

```sh
python3 -m agent.autonomous_fpga --inspect .pqc_runs/autonomous-fpga/mldsa-001
```

Inspection rechecks persisted records, original inputs, working state, snapshots
and report hashes. It rejects pending/unknown paid requests and incomplete
promotion persistence. It never makes another request. Review provider usage
before authorizing any new run after an uncertain outcome. Local hashes detect
accidental/stale changes under the trusted-adapter boundary; they are not vendor
signatures against a malicious local tool installation.

The current dashboard displays saved autonomous runs under
`.pqc_runs/autonomous-fpga/<run>`, including iteration verdicts, provisional versus
recorded-accepted counts and cost uncertainty. It checks local summary/journal
records only, does not traverse live source paths, and never requalifies hardware.

## Extension boundary

The controller's request/response protocol reuses the whole-design target/source,
functional, latency, report and metric contracts. A future shared orchestrator can
select qualified Genus/DC adapters with RTL flip-flop memories and immutable
libraries/corner/constraints. It must preserve these same safety and provenance
requirements and keep FPGA/ASIC measurements separate. This FPGA implementation
does not imply that those adapters or other PQC designs are already qualified.

## Validation

Synthetic API and tool fixtures exercise orchestration, failures, cost uncertainty,
rollback, source drift, ownership, context bounds and report tampering. Synthetic
PASS and PPA values are only software tests. This change does not run paid APIs,
licensed Vivado, or new full hardware KATs. The recorded permitted test run omits
the same 19 HQC-restricted cases in normal and `python -O` modes.
