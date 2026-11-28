---
name: arch-code-review
description: 架构优先的合并决策评审。仅在明确要求评审某个 diff/PR/分支能否合并时使用。推断本次改动必须完成的最小闭环，对照权威文档检查该 diff，收集验证证据，并判定可合并性。不用于普通编码、调试、重构或随意阅读代码。
argument-hint: "<可选的 PR 链接、diff、文件路径、基线分支或评审焦点>"
---

# /arch-code-review

一次架构优先的**合并决策**。判定本次改动是否完成了其最小可合并闭环。不要逐条罗列所有小毛病。

默认输出语言：英语。优先散文，而不是 Markdown 表格。

## 何时使用

仅用于明确的评审请求——“评审这个 PR”、“这个能合吗？”、“对这个 diff 做架构评审”、“合并前评审”。不用于普通编码、调试、重构，或随意的“看看这段代码”。

## 心智

用**最小闭环**衡量每一项发现：本次改动为了可合并而必须完成的最小端到端行为、边界、数据流或生命周期。在报告开头说明该闭环，然后只报告影响它的**主要矛盾**。一个正确但不重要的细节是噪声；一个小问题只有在揭示系统性风险或破坏闭环时才值得报告。

两个权威：

- **文档 > 实现。** 先读相关文档（README、`docs/`、`ARCHITECTURE.md`、`CONTEXT.md`、ADR、模块文档）。若文档说 X 而代码做 Y，则实现偏离了文档。你可以标出疑似过期的文档，但未经用户确认不得反转该判断。
- **事实 > 声明。** 发现必须建立在代码、diff 与验证输出之上——而不是注释、TODO 或 PR 描述。没有代码/验证事实支撑的发现最多只能作为后续观察。

## 输入

若用户给出 PR 链接、diff、文件、压缩包、文档、参考实现或基线分支，就使用它。否则评审当前仓库的 diff：优先整分支对 `main`/`master` 的 diff，退化为已暂存 + 工作区 diff。若无法获得 diff，就询问。

没有评审配置文件。只遵从当前请求中的参数（输出语言、基线分支、深度、参考实现、是否评估测试）。

## 如何评审

1. **收集事实。** 阅读 diff、变更文件以及邻近的依赖/边界代码。找到并阅读管辖该改动区域的文档。记录任何文档/代码冲突。
2. **陈述最小闭环。** 从 diff、文档、目录结构、变更的测试、公开 API 与执行路径中推断它。明确说明：*“本次评审的最小闭环是 X。”*
3. **透过对本次改动真正重要的视角检查**——不要机械地覆盖全部视角：
   - 数据结构、归属关系与流向
   - 生命周期与销毁
   - 性能
   - 抽象边界
   - 测试（仅在其属于本次范围时——见下文）
4. **收集验证证据。** 识别项目类型，先跑廉价检查（lint、类型检查、相关测试），若有助于验证，则扩展到全量测试。验证是证据，不能替代阅读代码。

**在无法推断闭环时停止，而不是强行评审**：存在多个互不相关的闭环且用户未选定其一（列出候选并询问哪一个是主要的）、必需的对比材料不可访问、仓库/diff 无法读取、文档与所述目标根本冲突且没有取舍依据，或事实不足。输出*“无法完成正式评审”*并说明缺少什么。不要臆造发现。

## 严重度

- **blocker** — 合并前必须修复。破坏核心边界或数据流、使生命周期/归属关系无法证明、使核心流程错误或不可执行、违反权威文档，或在测试/验证中掩盖真相。任何 blocker ⇒ 不可合并。
- **high** — 强烈建议修复；多项 high 可使改动实际上不可合并。
- **medium** — 若闭环其余部分完好则可合并；应排期处理。
- **low** — 通常省略；只在揭示系统性风险或影响闭环时纳入。

## 验证与测试

按**对最小闭环的影响**来判断验证失败，而不是机械处理。破坏可编译性、核心路径、数据真实性、生命周期安全或验证可信度的失败属于 blocker/high。不触及闭环的 lint/格式失败属于 medium 或后续项。验证通过是证据，不是可合并性的证明。

不要默认惩罚缺失的测试——测试常在闭环稳定后才补写。仅在以下情况评估测试套件：用户要求、闭环本身*就是*测试/验证闭环、测试发生实质变更，或测试脚手架扭曲了闭环。否则把测试维度记为“本轮未评估”。临时标记（`FOR TEST`、fixture、调试辅助）不自动构成问题。

## 合并门禁

只有在没有 blocker 且围绕最小闭环的主要矛盾均已解决时才可合并。陈述门禁结果与理由（blockers、严重度分布、验证事实）。判断力做最终决定——干净的表面本身永远不能使代码可合并。

## 输出

一份聚焦的报告，让维护者能做出决定。建议结构——按改动调整，但始终陈述闭环与门禁：

```markdown
# Architecture Code Review

## 1. Minimum closed loop
[the inferred loop and why; or "Cannot complete formal review" + what's missing]

## 2. Merge decision
[Mergeable / Not mergeable / Needs user decision, with reasoning]

## 3. Findings
[Each: Severity · affected area · code/validation facts · why it breaks the loop · repair direction.
Lead with blockers and highs. Give a strategic repair direction, not a full patch unless asked.]

## 4. Validation evidence
[commands run + results + how failures affect the loop; or why not run]

## 5. Doc/code conflicts
[docs vs implementation; or None]

## 6. Follow-ups
[few restrained notes — current non-blockers that may become principal contradictions later; no gate impact]
```

不要泛泛的褒奖段落。若某项关键设计有效且对门禁重要，在决策中简短说明。直接、基于证据——不奉承，不贬损。

若 blocker 数量众多，不要逐一枚举：说明该改动整体不可合并，详述代表性 blocker，并按类别概括其余部分。
