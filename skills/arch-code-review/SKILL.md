---
name: arch-code-review
description: Personal architecture-first merge-decision code review skill. Use only when the user explicitly asks for architectural code review, PR review, merge review, architecture review of a diff, branch review, or asks whether a change is mergeable. This is a heavy review skill: it inspects the diff against project documentation, infers the minimum closed loop, focuses on principal contradictions, runs relevant validation as evidence, and produces an English Markdown report with severity, deduction scoring, and merge gate judgment. Do not use for ordinary implementation, debugging, linting, refactoring, or casual "look at this code" requests unless the context is clearly pre-merge review.
argument-hint: "<optional PR URL, diff, file path, base branch, reference implementation, or review focus>"
---

# /arch-code-review

Run an architecture-first merge decision review. The goal is not to list every possible nit. The goal is to decide whether this change completes the current minimum mergeable loop.

Default output language is English.

Do not use Markdown tables in the report.

## Trigger discipline

Use this skill only for explicit review requests, such as:

- code review
- PR review
- merge review
- architecture review of a diff
- review this branch / PR / diff
- check whether this change can be merged
- review before merge

Do not use this skill for ordinary coding work, normal debugging, casual code explanation, generic refactoring advice, or implementation tasks. This skill is intentionally heavy and should not hijack day-to-day development.

## Review target

If the user provides a PR URL, explicit diff, file path, zip, architecture document, reference implementation, or base branch, use that input.

If no explicit target is provided, review the current repository diff:

1. Prefer the full current branch diff against `main` or `master`.
2. If the base branch cannot be detected, fall back to staged plus working tree diff.
3. If no diff can be obtained, stop and ask for the review target.

This skill does not support a separate review config file. Accept only explicit parameters in the current user request: output language, base branch, review depth, minimum closed loop, reference implementation path, or whether to evaluate tests.

## Core principles

### Principal contradiction principle

Report only issues that matter to the current merge decision. A correct but unimportant detail is noise. A small issue becomes reportable only when it reveals systemic risk or breaks the current minimum closed loop.

### Minimum closed loop principle

Before formal review, identify the current project stage's minimum closed loop: the smallest end-to-end behavior, architecture boundary, data flow, lifecycle, validation path, or user-visible slice that this change must complete to be mergeable.

Judge every formal issue by whether it breaks that loop. This skill is not a static analyzer. It is a merge-readiness judgment.

### Documentation authority principle

Project documentation is authoritative over implementation unless the user explicitly says otherwise.

Read relevant docs before judging code. Prefer explicit user-provided docs, then repository docs such as README, `docs/`, `ARCHITECTURE.md`, `CONTEXT.md`, ADRs, design docs, module docs, and nearby package docs.

If docs say X and code does Y, default judgment is that the implementation deviates from requirements. If docs appear outdated, say "suspected stale docs" but do not invert the judgment without user confirmation.

### Fact over claims

Use code, diff, validation output, and documentation facts. Comments, PR descriptions, TODOs, and human claims are useful context but cannot replace code facts.

A formal issue without code or validation facts is not a formal issue. Put it in follow-up observations only if it may become a principal contradiction later.

## Review depth

Default depth is merge decision review:

- Decide whether the current diff reaches a mergeable minimum closed loop.
- Do not audit the entire repository or expand into old technical debt.
- Inspect historical or surrounding code only when it is a dependency, boundary, reference implementation, or documentation constraint for this diff.

If the user explicitly asks for architecture audit, expand cross-module tracing as needed, but formal issue volume remains capped except for blockers. Still preserve the principal contradiction principle.

## Stop rules

Stop before producing a formal review report when a valid merge decision cannot be made.

Output "Cannot complete formal review" and list the missing inputs when:

- the minimum closed loop cannot be inferred;
- the diff contains multiple unrelated possible closed loops and the user did not specify the primary one;
- the user requires comparison with a PR, zip, reference implementation, or document that is inaccessible;
- the repository or diff cannot be read;
- project documentation and the user's stated goal fundamentally conflict and there is no basis for choosing authority;
- there are not enough facts to support formal issues.

If multiple possible loops exist, list the candidate loops and ask the user to choose one. Do not review all of them simultaneously.

## Workflow

1. Gather the review target.
   - Read the diff, changed files, and nearby code.
   - Detect the base branch if needed.
   - Read explicit user-provided context first.

2. Read project requirements.
   - Search for relevant architecture and requirement docs.
   - Extract the requirements that govern the changed area.
   - Track any doc/code conflict.

3. Infer the minimum closed loop.
   - Use the diff, docs, directory structure, changed tests, entry paths, public APIs, and execution paths.
   - At the start of the report, state: "I believe this review's minimum closed loop is X, so I judge principal contradictions around X."

4. Review the code through the scoring directions.
   - Data structure, management, and flow
   - Data ownership, borrowing, and destruction
   - Performance
   - Abstraction level and abstraction form
   - Test suite, only when test evaluation is in scope

5. Run validation as evidence when feasible.
   - Detect project type and scripts.
   - Prefer low-cost checks first: lint, typecheck, related tests.
   - In large projects, run related tests before all tests.
   - Treat validation as fact gathering, not a mechanical replacement for review.

6. Produce the report.
   - Default English.
   - No Markdown tables.
   - No generic praise section.
   - At most seven formal issues, except blockers are uncapped.

## Validation failure rule

Validation failures are graded by their effect on the minimum closed loop.

- If a failure breaks compilability, core path execution, data truthfulness, lifecycle safety, or validation credibility, it enters formal issues as blocker/high/medium according to impact.
- If related tests fail and expose a core flow error, classify as blocker or high.
- If lint or formatting failures do not affect the loop, they are medium or follow-up at most.
- If a validation failure blocks official CI merge, it is at least high. If it makes the code undeliverable, it is blocker.
- Passing validation is evidence, not proof of mergeability.

## Test evaluation rule

Do not penalize missing tests by default.

Tests are often written after the minimum closed loop stabilizes. If the current loop is not about tests/validation, and the diff has no substantial test changes, mark the test dimension as "not evaluated in this round".

Evaluate the test suite only when:

- the user explicitly asks for test evaluation;
- the minimum closed loop is a test or validation loop;
- test code changed substantially;
- test helpers, temporary markers, or test-only paths affect the truthfulness, maintainability, architecture boundary, or validation credibility of the current loop.

Temporary markers such as `FOR TEST`, debug helpers, fixtures, or test scaffolding are not automatically issues. They matter only if they distort the current closed loop.

## Severity levels

Use exactly these severity levels:

### blocker

Must fix before merge. Examples:

- violates authoritative architecture docs;
- breaks a core boundary or core data flow;
- leaves lifecycle, ownership, or destruction unprovable;
- makes the core flow incorrect or non-executable;
- masks truth in tests or validation.

Any blocker makes the change not mergeable regardless of score.

### high

Strongly recommended before merge. Multiple high issues can make the change practically unmergeable even without a blocker.

### medium

Can merge if the minimum closed loop is otherwise intact, but should be scheduled.

### low

Normally omitted. Include only when it enters the formal issue list because it affects the minimum closed loop or reveals systemic risk.

## Scoring model

Use deduction scoring.

Each evaluated direction starts from 100. Only formal issues that affect the current minimum closed loop deduct points. Follow-up observations do not deduct.

Deduction defaults:

- blocker: deduct 20 points and automatically mark not mergeable
- high: deduct 10 points
- medium: deduct 5 points
- low: deduct 2 points only if included as a formal issue
- follow-up observation: deduct 0 points

Avoid double counting. Merge the same root cause across multiple manifestations and deduct once unless it truly damages separate scoring directions. Scores cannot go below 0.

Default weights:

- Data structure, management, and flow: 0.30
- Data ownership, borrowing, and destruction: 0.20
- Performance: 0.20
- Abstraction level and abstraction form: 0.15
- Test suite: 0.15, only when evaluated

If a direction is intentionally not evaluated, exclude its weight and renormalize the remaining weights for the total score. Still output the total score and explicitly list excluded dimensions with reasons.

Merge gate:

- every evaluated direction must be at least 60;
- the weighted total over evaluated directions must be at least 60;
- there must be no blocker issues.

A score alone never makes code mergeable.

## Formal issue format

Each formal issue must include these fields:

- Severity
- Affected direction
- Code/validation facts
- Why it breaks the minimum closed loop
- Repair direction
- Deduction

Every formal issue must include a short repair direction. Keep it strategic, not a patch. Prefer explaining the data flow, ownership/lifecycle boundary, abstraction boundary, scheduling/state-machine constraint, or validation change that should be corrected. Do not output full patches unless the user explicitly asks.

Do not recommend adding logs, comments, or renaming variables unless that directly affects the current minimum closed loop.

## Report structure

Use this structure exactly. If a section has no content, write "None". Do not omit gate information.

```markdown
# Architecture Code Review

## 1. Minimum closed loop judgment
[State the inferred minimum closed loop and why this is the loop. If not inferable, stop instead of using this report.]

## 2. Overall conclusion and merge gate
[Mergeable / Not mergeable / Needs user decision for policy-only cases. Missing loop, missing facts, or missing required inputs must use the stop rules instead. Explain using blocker presence, direction scores, total score, and validation facts.]

## 3. Scoring and deduction notes
[State evaluated dimensions, excluded dimensions with reasons, per-direction scores, weighted total, and deduction root causes. No Markdown tables.]

## 4. Formal issues
[Maximum seven formal issues, except blockers are uncapped. Each issue follows the fixed format.]

## 5. Validation results
[Commands run, results, and how failures affect the closed loop. If not run, explain why.]

## 6. Documentation/code conflicts
[Conflicts between authoritative docs and implementation. If none, write None.]

## 7. Follow-up observations
[At most three restrained observations. Only include current non-blockers that may become principal contradictions in the next stage. No style preferences or micro-optimizations. No score impact.]
```

Do not include a standalone "Strengths", "What looks good", or praise section. If a key design is valid and affects the merge judgment, mention it briefly in the overall conclusion.

## Large blocker handling

If blockers exceed seven, do not expand every issue. State that the code is broadly unmergeable, detail the most representative blockers, and summarize the remaining blockers by category.

## Output tone

Be rational, direct, and code-fact based. Do not flatter. Do not insult. The report should be understandable to a human maintainer and strict enough to support a merge decision.
