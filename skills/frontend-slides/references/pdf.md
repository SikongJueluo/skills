# PDF export

The PDF is a sequence of screenshots, one per slide. Animations and
interactivity are not preserved; the final visual state is.

## Requirements

- Node.js 22 or newer.
- Chromium or Google Chrome. The script looks for `chromium`,
  `chromium-browser`, `google-chrome`, `google-chrome-stable`, and the usual
  macOS application paths. Point it at a specific binary with
  `FRONTEND_SLIDES_CHROMIUM=/path/to/chrome`.
- No Playwright, no `npm install`, and no browser download. The driver talks to
  Chromium's DevTools Protocol directly.

If the browser is missing, report the exact command and path checked; do not
install packages or download a browser without the user's explicit agreement.

## Command

From the skill directory:

```bash
node scripts/export-pdf.mjs <deck>/index.html [<deck>/deck.pdf]
node scripts/export-pdf.mjs <deck>/index.html --compact
node scripts/export-pdf.mjs <deck>/index.html --png-dir /tmp/deck-shots --viewport 1280x720
node scripts/export-pdf.mjs <deck>/index.html --png-dir /tmp/deck-phone --viewport 390x844
```

- With no output path and no `--png-dir`, the PDF is written next to the HTML.
- `--png-dir` alone is screenshot-only; pass an output path to produce both.
- `--compact` renders at 1280×720 instead of 1920×1080.
- `--png-dir DIR` also saves PNG screenshots for inspection. It is the normal
  verification path; actually view the images.
- `--viewport WxH` changes the screenshot viewport. It is useful for
  `1280x720` and `390x844` checks; the stage letterboxes rather than reflowing.

## What the script does

1. Starts a local HTTP server bound to `127.0.0.1` on a free port, rooted at the
   deck directory. Requests that resolve outside that root return 404.
2. Launches headless Chromium with a temporary profile and opens the deck with
   `?export=1`.
3. Waits for `document.fonts.ready` and `window.deck.ready`; warns about
   broken images and slide content that exceeds the 1920×1080 stage.
4. Calls `window.deck.goToSlide(i)` for each `.slide`, waits for layout, and
   captures a screenshot. If the deck has no `window.deck`, it falls back to
   toggling `.active` / `.visible` on `.slide` elements.
5. Embeds the screenshots into a PDF and cleans up the server, browser, and
   temporary files even on failure.

Generated decks freeze entrance transitions under `is-exporting` and render
counter-like JavaScript effects at their final values. A legacy deck that lacks
that handling may capture an in-between animation state; inspect the PNGs.

## Checks

- The PDF page count equals the deck slide count.
- No blank pages, missing images, or tofu glyphs.
- Chinese text and punctuation are correct.
- Relative image paths, Chinese filenames, and paths with spaces work.
- The command exits successfully in a headless session; it must not depend on
  `open`/`xdg-open` or a desktop.
- Animations are frozen at a readable final state.

A successful exit is not visual verification. Open or inspect the rendered PNGs
and at least one PDF page before reporting success.

## Troubleshooting

- **No browser found:** set `FRONTEND_SLIDES_CHROMIUM` to the executable.
- **Browser exits immediately:** run the same binary with `--version`, and
  check that its user profile can be created in a temp directory.
- **Fonts missing:** remote Fontshare/Google Fonts need network access; system
  CJK fallbacks may differ. The layout may change when a webfont fails.
- **0 slides:** the deck does not use `class="slide"`; this exporter requires
  that contract.
- **Wrong slide captured:** the deck's custom navigation may not implement
  `window.deck.goToSlide`; add the contract or test the fallback.
