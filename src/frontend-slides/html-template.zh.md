# HTML 演示模板

这是每个生成 deck 的参考架构。幻灯片在 1920×1080 下创作，整块舞台缩放到视口。

## 文件布局

```text
my-deck/
  index.html          # CSS and JS inline
  assets/             # images referenced by relative path
```

可移植单文件是变体，不是默认：仅当用户要求时才内联图片并移除所有外部字体/资源引用，然后核实不再残留 `http(s)://` 或 `assets/` 依赖。

## 基础 HTML

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

示例在 `body` 上设置 `color: var(--text-primary)`，标题继承它。对浅色 deck，一起覆盖 `--stage-bg`、`--slide-bg` 与 `--text-primary`；不要在浅色背景上留下白色标题。

## 舞台缩放

`scaleStage()` 为整块 1920×1080 画布计算一个等比因子并居中结果。舞台内没有响应式断点，也没有按设备重排。视口 CSS 裁切溢出，舞台保持其创作尺寸。

<!-- 稳定锚点：中文标题的 slug 不是 export-contract，故显式声明；仅中文源需要，英文输出由 ## Export contract 提供同名 slug。 -->
<a id="export-contract"></a>
## 导出契约

PDF 导出器与任何浏览器自动化都使用此契约，而不是猜测布局。对可编辑 PPTX，使用[转换参考](references/editable-pptx.md)；外部转换器必须经过检查或改造以消费该状态，而不能假定它会遵守：

- 以 `?export=1` 加载会在首帧绘制前加入 `is-exporting`。CSS 冻结入场过渡；deck 从第 1 页开始，与 hash 无关。
- `window.deck.ready` 在字体与初始布局之后 resolve。
- `window.deck.count` 返回幻灯片数量。
- `window.deck.goToSlide(index)` 激活一张幻灯片，并在两个动画帧后 resolve（布局完成，但不一定每个自定义动画都完成）。
- 每张幻灯片都是带 `class="slide"` 的元素。活动页：`.active` 与 `.visible`；非活动页：两者都没有。
- JavaScript 驱动的效果（计数器、打字机、canvas 循环）必须在存在 `is-exporting` 时立即渲染其**最终**值，或暴露一个 `window.deck.ready` / `goToSlide` 可以等待的 promise。不要因为动画从未运行就把计数器留在零。

示例最终状态处理：

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

不暴露 `window.deck` 的 deck 仍有回退：导出器切换 `.slide` 元素上的 `.active` / `.visible` 并短暂等待。该回退无法强制未知的 JavaScript 动画进入最终状态，因此生成的 deck 应始终实现上述契约。

## 内联编辑

编辑是草稿之后的便利能力，默认包含，除非用户要求锁定文件或仅用于导出的文件。

- `E` 进入编辑模式；左上角按钮切换它；`Esc` 退出。编辑时导航键被禁用，因此它们移动光标而不是切换 deck。
- 可编辑文本：标题、段落、列表项、引语、图注与表格单元格。`pre`、`code`、`.no-edit` 与 `[data-no-edit]` 保持锁定。
- `Esc` 退出编辑模式。
- `Ctrl/Cmd+S` 下载一个**新的** HTML 文件。它绝不回写源文件，且有意不做 localStorage 自动保存：浏览器里过期的草稿静默覆盖源文件，比一次显式下载更糟。
- 浏览器无法替你写入 deck 文件夹。在打开下载的文件之前，把它移到 deck 文件夹内 `assets/` 旁边。编辑器中的一条简短提示会在下载后重复该说明。对位于 `my-deck/index.html` 的 deck，要么用下载文件替换 `my-deck/index.html`，要么保留为 `my-deck/index-edited.html`；两条路径都能解析 `assets/`。留在下载文件夹的副本无法加载 deck 的图片。
- `serialize()` 移除编辑器状态，把 deck 重置到第 1 页，并从下载副本中剥离 `contenteditable`。从 deck 文件夹重新打开该副本，确认图片能加载，并导出一次 PDF 检查图片页，然后才把这次编辑视为已交付。

按钮悬停行为使用带宽限期的 JS class。不要用 CSS `~` 兄弟选择器替代它：`pointer-events: none` 会打断悬停链，按钮会在可点击之前消失。

## 图片

把处理过的图片保存在 `assets/` 下并用相对路径引用：

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

依赖：Pillow（`uv run --with pillow python ...` 或准备好的 venv）。把大于约 1 MB 的图片缩放到最大边长 1200 px，且绝不覆盖原文件。仅在要求可移植单文件时使用 base64。

不要在多个幻灯片上重复同一张截图；logo 可以出现在标题页与结尾页。

### 可移植单文件

仅在用户明确要求一个可邮件发送/离线的文件时：

1. 把每个图片引用转换为 `data:image/...;base64,...` URI。
2. 把实际使用的确切字重作为 `@font-face` 规则嵌入，使用 base64 `woff2` 源，然后移除 Fontshare/Google 的 `<link>` 标签。使用许可允许再分发的字体。
3. 移除 `assets/` 引用以及任何残留的 `http://` 或 `https://` 资源 URL。CSS 与 JS 已经是内联的。
4. 在文件中搜索 `http://`、`https://` 与 `assets/`；deck 资源应只剩 `data:` URI。
5. 在禁用网络访问的情况下打开文件验证，并报告任何无法嵌入的回退或资源。

## 质量

- 用 `/* === SECTION NAME === */` 块为每个区块加注释。
- 语义化 HTML（`<main>`、`<section>`、按序的标题）。
- 键盘导航、`prefers-reduced-motion`（来自基础 CSS），以及交互控件可见的焦点状态。
- 没有占位文本、没有死链、没有不存在的图片路径。
- 在 1280×720 与 390×844 下检查渲染截图；仅靠 `scrollHeight` 无法发现一个面板遮住另一个面板。
