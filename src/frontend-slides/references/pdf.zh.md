# PDF 导出

PDF 是一串截图，每张幻灯片一页。动画与交互不会被保留；被保留的是最终视觉状态。

## 要求

- Node.js 22 或更新版本。
- Chromium 或 Google Chrome。脚本会查找 `chromium`、`chromium-browser`、`google-chrome`、`google-chrome-stable`，以及 macOS 上常见的应用路径。用 `FRONTEND_SLIDES_CHROMIUM=/path/to/chrome` 指向具体的可执行文件。
- 不需要 Playwright，不需要 `npm install`，也不下载浏览器。驱动直接与 Chromium 的 DevTools Protocol 通信。

若缺少浏览器，报告所检查的确切命令与路径；未经用户明确同意，不要安装包或下载浏览器。

## 命令

在技能目录下：

```bash
node scripts/export-pdf.mjs <deck>/index.html [<deck>/deck.pdf]
node scripts/export-pdf.mjs <deck>/index.html --compact
node scripts/export-pdf.mjs <deck>/index.html --png-dir /tmp/deck-shots --viewport 1280x720
node scripts/export-pdf.mjs <deck>/index.html --png-dir /tmp/deck-phone --viewport 390x844
```

- 既无输出路径也无 `--png-dir` 时，PDF 写在 HTML 旁边。
- 只用 `--png-dir` 时仅截图；同时给出输出路径才会两者都产出。
- `--compact` 以 1280×720 而非 1920×1080 渲染。
- `--png-dir DIR` 还会保存 PNG 截图以供查看。这是常规验证路径；要真正查看这些图片。
- `--viewport WxH` 改变截图视口。它对 `1280x720` 与 `390x844` 检查有用；舞台留边而不重排。

## 脚本做什么

1. 在空闲端口启动绑定到 `127.0.0.1` 的本地 HTTP 服务，根目录为 deck 目录。解析到该根目录之外的请求返回 404。
2. 用临时配置启动无头 Chromium，并以 `?export=1` 打开 deck。
3. 等待 `document.fonts.ready` 与 `window.deck.ready`；对损坏的图片与超出 1920×1080 舞台的幻灯片内容给出警告。
4. 对每个 `.slide` 调用 `window.deck.goToSlide(i)`，等待布局，然后截图。若 deck 没有 `window.deck`，则回退为切换 `.slide` 元素上的 `.active` / `.visible`。
5. 把截图嵌入 PDF，并在失败时也清理服务、浏览器与临时文件。

生成的 deck 会在 `is-exporting` 下冻结入场过渡，并把计数器类 JavaScript 效果渲染为其最终值。缺少该处理的旧 deck 可能捕获到动画中间状态；检查 PNG。

## 检查

- PDF 页数等于 deck 幻灯片数。
- 没有空白页、缺失图片或豆腐块字形。
- 中文文本与标点正确。
- 相对图片路径、中文文件名与含空格路径都能工作。
- 命令在无头会话中成功退出；它不得依赖 `open`/`xdg-open` 或桌面环境。
- 动画被冻结在可读的最终状态。

成功退出不等于视觉验证。在报告成功之前，打开或查看渲染出的 PNG 以及至少一页 PDF。

## 排障

- **找不到浏览器：** 把 `FRONTEND_SLIDES_CHROMIUM` 设为可执行文件路径。
- **浏览器立即退出：** 用同样的二进制运行 `--version`，并检查其用户配置能否在临时目录中创建。
- **字体缺失：** 远程 Fontshare/Google Fonts 需要网络访问；系统 CJK 回退可能不同。webfont 加载失败时布局可能变化。
- **编辑后图片缺失：** 保存的副本在 deck 文件夹之外。把它移到 `assets/` 旁边；相对 URL 从 HTML 文件位置解析。
- **0 张幻灯片：** deck 未使用 `class="slide"`；本导出器要求该契约。
- **捕获到错误的幻灯片：** deck 的自定义导航可能未实现 `window.deck.goToSlide`；补上该契约或测试回退路径。
