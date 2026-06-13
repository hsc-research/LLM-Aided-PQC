# Optimization Agent Architecture

The agent applies the optimization taxonomy automatically. Its design principle,
arrived at through eleven-plus supervised flights, is a strict division of
labor: **code performs every decision that can be checked mechanically; the
language model performs only the irreducibly creative step** (classifying a
critical-path cluster and designing an equivalence-preserving edit). Every
defect observed in early flights came from the model guessing at file state it
could not see, so the harness removes those guesses one by one.

## Pipeline (loop_v21.py)

1. **Target selection (code).** `target_selector.py` parses the top-N
   critical-path report, groups paths by source register into clusters, ranks by
   worst slack, and skips clusters that are exhausted (no live combinational
   comparison remains on the source register, checked by a search that excludes
   the agent's own flag-update assignments) or skip-listed from a prior run. It
   hands the model exactly one cluster. The model does not choose targets.

2. **Ground truth (code).** `ground_truth.py` emits a machine-computed inventory
   for the chosen register: every assignment site with its right-hand side,
   every live comparison, existing flag machinery, combinational sensitivity
   lists that mention the register, and the complete always-blocks. The model
   reads these counts; it never derives them. A sanity assertion fires if a
   register has comparisons but zero assignment sites, which catches inventory
   bugs rather than passing a false inventory to the model.

3. **Proposal (model).** `optimizer_v2.py` sends the board, the inventory, and
   the always-blocks to the model, which returns either `no_action` (with a
   reason) or a typed experiment: a list of edit operations.

4. **Dry-run echo (code + model).** The proposed operations are applied to
   temporary copies and the resulting unified diff is shown back to the model for
   confirmation before any real file is touched. This converts "a gate refused
   after the fact" into "the model inspects the actual effect of its own edit."

5. **Gated apply (code).** `edit_ops.py` applies the operations to the real
   build trees only if every gate passes. Application is all-or-nothing, with a
   timestamped backup of each file.

6. **Synthesis and measurement (code).** The change is synthesized and the
   per-cluster slack is compared to the pre-edit value. A change that does not
   improve the targeted cluster by a minimum threshold is reverted and
   skip-listed.

7. **KAT (code).** A change that passes the gain threshold is checked against the
   full KAT chain. A KAT failure reverts the change and halts the run for human
   review (a semantic miss warrants eyes). A pass leaves the change staged with
   its backup for manual commit.

Every flight appends one line to `flight_log.jsonl` recording the target and the
verdict, so failures accumulate into a dataset rather than scrolling away.

## Edit operations (edit_ops.py)

The model cannot write free-form Verilog. It emits typed operations:

- `declare_reg` — declare a new register; the harness places it at module scope
  (after the last module-scope `reg`/`wire`). The model does not choose the
  declaration's location.
- `pair_assignments` — for a named register and flag, insert a flag-update
  assignment at every assignment site, computed from each site's right-hand
  side. The expected site count is asserted.
- `regex_swap` — replace a comparison expression with a flag read, guarded so the
  pattern must mention the register it claims to be about, and refused on
  assignment lines.
- `replace_exact` — exact-match replacement with an expected hit count, used for
  sensitivity-list edits and similar precise changes.

## Safety gates and their origins

Each gate was added in response to a real failed proposal. Together they form the
agent's immune system.

| Gate | What it prevents | Originating failure |
|------|------------------|---------------------|
| Exact-count assertion | Wrong number of sites/consumers edited | Multiple early flights |
| Duplicate-text | Re-proposing an edit already in the file | A re-proposed existing flag |
| `whole_line` match mode | A legal substring match corrupting an unintended line | A test-harness incident that corrupted a FIFO file |
| Cross-register | Swapping a comparison that belongs to a different register | A flag paired to one register while swapping another's compare |
| Flag-of-a-flag | Editing the right-hand side of an existing flag-update line | A proposal targeting flag machinery |
| Sensitivity-list add-only | Removing a signal from a sensitivity list (simulation/synthesis mismatch) | A proposal that deleted a sensitivity-list entry |
| New-flag-name | Reusing an existing flag's name and double-driving it | A proposal pairing an existing flag onto a new register |
| Declaration-placement | A `reg`/`wire` declaration inserted inside an always block (illegal) | The first full v2.1 flight (resolved structurally by `declare_reg`) |

## Flight log narrative

The supervised flights show a clear progression from gated-but-failing to
operational:

- **Reasoned declines.** On boards whose clusters are genuinely exhausted, the
  agent returns `no_action` with a correct, conservative reason (for example,
  recognizing that every comparison on a register is already a flag). Declining
  a non-target is a required capability for an autonomous optimizer.
- **A caught illegal edit.** The first attempt to optimize a new board produced
  a correct target and a sound equivalence argument but placed the flag
  declaration inside an always block. Synthesis would have failed; the
  declaration-placement gate caught it, and the `declare_reg` operation then made
  the error structurally impossible.
- **An autonomous reverted non-win.** With the harness complete, the agent ran a
  full flight end to end on a board previously believed RTL-exhausted: it found a
  real comparison target the human analysis had missed, proposed a correct
  edit, applied it through every gate, synthesized, measured a per-cluster
  regression (the cone was logic-light, a documented non-candidate), and reverted
  autonomously. Finding a real target *and* correctly declining it on the
  measured result is the key behavior: an autonomous optimizer must reject
  non-improvements without human intervention, not merely find improvements.

The same discipline that governs the manual methodology — read the path detail
before theorizing, argue equivalence before editing, trust the synthesis verdict
over intuition, and revert without sentiment — is what the harness enforces in
code.
