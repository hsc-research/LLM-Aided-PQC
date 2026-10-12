# Learn the project

[Project home](../README.md) · [Documentation](README.md) · [Results](RESULTS.md) · [Run](REPRODUCE.md)

## What is this repository trying to do?

Improve the timing or resource use of existing post-quantum cryptographic
hardware without breaking its tested behavior. The starting point is RTL,
not a new algorithm. A timing report identifies a slow path; an optional LLM
suggests a small source edit; ordinary scripts test and measure the result.

There are three kinds of material here:

1. **Hardware:** reference designs, edited candidates, memories and test data.
2. **Tools:** Python/Tcl scripts for testing, synthesis, implementation,
   source protection and accepting or rejecting an edit.
3. **Evidence:** simulator records, timing/resource reports, accepted and
   rejected experiments, and corrections to earlier claims.

You can study the designs and reports without running an optimization or
using a model API. Start with the [repository map](REPOSITORY_LAYOUT.md).

## The four design families

| Family | Operations | Starting point in this repo |
|---|---|---|
| ML-KEM | Generate keys, encapsulate a shared secret, decapsulate it | Adam's Bridge: a shared ML-KEM-1024 / ML-DSA-87 accelerator, including memory models |
| ML-DSA | Generate keys, sign a message, verify a signature | Pinned ML-DSA-OSH mixed Verilog/VHDL sources, with separate edited FPGA/ASIC snapshots |
| HQC | Generate keys, encapsulate a shared secret, decapsulate it | Preferred SAC 2026 source-only snapshot; earlier SAC 2023 operation/joint-design experiments remain separate |
| SLH-DSA | Hash-based signing and verification | SPHINCSLET baseline and edited RTL; the current differential checker supports six SHA2 parameter sets |

These describe the design families, not a promise of full local test coverage.
Check [current status](PROJECT_STATUS.md) for the exact tested operations,
parameter sets, simulators and open limitations. The Adam's Bridge core is
shared hardware: testing its ML-KEM interface does not separately verify its
ML-DSA function or yield an ML-KEM-only area measurement.

## Why start with the complete design?

A fast arithmetic block does not necessarily make an accelerator faster.
After integration, a mux, control signal, RAM port or long routed connection
can be the slowest path. An edit can also move the bottleneck to another block.

The intended sequence is:

```text
Test baseline → measure complete design → inspect worst timing paths
    → choose a small RTL region → propose and apply an edit
    → test complete candidate → remeasure with identical settings
    → accept a measured improvement, or restore the previous sources
```

The [historical ML-DSA result](RESULTS.md#historical-fpga-results) illustrates
this: block work did not expose the complete design's encoder bottleneck.
After a human-authored banked encoder rewrite, the binding path moved to the
challenge sampler. The complete design's timing decided the result.

The [whole-design controller](WHOLE_DESIGN.md) implements this sequence with
explicit test and measurement commands. Its current tests use synthetic
measurements to check the control flow. Real vendor tools, report parsing and
path-to-source mapping still need qualification at the user's site.

## What the model does, and what the scripts do

| Part | Responsibility |
|---|---|
| Optional LLM proposer | Read selected RTL/timing context and return a bounded edit proposal |
| Edit code | Enforce allowed files and exact edit locations; apply the proposal |
| Functional runner | Simulate the selected design and compare the declared outputs/checks |
| Measurement tool | Synthesize or implement the actual candidate and emit timing/resource reports |
| Controller | Compare matched full-design results, retain accepted edits, and restore failed or rejected edits |

The proposer does not certify correctness, invent measurements, or decide that
a missing test passed. Tests and reports must refer to the same candidate
source bytes. Use a dedicated checkout; these protections are for cooperating
research workflows, not hostile programs.

## How to read a result

Ask these questions in order:

1. **What was built?** Full accelerator or one block? Which operation,
   parameter set, source revision and memories?
2. **What was tested?** Official known-answer samples, a reference-output
   comparison, or internal consistency? How many cases actually completed?
3. **What was measured?** FPGA post-route timing, ASIC pre-layout logic
   synthesis, or only a software test with fake reports?
4. **Was the comparison fair?** Same tool, constraints, library/device,
   hierarchy, memory treatment and functional coverage?
5. **What changed?** Timing, area and cycle count can trade against each other.
   A timing gain alone does not establish lower power or energy.

The [results guide](RESULTS.md) starts with the evidence available now and
then points to the historical measurements. The [verification record](VERIFICATION.md)
explains actual local runs separately from source checks and mock-tool tests.

## Small glossary

| Term | Meaning here |
|---|---|
| RTL | Verilog/SystemVerilog/VHDL source describing clocked hardware |
| Baseline / candidate | Reference source version / proposed edited version |
| Gate | A check that must pass before the next stage; not a physical logic gate |
| KAT | Known-answer test; inspect its provenance because some legacy scripts use this name for consistency or differential checks |
| ACVP | Automated Cryptographic Validation Protocol; this repo uses published sample vectors, without claiming validation certification |
| Critical path | A timing path that limits operation at the selected clock constraint |
| WNS | Worst negative slack in a timing report; a negative value means a reported setup path misses the constraint |
| Closing period | A tested clock period at which the recorded implementation meets setup timing |
| OOC | Out-of-context: implement a block or core apart from a board's top-level IO; always state the hierarchy boundary |
| PPA | Power, performance and area; missing power or physical implementation must remain missing |
| LUT / FF / BRAM / DSP | FPGA lookup tables, flip-flops, block RAM and arithmetic resources |
| SDC | Timing constraints supplied to the synthesis/implementation tool |
| Adapter | A reviewed command wrapper connecting the controller to a particular checker or hardware tool |

## Where to go next

- **Run something now:** [offline setup and checks](REPRODUCE.md#2-run-the-offline-checks)
- **Read numerical results:** [historical FPGA results](RESULTS.md#historical-fpga-results)
- **Inspect actual test evidence:** [verification record](VERIFICATION.md)
- **Start a hardware experiment:** [staged run guide](REPRODUCE.md)
- **Add a design or measurement tool:** [controller protocol](WHOLE_DESIGN.md)
