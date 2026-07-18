# Agent Architecture & New-Design Onboarding Runbook

Purpose: how the LLM-aided PPA optimization agent is structured, what its
safety invariants are, and the exact steps to onboard a new PQC hardware
design. Current designs: ML-DSA (GMU/Beckwith), HQC (Yale/Deshpande).

## 1. Pipeline overview

Two tiers, one measurement law:

- **Block tier (autonomous)**: per-block OOC synthesis as filter; latency-
  neutral edit menu (POLICY); block orchestrator proposes -> applies ->
  gates -> synthesizes -> accepts/reverts. Model: Sonnet.
- **Chip tier (`chip_orchestrator.py`)**: regen checkpoint -> post-route
  closure search (binary search WNS>=0) -> worst-path extraction -> map cone
  to file -> dispatch block orchestrator (or graceful NO_TARGET exit when
  the cone is out of block scope) -> functional KAT gate -> regen ->
  re-judge. Post-route closure is the ONLY acceptance judge; post-synth
  numbers are targeting hints and mispredict even the sign of chip-level
  outcomes (measurement law, established on ML-DSA integration inversion).

Architectural-tier edits (e.g. ML-DSA banked encoder, HQC shared-mux
retiming) are human/Claude-designed, KAT-gated, then judged post-route like
everything else.

## 2. Safety invariants (do not weaken)

1. **Correctness gate before judgment**: every applied edit passes the
   design's full functional KAT gate before any PPA number is trusted.
   Gate failure => targeted git revert of the dispatched file, verdict
   logged, loop ends.
2. **Git is the restore mechanism** (not .bak files). Pristine trees are
   never edited; all edits live in tracked overrides (`build/...`,
   `agent/mldsa/mldsa_src/...`).
3. **Anchored edits**: byte-exact anchors, assert count==1, repr() probe on
   whitespace mismatch (trailing-space failures are common in this RTL).
4. **Probe validity** (`fmax_search.py`): stale reports removed before each
   probe; a probe is valid only if Vivado rc==0, WNS parses, and routing
   completed; one retry, then abort loudly. Never trust a number from an
   interrupted run.
5. **Negative results are data**: rejects and no-actions are logged with
   the same fidelity as wins (flight log / transfer log / orchestrator log).

## 3. Learned-rules system (`agent/learned_rules.py`)

- Append-only `agent/learned_rules.jsonl`; each record: rule text (<=40
  words, conditions-not-outcomes), design, timestamp, evidence pointer,
  source model.
- Distilled automatically from ACCEPTED and REJECTED_MARGINAL verdicts only
  (hard failures stay in logs undistilled to avoid noise rules).
- Injected into orchestrator system prompts AFTER the hand-written POLICY
  with explicit precedence: the hand-written menu WINS on conflict. Rules
  guide; POLICY constrains. This prevents overnight learning from silently
  constraining strategies that could win in other scenarios.

## 4. Onboarding a new design (checklist)

1. **Register sources** in `agent/synthesizer.py`:
   - `MODULE_SOURCES["<design>_opt"]` and `..._pristine"` (tracked-override
     dict pattern: pristine glob, overrides win on basename).
   - `TOP_OVERRIDE` entries; `VHDL_SOURCES` if mixed-language.
   - If the design needs `include_dirs`/`verilog_define`, extend
     `synth_flags()` — single source of truth; synthesizer, path_extractor,
     and regen_ckpt all consume it. Do NOT inline flags anywhere else.
   - Header/macro files (`clog2.v`-style) go in `HDR_FIRST` for read order.
2. **Build the functional KAT gate** (`agent/<design>/..._kat_gate.py`):
   - Must exercise the full algorithm chain (keygen->encap->decap or
     sign->verify), compare against known-good reference output, print a
     final PASS/FAIL line (or json status field), exit nonzero on FAIL,
     watchdog-kill hung sims (process-group kill).
   - Corruption-validate before trusting: inject a known bug, confirm FAIL,
     restore, confirm PASS. A gate that has never failed proves nothing.
   - Expect the vendor sim flow to be broken as shipped (HQC joint config
     had 5 independent defects: define overwrite, incomplete TB, undriven
     ifdef ports, parameter-default skew). Budget a debugging session.
3. **Add the DESIGNS entry** in `agent/chip_orchestrator.py`:
   `key`, `ckpt`, `bracket` (narrow after first closure measurement),
   `hier2file` (instance-name -> editable file; shared-resource input cones
   map to the top-level integration file, not the resource's own file),
   `orchestrator`, `kat_gate` (argv list).
4. **First measurements before any edit**:
   - `path_extractor.py <design>_opt <param> 5` — chip-level cone.
   - Stage-1 `chip_orchestrator.py <design>` — baseline closure + worst path.
   - Compare optimized-tree vs pristine at their own closing periods.
5. **Then edit**, in tier order: block-orchestrator families first for
   in-scope cones; shared-mux/control fan-in retiming (KAT-gated) next;
   architectural restructuring last, with a design doc for advisor sign-off.

## 5. Known cross-design patterns (transfer priors)

- Chip-critical cones are usually invisible to block-level OOC runs; the
  binding path in both designs was control/select fan-in into a shared wide
  datapath (ML-DSA: PISO variable shift; HQC: pm client mux into POLY_MULT).
- Select retiming is safe when ownership is stable across the operation and
  settles >=1 cycle before the resource's start pulse; keep 1-cycle start
  pulses on combinational selects (a registered select can swallow the
  first pulse after an ownership change -> deadlock).
- Route-dominated cones (>=75% route) respond to fan-in restructuring, not
  logic-depth reduction.

## 6. Standing tools

`synthesizer.py` (OOC synth + flags SoT) | `path_extractor.py` (top-N chip
paths) | `fmax_search.py` (validated post-route closure search) |
`chip_orchestrator.py` (stage-1/2 loop) | `learned_rules.py` (rulebook) |
per-design KAT gates | `ppa_reader.py` / `ppa_table.py` (reports).
