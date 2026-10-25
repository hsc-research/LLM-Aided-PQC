# Agent status and next improvements

[Agent workflow](../agent/README.md) · [Design coverage](PROJECT_STATUS.md) ·
[ASIC qualification](../asic/README.md)

Code audit, 2026-10-12. The agent is a constrained, report-guided experiment
driver. Its existing safeguards are useful; they do not establish that an
LLM-generated implementation is correct, faster, or secure before measurement.

## Whole-design-first default

The intended default workflow is:

1. Establish the complete baseline with a fixed design/configuration and its
   correctness evidence.
2. Measure the full design and inspect several of its worst critical paths.
3. Trace those paths to the smallest responsible RTL blocks and their relevant
   control, memory, or integration context.
4. Propose a small, constrained edit; run inexpensive checks and the applicable
   correctness gates. A block-only result is a filter or diagnostic.
5. Rebuild and remeasure the complete candidate under matched settings, accept
   only a valid objective improvement, and otherwise restore the prior state.
6. After acceptance, extract fresh full-design paths before the next iteration;
   the bottleneck may have moved.

The new [whole-design controller](WHOLE_DESIGN.md) implements this sequence
through explicitly configured adapters. It includes a candidate budget,
repeated-attempt filtering, failure feedback, fixed-configuration comparison,
operation-cycle and area guards, and rollback through final outcome recording.
Its built-in proposer uses the existing model opt-in; its ASIC adapter uses the
fixed-period synthesis runner. It has passed offline software tests, not an
end-to-end licensed-tool optimization run. Real timing-path ownership, full
functional coverage and site inputs remain qualification requirements.

The older chip driver remains a one-round FPGA flow with one worst-path mapping.
Its block runners do not yet receive the complete multi-path context used by the
new controller. The interfaces remain separate to preserve existing workflows.

## Implemented now

- **Vivado:** verify the full baseline before measuring it, map its worst reported routed path to an
  RTL file, and optionally dispatch one supported optimization round. Block
  runners use timing-path features and a strategy menu, exact-anchor edits,
  design-specific tests, synthesis feedback, and acceptance/reversion. The
  top-level driver independently checks the candidate and remeasures routed
  setup closure. It retains an edit only if the observed closing frequency
  improves. Search is bounded heuristic sampling, not proof of maximum Fmax.
- **Protection:** scoped snapshots preserve pre-existing working changes;
  failures restore paired files and checkpoints. Effective source hashes are
  checked across verification and implementation, with unique measurement
  artifacts and a top-level checkout lock.
- **Feedback:** block successes are recorded as preliminary filter passes.
  Only the chip driver records final acceptance, after correctness checks and
  full remeasurement. History-write failure still rolls back the candidate.
  Applied-edit claims require matching current source/include hashes. Rule
  distillation waits for recorded final acceptance and a successful source
  transaction; provisional and
  legacy unqualified rules remain archived but are excluded from automatic
  prompt injection. Full-chip rejections remain diagnostic context, without
  automatically banning the strategy. A
  separate experimental ML-DSA latency runner can feed stream divergence back
  into pipeline/retap repair. It is not selected by generic chip dispatch.
- **Genus / Design Compiler:** separate configurable, fixed-period logical
  synthesis measurements, with manifests, input/report hashes, error checks,
  and timing/area/power parsing. The runner does not propose RTL changes or
  make an automatic baseline/candidate acceptance decision. Neither commercial
  tool has qualified this revision; offline mocks and Tcl stubs are software
  tests, not vendor-tool or PPA results. ASIC place-and-route is absent.

### Generic dispatch coverage

ML-DSA's block runner registers `rejection_a`, `rejection_s`, `rejection_y`,
`makehint`, `gen_c`, `decoder`, and `usehint`. Actual selection also depends on
the chip hierarchy-to-file mapping. Mapped `encoder`, `coeff_decomposer`, and
`butterfly` targets fail closed as unsupported by this runner.

HQC transfer dispatch supports `encap` and `decap`, now explicitly passing
`hqc128` to the block runner. Full-design candidate admission still requests
all three levels. The joint integration file uses its separate bounded runner.
Other currently mapped HQC file stems are rejected before starting an optimizer;
their source filenames are not automatically valid synthesis module keys.
SLH-DSA and ML-KEM generic optimization dispatch remain unavailable. The pinned
ML-KEM reference source and baseline launch inputs are now bundled; see
[design coverage](PROJECT_STATUS.md).

These are software dispatch capabilities, conditional on complete sources,
working tests, tool access, and model opt-in. They are not newly measured wins.

## Remaining qualification and improvements

1. **Real tool adapters:** qualify complete source lists, functional checks,
   cycle profiles and timing-path ownership against the actual tool versions.
   The new ASIC adapter runs synthesis but requires a reviewed path extractor;
   FPGA normalized measurement remains site-provided.
2. **Legacy entry points:** the older chip driver still uses one worst path and
   timing-only acceptance. The new controller supplies explicit area/latency
   limits and fixed-configuration comparison; it does not silently change the
   behavior of all historical scripts.
3. **Verification coverage:** legacy HQC uses shared-secret consistency; the
   SAC 2026 import is still source-only. Legacy ML-DSA dispatch and the built-in
   controller adapter declare KeyGen-only coverage. Separate guarded/corrected
   ML-DSA variants now pass 210 portable cases, and corrected SLH variants have
   pinned vendor-stream evidence; consult [current status](PROJECT_STATUS.md)
   for exact source/mode coverage. These are not automatic source-routing or
   coverage upgrades for legacy dispatch. ML-KEM has separate official-vector
   sample evidence. No wrapper creates formal equivalence, constant-time or
   leakage proof, and SHAKE-family SLH remains unsupported.
4. **Learning:** only final accepted, source-matching legacy outcomes qualify
   applied-edit history. More precise reuse across equivalent tool/library/
   constraint settings and richer first-failing-cycle diagnostics remain useful.
   The new controller already passes recent failure feedback and whole-design
   critical-path context to the proposer and rejects repeated attempts.
5. **Objectives:** current whole-design admission supports timing/area objectives
   with declared limits and exact measured operation cycles. Workload-qualified
   power, statistical repeatability, Pareto search and ASIC physical design are
   separate future work.

A larger model alone does not resolve missing inputs, invalid comparisons or
unsupported correctness claims. Qualify the measurement and checking flow first.
