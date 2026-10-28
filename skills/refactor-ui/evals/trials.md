# Trials — 2026-10-28

Two fresh agents followed `SKILL.md` as a real request. Each worked on a copy; the originals were left untouched. The trials test the skill's process, not a controlled comparison against an unaided agent.

## Limits

- Both trial models rejected image input. They verified structure with DOM counts, computed styles, overflow audits, and pixel statistics, and reported visual quality as unverified. The orchestrator later viewed the PNGs and confirmed the layout findings below; the trial agents did not see them.
- One run per artifact. No blind comparison, no user preference test, no trigger-set runner.
- The skill changed after the trials to close the gaps they found. Both runs used the pre-patch core loop; the dashboard run also predates the routing and no-vision patches.

## 1. Real deck — six-slide live talk

Artifact: copy of the English course deck at `.dsh/ui-skill-trial/lingshu-trial/`; baseline at `.dsh/ui-skill-trial/render/baseline/`, result at `.dsh/ui-skill-trial/render/after/`. Feedback: too much text, inconsistent headings and labels, too much decoration.

What the agent did:

- Moved the two "Ask the room" prompts into the existing speaker-note comments.
- Shortened the slide 3 explanation; kept the claim and the takeaway.
- Removed the redundant chips on slides 2 and 6, the six-block triad recap, and the closing exhortation.
- Reduced the emphasis stack on slides 3 and 4: removed yellow highlights from already-large claims, so the yellow through-line is the cover question and the closing answer.
- Unified the two callout styles, the three takeaway treatments, the caption grammar, and the footer labels.
- Removed the cover's outer ring and one of the two cover text blocks; kept the yellow "=" orb, the frame, the type system, the palette, and all credits.

Measured result:

| Slide | Content words | Text blocks |
| --- | --- | --- |
| 1 cover | 36 → 15 | 4 → 2 |
| 2 shortlist | 49 → 41 | 7 → 6 |
| 3 door | 73 → 48 | 6 → 5 |
| 4 calculator | 59 → 53 | 6 → 6 |
| 5 remotes | 53 → 47 | 4 → 4 |
| 6 conclusion | 136 → 80 | 14 → 4 |

Total content words 406 → 284. The reduction is not uniform: the conclusion loses the most, the visual comparison page almost nothing. Zero overflow; all images load. Rendered inspection confirms a clear first read on every slide and the same visual direction.

Judgment:

- The revision is bounded and keeps the deck's identity. The cover, slide 3, and slide 6 are noticeably calmer; the visual comparison page is left to do its job.
- The cover cut is a judgment call: the premise subtitle had a job, and removing it shifts that job to the speaker. The updated skill now says a quiet surface is not improved by becoming quieter and that an optional block with a distinct job stays.
- The heading anchor still varies between split pages (title in the column) and full-width pages (title at top). The result reads consistently because the split pages keep the title with the text column, but the agent did not state this as a rule. Whether it is a real inconsistency or legitimate structural variation remains a taste decision.
- **Image truth failed.** The left remote image in slide 5 shows the back of a remote with no buttons, but the caption and alt text say "Too many buttons". The trial agent trusted the alt text and reported photo content unverified; it did not catch the mismatch. The skill now tells an agent to name the specific claim that remains unverified instead of repeating it as fact.

## 2. Dense dashboard — anti-minimalism counterexample

Artifact: `evals/fixtures/dense-dashboard/index.html`, copied to `.dsh/ui-skill-trial/dashboard-trial/`. Twelve metrics, a ten-row event table, and three daily filters. Feedback: too busy.

What the agent did (CSS only; markup and data unchanged):

- Merged twelve bordered, shadowed cards into one panel with hairline dividers.
- Reduced the delta weight and stopped spending the accent blue on every sparkline.
- Removed the box around the filter row.
- Kept every metric, the table, the filters, the navigation, and all controls.

Measured result: saturated pixels in the metrics band 955 → 270; accent-blue pixels 637 → 0; vertical box lines 8 → 5. All twelve metrics, three filters, and ten rows by seven columns remain. The narrow breakpoint keeps the three-column grid without doubled or missing dividers. The orchestrator inspected the after and narrow PNGs: the page is calmer without losing data or controls.

## What the trials changed in the skill

- Route "busy" to both `surface.md` and `emphasis.md`; the dashboard's dominant cause was emphasis competition, not raw density.
- Add a concrete move set for dense-and-busy surfaces: group, merge containers, spend the accent once, quiet metadata, set the scan path.
- State that programmatic measurements are supporting evidence, not vision, and require an explicit unverified report when the agent cannot view images.
- Add a branch for artifacts with no project rules: use their own tokens and repeated treatments, and keep inferred rules provisional.
- Clarify that changing a visual encoding is a design move when the distinction stays legible; confirm only when the encoding is the only carrier or the user relies on it.
- Add a stop checklist to `emphasis.md`, the "optional is not competing" rule and a recap boundary test to `surface.md`, and remove the cut-quota failure mode.
- Clarify same-size before/after for scaled fixed-stage decks, and remove orphaned CSS, classes, and assets with the change.

## Not tested

- A vision-capable agent following the skill end to end; the image-truth path is instructed but was not executed successfully here.
- Trigger behavior; `trigger-set.json` is defined but no local runner was available.
- A real user's preference judgment on either revision.
- Keyboard, pointer, edit-mode, print, and cross-browser behavior.
