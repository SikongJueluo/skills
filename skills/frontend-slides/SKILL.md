---
name: frontend-slides
description: Create, convert, or revise browser-based 16:9 HTML slide decks, including PPT/PPTX conversion, Chinese/CJK typography, and PDF export. Use when the user asks for a presentation, slide deck, pitch or talk slides, or wants an existing HTML deck changed. Not for ordinary websites, landing pages, or written documents.
argument-hint: "[deck request, .pptx path, or existing HTML deck]"
---

# /frontend-slides

Build a presentation that runs in a browser: one fixed 1920×1080 stage, scaled as a whole, with no build step. A deck is a folder:

```text
<deck>/index.html
<deck>/assets/...
```

All paths in this skill are relative to **this skill directory**. Resolve that directory before reading support files or running scripts; do not assume the current working directory is the skill root.

## Non-negotiables

- **Fixed stage.** Every slide is authored at 1920×1080 inside one stage that scales uniformly. Letterbox or pillarbox on other aspect ratios; never reflow slide content for phones.
- **Visibility contract.** Switch slides with `.active` / `.visible` on `.slide`; never `display: none` for slide switching. Include the full contents of [viewport-base.css](viewport-base.css) in every generated deck.
- **One runtime.** Generated decks use the inline controller in [html-template.md](html-template.md). Do not mix in a second navigation component or a second stage scaler.
- **No build step.** CSS and JS stay inline in the HTML. Images normally live in `assets/`; only inline them when the user asks for a portable single file.
- **Progressive disclosure.** Read `selection-index.json` before template metadata, `preview.md` before a full `design.md`, and exactly one selected `design.md` when generating.
- **Honest delivery.** Do not claim a browser, screenshot, PDF, or deployment was verified unless it was.

## 1. Classify the request

- **New deck** — create from the brief in steps 2–4.
- **PPT/PPTX conversion** — extract first; use [references/pptx.md](references/pptx.md), then continue with steps 2–4.
- **Revise an existing HTML deck** — read the deck and its assets before editing; follow "Changing an existing deck" below.
- **Export only** — go straight to [references/pdf.md](references/pdf.md).
- **Share or publish** — only when the user explicitly asks; use [references/deploy.md](references/deploy.md).

Reuse every fact the user already supplied: topic, audience, length, content, language, visual direction, and file path. Do not ask again. Ask one compact batch only for facts that block the work.

## 2. Brief

Ask in one message, with numbered choices when no structured question UI is available:

1. **Purpose and audience** — pitch, teaching, conference, internal review, etc.
2. **Length** — short 5–10, medium 10–20, long 20+ slides.
3. **Content** — ready, rough notes, or topic only. Ask the user to share the material.
4. **Density** — low-density/speaker-led or high-density/reading-first.
5. **Language** — only if the deck language is not obvious from the request.
6. **Images** — only if the request mentions or supplies them.

Never ask about inline editing before a draft exists. Include it by default; omit it only when the user asks for a locked or export-only file.

Default the output to `./<deck-slug>/index.html` plus `assets/` unless the user named a path. Completion: mode, output path, content, density, and language are known.

## 3. Choose the style

If the user names a preset or template, or gives a visual direction that maps cleanly to one, use it directly and say which. Otherwise run visual exploration.

For exploration:

1. Read [STYLE_PRESETS.md](STYLE_PRESETS.md) and the metadata in [bold-template-pack/selection-index.json](bold-template-pack/selection-index.json).
2. Shortlist 2–4 bold candidates by `mood`, `tone`, `best_for`, `avoid_for`, `formality`, `density`, and `scheme`. Read only those candidates' `preview.md`.
3. Generate three title-slide previews with the user's real content: one safe preset, one bold template, one wildcard (another bold template or a custom design).
4. Save them under `<deck>/.previews/` as `style-a.html`, `style-b.html`, `style-c.html`. Show them with the agent's browser/image/file-present capability; if none exists, deliver the paths and ask the user to open them.
5. Ask which direction to use. If "mix", ask what to combine.

Preview rules:

- Each preview must look like a real first slide of this deck, not a diagnostic card.
- Never render template names, slugs, `preview`, `Option A/B/C`, file names, paths, or requirement notes on the slide. Names belong in the chat message only.
- Keep the three directions genuinely different. Do not force every expressive option to come from the template pack.
- Delete `.previews/` after the user chooses.

Completion: one style is selected, and if it is a bold template, its single `design.md` path is known.

## 4. Generate the deck

Read these before writing HTML:

- [viewport-base.css](viewport-base.css) — paste it in full into `<style>`.
- [html-template.md](html-template.md) — structure, controller, editing, export contract.
- [animation-patterns.md](animation-patterns.md) — only the patterns that fit the chosen direction.
- The selected bold template's `design.md` — exactly one, only after selection.

For a `design.md`, treat `vw`, `vh`, and `clamp()` as design proportions to translate into 1920×1080 coordinates. Preserve its fonts, palette, decorative vocabulary, spacing rhythm, and component grammar; do not copy demo content. Generate the same visual system for every slide type the deck needs.

Apply the density choice throughout:

- **Low density / speaker-led:** one idea per slide, large type, short phrases, more slides.
- **High density / reading-first:** structured grids, tables, annotations, 4–8 bullets or 4–6 cards where readable.

Split into another slide instead of shrinking text or letting panels overlap.

### Chinese and CJK decks

- Set `<html lang="zh-CN">` (or the correct locale) and keep the file UTF-8.
- Use a distinctive Latin display face if the design calls for one, but always provide a CJK stack, for example `"Noto Sans SC", "Source Han Sans SC", "LXGW WenKai", sans-serif` or `"Noto Serif SC", "Source Han Serif SC", "Songti SC", serif`.
- CJK runs get `letter-spacing: 0`. If a design uses negative tracking for Latin display type, scope it to a Latin-only class; never apply it to Chinese.
- Use generous line height: about `1.7–1.9` for body text and `1.2–1.35` for headings. Avoid weight 300 for small Chinese text and avoid faux bold/italic.
- Do not uppercase or italicize Chinese text. Use Chinese punctuation in Chinese sentences and keep mixed CJK/Latin spacing readable.
- Keep body text at roughly 24px or larger on the 1920×1080 stage; table and caption text at roughly 22px or larger. Split the slide if that does not fit.
- Add `overflow-wrap: anywhere` for long URLs and mixed tokens, then check actual line breaks in a rendered screenshot.

### Output contract

- `index.html` with CSS/JS inline; `assets/` for images unless the user asks for one portable file.
- Include the full viewport CSS, the export contract (`?export=1` and `window.deck`), and the inline editor by default.
- Remote fonts are allowed. Tell the user that a deck relying on Fontshare/Google Fonts may fall back when offline; only claim a portable/offline file after inlining the required resources and checking for remaining external references.
- No placeholder text, lorem ipsum, empty sections, or broken image paths.

Completion: every requested slide exists, all supplied content and images are placed, and the deck opens.

## 5. Verify

Use the exporter's screenshot mode when Node and Chromium/Chrome are available:

```bash
node scripts/export-pdf.mjs <deck>/index.html --png-dir /tmp/deck-shots --viewport 1280x720
node scripts/export-pdf.mjs <deck>/index.html --png-dir /tmp/deck-phone --viewport 390x844
```

Inspect the PNGs — actually look at them, not just at file sizes. Then check:

- The stage stays 16:9 and scales uniformly; the phone view letterboxes instead of reflowing.
- No clipped headings, overflowing cards, overlapping panels, or text below comfortable size.
- Chinese glyphs render, line breaks are sensible, and tracking is not negative.
- Tables and comparison layouts are readable.
- The exporter reports no broken images or 1920×1080 overflow warnings, and
  `.reveal` elements are visible in the captured final state.
- Navigation works, and typing in the editor does not change slides.
- `Ctrl/Cmd+S` downloads a cleaned copy and does not write back to the source file.

If no browser or screenshot capability exists, say exactly that and report which checks remain unverified. Completion: every slide inspected at desktop and phone sizes, or the limitation is stated explicitly.

## 6. Deliver

Report the deck path, slide count, style name, navigation keys, and how editing works. Mention that browser save downloads a new HTML file rather than overwriting the source, and that images live in `assets/`.

Use the agent's file-present or open capability when available; otherwise give the path. Never assume macOS `open`, a desktop session, or a GUI browser.

Do not offer or perform public deployment as part of normal delivery. If the user asks to share it publicly, read [references/deploy.md](references/deploy.md) and obtain explicit consent before uploading.

## Changing an existing deck

1. Read the HTML, the viewport CSS, and the current slide structure before editing. Preserve the existing design system.
2. Keep the fixed-stage model. When new content would overflow, split the slide or tighten the layout; do not add responsive breakpoints or shrink text.
3. Preserve the deck's existing runtime if it works. If it lacks `window.deck`, the exporter falls back to toggling `.slide.active/.visible`; check that the deck uses those classes.
4. Re-run the verification in step 5 after the change, including at least one phone viewport.
5. Do not refactor unrelated markup or restyle other slides.

## Supporting files

| File | Purpose | Read when |
| --- | --- | --- |
| [STYLE_PRESETS.md](STYLE_PRESETS.md) | 12 original presets with colors, fonts, signature elements | style exploration |
| [bold-template-pack/selection-index.json](bold-template-pack/selection-index.json) | Compact metadata for 34 bold templates | shortlisting |
| [bold-template-pack/templates/*/preview.md](bold-template-pack/templates/) | Title-slide preview cards | only for shortlisted candidates |
| [bold-template-pack/templates/*/design.md](bold-template-pack/templates/) | Full design system | only the selected template |
| [viewport-base.css](viewport-base.css) | Mandatory fixed-stage CSS | every generation |
| [html-template.md](html-template.md) | HTML structure, controller, editor, export contract | every generation |
| [animation-patterns.md](animation-patterns.md) | Animation snippets and effect-to-feeling guide | when motion matters |
| [references/pptx.md](references/pptx.md) | PPTX extraction and conversion | PPT/PPTX input |
| [references/pdf.md](references/pdf.md) | Screenshot-based PDF export | PDF requested |
| [references/deploy.md](references/deploy.md) | Public sharing checklist | user explicitly asks to publish |
| [UPSTREAM.md](UPSTREAM.md) | Pinned upstream commit, imported scope, local changes | maintenance and upgrades |
