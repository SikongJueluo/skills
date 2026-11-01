# HTML → editable PPTX

Use this branch for an existing HTML deck that needs a `.pptx` copy. Preserve its content, order, and visual direction; go directly to conversion rather than repeating the brief or style exploration. For a new deck requested in both formats, read this before authoring, then use the normal HTML generation flow.

This is an operating reference, not a bundled exporter. The skill ships no HTML-to-PPTX engine, maintained fork, or patch set. [PPTX → HTML](pptx.md) is a separate branch.

## Conversion contract

**Editable** means content text remains native text, simple geometry remains native shapes/lines, and tables or charts remain native objects when required for the user's editing task. Photos and logos remain pictures. An SVG or PNG can be moved and resized without making its text or geometry editable.

Choose representations in this order:

| Source content | Preferred PPT representation |
| --- | --- |
| Titles, body text, captions, labels, numeric values | Native text with font/run styling |
| Cards, solid fills, borders, arrows, circles, axes, connectors | Native shapes/lines; a polygon is not inherently a screenshot requirement |
| Tables or charts whose data must be edited | Native table/chart, or an explicit agreement about a less editable representation |
| Photos and logos | Original asset embedded as a picture; reproduce crop/fit separately |
| Complex effects without a suitable native mapping | A local fallback with a recorded reason and editability loss |

A screenshot is a fallback, not proof of conversion. Outlined text, SVG text, or a whole-slide picture does not satisfy a request for editable content. Get the user's agreement before degrading required editable content or materially changing the design. Grouping many native shapes does not turn them into an editable data chart.

## 1. Inspect the deck and tool

Read the HTML, asset files, and runtime before choosing a tool. Record slide count/order, authored stage size, fonts/weights, images, overlays/captions, tables/charts, and interactive content's intended static state. Identify which objects the user needs to edit; use the native-first contract above unless they specify otherwise.

One candidate is [Hasasasa/html-to-editable-pptx](https://github.com/Hasasasa/html-to-editable-pptx), used in the motivating conversion case. Read its `SKILL.md`, dependency declaration, and CLI help at the revision actually used. Record repository/revision, command/options, and any existing local modifications in the job report. A moving `main` is not a reproducible version. This link is a discovery pointer, not an endorsement of every output or upstream workflow rule.

After preparing its environment and the export copy, the candidate's basic invocation is:

```text
python <converter-dir>/convert.py <deck>/index.pptx-source.html --out <deck>/index.pptx
```

Confirm flags with `python <converter-dir>/convert.py --help` before use. Any automatically created/reused audit copy must derive from the prepared view. Keep verification enabled; inspect warnings and evidence rather than equating the command with acceptance.

Check the chosen implementation, not only its advertised CSS support:

- Does `<img>` embed source bytes, or capture its rendered box? Does inline SVG become native objects, an SVG picture, or PNG?
- Which CSS patterns trigger decoration screenshots? Do they capture captions, siblings, or ancestor backgrounds?
- How are stage transforms, font weights, empty decorative elements, and shape theme effects handled?
- Can it honor the deck's export state and produce evidence for both visual fidelity and editability?

Check Python/Node as applicable, browser launch, fonts, and a PPTX renderer before a full run. Rendering requires a usable Office/LibreOffice path; LibreOffice-to-PDF-to-PNG workflows may also need Poppler. Use the project's environment mechanism for missing packages, with required approval; on Nix use declarative project configuration, not imperative system installation. Reuse a system browser only if the converter supports it.

Keep tool code separate from the deck and avoid writes into a read-only installed skill. Place permitted caches/profiles in a writable job directory using supported settings. Font installation and other user/system changes require consent. Embedding a font is not proof that every viewer will use it; inspect embedding permissions and the renderer's available fonts.

Completion: the deck inventory, editing requirements, tool identity, conversion command, and available renderer are known. If dependencies or tool capabilities block the request, state the blocker rather than promising an export.

## 2. Prepare an export view

Preserve the original HTML and assets. Apply conversion-only changes to a sibling working copy so relative assets still resolve; record deviations from the source. Check whether the selected converter automatically reuses an old working copy before converting a newly edited source.

Use the [existing export contract](../html-template.md#export-contract): load `?export=1`, await `window.deck.ready`, and activate each page with `window.deck.goToSlide(index)`. Inspect dynamic widgets for their final static state. Older decks need an equivalent explicit preparation step. If a converter ignores this contract, use a documented adapter/preparation facility or a prepared copy; adding a query string to an unrelated screenshot run does not change the converter's input.

The export view excludes editing toggles, navigation controls, dialogs, and tooltips that are not slide content. Keep the browser editor in the original deck. Verify the actual conversion view, not only an independently opened browser tab.

Keep one coordinate space: convert measured viewport coordinates back to authored stage coordinates exactly once, accounting for scale and translation, or measure with the stage at unit scale. Distinguish transformed `getBoundingClientRect()` bounds from computed CSS values such as `font-size`, which may already be in authored units. Check known text/picture bounds, crop rectangles, font sizes, and slide dimensions for consistent units rather than applying the inverse scale indiscriminately. Changing CSS widths cannot repair a converter that mixes coordinate spaces.

For dual-format authoring, prefer explicit geometry for simple diagrams and local asset references where the design permits. Preserve the chosen design rather than banning gradients or shadows from every HTML deck.

Completion: the prepared view has the correct slide count, no editor chrome, settled fonts/media/widgets, and a consistent stage coordinate mapping.

## 3. Prove the route on representative pages

Before converting the full deck, test pages covering its actual risks: dense CJK text, mixed font weights, a photo with overlapping caption, a diagram/table, or complex decoration. Convert a temporary subset if the tool cannot select pages.

Inspect both the rendered PPTX and its object structure. Inventory each required element as native text, shape/line, table/chart, source image, or fallback image. Confirm source-image reuse from the embedded media and relationships, not the presence of an `<img>` tag. Unchanged originals can be compared by hash; if a tool re-encodes an asset, record that and inspect dimensions, crop, and quality instead of claiming byte-for-byte reuse.

Check text independently of shape counts: hidden text under a screenshot and captions duplicated inside images can make counts look healthy. A full-page photo is legitimate when it is the source background; a full-page image of the composed slide is not the same thing.

If the pilot fails, use [symptom-based troubleshooting](pptx-troubleshooting.md) to distinguish export preparation, coordinate errors, tool defects, renderer behavior, and actual format limits. Choose another route or agree on a bounded compromise before scaling the failure to every page.

Completion: each representation needed by this deck has evidence, and any proposed loss of editability or material design change has been accepted.

## 4. Convert and repair

Run the full conversion against the prepared copy. Save the command, warnings, object/fallback inventory, and HTML/PPT comparison renders. A produced file or successful exit is not acceptance; some converters continue after failed font resolution, rendering, or audit generation.

For each finding, record page, stable element name, HTML state, PPT difference, suspected output channel, and supporting evidence. Batch related repairs, rebuild, and inspect the changed pages plus likely regressions.

- Page-local changes may use incremental conversion only when cache validity is established.
- Global CSS, fonts, export preparation, converter options/code, or page-order changes invalidate affected cached evidence; rebuild/review all potentially affected pages. When the affected set is uncertain, use a full run.
- A repeated finding calls for a targeted probe and diagnosis, not endless CSS guesses or automatic acceptance as a format limit. Inspect measurements, output XML, and tool behavior as needed.
- A tool defect is not an HTML anti-pattern or an OOXML limitation. Do not turn a task into converter maintenance: try a supported route, another tool, or an agreed workaround. If none meets the request, report the blocker; maintaining a patch/fork is separate work.

Keep audit summaries and evidence until acceptance. Remove bulky intermediate files only within the agreed cleanup scope; preserve the final findings, tool identity, and fallback list.

## 5. Accept on two axes

### Visual fidelity

Render the final PPTX and compare every page with the prepared HTML at a common aspect ratio/scale. Look for missing objects, wrong size/crop, background contamination, duplicate captions, clipped text, font/weight/line-break changes, z-order, and unintended theme shadows. Contact sheets help triage; inspect detailed pages before dismissing a suspected defect.

Use an image-capable agent for visual inspection when needed and verify that it can actually view the images before dispatching a deck-wide audit. If the runtime cannot provide vision, ask for human inspection. Generated comparison images alone are not an inspection.

### Editability and integrity

Inspect the PPTX structure for every page against the inventory: content text is native text, required geometry is native, required tables/charts are the promised object type, pictures resolve to the intended assets, and each fallback has a reason. Check for hidden duplicates and composed-slide screenshots. Text extraction and XML/object counts are supporting evidence, not a complete pass.

In the intended presentation application, test representative edits: change text, move/resize a shape, and edit table/chart data when required. If that application is unavailable, distinguish structural checks from unverified application-level editing. A LibreOffice render does not establish PowerPoint or WPS compatibility.

Completion: both axes have evidence tied to the final build; remaining defects and verification gaps are explicit and any required compromise has user agreement. If no renderer is available, ask whether to install/use one, move verification elsewhere, or deliver an explicitly unverified draft. Never call that draft visually approved.

## 6. Deliver

Report:

- PPTX path and slide count; source HTML unchanged; prepared copy path if retained.
- Tool revision, invocation, and renderer/application used for checks.
- What remains native, what reuses source assets, and which pages/elements were rasterized, outlined, re-encoded, or visually simplified and why.
- Visual coverage, structural coverage, application edit tests, and all outstanding checks/defects.
- Paths to the final audit summary and any retained evidence.

Use precise claims such as “body text and card shapes are native; two decorative labels are pictures.” Reserve “fully editable” for the agreed scope with evidence. A clean visual review alone cannot justify that claim.

## Basis and limits

This workflow distills a 36-slide HTML-to-PPTX case: screenshot background contamination, captions baked into images and then duplicated as text, editor chrome leakage, missing simple geometry, font/coordinate mismatches, and inherited theme shadows. The conversation's final success report is not a verified benchmark and its local patches are not shipped here. Treat these as regression scenarios to reproduce, not permanent facts about an evolving converter. For current symptoms and evidence to collect, read [PPTX troubleshooting](pptx-troubleshooting.md).
Several SVG workarounds in that case improved appearance by becoming pictures; they motivate the separate editability gate, not a promise of editable SVG conversion.
