# HTML presentation template

Reference architecture for every generated deck. Slides are authored at
1920×1080 and the whole stage scales to the viewport.

## File layout

```text
my-deck/
  index.html          # CSS and JS inline
  assets/             # images referenced by relative path
```

A portable single file is a variant, not the default: inline the images and
remove every external font/resource reference only when the user asks for one,
then verify that no `http(s)://` or `assets/` dependency remains.

## Base HTML

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Presentation Title</title>

    <!-- A distinctive Latin display face is optional; CJK always needs a stack. -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&family=Noto+Serif+SC:wght@600;700&display=swap" rel="stylesheet">

    <script>
        /* Set this before first paint so export screenshots never catch an entrance animation. */
        document.documentElement.classList.toggle(
            'is-exporting',
            new URLSearchParams(location.search).has('export')
        );
    </script>

    <style>
        /* ===========================================
           THEME — change these to change the deck
           =========================================== */
        :root {
            /* Light theme: change stage-bg, slide-bg, and text-primary together. */
            --stage-bg: #0a0f1c;
            --slide-bg: #0a0f1c;
            --text-primary: #ffffff;
            --text-secondary: #9ca3af;
            --accent: #00ffcc;
            --deck-chrome: rgba(255, 255, 255, 0.55);

            --font-display: 'Noto Sans SC', 'Source Han Sans SC', 'LXGW WenKai', sans-serif;
            --font-body: 'Noto Sans SC', 'Source Han Sans SC', 'LXGW WenKai', sans-serif;
            --title-size: 112px;
            --subtitle-size: 34px;
            --body-size: 28px;

            --slide-padding: 72px;
            --content-gap: 32px;

            --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
            --duration-normal: 0.6s;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        /* The theme's primary text color must reach the slides. Headings inherit
           from body; p/li opt into --text-secondary below. */
        body {
            color: var(--text-primary);
        }

        h1, h2, h3, h4, h5, h6 {
            color: inherit;
        }

        /* --- PASTE THE FULL viewport-base.css CONTENTS HERE --- */

        /* ===========================================
           DECK LAYOUT
           =========================================== */
        .slide {
            padding: var(--slide-padding);
        }

        .slide-content {
            display: flex;
            flex-direction: column;
            gap: var(--content-gap);
            height: 100%;
            overflow: hidden;
        }

        .title-slide {
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 28px;
            padding: 0 140px;
        }

        h1 {
            font-family: var(--font-display);
            font-size: var(--title-size);
            line-height: 1.15;
            letter-spacing: 0;
            font-weight: 700;
        }

        h2 {
            font-family: var(--font-display);
            font-size: 64px;
            line-height: 1.25;
            letter-spacing: 0;
            font-weight: 700;
        }

        p, li {
            font-family: var(--font-body);
            font-size: var(--body-size);
            line-height: 1.8;
            color: var(--text-secondary);
        }

        .slide-image {
            max-width: 100%;
            max-height: 400px;
            object-fit: contain;
            border-radius: 12px;
        }

        /* ===========================================
           ENTRANCE ANIMATION
           =========================================== */
        .reveal {
            opacity: 0;
            transform: translateY(30px);
            transition: opacity var(--duration-normal) var(--ease-out-expo),
                        transform var(--duration-normal) var(--ease-out-expo);
        }

        .slide.visible .reveal {
            opacity: 1;
            transform: translateY(0);
        }

        .reveal:nth-child(1) { transition-delay: 0.05s; }
        .reveal:nth-child(2) { transition-delay: 0.12s; }
        .reveal:nth-child(3) { transition-delay: 0.19s; }
        .reveal:nth-child(4) { transition-delay: 0.26s; }

        /* ===========================================
           CHROME AND EDITING
           =========================================== */
        .deck-controls {
            position: fixed;
            left: auto;
            right: 24px;
            bottom: 18px;
            transform: none;
            z-index: 1000;
            font: 14px/1.4 ui-monospace, monospace;
            color: var(--deck-chrome);
            pointer-events: none;
        }

        .edit-hotzone {
            position: fixed;
            top: 0;
            left: 0;
            width: 80px;
            height: 80px;
            z-index: 10000;
        }

        .edit-toggle {
            position: fixed;
            top: 18px;
            left: 18px;
            width: 40px;
            height: 40px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 999px;
            background: rgba(0, 0, 0, 0.55);
            color: #fff;
            font-size: 18px;
            cursor: pointer;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            z-index: 10001;
        }

        .edit-toggle.show,
        .edit-toggle.active {
            opacity: 1;
            pointer-events: auto;
        }

        .editable {
            outline: 2px dashed rgba(0, 255, 204, 0.7);
            outline-offset: 4px;
            cursor: text;
        }

        html.is-editing .slide {
            cursor: text;
        }

        .save-notice {
            position: fixed;
            left: 50%;
            bottom: 64px;
            transform: translateX(-50%);
            z-index: 10002;
            max-width: 780px;
            padding: 14px 20px;
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.86);
            color: #fff;
            font: 14px/1.5 ui-monospace, monospace;
            pointer-events: none;
        }

        html.is-exporting .deck-controls,
        html.is-exporting .edit-hotzone,
        html.is-exporting .edit-toggle {
            display: none !important;
        }
    </style>
</head>
<body>
    <div class="deck-viewport">
        <main class="deck-stage" id="deckStage">
            <section class="slide title-slide active visible" aria-hidden="false">
                <h1 class="reveal">Presentation Title</h1>
                <p class="reveal">Subtitle or author</p>
            </section>

            <section class="slide" aria-hidden="true">
                <div class="slide-content">
                    <h2 class="reveal">Slide Title</h2>
                    <p class="reveal">Content...</p>
                </div>
            </section>

            <!-- More slides... -->
        </main>
    </div>

    <!-- Optional: remove if the deck design already has its own page chrome. -->
    <div class="deck-controls" aria-hidden="true">
        <span data-deck-current>1</span> / <span data-deck-total>1</span>
    </div>

    <div class="edit-hotzone" aria-hidden="true"></div>
    <button class="edit-toggle" id="editToggle" type="button" title="编辑文字 (E)" aria-label="编辑文字">✏️</button>

    <script>
        (() => {
            'use strict';

            const STAGE_W = 1920;
            const STAGE_H = 1080;
            const isExporting = new URLSearchParams(location.search).has('export');

            let editor;

            class SlidePresentation {
                constructor() {
                    this.stage = document.getElementById('deckStage');
                    this.slides = Array.from(document.querySelectorAll('.slide'));
                    this.index = 0;
                    this.wheelLock = false;
                    this.touchStart = null;

                    this.scaleStage();
                    window.addEventListener('resize', () => this.scaleStage());
                    this.bindKeyboard();
                    this.bindWheel();
                    this.bindTouch();
                    this.updateChrome();

                    this.ready = this.boot();
                    const controller = this;
                    window.deck = {
                        get count() { return controller.slides.length; },
                        get index() { return controller.index; },
                        goToSlide: (i) => controller.goToSlide(i),
                        ready: this.ready,
                    };
                }

                async boot() {
                    // Fonts can fail (offline); fonts.ready still resolves.
                    await document.fonts.ready;
                    const hash = location.hash.match(/^#(\d+)$/);
                    const initial = isExporting ? 0 : (hash ? Number(hash[1]) - 1 : 0);
                    await this.goToSlide(initial, { updateHash: false });
                }

                scaleStage() {
                    const factor = Math.min(window.innerWidth / STAGE_W, window.innerHeight / STAGE_H);
                    const x = (window.innerWidth - STAGE_W * factor) / 2;
                    const y = (window.innerHeight - STAGE_H * factor) / 2;
                    this.stage.style.transform = `translate(${x}px, ${y}px) scale(${factor})`;
                }

                goToSlide(i, { updateHash = true } = {}) {
                    if (!this.slides.length) return Promise.resolve();
                    const next = Math.max(0, Math.min(i, this.slides.length - 1));
                    this.index = next;

                    this.slides.forEach((slide, n) => {
                        const active = n === next;
                        slide.classList.toggle('active', active);
                        slide.classList.toggle('visible', active);
                        slide.setAttribute('aria-hidden', active ? 'false' : 'true');
                    });

                    if (updateHash) {
                        try { history.replaceState(null, '', `#${next + 1}`); } catch (e) { /* file:// */ }
                    }
                    this.updateChrome();

                    // Resolve after the new slide has been laid out.
                    return new Promise((resolve) => {
                        requestAnimationFrame(() => requestAnimationFrame(resolve));
                    });
                }

                updateChrome() {
                    document.querySelectorAll('[data-deck-current]').forEach((el) => {
                        el.textContent = String(this.index + 1);
                    });
                    document.querySelectorAll('[data-deck-total]').forEach((el) => {
                        el.textContent = String(this.slides.length);
                    });
                }

                bindKeyboard() {
                    document.addEventListener('keydown', (event) => {
                        if (document.documentElement.classList.contains('is-editing')) return;
                        if (event.metaKey || event.ctrlKey || event.altKey) return;
                        const target = event.target;
                        if (target && (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName))) return;

                        let handled = true;
                        switch (event.key) {
                            case 'ArrowRight':
                            case 'PageDown':
                            case ' ':
                            case 'Spacebar':
                                this.goToSlide(this.index + 1);
                                break;
                            case 'ArrowLeft':
                            case 'PageUp':
                                this.goToSlide(this.index - 1);
                                break;
                            case 'Home':
                                this.goToSlide(0);
                                break;
                            case 'End':
                                this.goToSlide(this.slides.length - 1);
                                break;
                            case 'e':
                            case 'E':
                                if (editor) editor.toggle();
                                break;
                            default:
                                handled = false;
                        }
                        if (handled) event.preventDefault();
                    });
                }

                bindWheel() {
                    window.addEventListener('wheel', (event) => {
                        if (document.documentElement.classList.contains('is-editing')) return;
                        if (this.wheelLock || Math.abs(event.deltaY) < 20) return;
                        this.wheelLock = true;
                        setTimeout(() => { this.wheelLock = false; }, 650);
                        this.goToSlide(this.index + (event.deltaY > 0 ? 1 : -1));
                    }, { passive: true });
                }

                bindTouch() {
                    window.addEventListener('touchstart', (event) => {
                        if (document.documentElement.classList.contains('is-editing')) return;
                        const touch = event.touches[0];
                        this.touchStart = touch ? { x: touch.clientX, y: touch.clientY } : null;
                    }, { passive: true });

                    window.addEventListener('touchend', (event) => {
                        if (!this.touchStart || document.documentElement.classList.contains('is-editing')) return;
                        const touch = event.changedTouches[0];
                        if (!touch) return;
                        const dx = touch.clientX - this.touchStart.x;
                        const dy = touch.clientY - this.touchStart.y;
                        this.touchStart = null;
                        if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy)) return;
                        this.goToSlide(this.index + (dx < 0 ? 1 : -1));
                    }, { passive: true });
                }
            }

            class DeckEditor {
                constructor(deck) {
                    this.deck = deck;
                    this.active = false;
                    this.toggleButton = document.getElementById('editToggle');
                    this.hotzone = document.querySelector('.edit-hotzone');
                    this.editableSelector = 'h1,h2,h3,h4,h5,p,li,blockquote,figcaption,td,th,dt,dd';
                    this.bind();
                }

                bind() {
                    let hideTimer = null;
                    const show = () => {
                        clearTimeout(hideTimer);
                        this.toggleButton.classList.add('show');
                    };
                    const scheduleHide = () => {
                        hideTimer = setTimeout(() => {
                            if (!this.active) this.toggleButton.classList.remove('show');
                        }, 400);
                    };

                    [this.hotzone, this.toggleButton].forEach((el) => {
                        el.addEventListener('mouseenter', show);
                        el.addEventListener('mouseleave', scheduleHide);
                    });
                    this.hotzone.addEventListener('click', () => this.toggle());
                    this.toggleButton.addEventListener('click', () => this.toggle());

                    document.addEventListener('keydown', (event) => {
                        if (!this.active) return;
                        if (event.key === 'Escape') {
                            event.preventDefault();
                            this.exit();
                        }
                        if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 's') {
                            event.preventDefault();
                            this.save();
                        }
                    });
                }

                enter() {
                    this.active = true;
                    document.documentElement.classList.add('is-editing');
                    this.toggleButton.classList.add('active', 'show');
                    this.toggleButton.textContent = '✓';
                    this.toggleButton.title = '完成编辑 (Esc)';

                    this.deck.slides.forEach((slide) => {
                        slide.querySelectorAll(this.editableSelector).forEach((el) => {
                            if (el.closest('pre, code, .no-edit, [data-no-edit]')) return;
                            el.setAttribute('contenteditable', 'true');
                            el.setAttribute('spellcheck', 'false');
                            el.classList.add('editable');
                        });
                    });
                }

                exit() {
                    this.active = false;
                    document.documentElement.classList.remove('is-editing');
                    this.toggleButton.classList.remove('active', 'show');
                    this.toggleButton.textContent = '✏️';
                    this.toggleButton.title = '编辑文字 (E)';

                    document.querySelectorAll('[contenteditable="true"]').forEach((el) => {
                        el.removeAttribute('contenteditable');
                        el.removeAttribute('spellcheck');
                        el.classList.remove('editable');
                    });
                }

                toggle() {
                    this.active ? this.exit() : this.enter();
                }

                serialize() {
                    const clone = document.documentElement.cloneNode(true);
                    clone.classList.remove('is-editing', 'is-exporting');

                    clone.querySelectorAll('[contenteditable]').forEach((el) => {
                        el.removeAttribute('contenteditable');
                        el.removeAttribute('spellcheck');
                        el.classList.remove('editable');
                    });

                    // Save a clean deck that opens on slide 1, not on whatever slide was active.
                    clone.querySelectorAll('.slide').forEach((slide, index) => {
                        slide.classList.toggle('active', index === 0);
                        slide.classList.toggle('visible', index === 0);
                        slide.setAttribute('aria-hidden', index === 0 ? 'false' : 'true');
                    });

                    const button = clone.querySelector('#editToggle');
                    if (button) {
                        button.classList.remove('show', 'active');
                        button.textContent = '✏️';
                        button.title = '编辑文字 (E)';
                    }

                    return '<!DOCTYPE html>\n' + clone.outerHTML;
                }

                save() {
                    const html = this.serialize();
                    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
                    const link = document.createElement('a');
                    let name = 'slides.html';
                    try {
                        name = decodeURIComponent(location.pathname.split('/').pop() || 'slides.html');
                    } catch (e) { /* keep the fallback */ }
                    link.href = URL.createObjectURL(blob);
                    link.download = `${name.replace(/\.html?$/i, '')}-edited.html`;
                    document.body.appendChild(link);
                    link.click();
                    link.remove();
                    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
                    this.showSaveNotice();
                }

                showSaveNotice() {
                    document.querySelectorAll('.save-notice').forEach((el) => el.remove());
                    const notice = document.createElement('div');
                    notice.className = 'save-notice';
                    notice.textContent =
                        'Downloaded. Put this file next to assets/ in the deck folder before opening.';
                    document.body.appendChild(notice);
                    setTimeout(() => notice.remove(), 7000);
                }
            }

            const presentation = new SlidePresentation();
            editor = new DeckEditor(presentation);
        })();
    </script>
</body>
</html>
```

The example sets `color: var(--text-primary)` on `body`, and headings inherit it.
For a light deck, override `--stage-bg`, `--slide-bg`, and `--text-primary`
together; do not leave a white title color on a light background.

## Stage scaling

`scaleStage()` computes one uniform factor for the full 1920×1080 canvas and
centers the result. There are no responsive breakpoints inside the stage and no
per-device reflow. The viewport CSS clips overflow and the stage keeps its
authored size.

## Export contract

The PDF exporter and any browser automation use this contract instead of
guessing at layout:

- Loading with `?export=1` adds `is-exporting` before first paint. CSS freezes
  entrance transitions; the deck starts on slide 1 regardless of the hash.
- `window.deck.ready` resolves after fonts and the initial layout.
- `window.deck.count` returns the slide count.
- `window.deck.goToSlide(index)` activates a slide and resolves after two
  animation frames (layout done, not necessarily every custom animation done).
- Every slide is an element with `class="slide"`. Active slide: `.active` and
  `.visible`; inactive: neither.
- JavaScript-driven effects (counters, typewriters, canvas loops) must render
  their **final** value immediately when `is-exporting` is present, or expose a
  promise that `window.deck.ready` / `goToSlide` can await. Do not leave a
  counter at zero because the animation never ran.

Example final-state handling:

```javascript
const isExporting = document.documentElement.classList.contains('is-exporting');

function renderCounter(el, target) {
    if (isExporting) {
        el.textContent = String(target);
        return;
    }
    // ... otherwise animate from 0 to target
}
```

Decks that do not expose `window.deck` still get a fallback: the exporter toggles
`.active` / `.visible` on `.slide` elements and waits briefly. That fallback
cannot force unknown JavaScript animations to their final state, so generated
decks should always implement the contract above.

## Inline editing

Editing is a post-draft affordance, included unless the user asks for a locked
or export-only file.

- `E` enters edit mode; the top-left button toggles it; `Esc` exits. While
  editing, navigation keys are disabled so they move the caret instead of the
  deck.
- Editable text: headings, paragraphs, list items, quotes, captions, and table
  cells. `pre`, `code`, `.no-edit`, and `[data-no-edit]` stay locked.
- `Esc` exits edit mode.
- `Ctrl/Cmd+S` downloads a **new** HTML file. It never writes back to the source
  file, and there is intentionally no localStorage autosave: a stale browser
  draft silently overriding the source is worse than an explicit download.
- The browser cannot write into the deck folder for you. Before opening the
  downloaded file, move it into the deck folder next to `assets/`. A short
  notice in the editor repeats this instruction after the download. For a deck at
  `my-deck/index.html`, either replace `my-deck/index.html` with the download or
  keep it as `my-deck/index-edited.html`; both paths resolve `assets/`. A copy
  left in the Downloads folder cannot load the deck's images.
- `serialize()` removes editor state, resets the deck to slide 1, and strips
  `contenteditable` from the downloaded copy. Reopen the copy from the deck
  folder, confirm its images load, and export the PDF once to check the image
  slides before treating the edit as delivered.

The button hover behavior uses JS classes with a grace period. Do not replace it
with a CSS `~` sibling selector: `pointer-events: none` breaks the hover chain,
so the button disappears before it can be clicked.

## Images

Save processed images under `assets/` and reference them relatively:

```html
<img src="assets/logo_round.png" alt="Logo" class="slide-image logo">
```

```css
.slide-image {
    max-width: 100%;
    max-height: 400px;   /* 1920×1080 stage px, never vh */
    object-fit: contain;
}
```

Dependency: Pillow (`uv run --with pillow python ...` or a prepared venv).
Resize images larger than about 1 MB to a maximum dimension of 1200 px and never
overwrite the original. Use base64 only for a requested portable single file.

Do not repeat the same screenshot on multiple slides; a logo may appear on the
title and closing slide.

### Portable single file

Only when the user explicitly asks for one emailed/offline file:

1. Convert every image reference to a `data:image/...;base64,...` URI.
2. Embed the exact font weights used as `@font-face` rules with base64 `woff2`
   sources, then remove the Fontshare/Google `<link>` tags. Use fonts whose
   license permits redistribution.
3. Remove `assets/` references and any remaining `http://` or `https://`
   resource URLs. CSS and JS are already inline.
4. Search the file for `http://`, `https://`, and `assets/`; only `data:` URIs
   should remain for deck resources.
5. Verify by opening the file with network access disabled, and report any
   fallback or resource that could not be embedded.

## Quality

- Comment each section with a `/* === SECTION NAME === */` block.
- Semantic HTML (`<main>`, `<section>`, headings in order).
- Keyboard navigation, `prefers-reduced-motion` (from the base CSS), and visible
  focus states for interactive controls.
- No placeholder text, no dead links, no image paths that do not exist.
- Check rendered screenshots at 1280×720 and 390×844; `scrollHeight` alone
  cannot detect a panel covering another panel.
