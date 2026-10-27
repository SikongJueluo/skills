---
name: code-craft
description: Contract-first coding standard for writing code. Use before you implement a feature or fix, refactor code, or write tests, and when trimming code you just wrote that accumulated defensive guards, silent fallbacks, speculative abstractions, or unrelated changes. Write against the checked contract and the current requirement instead of coding around uncertainty. Not an independent review or merge decision; to review a diff, use code-craft-review.
argument-hint: "[optional task, file, or decision to focus]"
---

# code-craft

Write code that satisfies the current requirement directly, on evidence. **Do not convert your own uncertainty into runtime complexity.**

The quality bar is [references/standards.md](references/standards.md). Read it before the first edit; this page is the working procedure.

## 1. Establish the local contract

Read the project's rules (AGENTS.md, CLAUDE.md, docs, lint, tests) and the code you are about to change. For every interface whose behavior changes the implementation, find the guarantee: declaration, implementation, boundary validation, tests, docs. Callers show usage, not the guarantee.

Investigate until the decision is determined, not until the repository is understood. When a question stays open, report the unknown instead of choosing a contract and defending against it.

Completion: for each guarantee you rely on or guard, you can name its source; open questions that would change behavior are stated, not coded around.

## 2. Implement the current need

Write the simplest direct implementation that satisfies the task under the standards. A new guard, default, retry, wrapper, config, or layer needs a fact it serves. Let errors propagate through the project's existing mechanism unless this code owns a recovery.

Put the judgment in the code shape, not in a justification report or design notes.

Completion: every added branch and abstraction has a current reason, and the diff contains nothing the requirement does not need.

## 3. Trim and verify

Reread your own diff for code added to satisfy uncertainty rather than a requirement. Prefer the clearer shape over the shorter one. Run the project's required checks (format, lint, typecheck, tests) and know their result.

Completion: the diff is what you would defend in review, and verification results are known or their absence is reported.
