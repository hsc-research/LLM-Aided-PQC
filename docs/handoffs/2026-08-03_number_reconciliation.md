> **SUPERSEDED 2026-08-04** by `2026-08-04_ooc_correction_and_paper.md`.
> The top-priority open problem in this doc (ML-DSA flow mode) is resolved:
> 82.7 MHz was pinned-flow and is retired. Canonical pair is M1 70.2 / M2
> 80.5 MHz, +14.7%, OOC. The "Reference: canonical numbers" ML-DSA table
> below is invalid.

# Handoff: number reconciliation and paper prep, 2026-08-03

For a fresh conversation. Read this first, then
`docs/findings/INDEX.md` for the canonical ledgers.

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

## What today was for

Every number in the repo was supposed to become defensible and traceable. Most
of that got done. One serious problem surfaced at the very end and is now the
top priority.

---

## THE OPEN PROBLEM (start here)

**The ML-DSA headline of 82.7 MHz may have been measured in the wrong flow
mode.**

From `agent/chip_orchestrator_log.jsonl`:

```
2026-07-17 14:59:09  mldsa  69.0   chipv2_mldsa_16361
2026-07-17 23:22:17  mldsa  71.4   chipv2_mldsa_46702
2026-07-18 00:25:50  mldsa  82.7   chipv2_mldsa_48831   <-- the headline
2026-07-19 08:53:45  hqc    114.3  chipv2_hqc_67757
2026-08-03 13:54:09  hqc    116.0  chipv2_hqc_85042
2026-08-03 14:49:52  hqc_baseline 109.6 chipv2_hqc_baseline_88566
```

Commit `23c5672` changed `regen_ckpt` in `agent/chip_orchestrator.py` to
out-of-context mode. Its message: *"HQC joint top has 1611 I/O, overflows
package pinning; also aligns regen with the OOC flow all reported numbers
use."*

**That commit lands after 2026-07-18.** So the 82.7 measurement used the
pre-patch `regen_ckpt`, which ran in default pinned mode. ML-DSA has few
enough ports that pinning succeeds silently rather than failing, so nothing
flagged it.

This was noticed in a July 20 session and recorded as *"mldsa's judged numbers
came from a pinned (non-OOC) flow while the original 78.6 measurement was OOC.
That could be the 79.1-vs-82.7 discrepancy's real cause."* It was never
resolved. Three ML-DSA optimized figures are in circulation: 78.6, 79.1, 82.7.
The abstract and INDEX now use 82.7.

**First task: confirm the commit date, then decide.**

```bash
git log -1 --format="%ci %h %s" 23c5672
grep -n "out_of_context\|mode " agent/chip_orchestrator.py | head
```

If 82.7 is pre-patch, ML-DSA must be re-closed in OOC mode exactly as HQC was
today, both arms:

```bash
python3 agent/chip_orchestrator.py mldsa            # optimized arm
# a baseline arm entry does not exist yet; add one mirroring hqc_baseline
```

Roughly an hour per arm. Until that lands, **82.7 and +17.8% are unverified**
and should not go in the paper.

Note the ML-DSA baseline of 70.2 MHz has no entry in
`chip_orchestrator_log.jsonl` at all, so its provenance also needs
establishing.

---

## What was settled today

### HQC now has a real baseline, and never had one before

Three closure runs, all at commit `6351cac`, same command, same bracket:

| Run | Arm | Result |
|---|---|---|
| 1 | `hqc_joint_pristine`, current RTL | 9.12 ns, 109.6 MHz, WNS +0.072 |
| 2 | `hqc_joint_opt`, current RTL | 8.62 ns, 116.0 MHz, WNS +0.006 |
| 3 | `hqc_joint_pristine`, pre-port-fix RTL (`cd92639`) | 9.12 ns, 109.6 MHz, WNS +0.072 |

**Canonical HQC pair: 109.6 -> 116.0 MHz, +5.8%.**

Full PPA, both from the `.rpt.util` files:

| | Baseline | Optimized | Delta |
|---|---|---|---|
| LUT | 13045 | 13331 | +2.2% |
| LUT as memory | 1019 | 1075 | +5.5% |
| FF | 6765 | 6887 | +1.8% |
| BRAM | 21 | 19.5 | -7.1% |
| DSP | 4 | 4 | — |

The BRAM reduction is the memory-retarget wins (MSG_MEM, FFT FIFO to
distributed RAM), which is also why LUT-as-memory rises.

**The binding path moves between arms, and that is the mechanism:**

| Arm | Worst path at closure |
|---|---|
| baseline | `DECAP/DECRYPT/V_MINUS_UY/uv_addr_0_mul_reg[1]/C` -> `POLY_MULT/dshift_reg[35]/D` |
| optimized | `SHAKE256/control_path/counter_reg[5]/C` -> `SHAKE256/data_path/state_ram/.../SP/I` |

The agent's one accepted HQC edit (`flag_precompute` on `v_minus_uy`, commit
`12d930d`, $0.037, one API call) sits on the baseline's binding path. After
the edit the design binds on shared Keccak, which the rule set does not
address.

### Why prior HQC numbers were wrong

| Number | What it actually was |
|---|---|
| 117.1 / 119.3 | Measured from `synth_out/sweep_hqc_joint_*` checkpoints produced by `flow_sweep.py` at a different regen period. Not comparable. |
| 114.8 | **Not a baseline.** The optimized arm while its composition was silently reverted to pristine by `a1a7ad2` for three days. |
| 114.3 | Optimized arm with a mux-retiming edit later reverted as a documented negative. |
| +1.9% | Derived from 117.1/119.3. Now +5.8%. |

Before today, **no properly measured HQC pristine baseline existed.** That is
the root cause of every prior discrepancy.

### Port fixes are FPGA-neutral, verified

Run 3 above is the control. The five cross-tool RTL portability fixes made for
the Genus port reproduce the baseline exactly, so declaration reordering does
not affect FPGA timing. The normalized RTL is now the common source artifact
for both backends. This is what Dr. Abideen asked to be verified rather than
assumed.

### Repo changes made today

- `docs/findings/INDEX.md`: HQC chip-level ledger added with reproduce
  commands, commit, PPA, both binding paths, superseded-numbers table, and an
  explicit "open question" block for what is still unexplained
- `docs/README.md`: rewritten. Was HQC-only, 200 MHz framing, no ML-DSA, no
  chip-level work, and restated numbers inline. Now points at INDEX as the
  single source
- `docs/DOCUMENTATION_STANDARD.md`: rule 11 added, supersession must be
  recorded in both directions and the number grepped for elsewhere
- `docs/findings/FINDINGS_crossdesign_closure.md`: supersession banner
- `docs/findings/asic/*`: four docs citing +1.9% corrected to +5.8%
- `agent/chip_orchestrator.py`: `hqc_baseline` design entry added
- `tools/check_numbers.py`: new. Extracts every MHz figure from tracked
  markdown and classifies it as canonical, retired, or unknown

---

## `tools/check_numbers.py` state

Last run: 61 files, 128 citations verified, **2 errors, 110 warnings**.

**Errors** are retired numbers quoted as current:
```
docs/REPRODUCE.md:521  65.3 MHz   projected from a violated run, invalid
docs/REPRODUCE.md:521  72.6 MHz   projected from a violated run, invalid
```

**Warnings** are figures in neither list. Most are legitimate block-level
results in findings docs that simply have not been catalogued. Working through
them is the remaining task, and the point is that each one ends up either in
ALLOWED with a note on what it is, or in RETIRED with a reason.

The checker only matches MHz. **It does not catch percentage deltas**, which is
how +1.9% survived in five documents after its source numbers were retired.
Extending it to percentages is worth doing.

---

## Still open

1. **ML-DSA OOC verification.** Top priority. See above.
2. **ML-DSA baseline provenance.** 70.2 MHz has no entry in the orchestrator
   log.
3. **Constant-time verification.** The ICCAD abstract's Figure 1 shows it as an
   independent checker obligation and Section I claims it. No such checker
   exists in the repo. Present gates are KAT (`agent/hqc/kat_gate.py`,
   `joint_kat_gate.py`, `agent/mldsa/full_kat_gate.py`) and cycle-accurate
   lockstep equivalence (`agent/mldsa/*_equiv_gate.py`). The latency-preserving
   lane holds cycle counts fixed, which is necessary for constant-time
   behaviour but is not a proof of it. Either soften the claim to
   "cycle-schedule neutrality, verified by lockstep equivalence" or build the
   checker.
4. **Cost figures disagree.** The abstract says $0.52 for HQC;
   `transfer_log.jsonl` maxes at $0.0682 over 15 records. INDEX says $0.245 for
   the ML-DSA latency campaign; `latency_log.jsonl` maxes at $0.1522. Likely
   `cost_usd` accumulates within a run and resets between runs, so a max
   undercounts. Needs summing per-run.
5. **The 110 checker warnings.**
6. **Table I rewrite.** Dr. Deshpande's note: the rules table names blocks
   (`sample_addr`, `cstate`) that mean nothing outside the project, and the
   rules read as generic synthesis techniques. They need PQC-specific
   applicability conditions.

---

## RTL freeze

`hardware/` and `build/` are frozen for the ICCAD abstract and D&T
submission. Every FPGA closure number was measured at commit `6351cac`.

Nine HQC files still carry cross-tool portability defects and are needed for
full-chip ASAP7, which is already out of reach before the deadline. Further
port fixes go on a branch and merge only together with a re-close of both arms
and a Results of Record update in the same commit.

Anything under `asic/` is safe to continue: it does not touch `hardware/` or
`build/`.

---

## ASIC status, for context

Target moved from GPDK045 45 nm to **ASAP7 7 nm** on advisor instruction, with
Genus plus Innovus. All four prior GPDK045 ASIC numbers are retracted. The
tutorial reference flow (`hsc-research/tutorial_innovus`, self-contained,
ships ASAP7) is validated on SHA256. Memories map to flip-flop arrays for now,
per instruction, with SRAM macros after the flow closes.

Full-chip ML-DSA on ASAP7 is not tractable in the available time: one point at
2000 ps ran over 20 hours without clearing generic synthesis. Note that
**periods are in picoseconds** in ASAP7, and the design is **mixed-language**
with a VHDL Keccak core whose packages must be read before their users.

Details in `docs/findings/asic/2026-08-02_asap7_transition.md` and
`docs/2026-08-02_asic_game_plan.md`.

---

## Reference: canonical numbers

**ML-DSA** (post-route closure, Artix-7 -1). **Flow mode unverified, see open
problem.**

| Arm | Fmax | LUT | FF |
|---|---|---|---|
| baseline | 70.2 MHz (14.25 ns) | 52987 | 29081 |
| optimized | 82.7 MHz (12.09 ns) | 53597 | 30123 |

**HQC** (post-route closure, joint KEM, OOC, commit `6351cac`, verified today)

| Arm | Fmax | LUT | FF | BRAM |
|---|---|---|---|---|
| baseline | 109.6 MHz (9.12 ns) | 13045 | 6765 | 21 |
| optimized | 116.0 MHz (8.62 ns) | 13331 | 6887 | 19.5 |

**Gate catch rate** (reconciled and reproducible): 59 proposals, 33 applied,
14 functionally incorrect, 4 accepted. By lane: 4 of 23 latency-preserving,
10 of 10 latency-changing. Script in
`docs/findings/FINDINGS_gate_catch_rate.md` reproduces 59/33/14 exactly.

**Deadlines:** ICCAD SRC abstract and IEEE D&T, both August 15. Lloyd owns
Methodology and Results; Dr. Deshpande takes Intro and Background. D&T limits:
5000 words including references and biographies, each figure or table counts
about 200 words, maximum 12 references, at least 15% tutorial content.
