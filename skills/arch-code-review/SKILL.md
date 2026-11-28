---
name: arch-code-review
description: Architecture-first merge-decision review. Use only when explicitly asked to review whether a diff/PR/branch can be merged. Infer the minimum closed loop this change must complete, check that diff against authoritative documentation, gather validation evidence, and decide mergeability. Not for ordinary coding, debugging, refactoring, or casual code reading.
argument-hint: "<optional PR link, diff, file paths, baseline branch, or review focus>"
---

# /arch-code-review

An architecture-first **merge decision**. Decide whether this change has completed its minimum mergeable closed loop. Do not itemize every small nit.

Default output language: English. Prefer prose over Markdown tables.

## When to use

Only for explicit review requests — "review this PR", "can this merge?", "architectural review of this diff", "review before merging". Not for ordinary coding, debugging, refactoring, or casual "take a look at this code".

## Mindset

Measure every finding by the **minimum closed loop**: the smallest end-to-end behavior, boundary, data flow, or lifecycle this change must complete to be mergeable. State that loop at the start of the report, then report only the **principal contradictions** affecting it. A correct but unimportant detail is noise; a small problem earns reporting only when it exposes systemic risk or breaks the loop.

Two authorities:

- **Documentation > implementation.** Read the relevant documentation first (README, `docs/`, `ARCHITECTURE.md`, `CONTEXT.md`, ADRs, module docs). If the documentation says X and the code does Y, the implementation has departed from the documentation. You may flag documentation that looks stale, but you may not reverse that judgment without user confirmation.
- **Facts > claims.** Findings must rest on code, diff, and validation output — not comments, TODOs, or PR descriptions. A finding without code/validation facts behind it is at most a follow-up observation.

## Input

If the user gives a PR link, diff, files, an archive, docs, a reference implementation, or a baseline branch, use it. Otherwise review the current repository's diff: prefer the whole branch against `main`/`master`, degrading to staged + working-tree diff. If no diff can be obtained, ask.

There is no review config file. Obey only the parameters in the current request (output language, baseline branch, depth, reference implementation, whether to evaluate tests).

## How to review

1. **Gather facts.** Read the diff, the changed files, and neighboring dependency/boundary code. Find and read the documentation that governs the changed area. Record any documentation/code conflicts.
2. **State the minimum closed loop.** Infer it from the diff, docs, directory structure, changed tests, public API, and execution paths. Say explicitly: *"The minimum closed loop for this review is X."*
3. **Inspect through the perspectives that genuinely matter to this change** — do not mechanically cover every perspective:
   - Data structures, ownership, and flow direction
   - Lifecycle and teardown
   - Performance
   - Abstraction boundaries
   - Tests (only when in scope for this change — see below)
4. **Gather validation evidence.** Identify the project type, run the cheap checks first (lint, type check, relevant tests), escalating to the full test suite when useful. Validation is evidence; it does not replace reading the code.

**Stop when the loop cannot be inferred instead of forcing a review**: multiple unrelated loops exist and the user has not chosen one (list the candidates and ask which is primary), required comparison material is inaccessible, the repository/diff cannot be read, documentation fundamentally conflicts with the stated goal with no basis for choosing, or the facts are insufficient. Output *"Cannot complete formal review"* and say what is missing. Do not fabricate findings.

## Severity

- **blocker** — must be fixed before merging. Breaks a core boundary or data flow, makes lifecycle/ownership unprovable, makes a core flow wrong or non-executable, violates authoritative documentation, or conceals the truth in tests/validation. Any blocker ⇒ not mergeable.
- **high** — strongly recommended to fix; several highs can make the change effectively unmergeable.
- **medium** — mergeable if the rest of the loop is intact; should be scheduled.
- **low** — usually omitted; include only when it exposes systemic risk or affects the loop.

## Validation and tests

Judge validation failures by their **impact on the minimum closed loop**, not mechanically. Failures that break compilability, the core path, data truthfulness, lifecycle safety, or validation credibility are blocker/high. Lint/format failures that do not touch the loop are medium or follow-ups. Passing validation is evidence, not proof of mergeability.

Do not penalize missing tests by default — tests are often written after the loop stabilizes. Evaluate the test suite only when the user asks, the loop itself *is* a test/validation loop, tests changed substantially, or test scaffolding distorts the loop. Otherwise record the test perspective as "not evaluated this round". Temporary markers (`FOR TEST`, fixtures, debug helpers) are not automatically problems.

## Merge gate

Mergeable only when there are no blockers and the principal contradictions around the minimum closed loop are resolved. State the gate result and reasoning (blockers, severity distribution, validation facts). Judgment makes the final call — a clean surface alone never makes code mergeable.

## Output

One focused report that lets a maintainer decide. Suggested structure — adapt to the change, but always state the loop and the gate:

```markdown
# Architecture Code Review

## 1. Minimum closed loop
[the inferred loop and why; or "Cannot complete formal review" + what's missing]

## 2. Merge decision
[Mergeable / Not mergeable / Needs user decision, with reasoning]

## 3. Findings
[Each: Severity · affected area · code/validation facts · why it breaks the loop · repair direction.
Lead with blockers and highs. Give a strategic repair direction, not a full patch unless asked.]

## 4. Validation evidence
[commands run + results + how failures affect the loop; or why not run]

## 5. Doc/code conflicts
[docs vs implementation; or None]

## 6. Follow-ups
[few restrained notes — current non-blockers that may become principal contradictions later; no gate impact]
```

No generic praise paragraphs. If a key design works and matters to the gate, say so briefly in the decision. Direct and evidence-based — no flattery, no disparagement.

If blockers are numerous, do not enumerate them all: state that the change is unmergeable as a whole, detail representative blockers, and summarize the rest by category.
