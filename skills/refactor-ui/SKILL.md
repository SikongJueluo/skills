---
name: refactor-ui
description: Improve an existing UI, screen, slide deck, or visual artifact that the user mostly accepts but finds too busy, unclear, inconsistent, ugly, plain, or over-decorated. Use when the user gives feedback on a rendered artifact and wants a bounded revision that preserves what works. Not for building from scratch, exploring an undecided visual direction, deck production or conversion, or implementing a specified design.
argument-hint: "[artifact path or URL, and the user's complaint]"
---

# refactor-ui

Revise an existing visual artifact from the user's dissatisfaction. The artifact is the starting point; the feedback is the brief. A good pass is small, evidenced, and keeps what the user already likes.

Use this for a page, app screen, component, slide deck, document layout, or visual mock that exists and is worth keeping. For a new artifact or an undecided direction, explore first with a small prototype. For a slide deck being generated or converted, `frontend-slides` owns production; use this skill for the feedback-driven revision of an existing deck. When the user only asks what is wrong, inspect and report without editing.

## Operating rules

- **Preserve before improving.** Name what the user has approved — direction, palette, type, content, interactions, prior decisions — and treat it as fixed unless the complaint targets it.
- **Edit the surface, not the product.** You may rewrite, merge, move, quiet, or remove visible content. Keep facts, meaning, capability, and required credits.
- **Ask before changing meaning.** Deleting an independent argument, changing a claim, or removing a capability needs confirmation. Repetition, migration, and compression do not.
- **One pass, one coherent set of causes.** Fix the causes the evidence supports; leave unrelated surfaces alone.
- **Evidence before verdict.** Render and compare at the same size and state. Code inspection and a clean screenshot do not establish that the complaint is resolved.
- **Taste belongs to the user.** Recommend with reasons, but do not present a preference as a defect or freeze your inference as a project rule. Do not write a new design document or convention unless the user adopts it.

## 1. Frame the complaint

Restate the dissatisfaction in the user's terms, then inspect the artifact, its assets, the project's design rules, and any earlier feedback or approvals. Render or open it at the size and state the user sees and capture a baseline; use the artifact's existing preview or screenshot path. For a scaled fixed-stage deck, the design size and the screenshot size are different; the important constraint is the same viewport before and after. If the artifact uses images as evidence, open them and describe what they actually show before judging the layout. If you cannot view images, delegate the check or report it unverified; a filename or alt text is not inspection.

Write down the preserved set: the design decisions, content, and behavior that must survive. Separate hard constraints — approved decisions, project rules, required facts — from soft preferences and your own inferences. Hard constraints need the user to change; soft preferences guide the choice. When the user has already approved a direction or the project has conventions, they outrank this skill's defaults. If there are no project rules or earlier decisions, treat the artifact's own tokens, components, and repeated treatments as its system, and keep inferred rules provisional.

Completion: the complaint is one sentence in the user's terms; a baseline exists (screenshot, or the exact state and source inspected); the preserved set is written; the task type is known.

## 2. Form a testable hypothesis

Separate the feeling from the cause. "Too busy" is a feeling; "three blocks all claim the first read" is a cause. A useful cause names an element and a mechanism.

List two to four candidate causes, then gather the evidence that distinguishes them: the rendered result, the source, measurements, the copy, the same role in other places, and the artifact's purpose. Read the reference files whose branch is live — usually one or two. If evidence contradicts a reference's default, follow the evidence and say why. If the artifact cannot distinguish two plausible causes and their fixes would differ materially, ask one focused question or show a small variant; otherwise test the smaller, reversible change.

If the cause is in the content's logic, an interaction flow, or the product itself, name that. A visual change that only hides it is not a fix.

State the hypothesis as **cause → change → signal**: what is causing the complaint, what you will change, and what observable result would show the complaint improved.

- Weak: "Too much text. Cut 30%."
- Testable: "The explanation paragraph and the speaker prompt repeat the claim already carried by the title and takeaway. Move both to the speaker notes. Signal: the slide has one ending, and a viewer can still state the claim."

| Signal in the feedback | Look first at | Read |
| --- | --- | --- |
| too much, busy, dense, long, "not restrained" | competing jobs, repeated content, layer placement, density, emphasis competition | [surface.md](references/surface.md), [emphasis.md](references/emphasis.md) |
| unclear, "can't tell what matters", "where do I look" | focal point, hierarchy, grouping, labels | [surface.md](references/surface.md), [craft.md](references/craft.md) |
| inconsistent, "doesn't feel like one system", headings or labels drift | role grammar, anchor positions, token drift | [consistency.md](references/consistency.md) |
| over-designed, decorated, "AI-looking", everything shouts | emphasis stacking, decoration without a job, focal competition | [emphasis.md](references/emphasis.md) |
| ugly, cheap, unfinished, plain, generic | type, color, spacing, depth, imagery | [craft.md](references/craft.md) |
| hard to use, "can't find it", too many steps | affordance, prominence, flow, progressive disclosure | [surface.md](references/surface.md) |
| "something feels off", mixed complaints | the artifact's job and first read, then the strongest evidence | the files for the two strongest candidate causes |

Completion: one working hypothesis with a cause, a change, and a signal; the alternatives are named and ruled out or deferred; every reference read was triggered by a live cause. If the task is analysis only, stop here and report the diagnosis and proposed changes without editing.

## 3. Choose the intervention

Pick the smallest set of moves that changes the named signal. Prefer moving, merging, or quieting over deleting; prefer structural and typographic moves over added decoration. Keep one distinctive element; restraint is not erasure. Do not convert the complaint into a quota; each removal needs its own cause. When the evidence points to grouping or structure rather than surface styling, reorganize or propose the structural change. When it points to the product's interaction model, say that a visual pass cannot solve it. Do not retreat to exploration merely because the change is large.

Confirm before acting when the choice is genuinely the user's: two or more materially different aesthetic directions, a standalone argument or claim that would disappear, a capability that would be removed, or a change of overall direction. Changing how a distinction is visually encoded is a design move, not a content change, as long as the same distinction remains legible; confirm only when the encoding is the only carrier of the meaning or the user relies on it. Act directly when the cause and fix are clear. If the complaint is about the direction rather than its execution, say so and offer two or three alternatives instead of polishing a direction the user rejects. Do not re-ask facts you can inspect or feedback the user already gave.

Completion: the change list is bounded and mapped to causes; the preserved set is still intact; meaning-changing or directional choices are confirmed.

## 4. Edit

Work inside the artifact's own system: existing tokens, components, type scale, spacing rhythm, layout grammar, and runtime. Move content to its proper layer — speaker notes, help, detail view, secondary panel — instead of forcing it onto the main surface.

Do not import a new visual language, restyle adjacent surfaces, or "fix" content the complaint did not reach. Remove CSS, classes, and assets that the change orphaned; leave unrelated code alone. For interactive work, preserve behavior, state, keyboard access, focus, labels, and error recovery.

Completion: the diff touches only the complained surfaces and their direct dependencies; every moved or removed block is accounted for at another layer or intentionally gone.

## 5. Verify against the complaint

Re-render the same state and size as the baseline and compare. Check in this order:

1. **Original signal.** The thing the hypothesis named, such as one ending instead of two, one first read, or a predictable heading role.
2. **Expression.** A new viewer can still state the main point, and the claims the change touches are supported by what they show — images, numbers, captions, examples.
3. **Regression.** Layout, overflow, clipping, interaction, navigation, accessibility, and neighboring surfaces are unchanged or better.
4. **Residual.** What is still unresolved, subjective, or unverifiable — no renderer, no browser, missing states, or taste.

If you cannot render, say which checks are source-only. Programmatic measurements — pixel counts, element counts, overflow, color histograms — are supporting evidence, not vision. If you cannot view the artifact, report the visual check as unverified, delegate it to a vision-capable agent, or ask the user; do not claim a visual improvement from proxies alone. When an image or example carries a claim you cannot verify, name that specific claim as unverified; do not repeat it as fact.

Completion: before/after evidence for the named signal, a regression pass, and an explicit list of what remains unverified.

## 6. Report

Lead with what changed and why. Show the before/after evidence for the named signal and restate the preserved set. Ask only for the taste decision that evidence cannot settle. Do not claim the design is "fixed" or "better" beyond what was verified, and do not assign an aesthetic score or a pass/fail verdict on taste. If the user still disagrees, revise the hypothesis rather than defending the change.

Completion: the user can see what changed, what was verified, and what remains theirs to judge.
