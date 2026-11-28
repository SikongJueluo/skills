---
name: code-craft
description: A contract-first standard for writing code. Use it before implementing a feature or a fix, before refactoring code, and before writing tests; also use it when trimming code you just wrote that accumulated defensive guards, silent fallbacks, speculative abstractions, or unrelated changes. Write against the verified contract and the current requirement rather than patching around uncertainty. Not an independent review or a merge decision; to review a diff, use code-craft-review.
argument-hint: "[optional focus: the task, file, or decision]"
---

# code-craft

Write code that satisfies the current requirement directly, with evidence behind it. **Do not turn your own uncertainty into runtime complexity.**

The quality bar is [references/standards.md](references/standards.md). Read it before the first edit; this page is the working procedure.

## 1. Establish the local contract

Read the project's rules (AGENTS.md, CLAUDE.md, docs, lint, tests) and the code you are about to change. For every interface that changes how the implementation behaves, establish its guarantee: declaration, implementation, boundary validation, tests, docs. Callers show usage, not the guarantee.

Investigate until the decision is settled, not until the repository is understood. When a question remains open, report that unknown rather than picking a contract and then defending it in code.

Completion: for every guarantee you rely on or guard, you can name its source; the open questions that would change behavior are stated, not coded around.

## 2. Implement the current need

Under the standards, write the simplest direct implementation that satisfies the task. Any new guard, default, retry, wrapper, config, or layer needs a fact it serves. Let errors travel through the project's existing mechanism, unless this code is the one that owns the recovery.

Put the judgment into the shape of the code, not into a justification report or design notes.

Completion: every branch and abstraction you add has a reason in the present, and the diff holds nothing the requirement does not need.

## 3. Trim and verify

Reread your own diff and hunt for code that exists to satisfy uncertainty rather than a requirement. Choose the clearer shape over the shorter one. Run the checks the project requires (format, lint, typecheck, tests) and know their result.

Completion: the diff is one you would defend in review, and the verification result is known — or its absence is reported.
