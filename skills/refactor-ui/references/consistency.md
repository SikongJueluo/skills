# Consistency: one system, not one template

Consistency is a stable grammar of roles, not identical layouts. What matters: are like things treated alike, and do unlike treatments each express a different meaning?

Read this file when the feedback says the work is inconsistent, feels like unrelated pieces stitched together, or when the user explicitly does not want every screen to share one layout.

## 1. Inventory the roles

List the roles the artifact actually uses, and how each is treated:

- page or section titles;
- lead-ins, eyebrows, or category labels;
- body text, emphasized text, and supporting text;
- captions, metadata, credits;
- navigation and progress indicators;
- primary and secondary actions;
- images, figures, and their frames;
- callouts, pull quotes, numbers, and status labels.

For each role, record where it appears and every treatment it receives. Feedback usually comes from one of three situations: one role gets several treatments; one treatment carries several roles; or different treatments imply a distinction that does not actually exist.

## 2. Role → treatment → meaning

- One role, one treatment; one treatment, one meaning.
- A difference is justified only when it expresses a real distinction, such as hierarchy, content type, interaction state, or narrative beat.
- Position carries meaning too. A title anchored inside the content column and a title placed in a full-width top bar read as different levels. At equal level, use the same rule; if the difference is intentional, make the distinction systematic and visible.
- A caption is not a label, and a label is not a heading. Do not let one visual style carry two responsibilities for convenience.

Test: point at one instance and ask what a reader would infer from its treatment. If the inference is wrong, the role grammar has a problem.

## 3. Ground the variation

- Layout follows content structure: comparisons use side-by-side, sequences use steps, a single claim uses one focal element, a gallery uses a grid.
- Alternation — an image left, then right — can create a reasonable rhythm. It is a problem only when it implies a distinction that does not exist or breaks the reading order.
- Different page types can share a system without sharing a template. A system is a grammar, not a straitjacket.
- Uniformity that erases a necessary distinction is also inconsistent: it treats unlike things as alike.

Do not use "every page looks different" as a reason to force every page into the same layout. Stabilize the role rules, and let the content structure decide the layout.

## 4. A label is a contract

- One label style carries one responsibility. If the same style is used for categories, questions, explainer tags, and calls to action at once, the reader cannot decode it; split the roles.
- A label should give information the heading does not. A label that repeats the heading's content is only decoration.
- Keep the label set small: section labels, status labels, note labels. If you need a fourth, check whether it should actually be a heading or body text.
- A label that is really an action should look like an action, not like metadata.

## 5. Do not check only the color tokens

Reusing tokens does not guarantee consistency. Check as well:

- **Type:** family, size scale, weight, case, letter spacing, line height.
- **Color:** semantic roles — text, muted text, accent, semantic colors — not merely shared hex values.
- **Space:** spacing scale, within-group versus between-group relationships, aligned edges.
- **Shape:** corner radii, border widths, shadows, dividers.
- **Media:** ratio, cropping, matte or frame, caption position, credit style.
- **Interaction:** hover, focus, active, disabled, icon style, control height.

Two elements can share one token and still express different meanings; two roles can use different values and still be coherent, as long as the differences are systematic. Fix the semantic rules, not just the variables.

## 6. Fix within scope

- Build the role map before editing, then fix the outlier treatments and ambiguous roles that produced the feedback.
- Do not stamp a template onto every screen, and do not reset approved differentiating styles.
- If the artifact has no stable grammar, define only the minimal rules that cover its actual roles; do not build a full design system.
- Keep a local exception that carries meaning, and state the rule it follows.
- Do not turn an inferred rule into a permanent project convention. Record it only after the user adopts it.

## 7. Completion check

- Pick any three instances of the same role and a reader can predict how each is treated.
- Pick any three different treatments and you can state the meaning of each difference.
- The specific inconsistency raised in the feedback is gone; unrelated screens were not redesigned.
- Reasonable variation — density, layout, imagery, rhythm — survives.
- Every label carries one responsibility.

## Avoid

- Making every page exactly the same.
- Using one type size for headings at different levels.
- Adding tokens while leaving conflicting semantics in place.
- Fixing one instance while other instances of the same role stay inconsistent.
- Calling any layout difference an inconsistency.
