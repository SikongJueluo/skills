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

## Plan the review

Understand every material behavior and boundary, using these lenses as prompts rather than a fixed checklist:

- data structures, state, and contracts
- data flow, state transitions, and lifecycle
- algorithms, control flow, and failure paths
- external interfaces, system boundaries, and side effects
- overall risks and omissions

Choose only the lenses that help explain this change, and order them by comprehension dependency. For a broad or unfamiliar change, show the human a short review map before the slices; for a focused change, a brief orientation can lead directly into the first slice. Mention a skipped lens only when its absence is useful evidence, not as bookkeeping.

## Build review slices

Within the chosen review path, select the **load-bearing code** where a human's independent reading has value, especially:

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

**What happens:** <the behavior this code implements, in plain words>
**Why it matters:** <what is at stake if it is wrong>

```<language>
<short excerpt of the consequential code>
// REVIEW ①
```

**Review:** <the concrete thing for the human to check or decide>
**Agent take:** <answer> — <the concrete cause or failure scenario>
Source: `<path:start-end>`

① <detailed explanation of the marked line or branch, below the block>
````

Keep code blocks short. Mark the consequential lines with bare numbered markers such as `// REVIEW ①`, and put every detailed explanation below the block under the matching number. Prefer a marker on its own line; move it to the end of a line only when that does not widen the excerpt. Rewrap or reindent an excerpt for display only when the result stays semantically identical, and say so; the Source location still names the real position.

Quote the code directly in the response. Add `REVIEW` markers only to the quoted copy, never to project files. Preserve enough surrounding control flow, inputs, and outcomes to make the question answerable. Show a cross-file flow inside one slice with several short blocks tracing input → transform → output or side effect, each carrying its own markers; a merged excerpt that hides the contract is worse than three small ones. A source location supports the slice—it never substitutes for showing the code.

Expose uncertainty plainly. Say when no reliable agent take exists. Include a major consequence or unknown only when it changes the judgment.

## Explain for an unfamiliar reader

Assume by default that the human reads the language fluently but does not know this module or its domain; the four plain fields exist for that reader.

- Explain a module or domain term in place the first time it appears; do not send the human elsewhere for vocabulary.
- Write What happens as the behavior the code implements, not the pattern name it resembles.
- Ground the Agent take in a concrete cause and failure scenario—what breaks, and along which path—never a restatement of abstract nouns.
- For a data-flow slice, state the input → processing → output/side-effect trace explicitly, not only implicitly through the blocks.
- For a complex algorithm, walk one concrete step-by-step example with real values instead of describing the steps abstractly.

When the human signals familiarity with the module or the concern, keep the fields terse for that slice and expand again on request. Teaching stays scoped to reviewing the slice—enough to judge it, not a general lesson.

## Run the human review

Open with a short orientation: what the range changes, its observable behavior, assumptions the code cannot confirm, and what the agent checked. Use rounds when they reduce cognitive load, not to satisfy a fixed ceremony.

- Keep each round coherent. It may follow one lens or combine tightly coupled lenses, and it may contain as many slices as the human can reasonably judge together.
- Pause when the human needs to make a judgment, when the next material depends on that judgment, or when the response would become hard to review. Otherwise continue without inventing a checkpoint.
- When work remains, end with a terse conclusion and say what comes next. Use a progress ledger only when several rounds or deferred decisions make progress unclear.
- Accept natural responses: looks right, concern confirmed, choose differently, explain more, inspect more context, or defer.
- Surface a consequential problem as soon as it matters, then reshape the remaining review around the human's response.
- Recompute the remaining review after each response; a changed premise may reopen slices or reorder the path.

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
