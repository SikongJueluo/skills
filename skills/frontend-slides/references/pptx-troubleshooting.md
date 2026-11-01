# Editable PPTX troubleshooting

Read this when an HTML → PPTX pilot or audit finds a mismatch. The [conversion workflow](editable-pptx.md) owns preparation, acceptance, and delivery; this file helps identify the failed representation. Paths and channel names below are examples from the candidate converter, not a stable API.

## Diagnose the representation

For the affected page and element, compare:

1. The source asset and prepared HTML render.
2. Measured text/shape/media records, including bounds, font/run styles, and intended output channel.
3. The PPTX object's XML, relationships/media, and rendered result.

Identify the first stage where the evidence diverges. If the prepared HTML is wrong, fix its export state. If records are wrong, diagnose measurement; if records are right but XML is wrong, diagnose assembly; if XML appears right but viewers differ, investigate fonts and renderer behavior. Use a minimal page/element probe when the full deck obscures the cause.

## Screenshot contamination and assets

| Symptom | Evidence to collect | Response |
| --- | --- | --- |
| A card or transparent logo has an unexpected rectangular background | Its actual channel and capture bounds; captured PNG alpha; ancestor backgrounds; final picture placement | Use native geometry or the original asset when possible. For a necessary capture, isolate the intended layer and bounds. `omit_background` alone does not remove backgrounds painted by ancestors. Removing a shadow may avoid a screenshot trigger, but that changes the design and does not repair capture isolation. |
| Captions or labels appear twice | Open the embedded media and look for baked-in text; count native text records and inspect overlap | Keep each foreground label in one representation. A screenshot can include an absolutely positioned sibling even when text is emitted only once. Hiding descendant text alone may not isolate a picture from its sibling overlay. Prefer original image bytes plus native caption. |
| The deck uses `<img>`, but the PPT contains resampled screenshots | Trace the object's relationship to its embedded media; compare source bytes/dimensions; inspect the tool's real image path | Choose a source-embedding route when available. Reproduce `object-fit`, `object-position`, transparency, and crop without baking adjacent text into the image. Tag/class changes alone do not prove original-asset reuse. |
| A picture is shifted, stretched, or has excessive padding | Source dimensions; element bounds; screenshot clip before/after viewport clamping; PPT picture bounds and crop | Check coordinate conversion and capture-box updates together. Preserve aspect ratio and match the intended crop; avoid compensating with arbitrary per-page offsets. |

## Missing geometry and unwanted effects

| Symptom | Evidence to collect | Response |
| --- | --- | --- |
| Timeline dots, lines, empty boxes, or pseudo-element decoration vanish | Whether the element produced a shape record; measured nonzero bounds; computed fill/border; pseudo-element handling | Map simple geometry to native lines/shapes using a supported route. If the engine omits empty elements, this is an extraction gap, not a PPT inability to draw circles. Inline SVG may restore the picture while losing geometry editability; classify it accordingly. |
| An arrow or clipped panel becomes a rectangle | `clip-path`/transform handling; native geometry or screenshot channel; final shape path | Prefer a native arrow/freeform polygon when it expresses the design. A tool's raster fallback is not evidence that OOXML cannot represent the polygon. |
| New shadows appear around otherwise flat PPT shapes | Explicit shape effects and style/theme references such as `effectRef`; the referenced theme effect style | Verify an unintended inherited effect before changing it. Use a supported explicit no-effect style if available; a blanket change to every theme reference can erase intentional design. |
| A simple diagram becomes one image | Representation of its labels, connectors, and geometry in the final PPTX | Use native objects when diagram editing is required. SVG insertion, even when vector, is not automatically editable geometry. For complex diagrams, agree on the acceptable editing scope. |

## Text, fonts, and coordinates

| Symptom | Evidence to collect | Response |
| --- | --- | --- |
| A title loses its last characters despite a wide HTML box | Actual measured text bounds vs. element bounds; stage transform/viewport scale; PPT textbox extent, insets, font size, and wrap | Locate the first width mismatch. Check for a scale applied twice or only to some fields before widening CSS. Text-box padding, glyph advances, and line breaking can also be responsible; do not infer a universal cause from one ratio. |
| Text or pictures are consistently too small or offset | Known authored coordinates, rendered coordinates, stage translation/scale, and PPT units | Normalize all coordinates once. A fixed-stage deck measured at a smaller viewport needs one inverse transform or unit-scale measurement, not ad hoc multipliers on individual objects. |
| Thin/medium text becomes regular/bold | Requested weight/style; resolved font file's internal names and weight; selected PPT typeface; embedded instances; renderer font availability | Test exact static font instances/typeface mapping supported by the tool. A bold flag is not arbitrary CSS weight, but that does not make all non-400/700 text impossible in PPT. Rasterizing or outlining text is a loss of text editing, not a font fix. |
| CJK glyphs are missing or a viewer changes line breaks | East Asian/Latin typeface assignments, actual glyph coverage, embedding status/permissions, and fonts available in that viewer | Verify the intended font path in the target application. Installing a font may resolve viewer fallback but needs consent; embedding alone is not cross-viewer proof. |
| Superscripts, labels, or table values move to another line | Run boundaries/baselines; textbox grouping/width; real paragraph spacing and alignment | Preserve native runs and adequate bounds, or use separate positioned textboxes. For a table, consider native cells. Repeated spaces and SVG text can mask layout bugs while weakening editing. |

## Export state and stale evidence

| Symptom | Evidence to collect | Response |
| --- | --- | --- |
| A pencil button, navigation, or dialog appears on every page | URL/state used by the actual converter; fixed-position nodes; prepared-view screenshot | Apply the deck export contract in the conversion view. Keep non-content UI out of that view while preserving the original HTML's editing behavior. |
| Counters show zero, diagrams are incomplete, or only one page is found | Runtime readiness, final-state handling, activation behavior, and measurement timing | Wait for the export-ready state and activate pages through the deck API or a verified adapter. Disabling animation alone does not compute a JavaScript widget's final value. |
| A fix seems ineffective or the audit disagrees with the output | Source vs. reused prepared copy; cache inputs; command/options; final PPTX and comparison build identities | Confirm the converter consumed the edited file. Invalidate affected cached measurement/renders; global preparation or tool changes require corresponding fresh evidence. |

## Record the outcome

A reusable finding contains the symptom, minimal trigger, tool revision, failed representation, evidence, chosen remedy, and remaining editing/visual cost. Separate confirmed causes from hypotheses. Keep deck-specific paths/page numbers in the job's report; promote a general rule only after checking its scope.

The motivating case used local image-isolation and theme-effect patches. Neither is maintained by this skill, and either may become obsolete upstream. When a workaround cannot meet the user's contract, report a tool limitation and options instead of silently weakening acceptance or starting a converter fork.
