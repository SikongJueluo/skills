---
name: loop-discuss
description: Cuts a vague idea down to the current minimum closed loop, aligns the endpoint and acceptance, and produces a contract that can be followed as written. Use when starting a new requirement, exploring a feature, or defining the next loop. Covers only this loop; it is not a design review of the final goal. Start implementing only after the user agrees.
argument-hint: "[idea or requirement]"
---

# loop-discuss

## Philosophy

The boundary of the endpoint usually hides in the unknown. Trying to reach it in one step and draw the whole circle tends to fall through; drawing one complete small circle at a time looks like the longer road, yet it grounds every step and lights the way to the next circle along the way.

## Content

Our final goal is a big circle, and what the current discussion must decide is the small circle inside it, the minimum closed loop. The big circle points at the final goal and prevents drift; the discussion itself stays on the current small circle: endpoint, boundary, acceptance.

**When the open questions pile up, the circle was cut too large.** Stop and cut again instead of asking through every question. This is the key difference between this skill and an exhaustive review.

At the start, establish the starting point, meaning the current state of the project. Investigate the relevant code, docs, configuration, and current state until a conclusion is possible, then compress them into a few verified facts for the human to check. Do not ask what the current state is.

Restate the big circle in one sentence and propose the current small circle: what this loop makes work, and what it explicitly does not do. Set defaults for ordinary details by project convention and list them; anything not overruled stands. Raise only the choices that are genuinely hard to redo, and settle acceptance at the same time. Stop once the contract is written; start work only after the user approves.

The boundary is what is explicitly not done. A negative boundary more reliably prevents an opportunistic extra move during implementation that turns the small circle into the big circle than a positive description does.

Acceptance comes in two kinds. When it can be automated, align on a small and complete test set: one or two main paths plus the most critical boundary, with one check command. When it cannot, align on reference works, core preferences, and red lines, and let the user judge a prototype instead of speaking in generalities or arguing with adjectives and abstract words.

When the user is unfamiliar with a concept, go to `loop-teach` and come back once it lands. Do not expand on it in the discussion.

## Contract template

After alignment, emit one page under `docs/plan`: the final goal is a folder, and the minimum closed loop is a numbered page inside it, for example `docs/plan/20260606-implement-skill-eval-framework/1-initial-dev-environment.md`. Create the directory if it does not exist; if it cannot be created, write the page nearby and state its location in the contract.

Omit sections that do not apply:

```markdown
# Loop contract: <task name>

## Final goal
<one sentence defining the final goal, only to prevent drift>

## Starting point
* <verified current state>

## Minimum closed loop
* Endpoint: <capability or output once it runs>
* Boundary: <explicitly excluded extensions>

## Implementation and discussion
* <details set by convention, and what was discussed and decided>

## Acceptance
* Automated: <check command, main paths, critical boundaries>
* Manual: <reference works, preferences, red lines, how to verify>

## Key path
1. <core change and its self-check steps>
```

This contract is the baseline `loop-iterate` reviews against; the review appends to the end of the same page.
