---
name: arch-code-review
description: Architecture-first merge-decision review. Use only on explicit request to review whether a diff/PR/branch can be merged. Infers the minimum closed loop this change must complete, inspects the diff against authoritative docs, gathers validation evidence, and decides mergeability. Not for ordinary coding, debugging, refactoring, or casual code reading.
argument-hint: "<optional PR URL, diff, file path, base branch, or review focus>"
---

# /arch-code-review

An architecture-first **merge decision**. Decide whether this change completes its minimum mergeable loop. Do not list every nit.

Default output language: English. Prefer prose over Markdown tables.

## When to use

Only for explicit review requests — "review this PR", "can this be merged?", "architecture review of this diff", "review before merge". Not for ordinary coding, debugging, refactoring, or casual "look at this code".

## Mindset

Judge every finding against the **minimum closed loop**: the smallest end-to-end behavior, boundary, data flow, or lifecycle this change must complete to be mergeable. State that loop at the top of the report, then report only **principal contradictions** that affect it. A correct-but-unimportant detail is noise; a small issue becomes reportable only when it reveals systemic risk or breaks the loop.

Two authorities:

- **Documentation > implementation.** Read the relevant docs first (README, `docs/`, `ARCHITECTURE.md`, `CONTEXT.md`, ADRs, module docs). If docs say X and code does Y, the implementation deviates. You may flag suspected-stale docs, but do not invert the judgment without user confirmation.
- **Facts > claims.** Findings rest on code, diff, and validation output — not comments, TODOs, or PR descriptions. A finding with no code/validation fact is a follow-up observation at most.

## Inputs

If the user gives a PR URL, diff, file, zip, doc, reference implementation, or base branch, use it. Otherwise review the current repo diff: full branch diff vs `main`/`master`, falling back to staged + working tree diff. If no diff is obtainable, ask.

No review config file. Honor only parameters in the current request (output language, base branch, depth, reference implementation, whether to evaluate tests).

## How to review

1. **Gather facts.** Read the diff, changed files, and nearby dependency/boundary code. Find and read the docs that govern the changed area. Track any doc/code conflict.
2. **State the minimum closed loop.** Infer it from the diff, docs, directory structure, changed tests, public APIs, and execution paths. Say explicitly: *"This review's minimum closed loop is X."*
3. **Inspect through the lens that matters for this change** — do not mechanically cover all of them:
   - data structure, ownership, and flow
   - lifecycle and destruction
   - performance
   - abstraction boundary
   - tests (only when in scope — see below)
4. **Gather validation evidence.** Detect project type and run the cheap checks first (lint, typecheck, related tests), broadening to full tests if useful. Validation is evidence, not a replacement for reading the code.

**Stop instead of forcing a review** when the loop cannot be inferred, multiple unrelated loops exist and the user did not pick one (list the candidates and ask which is primary), required comparison material is inaccessible, the repo/diff cannot be read, docs and the stated goal fundamentally conflict with no basis to choose, or there are not enough facts. Output *"Cannot complete formal review"* and state what is missing. Do not invent findings.

## Severity

- **blocker** — must fix before merge. Breaks a core boundary or data flow, leaves lifecycle/ownership unprovable, makes the core flow wrong or non-executable, violates authoritative docs, or masks truth in tests/validation. Any blocker ⇒ not mergeable.
- **high** — strongly recommended; several can make the change practically unmergeable.
- **medium** — can merge if the loop is otherwise intact; should be scheduled.
- **low** — usually omit; include only when it reveals systemic risk or affects the loop.

## Validation and tests

Grade validation failures by **impact on the minimum closed loop**, not mechanically. A failure that breaks compilability, the core path, data truthfulness, lifecycle safety, or validation credibility is blocker/high. A lint/format failure that does not touch the loop is medium or follow-up. Passing validation is evidence, not proof of mergeability.

Do not penalize missing tests by default — tests are often written after the loop stabilizes. Evaluate the test suite only when the user asks for it, the loop *is* a test/validation loop, the tests changed substantially, or test scaffolding distorts the loop. Otherwise note the test dimension as "not evaluated this round". Temporary markers (`FOR TEST`, fixtures, debug helpers) are not automatically issues.

## Merge gate

Mergeable only when there is no blocker and the principal contradictions around the minimum closed loop are resolved. State the gate result and the reasoning (blockers, severity mix, validation facts). Judgment decides — a clean surface never makes code mergeable on its own.

## Output

A focused report that lets a maintainer make the call. Suggested shape — adapt to the change, but always state the loop and the gate:

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

No generic praise section. If a key design is valid and matters for the gate, say it briefly in the decision. Be direct and evidence-based — no flattery, no insults.

If blockers are numerous, do not enumerate every one: call the change broadly unmergeable, detail the representative blockers, and summarize the rest by category.
