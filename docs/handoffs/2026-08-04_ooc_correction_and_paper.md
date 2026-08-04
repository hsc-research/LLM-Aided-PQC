# Handoff: ML-DSA OOC correction and ICCAD paper prep, 2026-08-04

For a fresh conversation. Read this first, then `docs/findings/INDEX.md` for
the canonical ledgers.

---

## Ground rules

1. **Never quote a number that is not in a canonical ledger** in
   `docs/findings/INDEX.md`. If asked about a result you cannot find there,
   say so rather than reconstructing it.
2. **Distinguish measured from proposed.** Next steps are not results.
3. **Measurement configuration travels with every number**: flow mode (OOC or
   pinned), regen period, bracket, directives, commit.
4. Lloyd runs all commands locally and pastes output. Give concise code and
   directions, not free-form RTL. **No em dashes.**
5. Ask before editing any source file.
6. Be concise. Lloyd is usage-constrained.

---

## Supersedes

This handoff supersedes `docs/handoffs/2026-08-03_number_reconciliation.md`.
That doc's top-priority open problem (ML-DSA flow mode) is now **RESOLVED**.
Its "Reference: canonical numbers" ML-DSA table is **invalid**: it lists
82.7 MHz optimized, which is retired.

---

## What was resolved

**The 82.7 MHz ML-DSA headline was measured in the wrong flow mode. Confirmed
and corrected.**

Commit `23c5672` (2026-07-19 08:29) moved `regen_ckpt` to out-of-context mode.
The 82.7 measurement ran 2026-07-18 00:25, before that commit, so it used
Vivado's default pinned mode. ML-DSA has few enough ports that pinning
succeeds silently rather than failing.

Both ML-DSA arms were re-closed in OOC on 2026-08-03. Same bracket
(12.0-16.0 ns), same regen period (8.600 ns), same recipe
(ExtraTimingOpt / Explore / Explore, hardcoded in `fmax_search.py`).

**Canonical ML-DSA pair, IDs M1 and M2 in the INDEX ledger:**

| ID | Arm | Period | Fmax | LUT | FF | BRAM | DSP | WNS |
|---|---|---|---|---|---|---|---|---|
| M1 | baseline (`combined_top_pristine`) | 14.25 ns | 70.2 MHz | 53127 | 29079 | 29 | 16 | +0.027 |
| M2 | optimized (`combined_top`) | 12.43 ns | 80.5 MHz | 53543 | 30078 | 29 | 16 | +0.029 |

**M2 vs M1: +14.7% Fmax, +0.8% LUT, +3.4% FF.**

Throughput recomputed from measured KAT cycle counts (cycles / Fmax):
level II +12.0%, level III +12.9%, level V +13.1%. Power is HELD for both
arms; `fmax_search.py` emits `report_utilization` only.

Binding path moves between arms:
- M1: `DECODER/encode_mode_reg[1]/C` -> `ENCODER/PISO_reg[117]/D` (encoder cone)
- M2: `ctr0_reg[1]/C` -> `CHALLENGE_SAMPLER/C_SIPO_reg[426]/R`

**Supporting evidence for the flow-mode explanation:**
- Area is flow-mode-insensitive. Pinned and OOC utilization agree within 0.3%
  (53127 vs 52987 LUT, 29079 vs 29081 FF). Only timing moved.
- The baseline closes at 70.2 MHz in both modes, but slack differs: pinned
  WNS +0.068 vs OOC +0.027 at the identical 14.25 ns period.
- Minerva TP_Opt reports 83.33 MHz optimized and 70.42 MHz pristine in its own
  separate flow (LUT ~57.4k, a third configuration). Both snapshots carry
  `is_complete="0"`. Minerva is not a Result of Record.

**Why OOC is canonical even though the pinned number was higher:** both ML-DSA
arms share one configuration only in OOC; HQC must be OOC (1611 I/O overflows
package pinning) so reporting ML-DSA pinned would mean two flows in one paper;
and OOC is correct for accelerator cores intended for integration.

---

## Commits, all pushed to `origin/main`

```
e3e51c6 check_numbers: percentage deltas and negative-WNS proximity
6d8fa3f INDEX: mark postroute_ppa entry partially superseded
5c5c3c6 Retire pinned-flow power figures; banner handoffs; drop dead args
a12acaf REPRODUCE: retire projected-Fmax corner table
0833a0f check_numbers: retire 82.7 and 78.6, add M2 80.5
5486966 Propagate OOC ML-DSA numbers repo-wide: 80.5 MHz, +14.7%
3edd76a ML-DSA chip ledger: OOC closure M1 70.2 / M2 80.5 MHz, +14.7%
```

Closure logs are committed under `logs/closure/mldsa_ooc_20260803/`, including
all intermediate bisection points and both orchestrator stdout logs. Note
`.gitignore` had a blanket `*.log` rule that silently blocked the stdout logs;
an exception `!logs/**/*.log` was added. **Verify committed evidence with
`git ls-files <dir> | wc -l` against `ls <dir> | wc -l`.**

---

## Repo state

`tools/check_numbers.py` reports **62 files, 241 citations, 0 errors**. It was
extended this session with two rules, both verified with a canary file:

1. `ALLOWED_PCT` / `RETIRED_PCT`. A delta is now checked independently of the
   numbers it came from. This was the failure mode that let +1.9% survive in
   five docs after its sources were retired.
2. Any Fmax on a line that also carries a negative WNS is flagged as a
   projection, regardless of list membership. This was the failure mode that
   let three of six rows in `docs/REPRODUCE.md` pass.

Retired this session: 82.7, 78.6, +17.8%, +16.2%, +15.9%, +15.0%, +11.2%,
+7.2%, and the pinned-flow power figures (1.286 W / 1.480 W). The optimized
power figure was at 12.73 ns, matching no closure point.

Still ALLOWED but tagged **PINNED FLOW**: 69.0 and 73.4 MHz. Both are still
quoted in the README progression table. Re-closing them is about two hours per
arm and has not been done.

Supersession banners added to `FINDINGS_mldsa_chip_orchestrator_stage2.md`,
`FINDINGS_mldsa_postroute_ppa.md`, `PPA_mldsa_fullchip.md`, and the two
2026-07-31 handoffs.

---

## The paper: what remains

**Deadline August 15 for both ICCAD SRC and IEEE D&T.**

A rewritten Results and Contributions section was drafted this session with
the corrected numbers and answers to Dr. Deshpande's four blue-text questions
for both designs. It is **not yet pasted into the .tex**. Ask Lloyd for it if
he has not already applied it.

Outside the Results section, still carrying retired numbers:
- Figure 2 panel (a): 82.7 and +17.8% are hardcoded in the TikZ node and the
  brace label.
- Section I: `$+17.8\%$` inside the `\hl{}` sentence.
- The HQC paragraph: "closed at 119.3 MHz against a baseline 117.1" and
  "\$0.52". All three retired.

**Open items:**

1. **Table I rewrite.** Lloyd owes Dr. Deshpande a concise rulebook to replace
   the current table by early afternoon 2026-08-04. Deshpande's note: the
   table names blocks (`sample_addr`, `cstate`) that mean nothing outside the
   project, and the rules read as generic synthesis techniques. They need
   PQC-specific applicability conditions.
2. **Constant-time checker.** Section I and Figure 1 present it as an
   independent obligation inside the agent. **No such checker exists.** Present
   gates are KAT (`agent/hqc/kat_gate.py`, `joint_kat_gate.py`,
   `agent/mldsa/full_kat_gate.py`) and cycle-accurate lockstep equivalence
   (`agent/mldsa/*_equiv_gate.py`). Lockstep holds the cycle schedule fixed
   against the reference on one input, which is necessary for constant-time
   behavior but does not show timing is independent of secrets. Lloyd emailed
   both advisors asking whether to soften the claim or build it before the
   15th. **Awaiting their answer.** A tractable scope was discussed: a
   differential cycle-count check across varying secret inputs, plus a
   structural scan of each patch for secret-dependent branches, variable
   shifts, and secret-derived addressing. Both are falsifiers, not proofs, and
   should be described that way. A full information-flow proof (the Iodine
   line) is out of scope before the deadline.
3. **Cost figures disagree.** Abstract says \$0.52 for HQC;
   `transfer_log.jsonl` maxes at \$0.0682. INDEX says \$0.245 for the ML-DSA
   latency campaign; `latency_log.jsonl` maxes at \$0.1522; Lloyd's email to
   Deshpande says \$0.15. Likely `cost_usd` accumulates within a run and resets
   between runs, so a max undercounts. **Needs summing per-run.** Not yet done.
4. **The checker's remaining warnings**, mostly uncatalogued block-level
   directive-sweep results in the 90-98 MHz range. Not deadline-critical.

---

## Do not re-litigate

- The 82.7 vs 80.5 question is settled. Do not propose re-running the
  optimized arm to "check stability": Vivado is deterministic given identical
  inputs, so a repeat of the same configuration returns the same number and
  diagnoses nothing. The gap is between configurations, not between runs.
- `closure_search` passed three directive strings that `fmax_search.py` never
  read (it reads `argv[1..4]` only). The recipe is hardcoded. The dead args
  were removed this session.

---

## RTL freeze

`hardware/` and `build/` remain frozen for both submissions. Anything under
`asic/` is safe to continue. ASIC target is ASAP7 7 nm with Genus plus
Innovus; all GPDK045 numbers are retracted. Full-chip ML-DSA on ASAP7 is not
tractable before the deadline.

Note for ASIC work: Genus effort setting alone moves Fmax about 11% (F3). At
+14.7% ML-DSA clears that by under 4 points, and HQC's +5.8% is below it
outright. The F3 argument in
`docs/findings/asic/2026-07-30_genus_asic_port.md` was restated this session
to say the effort gap is comparable to, not smaller than, the FPGA deltas.

---

## Reference: canonical numbers

**ML-DSA** (post-route closure, Artix-7 xc7a200tfbg676-1 grade -1, OOC,
measured 2026-08-03)

| Arm | Fmax | LUT | FF |
|---|---|---|---|
| M1 baseline | 70.2 MHz (14.25 ns) | 53127 | 29079 |
| M2 optimized | 80.5 MHz (12.43 ns) | 53543 | 30078 |

**HQC** (post-route closure, joint KEM, OOC, commit `6351cac`, measured
2026-08-03)

| Arm | Fmax | LUT | FF | BRAM |
|---|---|---|---|---|
| baseline | 109.6 MHz (9.12 ns) | 13045 | 6765 | 21 |
| optimized | 116.0 MHz (8.62 ns) | 13331 | 6887 | 19.5 |

**Gate catch rate:** 59 proposals, 33 applied, 14 functionally incorrect, 4
accepted. By lane: 4 of 23 latency-preserving, 10 of 10 latency-changing.
Script in `docs/findings/FINDINGS_gate_catch_rate.md` reproduces 59/33/14.

**D&T limits:** 5000 words including references and biographies, each figure
or table about 200 words, maximum 12 references, at least 15% tutorial
content. Lloyd owns Methodology and Results; Dr. Deshpande takes Intro and
Background.
