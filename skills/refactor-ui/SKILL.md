---
name: refactor-ui
description: When the user largely accepts an existing interface, screen, presentation, or visual artifact but finds it too busy, unclear, inconsistent, ugly, plain, or over-decorated, revise it within bounds from feedback on the rendered artifact while keeping what works. Not for building from scratch, exploring an undecided visual direction, producing or converting presentations, or implementing an already-specified design.
argument-hint: "[artifact path or URL, plus the user's specific feedback]"
---

# refactor-ui

Revise an existing visual artifact from the user's dissatisfaction. The existing artifact is the starting point; the user's feedback is the task statement. A good revision is small and evidenced, and keeps what the user has already accepted.

This applies to an existing web page, app interface, component, slide, document layout, or visual model that is worth keeping. If the artifact is new, or the direction is still undecided, explore it with a small prototype first. If the task is producing or converting a presentation, `frontend-slides` owns that; this skill handles only feedback-driven revision of an existing presentation. If the user only asks where the problem is, inspect and report without editing.

## Operating rules

- **Preserve, then improve.** Name the direction, palette, type, content, interactions, and earlier decisions the user has accepted; treat them as fixed requirements unless the feedback explicitly targets them.
- **Keep information; choose a new representation.** Preserve facts, meaning, capabilities, and required credits. As long as the original information and actions remain available, you may merge, move, or replace the cards, charts, and copy that carry them.
- **Ask before changing meaning.** Deleting an independent argument, changing a claim, or removing a capability needs confirmation; duplication, migration, and compression do not.
- **Address one group of related causes at a time.** Fix the causes the evidence supports; leave unrelated surfaces untouched.
- **Get evidence before concluding.** Render and compare at the same size and state. Reading only the code or a clean screenshot cannot prove the problem the feedback names is solved.
- **The user owns aesthetics.** Give reasoned recommendations, but do not present preference as defect, and do not state an inference as a project rule. Do not add design docs or conventions unless the user adopts them.

## 1. Define the problem

Restate the dissatisfaction in the user's own words, then inspect the artifact, its assets, the project's design rules, and any earlier feedback and approvals. Render or open the artifact at the size and state the user actually sees, and record a baseline; use the artifact's existing preview or screenshot path. For a fixed-stage presentation that is scaled as a whole, the design size is not the screenshot size; what matters is using one viewport both before and after. If the artifact relies on images as evidence, open the images first, describe what they actually show, and only then judge the layout. If you cannot view the images, delegate to an assistant that can, or report honestly that it is unverified; do not claim to have checked them from a filename or alt text alone.

Write down what must be preserved: the design decisions, content, and behaviors that have to continue. Separate hard constraints (approved decisions, project rules, required facts) from soft preferences and your own inferences. Hard constraints require the user to change; soft preferences guide the choice. A direction the user has accepted, or a project convention, outranks this skill's defaults. If there are no project rules or earlier decisions, treat the artifact's own design tokens, components, and repeated treatments as its existing system, and keep your inferred rules as provisional conclusions.

Completion: a one-sentence problem in the user's words; a baseline exists (a screenshot, or the exact state and source checked); the preserve list is written; the task type is clear.

## 2. Build a verifiable hypothesis

Separate the feeling from the cause. "Too busy" is a feeling; "all three blocks are competing for the first focal point" is a cause. A working cause points to a specific element and the mechanism by which it produces the effect.

List 2–4 candidate causes, then gather evidence that distinguishes them: the rendered result, the source files, measurements, the copy, the same kind of content elsewhere, and the artifact's purpose. Read the reference files the current cause branch will use, usually one or two. If the evidence contradicts a reference file's default recommendation, follow the evidence and say why. If the artifact cannot distinguish two plausible causes and the fixes differ materially, ask one focused question or show a small variant; otherwise try the smaller, reversible change first.

If the cause lies in the content logic, the interaction flow, or the product itself, say so explicitly. A visual change that only hides the problem is not a fix.

Write the hypothesis as **cause → change → signal**: what produced the feedback, how you intend to change it, and what observable result would show the problem improved.

- Weak: "Too much text; cut 30%."
- Verifiable: "The explainer paragraph and the speaker prompt repeat the claim the heading and conclusion already make. Move both to the speaker notes. Signal: the slide presents one way to close, and the audience can still state the core claim."

### Too much, busy, dense, or long

Check which content, containers, or graphics repeat the same information or compete for attention, and whether they sit at the wrong tier. Read [Density and presentation tiers](references/surface.md) and [Emphasis](references/emphasis.md).

### Unclear, "can't tell what matters," or "where do I look?"

Check the focal point, hierarchy, grouping, and labels. Read [Visual surface](references/surface.md) and [Craft](references/craft.md).

### Inconsistent, with drifting headings or labels

Check role grammar, anchor positions, and token drift. Read [Consistency](references/consistency.md).

### Over-designed, decorated, or "AI-made"

Check stacked emphasis, decoration without a job, and competing focal points. Read [Emphasis](references/emphasis.md).

### Cheap, unfinished, plain, or generic

Check type, color, spacing, depth, and imagery. Read [Craft](references/craft.md).

### Hard to use, hard to find, or too many steps

Check affordance, prominence, flow, and progressive disclosure. Read [Interaction prominence](references/surface.md).

### "Feels wrong" or mixed feedback

Start with the artifact's purpose and first focal point, then inspect the reference files for the two best-evidenced causes.

### Completion

There is one working hypothesis with a cause, a change, and a signal; the other candidates are stated and either ruled out or deferred; every reference file read was triggered by the current cause. If the task is analysis only, stop here, report the diagnosis and proposed changes, and do not edit.

## 3. Choose the intervention

Choose the smallest set of changes that moves the named signal. Prefer structure and type to establish hierarchy. Merge or remove visual elements that only repeat existing information; choose a new representation or tier for elements that carry distinct information. Keep one distinctive element; restraint is not flattening. Give each reduction a specific reason instead of targeting a quota. When evidence points to grouping or structure rather than surface styling, restructure or propose a structural change. When the problem is the product's interaction model, state that a purely visual adjustment cannot solve it. Do not retreat into exploration merely because the change is large.

When the choice genuinely belongs to the user, confirm before acting: two or more materially different aesthetic directions exist; an independent argument or claim would disappear; a capability would be removed; or the overall direction would change. As long as the original distinction stays clear, changing the way something is visually encoded is itself a design adjustment, not a content change; confirm only when that encoding is the sole carrier of the information, or the user depends on it. If the cause and the fix are both clear, act directly. If the user is rejecting the direction rather than the execution, say so and offer two or three alternatives instead of continuing to polish a direction that has been rejected. Do not re-ask facts you can check in the artifact, and do not re-ask feedback the user has already given.

Completion: the change list is scoped and maps to the causes; the preserve list is still intact; the choices that touch meaning or direction are confirmed.

## 4. Edit

Work inside the artifact's own system: its existing tokens, components, type scale, spacing rhythm, layout rules, and runtime. Move content to the appropriate tier — speaker notes, help text, a detail page, a secondary panel — instead of cramming it into the primary presentation area.

Do not introduce a new visual language, restyle adjacent screens, or fix content the feedback did not mention. Remove the CSS, class names, and assets this change leaves behind; leave everything else untouched. For an interactive interface, keep behavior, state, keyboard access, focus, labels, and error recovery.

Completion: the diff touches only the surface the feedback named and its direct dependencies; every moved or deleted block is accounted for at another tier, or explicitly treated as an intentional removal.

## 5. Verify against the feedback

Re-render and compare at the same state and size as the baseline. Check in order:

1. **The original signal.** The phenomenon the hypothesis named, such as one way to close instead of several, a clear first focal point, or a predictable heading role.
2. **The expression.** A new reader can still state the point; the claims the change touches are supported by the artifact's content, including images, numbers, captions, and examples.
3. **Regression.** Layout, overflow, clipping, interaction, navigation, accessibility, and adjacent screens stay unchanged or improve.
4. **Residual issues.** Anything still unresolved, subjective, or unverifiable — no renderer, browser, or required state, or an aesthetic judgment still left to the user.

If you cannot render, state which checks are based on source files alone. Programmatic measurements (pixel counts, element counts, overflow, color histograms) are supporting evidence only; they do not replace visual judgment. If you cannot view the artifact, delegate the visual check to an assistant with vision, report it as unverified, or ask the user; do not claim a visual improvement from proxy metrics alone. If a claim carried by an image or example cannot be verified, name exactly which one is unverified instead of repeating it as fact.

Completion: before-and-after evidence for the named signal; the regression check is done; what remains unverified is listed explicitly.

## 6. Report

Start with what changed and why. Show the before-and-after evidence tied to the named signal, and restate the preserve list. Ask only the aesthetic choices that the evidence cannot decide. Do not claim the design is "fixed" or "better" beyond the scope you verified, and do not grade the aesthetics or issue a pass/fail verdict. If the user is still dissatisfied, revise the hypothesis instead of defending it.

Completion: the user can see what changed, what was verified, and what still rests on their judgment.
