---
name: review-with-me
description: Curate the code worth a human's attention and present it as reviewable slices.
disable-model-invocation: true
argument-hint: "<review scope: commit, revset, branch, bookmark, or natural-language description>"
---

# /review-with-me

Prepare a **human code review**, not another agent findings report. The agent investigates the whole change, then lays the load-bearing code in front of the human with enough context for them to decide without hopping around the repository.

This skill records human judgment; it does not issue a merge verdict.

## Scope

Accept a natural-language scope, commit id, branch/bookmark, or revset. Resolve it precisely and restate:

- VCS
- the normalized scope
- whether the working copy is included
- the net effect under review

When `.jj/` exists, treat Jujutsu as the source of truth and follow the `jujutsu` skill; otherwise use Git. When resolution is ambiguous, ask the human to confirm. If no scope is given, ask once and offer plausible scopes as shortcuts.

Version 1 reviews contiguous ranges, including the working copy when asked. For a discrete set of commits, ask the human to choose between split reviews or a contiguous boundary. Prefer reviewing the final net effect; inspect commit evolution only when needed to recover intent or locate changes.

The scope bounds what is judged, not where evidence may come from. Read relevant existing code, tests, docs, callers, and commit descriptions, but report only what this scope introduces, exposes, or changes.

## Planning the review

Understand each substantive behavior and boundary, treating these perspectives as prompts rather than a fixed checklist:

- Data structures, state, and contracts
- Data flow, state transitions, and lifecycle
- Algorithms, control flow, and failure paths
- External interfaces, system boundaries, and side effects
- Overall risk and omissions

Choose only the perspectives that help explain this change, and order them by dependency of understanding. For a broad or unfamiliar change, give the human a short review map before slicing; for a focused change, a brief orientation can lead straight into the first slice. Mention a perspective only when its absence is itself useful evidence, never as bookkeeping.

## Building review slices

Within the chosen review path, pick the **load-bearing code whose independent reading is valuable to a human**, especially:

- Domain policy and user-visible behavior
- Control flow, failure handling, and irreversible effects
- Ownership, lifecycle, and trust boundaries
- Public contracts and abstractions that shape future changes
- Surprising implementation choices or assumptions
- Consequential problems the agent found

Present each selection as one of three kinds of review slice:

- **Verify** — the agent believes it is sound; the human independently verifies the key implementation.
- **Problem** — the agent found a consequential problem; the human sees that claim beside the evidence.
- **Decision** — correctness depends on intent, taste, local knowledge, trade-offs, or ownership.

Fold away mechanical changes, repetition, generated code, and local declarations that carry no behavior or boundary. Declarations or data shapes that define contracts are load-bearing, not mechanical. Any scope containing non-mechanical changes must produce at least one slice. Zero slices are permitted only when the entire scope is mechanical, and the response must explain why.

## Make each slice self-contained

Use this compact shape, adjusting labels when needed:

````markdown
### [Verify | Problem | Decision] <what this code controls>

**What happens:** <the behavior this code implements, in plain words>
**Why it matters:** <what it costs if this is wrong>

```<language>
<a short excerpt of the consequential code>
// REVIEW ①
```

**Review:** <the specific thing for the human to check or decide>
**Agent take:** <the answer> — <the concrete cause or failure scenario>
Source: `<path:start-end>`

① <a detailed explanation of the marked line or branch, below the code block>
````

Keep code blocks short. Mark consequential lines with a bare number such as `// REVIEW ①`, and put each detailed explanation below the code block at its number. Prefer the marker on its own line; move it to end of line only when that does not widen the excerpt. Rewrap or reindent the excerpt for presentation only when the resulting semantics are identical, and say that you did; the Source location still points at the real location.

Quote code directly in the response. Add `REVIEW` markers only to the quoted copy, never to project files. Keep enough surrounding control flow, inputs, and results that the question can be answered. Present cross-file flows within one slice as several short code blocks tracing input → transformation → output or side effect, each carrying its own marker; a merged excerpt that hides the contract is worse than three small excerpts. The source location supports the slice — it can never replace showing the code.

Expose uncertainty candidly. Say plainly when there is no reliable agent judgment. Include only the consequential risks or unknowns that would change a judgment.

## Explain for an unfamiliar reader

Assume the human reads this language fluently but does not know the module or its domain; the four plain fields exist for that reader.

- Explain module or domain terms in place the first time they appear; do not send the human elsewhere to look up vocabulary.
- Write What happens as the behavior the code implements, not the name of a pattern it resembles.
- Ground Agent take in concrete causes and failure scenarios — what breaks, along which path — and never restate abstract nouns.
- For data-flow slices, state the input → processing → output/side-effect trace explicitly rather than conveying it only through code blocks.
- For complex algorithms, walk a concrete step-by-step example with real values instead of describing the steps abstractly.

When the human says they are already familiar with the module or the concern, write that slice's fields more briefly and expand on demand. Teaching is scoped to reviewing that slice — enough to decide, not a general course.

## Conducting the human review

Open with a short orientation: what this scope changed, its observable behavior, assumptions the code cannot confirm, and what the agent checked. Use rounds when they reduce cognitive load, not to satisfy a fixed ritual.

- Keep each round coherent. It may follow one perspective or a tight cluster of perspectives, and may contain any number of slices the human can reasonably judge together.
- Pause when the human needs to make a judgment, when the next material depends on that judgment, or when the response would become hard to review. Otherwise continue; do not invent checkpoints.
- When work remains, close with a short conclusion and say what is next. Use a progress ledger only when multiple rounds or deferred decisions make progress unclear.
- Accept natural responses: looks right, concern confirmed, choose another option, explain more, show more context, or defer.
- Raise a consequential problem as soon as it becomes important, then reshape the remaining review around the human's response.
- Recompute the remaining review after each response; changed premises may reopen slices or reorder the path.

Integrate the agent's consequential findings into **Problem** slices rather than a separate findings list. Summarize outside slices only:

- Mechanical problems fixed and verified
- Authorization state and required actions; any consequential problem itself still appears in a Problem slice
- Repeated instances represented by one slice
- Folded material, with reason and count

Use Plannotator only when the human asks for a broader visual pass and Plannotator can display the normalized scope precisely; when it cannot, state that limitation.

## Closing

Maintain a short record of reviewed slices:

- Accepted implementations
- Confirmed problems and required changes
- The human's decisions
- Accepted or deferred risks, including what they block

When code changes, rerun the relevant checks, review the resulting net effect, and reopen slices whose premises changed. Renormalize the scope when its boundary moves.

The review is complete when every substantive behavior or boundary is represented by a reviewed slice or an explicit mechanical-fold category; every non-mechanical scope has at least one slice; every slice has been accepted, redirected, or deferred; the required agent work is handled or recorded; and the scope is still valid. If a judgment forms a lasting architectural constraint, public API commitment, accepted risk, or maintenance trade-off, ask once at the end whether to persist it in an issue or document.
