---
name: frontend-slides
description: 创建或修改浏览器中的 16:9 幻灯片，把 PPT/PPTX 转为 HTML，或把 HTML 幻灯片导出为 PDF 或可编辑 PPTX。用于演示文稿的创建、修改与转换，包括中文/CJK 幻灯片。不用于普通网站、落地页、书面文档，或对已有演示的概括。
argument-hint: "[deck request, .pptx input, or HTML deck + target format]"
---

# /frontend-slides

制作一个在浏览器中运行的演示文稿：一块固定的 1920×1080 舞台，整体等比缩放，无构建步骤。一个 deck 就是一个文件夹：

```text
<deck>/index.html
<deck>/assets/...
```

本技能中的所有路径都相对于**本技能目录**。在读取支持文件或运行脚本之前先解析该目录；不要假定当前工作目录就是技能根目录。

## 不可让步项

- **固定舞台。** 每张幻灯片都在 1920×1080 下创作，位于一块整体等比缩放的舞台内。其他宽高比下留黑边或留竖边；绝不为手机重排幻灯片内容。
- **可见性契约。** 用 `.slide` 上的 `.active` / `.visible` 切换幻灯片；绝不用 `display: none` 切换幻灯片。每个生成的 deck 都必须包含 [viewport-base.css](viewport-base.css) 的全部内容。
- **单一运行时。** 生成的 deck 使用 [html-template.md](html-template.md) 中的内联控制器。不要混入第二套导航组件或第二套舞台缩放器。
- **无构建步骤。** CSS 与 JS 保持内联在 HTML 中。图片通常放在 `assets/`；仅在用户要求可移植的单文件时才内联。
- **渐进披露。** 先读 `selection-index.json`，再读模板元数据；先读 `preview.md`，再读完整的 `design.md`；生成时只读一个已选中的 `design.md`。
- **诚实交付。** 若未实际验证浏览器、截图、PDF 或部署，就不得声称已验证。

## 1. 归类请求

- **新建 deck** —— 按步骤 2–4 依据简报创建。若同时要求可编辑 PPTX，则在创作前读 [references/editable-pptx.md](references/editable-pptx.md)。
- **PPT/PPTX → HTML** —— 先抽取；使用 [references/pptx.md](references/pptx.md)，然后继续步骤 2–4。
- **修改已有 HTML deck** —— 编辑前先读该 deck 及其资源；遵循下文“修改已有 deck”。
- **HTML → 可编辑 PPTX** —— 直接使用 [references/editable-pptx.md](references/editable-pptx.md)；保留现有设计。这是外部工具工作流，不是内置导出器。分别验证视觉保真度与原生对象可编辑性，并披露任何回退图片。
- **HTML → PDF** —— 直接转到 [references/pdf.md](references/pdf.md)。
- **分享或发布** —— 仅当用户明确要求时；使用 [references/deploy.md](references/deploy.md)。

复用用户已提供的每一项事实：主题、受众、长度、内容、语言、视觉方向与文件路径。不要重复询问。只为阻碍工作的事实提一批紧凑的问题。

## 2. 简报

用一条消息提问，在没有结构化提问 UI 时给出编号选项：

1. **目的与受众** —— 路演、教学、会议、内部评审等。
2. **长度** —— 短 5–10 页，中 10–20 页，长 20+ 页。
3. **内容** —— 已就绪、粗略笔记，或仅有主题。请用户提供材料。
4. **密度** —— 低密度/演讲引导型，或高密度/阅读优先型。
5. **语言** —— 仅当 deck 语言无法从请求中判断时。
6. **图片** —— 仅当请求提及或提供了图片时。

在草稿存在之前，绝不要询问内联编辑。默认包含它；仅当用户要求锁定文件或仅用于导出的文件时省略。

除非用户指定路径，输出默认写到 `./<deck-slug>/index.html` 加 `assets/`。完成条件：模式、输出路径、内容、密度与语言均已确定。

## 3. 选择方向

约束不是选择。“浅色背景、深色文字、大号字体”可以塑造推荐，但并不表示已选中某个预设。

仅在用户满足以下条件时才跳过预览轮次直接生成：

- 点名某个预设、模板、参考 deck 或视觉方向，并要求使用它 —— 就使用它，并说明用的是哪个；
- 已在本次对话或提供的材料中选择过方向；
- 委托选择（“你来定”“不必问”）。

如果记录含糊 —— 一处顺带提及、一个约束，或先前 agent 的建议 —— 在生成前确认方向。若上述路径都不适用，则进行视觉探索。推荐一个方向，但让用户选择；人们是通过看到设计来选择，而不是通过命名模板。

探索时：

1. 读 [STYLE_PRESETS.md](STYLE_PRESETS.md) 与 [bold-template-pack/selection-index.json](bold-template-pack/selection-index.json) 中的元数据。
2. 按场合、受众、内容、密度以及任何已述约束，初筛 2–4 个候选。只读这些候选的 `preview.md`。把用户主动表达的品味（一个参考、某种不喜欢的观感、一条品牌规则）用于塑造初筛，而不是作为选择的替代。
3. 用 deck 的真实标题和副标题制作三张确实不同的标题页：一个稳妥预设、一个 bold 模板、一个 wildcard（另一个 bold 模板或自定义设计）。当材料只支持两个不同方向时，就做两张。它们必须是不同的设计构想，而不是同一构想配三种颜色。
4. 将它们保存到 `<deck>/.previews/` 下，命名为 `style-a.html`、`style-b.html`、`style-c.html`。用 agent 的浏览器/图像/文件呈现能力展示；若无此能力，则给出路径并请用户自行打开。
5. 询问使用哪个方向。若回答“混合”，询问要混合什么。

预览规则：

- 每个预览是一张标题页，不是迷你 deck：只搭建共享舞台与那一张幻灯片。
- 每个预览必须看起来像本 deck 真实的第一页，而不是诊断卡片。
- 绝不在幻灯片上渲染模板名称、slug、`preview`、`Option A/B/C`、文件名、路径或需求备注。名称只属于聊天消息。
- 不要强迫每个有表现力的选项都来自模板包。
- 若预览使用了图片或 logo，先检查实际文件；见 [references/design-review.md](references/design-review.md)。
- 用户选定后删除 `.previews/`。

选定之后，在制作其余幻灯片之前，先在所选方向下制作最难的代表性正文页（内容最多、带图片、带表格或带对比的那一页）。当 deck 含有用户提供的图片、表格、图表或密集对比，或用户要求评审设计时，把它展示给用户 —— 除非用户已委托方向并要求不要打扰。否则把它作为你自己的检查。

完成条件：用户已选定一个方向，或明确点名/委托了选择；任何 bold 模板的单个 `design.md` 路径已知；代表性正文页已在所选方向下制作完成且内容适配。

## 4. 生成 deck

在编写 HTML 之前读这些：

- [viewport-base.css](viewport-base.css) —— 全文粘贴进 `<style>`。
- [html-template.md](html-template.md) —— 结构、控制器、编辑、导出契约。
- [animation-patterns.md](animation-patterns.md) —— 只读适配所选方向的模式。
- 所选 bold 模板的 `design.md` —— 恰好一个，且仅在选定之后。
- [references/design-review.md](references/design-review.md) —— 图片真实性、页面构图与整 deck 评审。在放置资源前读图片与构图部分，在交付前读完整文件。

对于 `design.md`，把 `vw`、`vh` 与 `clamp()` 视为设计比例，换算到 1920×1080 坐标。保留它的字体、调色板、装饰语汇、间距节奏与组件语法；不要复制演示内容。为 deck 所需的每种幻灯片类型生成同一视觉系统。

同样的保真度也适用于点名的预设或自定义方向：跨幻灯片类型保持其调色板、字体角色与布局语法。至少做出一个源自本 deck 主题的决定 —— 一种字体处理、一种图片处理、一个布局动作 —— 而不是模板的演示默认值。独特意味着贴合材料本身，而不是更多装饰。

全程应用密度选择：

- **低密度 / 演讲引导型：** 一页一个观点，大号字体，短句，更多页数。
- **高密度 / 阅读优先型：** 结构化栅格、表格、注解，可读前提下 4–8 条要点或 4–6 张卡片。

拆分到另一张幻灯片，而不是缩小文字或让面板重叠。

### 内容是主张

- 只使用所提供材料或已引用来源中的事实、数字、引语与示例。不要用看似合理的细节填补空缺；把推断标注为推断，或删掉。
- 示例必须证明其旁边的主张。若图片或示例展示的是别的东西，就改示例或改主张。
- 打开你放置的每张图片，描述它实际展示了什么。让图注与 alt 文本匹配该描述。文件名、搜索结果或你自己写的 alt 文本都不是检查。
- 若无法查看图片，把检查委托给能查看的 agent，或询问用户。若两者都不可用，把图片检查报告为未验证。不得依据元数据声称图片已验证。

### 为受众构图

- 每张幻灯片只承担一个任务、一个焦点。当标题、主张、解释、图片、演讲提示与结论全部相互竞争时，拆分或删减该页。
- 装饰必须承担内容或结构职责。反复出现的边框、标签、数字、浮签与分隔线若放在任何 deck 中都成立，那就是模板习惯，而不是设计。
- 幻灯片表面属于受众。把讲稿、计时、主持提示与提醒放入 HTML 注释或单独的笔记文件，而不是可见的界面元素 —— 除非用户要求一份展示它们的教学讲义。
- 结尾页只做一个收尾动作。不要把总结、引语、行动号召与感谢堆在它上面。

### 中文与 CJK deck

- 设置 `<html lang="zh-CN">`（或正确的 locale），并保持文件为 UTF-8。
- 若设计需要，使用有辨识度的拉丁展示字体，但始终提供 CJK 字体栈，例如 `"Noto Sans SC", "Source Han Sans SC", "LXGW WenKai", sans-serif` 或 `"Noto Serif SC", "Source Han Serif SC", "Songti SC", serif`。
- CJK 文本段使用 `letter-spacing: 0`。若设计中拉丁展示字体使用负字距，将其限定到仅含拉丁字符的 class；绝不施加于中文。
- 使用宽裕的行高：正文约 `1.7–1.9`，标题 `1.2–1.35`。小号中文文本避免 300 字重，避免伪粗体/伪斜体。
- 不要对中文文本做大写转换或斜体。中文句子使用中文标点，并保持中英混排间距可读。
- 在 1920×1080 舞台上正文保持约 24px 或更大；表格与图注约 22px 或更大。若不合适，拆分该页。
- 为长 URL 与混合 token 加上 `overflow-wrap: anywhere`，然后在渲染截图中检查实际换行。

### 输出契约

- `index.html`，CSS/JS 内联；图片放在 `assets/`，除非用户要求单文件可移植。
- 默认包含完整视口 CSS、导出契约（`?export=1` 与 `window.deck`）以及内联编辑器。
- 允许远程字体。告知用户依赖 Fontshare/Google Fonts 的 deck 在离线时可能回退；只有在内联所需资源并检查剩余外部引用之后，才能声称文件可移植/离线可用。
- 不要占位文本、lorem ipsum、空区块或损坏的图片路径。

完成条件：所有要求的幻灯片都存在，所有提供的材料都可溯源，放置的每张图片都已打开且与图注、alt 文本匹配（或已明确报告图片检查未验证），且 deck 能打开。

## 5. 验证

执行三轮检查。技术检查不能替代内容真实性与设计。

### 内容真实性

- 每条主张、数字、名称与引文都可溯源到所提供材料或已引用来源；推断要么标注为推断，要么移除。
- 每张承担证据作用或被标注为证据的图片，展示的正是幻灯片声称的内容。打开文件，与句子、图注和 alt 文本比对，不一致时就替换或移除。
- 仅演讲者可见的文本不出现在受众视图中。

### 设计

读 [references/design-review.md](references/design-review.md) 并应用其中的检查：

- 每张幻灯片的任务、焦点与阅读顺序；
- 图文关系与图注放置；
- 装饰审计：每个重复元素都得其位置；
- 整 deck 的节奏与单一收尾动作；
- 与所选方向的一致性，包括预设与自定义设计。

当用户说 deck 看起来很通用或“像 AI 做的”时，先诊断视觉系统与信息层级。通过删减内容与重排优先级来修，而不是增加装饰。

### 技术

在 Node 与 Chromium/Chrome 可用时，使用导出器的截图模式：

```bash
node scripts/export-pdf.mjs <deck>/index.html --png-dir /tmp/deck-shots --viewport 1280x720
node scripts/export-pdf.mjs <deck>/index.html --png-dir /tmp/deck-phone --viewport 390x844
```

查看这些 PNG —— 真正去看，而不是只看文件大小。然后检查：

- 舞台保持 16:9 且等比缩放；手机视图留边而不是重排。
- 没有裁切的标题、溢出的卡片、重叠的面板，或低于舒适字号的文本。
- 中文字形正常渲染，换行合理，且字距不是负值。
- 表格与对比布局可读。
- 导出器未报告损坏图片或 1920×1080 溢出警告，且 `.reveal` 元素在捕获的最终状态中可见。
- 导航可用，在编辑器中输入不会切换幻灯片。
- `Ctrl/Cmd+S` 下载一份清理过的副本，且不回写源文件。若你测试它，先把下载文件移到 deck 文件夹内 `assets/` 旁边再重新打开；留在下载目录的副本无法加载 deck 的图片。

若不存在浏览器或截图能力，就如实说明，并报告哪些检查仍未验证。

完成条件：三轮检查全部完成；每张幻灯片都在桌面与手机尺寸下查看过，每张图片都打开过，且任何无法执行的检查都已点名。

## 6. 交付

报告 deck 路径、幻灯片数量、样式名称、导航按键，以及编辑如何工作。若用户委托了方向，说明选择的依据。提及浏览器保存会下载新的 HTML 文件而不是覆盖源文件，图片位于 `assets/`，且下载的文件在重新打开或导出前必须移到 deck 文件夹内 `assets/` 旁边。

在可用时使用 agent 的文件呈现或打开能力；否则给出路径。绝不要假定 macOS 的 `open`、桌面会话或图形浏览器。

不要在常规交付中提议或执行公网部署。若用户要求公开分享，读 [references/deploy.md](references/deploy.md)，并在上传前取得明确同意。

## 修改已有 deck

若改动是替换视觉方向而非保留它，先执行步骤 3。

1. 编辑前先读 HTML、视口 CSS 与当前幻灯片结构。保留现有设计系统。
2. 保持固定舞台模型。新内容会溢出时，拆分幻灯片或收紧布局；不要添加响应式断点或缩小文字。
3. 若 deck 现有运行时可用就保留它。若它缺少 `window.deck`，导出器会回退为切换 `.slide.active/.visible`；确认该 deck 使用了这些 class。
4. 改动后重新执行步骤 5 的验证，至少包含一个手机视口。
5. 不要重构无关标记，或给其他幻灯片换样式。
6. 添加内容或图片时，应用步骤 4–5 中的内容真实性检查。

## 支持文件

| 文件 | 用途 | 何时读 |
| --- | --- | --- |
| [STYLE_PRESETS.md](STYLE_PRESETS.md) | 12 个原始预设，含配色、字体与标志性元素 | 样式探索 |
| [bold-template-pack/selection-index.json](bold-template-pack/selection-index.json) | 34 个 bold 模板的精简元数据 | 初筛 |
| [bold-template-pack/templates/*/preview.md](bold-template-pack/templates/) | 标题页预览卡 | 仅对初筛候选 |
| [bold-template-pack/templates/*/design.md](bold-template-pack/templates/) | 完整设计系统 | 仅所选模板 |
| [viewport-base.css](viewport-base.css) | 强制固定舞台 CSS | 每次生成 |
| [html-template.md](html-template.md) | HTML 结构、控制器、编辑器、导出契约 | 每次生成 |
| [animation-patterns.md](animation-patterns.md) | 动画片段与“效果到感受”指南 | 涉及动效时 |
| [references/design-review.md](references/design-review.md) | 图片真实性、页面构图、装饰与整 deck 检查 | 每次交付；图片密集 deck 与“通用/AI 感”反馈 |
| [references/pptx.md](references/pptx.md) | PPTX → HTML 抽取与转换 | 输入为 PPT/PPTX |
| [references/editable-pptx.md](references/editable-pptx.md) | HTML → 可编辑 PPTX 工作流与双轴验收 | 要求可编辑 PPTX；创作双格式 deck 前 |
| [references/pptx-troubleshooting.md](references/pptx-troubleshooting.md) | 基于表示形式的诊断与已知转换陷阱 | HTML → PPTX 试点或审计发现不匹配 |
| [references/pdf.md](references/pdf.md) | 基于截图的 PDF 导出 | 要求导出 PDF |
| [references/deploy.md](references/deploy.md) | 公网分享清单 | 用户明确要求发布 |
| [UPSTREAM.md](UPSTREAM.md) | 锁定的上游提交、导入范围、本地改动 | 维护与升级 |
