---
name: review-with-me
description: Prepare a low-noise code review for human judgment.
disable-model-invocation: true
argument-hint: "<review scope: commits, revset, branch, bookmark, or natural language>"
---

# /review-with-me

Prepare a **human review brief**. The agent owns what code and tools can determine; the human judges intent, taste, local knowledge, trade-offs, and responsibility. This skill records those judgments—it does not issue a merge verdict.

## Scope

Accept a natural-language scope, commit IDs, branches/bookmarks, or a revset. Resolve it precisely and restate:

- VCS
- normalized range
- whether the working copy is included
- the net effect being reviewed

When `.jj/` exists, use Jujutsu as the source of truth and follow the `jujutsu` skill; otherwise use Git. Ask for confirmation when the interpretation is ambiguous. If no scope was supplied, ask once and offer likely ranges as shortcuts.

Version 1 reviews a contiguous range, including the working copy when requested. For a disconnected commit set, ask the human to choose separate reviews or a contiguous boundary. Review the final net effect first; inspect commit evolution only to recover intent or locate a change.

The range limits what is judged, not where evidence may come from. Read relevant existing code, tests, documentation, callers, and commit descriptions, while reporting only matters introduced, exposed, or changed by the range.

## Division of judgment

Before involving the human, understand the changed behavior and gather enough evidence to resolve questions the agent can answer. A candidate enters the human **frontier** only when all three are true:

1. Its answer depends on intent, taste, local knowledge, or responsibility that the code cannot reliably reveal.
2. Different answers materially change behavior, risk, or maintenance cost.
3. The answer changes implementation, acceptance, or release.

Uncertainty alone is not admission. Search, test, and reason first. Keep definite defects and mechanical work agent-owned; fix them when already authorized, then rerun relevant checks and review the resulting net effect. Otherwise surface only blockers and work needing authorization.

Fold low-sensitivity material such as mechanical changes, local declarations, data-shape details, and test scaffolding once it has no remaining decision relevance. Keep the fold reversible and summarize it by category and count.

## Meet the human where they are

Adapt each explanation to whether the human already knows the concern and is familiar with the area:

- unknown + unfamiliar → teach the smallest useful mental model
- unknown + familiar → point out the deviation or omission
- known + unfamiliar → help with implementation evidence and trade-offs
- known + familiar → complete the agent-owned work and summarize it

Start with the shortest useful explanation and adjust from natural cues such as “familiar”, “explain”, “I know the intent but not the implementation”, or “handle it”. Teaching covers the problem, how this design works, and the present trade-off—enough to make the current decision. Treat irreversible, high-impact, or insufficiently verifiable choices as human decisions regardless of familiarity.

## Human review brief

Begin with a short orientation organized by behavior:

- what the range is trying to change
- the final observable behavior
- assumptions the code cannot confirm
- what the agent checked

Then present the current frontier, ordered by consequence, at most five decisions per round:

```markdown
### <decision>

Suggestion: <answer> — <single most important reason>
Inspect: <1–3 necessary code, test, or documentation anchors>
```

Say when no reliable suggestion exists. Add a major consequence or unknown only when it changes the decision. Explain what each anchor establishes; inline only the smallest code fragment required to decide.

Accept natural responses: agree, choose differently, inspect evidence, or defer. Recompute the frontier after each round. Use Plannotator only when the human asks to inspect code and it can show exactly the normalized range; state the limitation when it cannot.

Keep these sections distinct:

- **Human decisions** — frontier items awaiting or recording judgment
- **Agent-owned findings** — blockers and authorization needs, each with status, evidence anchor, impact, and required action; plus final counts
- **Folded** — omitted material summarized by reason and count, available on request

If no candidate passes the gate, say: **“This range contains no issue worth transferring to human judgment.”** Still show the normalized scope, agent-owned findings, and folded summary.

## Closure

Maintain a concise decision record in the conversation:

- confirmed decisions
- changes the agent should make
- accepted or deferred risks
- open decisions and exactly what they block

A deferred decision is a blocker only when it actually blocks implementation, acceptance, or release. Existing decisions survive code changes that do not affect their premises; reopen affected decisions when evidence changes, and renormalize the scope when its boundary changes.

The review is complete when every material behavior or boundary in the normalized range is classified under Human decisions, Agent-owned findings, or Folded; every frontier item is agreed, changed, or deferred; agent-owned changes are validated against the resulting net effect; and the scope remains valid. Reopen decisions whose premises changed. The human need not read every line. If a decision creates a durable architectural constraint, public API commitment, accepted risk, or maintenance trade-off, ask once at the end whether to persist it in an issue or documentation.
