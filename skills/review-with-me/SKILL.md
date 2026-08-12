---
name: review-with-me
description: Curate the code worth a human's attention and present it in reviewable slices.
disable-model-invocation: true
argument-hint: "<review scope: commits, revset, branch, bookmark, or natural language>"
---

# /review-with-me

Prepare a **human code review**, not another agent findings report. The agent investigates the full change, then puts the load-bearing code in front of the human with enough context to judge it without navigating the repository.

This skill records human judgments; it does not issue a merge verdict.

## Scope

Accept a natural-language scope, commit IDs, branches/bookmarks, or a revset. Resolve it precisely and restate:

- VCS
- normalized range
- whether the working copy is included
- the net effect being reviewed

When `.jj/` exists, use Jujutsu as the source of truth and follow the `jujutsu` skill; otherwise use Git. Ask for confirmation when the interpretation is ambiguous. If no scope was supplied, ask once and offer likely ranges as shortcuts.

Version 1 reviews a contiguous range, including the working copy when requested. For a disconnected commit set, ask the human to choose separate reviews or a contiguous boundary. Review the final net effect first; inspect commit evolution only to recover intent or locate a change.

The range limits what is judged, not where evidence may come from. Read relevant existing code, tests, documentation, callers, and commit descriptions, while reporting only matters introduced, exposed, or changed by the range.

## Build review slices

Understand every material behavior and boundary in the range. Select the **load-bearing code** where a human's independent reading has value, especially:

- domain policy and user-visible behavior
- control flow, failure handling, and irreversible effects
- ownership, lifecycle, and trust boundaries
- public contracts and abstractions that shape future changes
- surprising implementation choices or assumptions
- consequential issues found by the agent

Present each selection as one of three review slices:

- **Verify** — the agent thinks it is sound; the human independently checks the critical implementation.
- **Problem** — the agent found a consequential issue; the human sees the claim beside its evidence.
- **Decision** — correctness depends on intent, taste, local knowledge, trade-offs, or responsibility.

Fold mechanical edits, repetition, generated code, and local declarations that carry no behavior or boundary. A declaration or data shape that defines a contract is load-bearing, not mechanical. Any range containing a non-mechanical change must produce at least one slice. Zero slices is allowed only when the entire range is mechanical, and the response must explain why.

## Make each slice self-contained

Use this compact shape, adapting labels when useful:

````markdown
### [Verify | Problem | Decision] <what this code controls>

<one or two sentences establishing the mental model>

```<language>
<enough exact code to understand the relevant behavior>
// REVIEW ①: <annotation attached to the consequential line or branch>
```

**Review:** <the concrete thing for the human to check or decide>
**Agent take:** <answer> — <single most important reason>
Source: `<path:start-end>`
````

Quote the code directly in the response. Add `REVIEW` annotations only to the quoted copy, never to project files. Preserve enough surrounding control flow, inputs, and outcomes to make the question answerable; use multiple small excerpts when one excerpt would hide a cross-file contract. A source location supports the slice—it never substitutes for showing the code.

Expose uncertainty plainly. Say when no reliable agent take exists. Include a major consequence or unknown only when it changes the judgment.

## Meet the human where they are

Adapt the slice explanation to whether the human knows the concern and is familiar with the area:

- unknown + unfamiliar → teach the smallest useful mental model
- unknown + familiar → point out the deviation or omission
- known + unfamiliar → explain implementation evidence and trade-offs
- known + familiar → show the critical code with minimal commentary

Infer this from natural cues such as “familiar”, “explain”, “I know the intent but not the implementation”, or “handle it”; start short and expand on request. Teaching covers the problem, how this code works, and the present trade-off—enough to review the slice rather than start a general lesson.

## Run the human review

Begin with a short orientation organized by behavior:

- what the range is trying to change
- the final observable behavior
- assumptions the code cannot confirm
- what the agent checked

Order slices by consequence and present at most five per round. Accept natural responses: looks right, concern confirmed, choose differently, explain more, inspect more context, or defer. Recompute the remaining review after each round.

Integrate consequential agent findings into **Problem** slices instead of placing them in a separate findings dump. Summarize only these outside slices:

- mechanical issues already fixed and verified
- authorization status and required action; any consequential problem itself still appears in a Problem slice
- repeated instances represented by one slice
- folded material, by reason and count

Use Plannotator only when the human asks for broader visual inspection and it can show exactly the normalized range; state the limitation when it cannot.

## Closure

Maintain a concise record of reviewed slices:

- accepted implementations
- confirmed problems and required changes
- human decisions
- accepted or deferred risks, including what they block

When code changes, rerun relevant checks, review the resulting net effect, and reopen slices whose premises changed. Renormalize the scope when its boundary changes.

The review is complete when every material behavior or boundary is represented by a reviewed slice or an explicit mechanical folded category; every non-mechanical range has at least one slice; each slice is accepted, redirected, or deferred; required agent work is handled or recorded; and the scope remains valid. If a judgment creates a durable architectural constraint, public API commitment, accepted risk, or maintenance trade-off, ask once at the end whether to persist it in an issue or documentation.
