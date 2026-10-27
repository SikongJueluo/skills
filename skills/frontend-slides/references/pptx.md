# PPT / PPTX conversion

Use this branch when the user supplies a `.pptx` file. The presentation style,
brief, generation, and verification steps still come from `SKILL.md`.

## 1. Extract

From the skill directory:

```bash
uv run --with python-pptx python scripts/extract-pptx.py <input.pptx> <deck-dir>
```

`<deck-dir>` becomes the output deck folder. The script writes:

```text
<deck-dir>/extracted-slides.json
<deck-dir>/assets/slide*-img*.*
```

If `uv` is unavailable, use a prepared Python environment with `python-pptx >= 1.0`; do not install into the system Python. The script prints a clear dependency error instead of silently installing anything.

## 2. Confirm the extraction

Before generating HTML, show the user a compact summary:

- slide count and order;
- each slide's title and text summary;
- image count and any missing/undecodable images;
- table dimensions if tables were extracted;
- speaker notes present or absent.

Ask the user to correct anything that matters. Do not silently drop content that the extractor does not understand.

## 3. Convert

- Preserve slide order, all text, relative images, and speaker notes.
- Put notes in HTML comments next to the slide they belong to, for example `<!-- notes: ... -->`.
- Render extracted tables as real HTML `<table>` elements, not screenshots.
- Keep images under `assets/` and reference them with relative paths. Never overwrite the originals.
- Apply the chosen density. If a converted slide is too dense for 1920×1080, split it into continuation slides rather than shrinking text.
- For Chinese decks, set the correct `lang`, use the CJK stack, and re-check punctuation and line breaks; PPT text often arrives with Latin punctuation and hard line breaks.

Known limits to state when relevant: SmartArt, charts, animations, embedded video, and grouped shapes may be reduced to text or lost. The extractor is not a pixel-perfect PPT renderer.

## 4. Verify

Run the normal screenshot checks from `SKILL.md`. Pay particular attention to:

- every original slide represented, in order;
- images loading from `assets/`;
- Chinese text not clipped;
- tables readable and not overflowing;
- notes present as comments.

Completion: every source slide is accounted for, and any content the extractor could not represent is listed for the user.
