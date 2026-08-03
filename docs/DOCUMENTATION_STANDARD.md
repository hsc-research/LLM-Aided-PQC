# Documentation Standard

Purpose: any number that reaches a paper must be traceable to a log in one
step, and any new conversation must be able to reconstruct project state
without re-deriving it.

Written after the ICCAD abstract, where numbers from different runs were
mixed up during writing.

---

## 1. The Results of Record rule

Every findings doc opens with a **RESULTS OF RECORD** table. Nothing outside
that table is a result.

Required columns:

| # | Design | Config | Effort/Directives | Metric | Value | Log path | Date |

Rules:

- **A number that is not in a Results of Record table may not be quoted
  anywhere.** Not in an abstract, not in a paper, not in a slide, not in an
  email.
- Every row carries a **log path** that exists in the repo. If the log is not
  committed, the number is not a result yet.
- Every row carries the **measurement configuration** that would change the
  number if varied (effort, directives, synthesis mode, corner, blackboxing).
- Rows get **stable IDs** (A1, A2, F1, F2 ...). Cite the ID in conversation
  and in drafts, never a bare number.
- Control experiments are **labeled as controls**, with an explicit line
  saying they are not results.
- A **"what does not exist yet"** paragraph follows the table. This is what
  prevents accidental claims.

## 2. Retractions are permanent and visible

When a number is retracted (as projected Fmax was), it stays in the doc struck
through with the reason, and the prohibition is written into the method
section. Deleting it means someone re-derives it in three weeks.

## 3. Terminology is fixed once

A findings doc defines its terms in a table and does not vary them. Current
fixed terms:

| Term | Means |
|---|---|
| baseline | Unmodified RTL, control arm |
| optimized | RTL after agent edits, treatment arm |
| initial characterization | The May 2026 Vivado PPA survey |
| closure | Binary search to minimum MET. Never projected |

Retired: "pristine".

## 4. Findings are numbered and portable

Each substantive finding gets an ID (F1, F2, ...) and states:

1. What was observed, with the exact tool message or number.
2. What was done about it.
3. How it was verified.
4. The commit hash.
5. What it implies for the paper, if anything.

A finding without a verification line is a hypothesis, and should say so.

## 5. Every doc ends with a file map

Table of what lives where, including what is on a server and not in git.
Prevents work existing in exactly one place.

## 6. Commit discipline

- RTL edits: `.bak` -> anchor-count assert -> gate -> KAT -> synth -> commit.
- Scripts that produced a number get committed **before** the number is
  quoted.
- Logs referenced by a Results of Record row get committed with the row.
- Commit messages state the verification: "KAT PASS at HQC-128/192/256".

## 7. File formats

- Findings: `.md` in `docs/findings/<area>/`
- Paper deliverables: `.docx` in IEEE format, or `.tex` for Overleaf abstracts
- Never deliver a paper artifact as Markdown

## 8. Session close checklist

Before ending a working session:

1. Results of Record updated with any new number.
2. Logs pulled off any remote machine and committed.
3. Scripts committed.
4. "Next steps" section updated with what actually gates progress.
5. Open questions for the advisor listed explicitly.

## 11. Supersession is recorded in both directions

A new result that replaces an old one must say so, and the old one must say it
was replaced. One direction is not enough: a reader who finds the old document
first has no way to know it is stale.

When a result supersedes another:

1. The new doc lists **what it invalidates**, by ID and by file, in a
   "Supersedes" block near the top.
2. The old doc gets a **banner at line 1** naming the replacement.
3. The retracted row stays in its Results of Record table, struck through,
   with the reason.
4. `docs/findings/INDEX.md` marks the old entry SUPERSEDED and the new one
   CURRENT.
5. **Grep for the number.** A result quoted in `01_results.md`, the README, an
   abstract, or a paper draft will not update itself:
   `grep -rn "<the number>" docs/ README.md`

Point 5 is the one that gets missed. A findings doc can be correctly retracted
while the number it retracted is still being quoted three files away.

---

# Handoff Prompt for a New Conversation

Paste this at the start of a new chat, with the current findings docs attached
or in the project.

---

I am continuing work on a correctness-gated, LLM-driven optimization agent for
post-quantum cryptographic FPGA and ASIC accelerators. Before answering
anything, read the findings docs in `docs/findings/` and treat their RESULTS
OF RECORD tables as the only valid source of numbers.

Ground rules for this conversation:

1. **Never quote a performance number that is not in a Results of Record
   table.** If I ask about a result and you cannot find it there, say so
   rather than reconstructing it from context or from your own earlier
   reasoning.
2. **Distinguish measured from proposed.** If something appears in a findings
   doc as a next step, a hypothesis, or a suggestion, do not describe it as a
   result or a decision.
3. **Cite finding IDs and result IDs** (F1, A1, ...) rather than restating
   numbers loosely.
4. **Measurement configuration travels with the number.** Effort level,
   synthesis directives, corner, OOC mode, and blackboxing all change results
   and must be stated whenever a number is used.
5. **Do not let me claim a delta that is smaller than the known tooling
   sensitivity** without flagging it. On Genus, effort setting alone moves
   Fmax by about 11% (F3).
6. I run all commands locally and paste output. Give concise code and
   directions, not free-form RTL. No em dashes in any deliverable.
7. RTL edits follow: `.bak` -> anchor-count assert -> gate -> KAT at all three
   security levels -> synth -> commit. Ask for explicit approval before any
   edit to a source file.
8. Watch for vacuity: a gate can pass on files that were never edited. Verify
   that the files being synthesized are the files that were changed.

If you are unsure whether something is established or proposed, ask rather
than assuming.
