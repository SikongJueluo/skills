# Bold 模板包

本包把 `beautiful-html-templates` 设计系统带入 `frontend-slides` 技能，而不把它们变成每个 deck 的默认选择。

## 该读什么

1. 先读 `bold-template-pack/selection-index.json`。
2. 仅凭元数据初筛候选：
   - `mood`
   - `tone`
   - `best_for`
   - `avoid_for`
   - `formality`
   - `density`
   - `scheme`
3. 制作标题页预览时，只读相关候选的 `preview.md` 文件。
4. 用户选定 bold 模板后，只读那一个模板的完整 `design.md`。
5. 不要读包内每个 `design.md`。
6. 除非选定的 `design.md` 缺少关键的实现细节，否则不要读取或复制源模板库中的 `template.html`。

完整的源元数据索引未捆绑进面向用户的技能。常规生成只应使用 `selection-index.json`。

## 在 Frontend Slides 中如何使用

预览组合：

- 1 个来自 `STYLE_PRESETS.md` 的稳妥选项
- 至少 1 个来自本包的 bold 选项
- 1 个 wildcard 选项，可以是本包中的另一个 bold 模板，或自行生成的自定义设计

在该默认组合内调整基调：

- 对董事会、法务、监管、医疗、投资者更新或高度正式的内部 deck，让稳妥选项非常克制，并选择更沉稳、正式度更高的 bold 模板。wildcard 应显得权威且具体，而不只是装饰。
- 对大胆、编辑感、有表现力、实验性或设计密度高的 deck，把稳妥选项保留为可读的回退，选择一个强烈的 bold 模板，并把 wildcard 用于第二个更大胆的模板，或一个更贴合用户场合与气质的自定义设计。

若 wildcard 是自定义的，它必须遵循 Frontend Slides 的“无 slop”美学：有辨识度的字体排印、坚定投入的调色板、可辨识的布局系统、切合语境的视觉构想、固定 16:9 舞台行为，且不出现 “custom”、“wildcard”、“template” 或 “preview” 之类的可见过程标签。

## 实现契约

`design.md` 是设计系统参考。把它当作风格配方，而不是要复制的内容。`preview.md` 只是用于生成三个标题页选项的轻量风格卡。

包内的 `design.md` 可能提到 `deck-stage.js`。那个上游 web component 运行时是有意不捆绑的：生成的 deck 使用 `../html-template.md` 中记录的内联控制器，它暴露 `window.deck` 与导出器理解的 `.slide` / `.active` / `.visible` 契约。英文原文 “Or an equivalent inline stage scaler” 是关键表述，即“或等效的内联舞台缩放器”。

预览幻灯片必须是用户 deck 的真实标题页。不要在幻灯片本身上渲染模板名称、选项标签、文件名、路径、`preview.md`、“生成自”，或用户需求备注。

生成最终幻灯片时：

- 让输出保持为一个 HTML 文件，CSS 与 JS 内联。图片可以放在相对 `assets/` 目录中；完全可移植的单文件是可选变体，不是默认。
- 包含 `viewport-base.css` 的全部内容。
- 把每个 deck 都生成为固定 1920×1080 舞台，并等比缩放到视口。即使源模板原本是视口流式的，也如此处理。
- 把源 `design.md` 中的 `vw`、`vh` 与 `clamp()` 值视为设计比例，换算成固定的 1920×1080 舞台坐标。
- 保留所选模板的字体、调色板、装饰语汇、间距节奏与组件语法。
- 对中文/CJK 文本，遵循所选 `design.md` 的 CJK 章节；绝不对 CJK 文本段施加负字距或大写转换。
- 保持用户真实幻灯片内容为第一位。模板风格应塑造呈现方式，而不是凌驾于信息或结构之上。
- 同时验证渲染输出的文本溢出与面板重叠。卡片可以通过 `scrollHeight` 检查，却仍被另一个栅格面板遮住。
