# Upstream provenance

## Pinned source

- Repository: <https://github.com/zarazhangrui/frontend-slides>
- Commit: `9906a34d640d2111f724544cbc50f7f130569ae1`
- Commit date: 2026-06-23
- License: MIT, Copyright (c) 2025 Zara Zhang (see `LICENSE`)

The `bold-template-pack/` resources inside that commit are derived from
<https://github.com/zarazhangrui/beautiful-html-templates> (MIT, Copyright
(c) 2026 Zara Zhang). The pack is used as bundled by the pinned
frontend-slides commit; this repository does not check out the template
library separately and does not need the network at generation time.

## Imported

- `bold-template-pack/selection-index.json` — 34-template metadata index.
- `bold-template-pack/templates/<slug>/preview.md` — one preview card per template.
- `bold-template-pack/templates/<slug>/design.md` — one design system per template.
- `STYLE_PRESETS.md` — 12 original presets.
- `animation-patterns.md` — animation reference.
- `viewport-base.css` — fixed-stage base CSS.
- `bold-template-pack/README.md` — pack loading contract.
- `LICENSE` — upstream MIT license.

## Deliberately not imported

- `.claude-plugin/`, `plugins/` — Claude Code marketplace packaging.
- Upstream `README.md` — installation and marketing material for the plugin
  distribution, not skill instructions.
- `bold-template-pack/deck-stage.js` — an alternative `<deck-stage>` web
  component with its own navigation and print implementation. Importing it
  would give the skill two competing runtimes. The pack's `design.md` wording
  ("`deck-stage.js` or an equivalent inline stage scaler") remains accurate:
  generated decks use the inline controller documented in `html-template.md`.
- Upstream demo images, videos, and source `template.html` files.
- `scripts/deploy.sh` — deployment is opt-in and documented in
  `references/deploy.md` instead. The upstream script installs a global Vercel
  CLI, can log in interactively, and uploads a computed directory; those are the
  wrong defaults for a shared skill.

## Local adaptations

The following files are intentionally not verbatim copies. The design content
of the 34 templates is preserved; adaptations are limited to paths, runtime
contract, Chinese text handling, and execution safety.

- `SKILL.md` — rewritten routing, branch split, CJK guidance, and delivery
  contract. Upstream phases were consolidated; behavior-specific branches moved
  to `references/`.
- `html-template.md` — export/edit contract made concrete, image sizing fixed
  to the 1920×1080 stage, unsupported "fully self-contained" claims corrected.
- `viewport-base.css` — export freeze helper and printing fixes; the stage,
  slide visibility, and reduced-motion rules are unchanged.
- `bold-template-pack/README.md` — points at the single local runtime and the
  output/offline contract.
- `scripts/extract-pptx.py` — dependency error, table support, notes, and
  UTF-8 output; extraction logic preserved.
- `scripts/export-pdf.mjs` — replaces Playwright with a Chromium DevTools
  Protocol driver and screenshots the documented runtime. No package install
  or browser download at run time.
- `references/deploy.md` — replaces `scripts/deploy.sh` with an explicit-consent
  checklist and host-neutral commands.
- `LICENSE` — carries both upstream copyright notices for the imported skill and
  design systems.
- `evals/` — new for this repository.

`STYLE_PRESETS.md`, `animation-patterns.md`, `bold-template-pack/selection-index.json`,
and all 34 `preview.md` / `design.md` pairs are verbatim copies from the pinned
commit. No template content was silently rewritten.

## Upgrading

1. Pick a new upstream commit and record its SHA and date here. Do not call a
   moving `main` a fixed version.
2. Fetch the tree at that commit, then compare `bold-template-pack/` and
   `STYLE_PRESETS.md` / `animation-patterns.md` against this copy.
3. Copy design resources wholesale unless a concrete defect justifies a local
   edit. Re-check that `selection-index.json` paths still resolve and that the
   template count in the index matches the directories.
4. Re-apply the adaptations above deliberately; do not overwrite `SKILL.md`,
   `html-template.md`, or the scripts with upstream versions.
5. Run the verification in `evals/` plus one Chinese deck and one PDF export.
