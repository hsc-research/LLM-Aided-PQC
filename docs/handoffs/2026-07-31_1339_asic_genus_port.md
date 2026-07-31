# Handoff: LLM-Aided-PQC, ASIC/Genus Port, 2026-07-31

Paste this at the start of a new chat. Attach or reference the findings docs in
`docs/findings/asic/`.

---

## Ground rules for this conversation

1. **Never quote a performance number that is not in a RESULTS OF RECORD table**
   in `docs/findings/`. If asked about a result you cannot find there, say so
   rather than reconstructing it.
2. **Distinguish measured from proposed.** Next steps and hypotheses are not
   results or decisions.
3. **Cite IDs** (A1, F3, ...) not bare numbers.
4. **Measurement configuration travels with every number**: effort level,
   synthesis directives, corner, OOC mode, blackboxing.
5. **Flag any claimed delta smaller than the tooling sensitivity.** On Genus,
   effort setting alone moves Fmax 10.9% (F3).
6. Lloyd runs all commands locally and pastes output. Give concise code and
   directions, not free-form RTL. **No em dashes in any deliverable.**
7. RTL edits follow: `.bak` -> anchor-count assert -> gate -> KAT at all three
   security levels -> synth -> commit. Ask approval before editing any source
   file.
8. **Watch for vacuity.** A gate can pass on files that were never edited.
   Verify the files being synthesized are the files that changed.
9. Findings go in `.md` under `docs/findings/<area>/`. Paper deliverables are
   `.docx` (IEEE) or `.tex`. Never deliver a paper artifact as Markdown.
10. Be concise. Lloyd is usage-constrained. Output code, directions, and
    confirmation. Skip explanation unless asked.

---

## Project

Correctness-gated, LLM-driven optimization agent for PQC hardware. An LLM
proposes equivalence-preserving RTL edits; deterministic code verifies each
one; a cryptographic KAT gates acceptance. Two designs: **HQC**
(Yale/Deshpande) and **ML-DSA** (GMU/Beckwith), both on Artix-7
`xc7a200tfbg676-1` under Vivado 2025.2, now being retargeted to ASIC.

Repo: `hsc-research/LLM-Aided-PQC`, local `/mnt/c/PQC/hqc`, branch `main`
(ASIC work merged from `asic-genus-port`).

**Deadline: IEEE Design & Test paper, August 15.** Lloyd owns Related Work and
Methodology/Design. Deshpande takes Intro/Background. Evaluation is joint.
ICCAD SRC abstract pushed to August 16.

**D&T hard limits:** 5,000 words including references and bios, each figure or
table counts ~200 words, max 12 references, title max 9 words, at least 15% of
the article must be tutorial content. Over-length submissions are auto-rejected.

---

## Server environment

| Item | Value |
|---|---|
| Host | `engr-r940s01.engr.uidaho.edu`, alias `engr` in `~/.ssh/config` |
| Access | SSH key, passwordless. Requires WSL `networkingMode=mirrored` |
| Genus | 25.12-s067_1 at `/tools/cadence/installs/DDI251/bin/genus` |
| License | `5280@ece-cadence-lic.ece.uidaho.edu`, shared pool |
| Library | GPDK045 `gsclib045_svt_v4.8`, 537 cells |
| Corner of record | `slow_vdd1v0_basicCells.lib` = PVT **0.9 V, 125 C** |
| Xcelium | 25.03 present, not yet used |
| Vivado | **Not on server.** All FPGA work stays on WSL |
| Server repo | `~/pqc/hqc` (currently rsync; deploy key now works, clone pending) |

### Operational hazards learned the hard way

- **Genus does not exit after a `read_hdl` failure.** It sits at low CPU
  holding a license. Always use `exit -force` and wrap in `timeout`.
- **Genus rotates logs per run** (`genus.log`, `genus.log1`, ...). Always read
  `ls -t genus.log* | head -n 1`. Reading stale logs caused two false
  diagnoses.
- **Genus aborts on the first error cluster**; everything after is cascade
  noise. Diagnose with `grep -n -m 1 -B 8 "Error"` and re-run.
- **Concurrent jobs in the same directory collide.** They share `genus.log*`
  and can share `OUTDIR`. Give every concurrent job its own working directory.
- Check for orphans before every launch:
  `ssh engr 'ps -u alco9414 -o pid,etime,pcpu,args | grep -i genus | grep -v grep'`
- Ctrl+C in WSL kills only the local ssh client, never the remote process.

---

## RESULTS OF RECORD (ASIC)

All: GPDK045 SVT slow, 0.9 V / 125 C, pre-layout, **zero wire load**.

| # | Design | Config | Effort | Min period | Fmax | Log |
|---|---|---|---|---|---|---|
| A1 | `poly_mult` HQC-128 | baseline, mem blackboxed | high | 1.281 ns | 780.49 MHz | `asic/results/fmax_poly_mult.log` |
| A2 | `poly_mult` HQC-128 | baseline, mem blackboxed | medium | 1.438 ns | 695.65 MHz | `asic/results/fmax_poly_mult_medium.log` |
| A3 | `v_minus_uy` HQC-128 | **baseline** | high | 0.711 ns | 1406.59 MHz | `asic/results/fmax_vmu_baseline.log` |
| A4 | `v_minus_uy` HQC-128 | **optimized** | high | 0.746 ns | 1340.31 MHz | `asic/results/fmax_vmu_optimized.log` |

**A1 vs A2 is a control, not a result** (effort sensitivity).
**A4 vs A3 is -4.7%**, inside the effort noise floor, so **not** a regression
claim.

**Does not exist yet:** any ML-DSA ASIC number, any HQC-192/256 ASIC number,
any post-layout number, any chip-level ASIC number.

### Terminology (fixed)

**baseline** = unmodified RTL, control arm. **optimized** = after agent edits.
**initial characterization** = the May 2026 Vivado PPA survey.
**closure** = binary search to minimum MET, never projected.
"Pristine" is retired.

**Never** compute Fmax as `1/(period - WNS)`. Formally retracted on the FPGA
side; same prohibition on ASIC.

---

## Findings

- **F1** `poly_mult.v`: three declarations used before declaration
  (`VLOGPT-20`). Hoisted, KAT PASS 128/192/256, commit `950bfc1`.
- **F2** Memories blackboxed. GPDK045 has **no SRAM macro** (all 585 LEF
  macros are standard cells, no memory compiler). Flat synthesis of one module
  with one memory did not finish in 30 min; blackboxed takes ~5 min.
- **F3** **Effort setting moves Fmax 10.9%** (A1 vs A2). Larger than the FPGA
  deltas being replicated (ML-DSA +17.8%, HQC +1.9%). Effort must be pinned,
  identical across arms, and reported. Any delta under ~11% needs search traces
  published.
- **F4** `v_minus_uy.v`: five symbols used before declaration. Hoisted, KAT
  PASS, commit `a279a1a`.
- **F5** `v_minus_uy.v`: duplicate `pm_out` declaration (`VLOGPT-22`),
  pre-existing since initial import. Removed, KAT PASS, commit `895662d`.
- **F6** The one accepted HQC edit does not transfer to ASIC at block level.
  ASIC critical path is `XOR_BASED_ADDER_state_reg[1]` ->
  `XOR_BASED_ADDER_in_addr_reg[8]`, inside the adder submodule, not the
  comparator logic the edit touches. **The arms invert with constraint
  tightness**: optimized wins at 5.0/2.75/1.625 ns, baseline wins at
  1.062/0.781/0.711 ns. This constraint-dependence is the most novel thing in
  the data so far.
- **F7** **Optimized RTL lives only in `build/`, which `make` regenerates.**
  `hardware/` holds baselines only; `git log -- hardware/` shows just the
  initial import plus portability fixes. Running `make build_decap` silently
  reverts accepted optimizations. Currently mitigated only by the `build/`
  copies being committed.

### Defect taxonomy (in progress)

| Code | Defect | Fix | Seen in |
|---|---|---|---|
| `VLOGPT-20` | Use before declaration | Hoist above first use | `poly_mult`, `v_minus_uy` |
| `VLOGPT-22` | Duplicate declaration | Remove redundant | `v_minus_uy` |
| `VLOGPT-37` | `initial` / reg initial value | Ignored by Genus; check reset covers it | `poly_mult`, `mem_dual` |
| `VLOGPT-506` | `ram_style` attribute | Discarded; drives blackbox decision | `mem_dual` |

**Two of two HQC modules examined carry latent standards violations that
Vivado accepts silently.** Possibly the strongest ASIC contribution: published,
peer-reviewed PQC RTL contains defects a permissive tool masked.

---

## IN FLIGHT when the session ended

**1. Parse sweep** (`asic/scripts/parse_sweep.sh`), elaborating all 59 files in
`build/joint_design/` to count defects per file. Was at ~42/59.

```bash
ssh engr 'wc -l < ~/pqc/hqc/asic/out/parse_sweep.txt; cat ~/pqc/hqc/asic/out/parse_sweep.txt'
```

**Caveats on this data.** Each file is elaborated in isolation with only
`clog2.v` alongside, and `hdl_search_path` is not set, so files with
`` `include `` directives produce artifact errors. Counts are inflated by
cascade. **Treat as a screen, then verify each hit individually** by confirming
the symbol is declared later in the same file. Rows ~17-20 were written while
an ML-DSA probe ran concurrently and may have read the wrong log; re-run those
four.

**2. ML-DSA arm comparison, staged but not started.** This is the highest-value
remaining experiment, because it is the case where the agent's edit sits on the
binding path (unlike F6).

- Arms at `asic/arms/mldsa_baseline/` and `asic/arms/mldsa_optimized/`,
  33 `.v` files each, top module `combined_top`, 36 modules total.
- Sourced from `minerva_ws/mldsa_pristine/src_rtl` and
  `minerva_ws/mldsa_combined/src_rtl`. Ten files differ between arms.
- The key edit is `encoder.v`: 256b variable-shift PISO replaced by a banked
  256b ACC plus 4-deep word FIFO (commit `dca29bc`). FPGA result was chip
  post-route closure 73.4 -> 78.6 MHz, +12.0% vs baseline 70.2 MHz.
- Probe script `asic/scripts/mldsa_probe.tcl` exists on the server but its
  first run was killed to protect the sweep. **Elaboration has never
  succeeded.**

```bash
ssh engr 'cd ~/pqc/hqc/asic/scripts && GENUS_SRCDIR=../arms/mldsa_baseline timeout 1800 genus -no_gui -f mldsa_probe.tcl > /dev/null 2>&1; echo EXIT=$?'
ssh engr 'ls -t ~/pqc/hqc/asic/scripts/genus.log* | head -n 1 | xargs grep -n -m 1 -B 8 "Error"'
```

Expect a portability tail on the GMU codebase. If v2001 fails on syntax, try
`-language sv`. **ML-DSA fixes must pass the ML-DSA equivalence gates**
(`agent/mldsa/*_equiv_gate.py`), not the HQC KAT.

---

## Known limitation needing a decision

**HQC's real chip-level binding path is unmeasurable under current method.**
From `chip_orchestrator_log.jsonl`, the HQC closure path is
`ENCAP_MODULE/theta_addr_reg[2]/C` ->
`SHAKE256/data_path_instance/state_ram_instance/...`. It terminates **inside**
the state RAM, which blackboxing removes.

Proposed fix, not yet implemented: **selective blackboxing by size.** The
Keccak state is small (25 entries x `PARALLEL_SLICES` bits, ~1600 flops) and
synthesizes flat fine; the large polynomial memories are what caused the
30-minute timeout. Blackbox above a stated size threshold, synthesize flat
below it, apply the identical rule to both arms, state it in the method.

---

## Next steps, priority order

1. Finish and **verify** the parse sweep (isolate real defects from artifacts).
2. ML-DSA baseline elaboration, then the arm comparison at high effort.
3. Selective blackboxing so HQC's SHAKE256 path becomes measurable.
4. **Backend abstraction in `agent/`.** The measurement path is ported; the
   optimizer loop still calls Vivado directly. Abideen asked for "the agent
   ported to Genus," and this is the remaining gap. Do not claim the agent is
   ported until this is done.
5. Repository reorganization (own session, KAT at the end to prove nothing
   broke): consolidate logs under `experiments/logs/{hqc,mldsa,cross}/`,
   gitignore `build/`, move optimized RTL into tracked source to fix F7.
6. Related Work and Methodology drafting for D&T.

**Deferred:** Innovus place-and-route, Xcelium-based ASIC KAT gate.

---

## Reference: verified numbers from the FPGA arc

Do not re-derive these; they are established.

- ML-DSA optimized 82.7 MHz vs baseline 70.2 MHz, +17.8%, reproduced twice
- HQC optimized 116.0 MHz vs baseline 114.8 MHz, +1.9%, post-route closure
- 59 gated proposals, 33 applied, 14 functionally incorrect. **Reconciled and
  reproducible**: 65 records across four edit logs less 6 terminators = 59.
  Script in `docs/findings/FINDINGS_gate_catch_rate.md` reproduces
  59/33/14 exactly. Latency-preserving 4/23 gate-caught, latency-changing
  10/10.
- Only one HQC edit was ever ACCEPTED: `flag_precompute` on `v_minus_uy`,
  WNS -2.233 -> -1.507, commit `12d930d`.

## Related Work outline (D&T, Lloyd's section)

1. LLM-generated RTL (VeriGen, RTLLM, VerilogEval, VeriThoughts): generation
   from spec, correctness measured but not enforced as a gate
2. LLM-assisted optimization and classical DSE (Minerva): no correctness gate,
   or search over tool directives rather than RTL
3. PQC reference hardware (Deshpande SAC 2023, GMU/Beckwith): hand-optimized
   expert designs, sets the bar. Note the SAC paper explicitly rejects
   SHAKE256 critical-path pipelining on cycle-count grounds, and the design
   now binds exactly there
4. Equivalence checking as a gate: rarely wired into an autonomous edit loop

Differentiator: optimize **existing verified** RTL under a gate the model
cannot influence, and report negatives including cross-target transfer failure
(F6) and portability defects a permissive tool masked (F1, F4, F5).

Reference budget is 12. This outline will need cutting.
