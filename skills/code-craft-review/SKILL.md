---
name: code-craft-review
description: Independent code-quality review of a finished change. Use when asked to review a diff, files, or patch for unearned defensive code, silent fallbacks, speculative abstractions, naming, control flow, and scope, or when dispatched after implementation as the reviewer. Checks the change against the shared code-craft standard and reports actionable findings. Not an architecture review or a merge decision.
argument-hint: "[optional diff, revset, files, or review focus]"
---

# /code-craft-review

Review the **code**, not the plan, the architecture, or whether the change should merge. The bar is [../code-craft/references/standards.md](../code-craft/references/standards.md), resolved from this skill's directory; read that file before judging anything. Read only the standards, not the `code-craft` procedure. If the standards file is missing, report that `code-craft` is not installed and stop.

## Scope

Fix the target before reading code:

- Use the diff, revset, files, or PR the user named.
- Otherwise review the current working-copy diff; if that is empty, review the branch against its merge base with the default branch.
- State the baseline and what is in scope. In a Jujutsu repo, resolve it with `jj log`/`jj diff` and follow the `jujutsu` skill; do not use raw git.
- Read every changed file in full and the adjacent code needed to judge it; do not audit the repository. If the diff is empty, say there is nothing to review and stop. If no baseline is obtainable, ask once.

**Read-only.** Do not edit, format, or fix at any point unless the user explicitly asks for fixes; that request switches you to `code-craft`, whose procedure you then follow under this bar.

This is a code-quality conclusion. It is not a merge gate, not an architecture verdict, and not a system-wide validation report; for those, use `arch-code-review`.

## How to review

1. Read the diff and each changed file. Use the request and commit descriptions for intent, code and tests for behavior. For every new guard, default, retry, wrapper, config, compatibility branch, or abstraction, look for the fact it serves: a contract, boundary validation, a test, a confirmed failure path, or the task. For every removed guard or boundary, find what now covers the same need. Check new comments against the comment default, and treat them as claims about the code, not evidence for it.
2. When you cannot find that fact, investigate before concluding: the definition and implementation behind the interface, the tests that pin it, the callers, the project's docs. A pattern match (`catch`, `??`, a default, a helper) is a prompt to look, not a finding.
3. Apply the symmetric evidence rule. Asking to delete needs a contract, a test that pins the guarantee by asserting the behavior, or a simpler implementation that covers the same need. Asking to add needs a confirmed external boundary or failure path that the code currently mishandles.
4. Report only what changes behavior or understanding. Each finding needs a location, evidence, a concrete cost, and the smallest direction. No score, no dimension checklist, no finding quota, no generic praise.
5. Run the project's cheap checks only when a behavior-affecting judgment needs confirmation. Passing checks do not excuse code that hides failures; a failing check unrelated to the change is a note, not a finding.

Prefer the smaller repair: remove the redundant guard, fix the source rather than masking it, use the established contract directly, clarify the name or data shape, or collapse a layer with no separate responsibility. Add code only for a confirmed failure path or requirement.

## Output

State the scope and baseline, then one of:

**No code-quality changes needed.** The changed code meets the bar. Name any assumption you could not verify.

**Rework needed.** Order findings by cost. For each:

- `path:line` or symbol
- **Evidence**: what the code does, and the contract, requirement, or failure path it contradicts
- **Cost**: the concrete consequence — hidden failure, ambiguous state, a concept the reader must hold, a misleading call site
- **Direction**: the smallest change that keeps the current need satisfied; describe it, do not rewrite the file

**Evidence insufficient.** Name the exact unresolved items and what would settle them: file, doc, or runtime fact. Do not present a guess as a verdict.

When findings and open items coexist, report both; the findings are still actionable.

If the code is fine, say so and stop.
