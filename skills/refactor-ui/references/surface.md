# Visual surface: what belongs here

A visual surface is the extent an audience can see at once. Every element on it competes for the same attention. Most "too complex" feedback comes from too many responsibilities carried at once, not from too many pixels.

Read this file when the feedback concerns quantity, density, clarity of purpose, repetition, or the prominence of an interaction.

## 1. Fix the visual surface's responsibility

State the responsibility in one sentence: understand one claim, make one decision, complete one task, compare options, or experience one moment. "Show everything about this topic" is not a responsibility.

- One visual surface carries one primary responsibility. If two responsibilities genuinely matter equally, split the visual surface, or order them one after the other.
- If the medium cannot be split — a modal, a single screen, one slide — then keep the responsibility that serves the user's next action and move the other to a lower tier.
- Different visual surfaces can carry different responsibilities; do not make the whole artifact carry one responsibility.

Test: if you remove everything that is not needed to fulfill the responsibility, what remains? What remains is the candidate core content.

## 2. Put content at the right tier

Content can sit at four tiers:

1. **Primary content** — the claim, decision, or action the visual surface serves.
2. **Supporting content** — the one or two pieces of information the audience needs in order to trust the primary content or act on it.
3. **On-demand** — details, definitions, edge cases, history, settings, and secondary actions. Tooltips, expandable regions, detail views, secondary panels, appendices, or notes files can carry them.
4. **Outside the surface** — the speaker script, timing, facilitation prompts, implementation notes, and reminders.

Move content down a tier before considering deletion. Delete only content that has no responsibility at any tier.

- **Talk or presentation.** The audience watches and listens at once. The visual surface gives the claim; the speaker explains. Unless the deck is explicitly a self-readable handout, put full explanations and prompts such as "ask the room" in the notes.
- **Reading document.** No speaker helps the reader. Keep the explanation, but establish hierarchy and grouping.
- **Application or tool.** Prominence follows frequency and consequence. Low-frequency settings and destructive operations can move into a menu, but the visible entry point must remain.
- **Reference material.** High information density is itself the goal. Keep the data; improve grouping, alignment, and browsing order.

## 3. Check for duplication

Two blocks carrying the same responsibility compete with each other. Merge them, or remove one.

Common forms:

- a heading and a conclusion saying the same thing in different words;
- a label stating a category the heading already made explicit;
- an explainer paragraph restating the claim;
- a closing summary repeating what the audience has just seen;
- help text that exists only because the design is unclear — improve the design first, then delete the text.

Duplication can also carry a narrative role: a question opened at the start and answered at the end, a motif that recurs, or a recap that is itself the point. Keep duplication that produces an effect through time or sequence; remove duplication that competes within one view.

Test: cover the block in question. Can the visual surface still make the same point? If it can, the block either has a different responsibility or can be removed. If it cannot, the block is carrying meaning; keep it and make it quieter.

Optional is not the same as competing. Subtitles, captions, credits, or notes with different responsibilities should stay even when they could be omitted. Do not impose a uniform word limit or a cut percentage; a visual surface that is already quiet does not improve by becoming quieter.

A recap that only restates an existing claim is duplication; one that adds a synthesis, a decision, or a consequence is new content. A closing page that merely repeats the earlier pages can be deleted; a paragraph that draws the recurring content into a conclusion is an argument, not a simple recap.

## 4. Edit the copy, do not rewrite the claims

- Merge sentences that carry the same responsibility.
- Compress a paragraph into one claim plus one piece of supporting information.
- Delete lead-ins, vague wording, and meta-narration such as "this page will…".
- Keep the author's voice, the facts, the qualifiers, and the meaning. Mark inferences; do not invent smoother facts.
- Prefer concrete nouns and verbs. Do not turn every line into a slogan; slogans lose precision.
- Credits, licenses, and legal text must stay, in a subdued, stable style.

Deleting an independent argument or changing a claim changes meaning and needs confirmation. Compression and migration do not change meaning.

## 5. Density is not complexity

Tables, dashboards, reference docs, schedules, data-rich interfaces, and detailed reading material may all need high density.

- Complexity comes from the number of decisions competing at once, not from the number of pixels.
- Manage density with grouping, alignment, hierarchy, and progressive disclosure. Do not shrink the type until it is hard to read, and do not hide data the user needs.
- If content still overflows, split the visual surface, or move details to a lower tier. Shrinking the type to fit is not layout design.
- A sparse visual surface that does not give enough information to act is also a failure. The goal is not empty space.

When a surface is dense and cluttered, order it around the user's next decision, then choose how to represent the data:

- Put information that changes a decision or next action in the first-read tier; group routine context in a compact list or table. Grouping only by data category may still leave every region equally prominent.
- Inspect each card, badge, and mini chart: if it were covered, could the original information still be read? Merge or remove elements that only repeat existing information. Keep a chart that uniquely communicates a useful change or trend, or replace it with another form that conveys the same information.
- Merge containers with the same responsibility. Use dividers, alignment, and type weight to establish hierarchy; reserve the strongest emphasis for the signal the user needs to see first.

### Operations dashboards: show what needs attention first

Set priority from the user's task and the existing states, thresholds, or alerts. When operators need to decide whether to intervene, show anomalies and pending events first, then present stable metrics compactly. Keep every required value and event record; keep frequent filters and the primary action easy to find and use. Compare with the baseline at the same size: can a viewer identify what needs attention first, while still finding the remaining data and actions easily?

## 6. Adjust the prominence of interactions

When the feedback is about use rather than appearance:

- Reproduce the task and find where the user hesitates, misreads, or turns back. Observe the actual path of use; do not judge from a screenshot alone.
- The primary action must be visible and easy to recognize. Reduce the prominence of secondary actions without hiding them.
- Progressive disclosure needs a visible entry point and a discoverable label. Hiding a feature is not simplifying.
- Keep keyboard access, focus states, labels, error messages, undo, and recovery.
- A flow problem is not a styling problem. Change the order, the default, or the affordance, not just the color.

## 7. Completion check

- A new user can state the point or the next action.
- Every visible block has a different responsibility; no two blocks in one view do the same thing.
- Every moved or deleted block has been placed at another tier, or is explicitly an intentional removal.
- A high-density visual surface is still easy to browse; a low-density one still provides enough information to act.
- Required facts, instructions, credits, and functions are all intact.

## Avoid

- Cutting every visual surface by a uniform percentage.
- Shrinking the type so the content fits.
- Hiding core functionality to look simple.
- Deleting credits or qualifiers because they hurt the look.
- Applying "one thing per page" to material meant to be read in full.
- Replacing explanations with vague slogans.
