# Assurance-Guided LLM-Based RTL Optimization for PQC Accelerators

An optimization agent for post-quantum cryptographic hardware. A language
model proposes RTL edits; deterministic code applies and verifies them; a
cryptographic correctness gate decides what is kept. The model is structurally
untrusted: it cannot influence any check that decides acceptance.

Two NIST-standardized designs:

- **ML-DSA** (FIPS 204, lattice signature), GMU/Beckwith implementation
- **HQC** (code-based KEM), Yale/Deshpande implementation, SAC 2023

Both target an AMD Artix-7 `xc7a200tfbg676-1`. An ASIC arc on ASAP7 7 nm
(Genus + Innovus) is in progress.

---

## THE ONLY VALID SOURCE OF NUMBERS

**[findings/INDEX.md](findings/INDEX.md)** carries the canonical ledgers:
block-level WNS, ML-DSA chip-level, and HQC chip-level. Each chip-level entry
records the command that reproduces it and the commit it was measured at.

A number that is not in a ledger may not be quoted in a paper, abstract,
slide, or email. Superseded numbers stay in the ledger, marked, with the
reason. See [DOCUMENTATION_STANDARD.md](DOCUMENTATION_STANDARD.md).

### Current headline results

| Design | Baseline | Optimized | Delta | Measured |
|---|---|---|---|---|
| ML-DSA `combined_top` | 70.2 MHz | 80.5 MHz | +14.7% | post-route closure, OOC |
| HQC joint KEM | 109.6 MHz | 116.0 MHz | +5.8% | post-route closure, OOC |

Every frequency is a *closing* frequency: binary-searched period, fully placed
and routed, non-negative slack. Frequency is never projected from a violated
run by `1/(T - WNS)`; numbers derived that way were retracted.

---

## Where to start

| Document | Contents |
|---|---|
| [findings/INDEX.md](findings/INDEX.md) | **Canonical ledgers and a one-line map of every experiment.** Start here. |
| [DOCUMENTATION_STANDARD.md](DOCUMENTATION_STANDARD.md) | How results are recorded, retracted, and superseded |
| [01_results.md](01_results.md) | The fifteen HQC block-level wins, cross-level timing, PPA deltas |
| [02_optimization_taxonomy.md](02_optimization_taxonomy.md) | Optimization patterns, the fingerprints that predict success or regression, and the negatives |
| [04_agent_architecture.md](04_agent_architecture.md) | Agent pipeline, gates, flight log |
| [REPRODUCE.md](REPRODUCE.md) | Fresh machine to reproduced results |
| [2026-08-02_asic_game_plan.md](2026-08-02_asic_game_plan.md) | Current ASIC plan and the RTL freeze |
| [findings/](findings/) | Dated lab notes, preserved verbatim, including every negative |

---

## The three findings that shaped the work

**Block-level acceptance does not predict chip-level outcome.** Composing four
individually verified ML-DSA block edits and re-closing gave 69.0 MHz against
a 70.2 MHz baseline, a net regression. The real bottleneck was a 256-bit
variable-shift serializer that no block-level run could see. Chip-level
closure is the only valid judge.

**Correctness cannot be sampled.** Of 33 applied edits, 14 were functionally
wrong. All 14 compiled and simulated cleanly. Only a checker separated them
from the 4 commits. The failure rate is lane-dependent: 4 of 23
latency-preserving, 10 of 10 latency-changing.

**Priors transfer across hardness assumptions; bottlenecks do not.** The
ML-DSA rule set applied verbatim to HQC produced a win for $0.037 in one call,
and the binding path moved off the edited datapath onto the shared Keccak
permutation. Neither design is limited by its own arithmetic.

---

## Repository layout

| Path | Contents |
|---|---|
| `hardware/` | **Authoritative RTL.** Common source for both Vivado and Genus. |
| `build/{keygen,encap,decap,joint_design}/` | Elaborated trees that are synthesized and simulated. Win-carrying files are tracked. |
| `agent/` | Agent code. `hqc/` and `mldsa/` hold per-design orchestrators and gates. |
| `agent/backends/` | Synthesis backend abstraction (Vivado, Genus) |
| `agent/port/` | Cross-toolchain port-fix loop and its three-stage gate |
| `asic/` | ASAP7 scripts, SDC, arms, results. Does not touch `hardware/` or `build/`. |
| `synth_out/` | Synthesis reports, checkpoints, extracted paths |
| `docs/` | This documentation |

## Correctness gates

Every accepted RTL change passes a Known-Answer Test. For HQC the full
keygen -> encap -> decap chain must reproduce matching shared secrets at
HQC-128, 192, and 256. For ML-DSA a 25-vector NIST KAT runs against the full
design, with cycle-accurate lockstep equivalence at block level.

Each gate is corruption-validated before autonomous use: it must reject an
injected boundary fault and a live-branch arithmetic fault. This found a real
blind spot in a Fisher-Yates comparison, which the repaired gate later used to
correctly reject an unsafe agent proposal.
