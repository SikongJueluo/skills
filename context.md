# Code Context — skills 仓库的 skill 验证惯例

## 1. 相近的交互式 review/teaching skill 及其 evals 覆盖

有 evals 的 skill（仅 2 个，均为模型自动调用型）：

| skill | evals.json（输出协议） | trigger-set.json（触发匹配） |
|---|---|---|
| `teaching` | `skills/teaching/evals/evals.json` — 6 cases（id 1–6，含 near-miss id5） | `skills/teaching/evals/trigger-set.json` — 9 条 query（4 正 + 4 near-miss，其中 4 条派生自 evals.json #1/#2/#5） |
| `arch-code-review` | `skills/arch-code-review/evals/evals.json` — 5 cases（id 1–5，含 near-miss id5） | `skills/arch-code-review/evals/trigger-set.json` — 10 条 query（5 正 + 5 near-miss） |

无 evals 的 skill：`review-with-me`（本任务目标）、`teach-me`（别名）、`jj-describe`。

关键区别：`review-with-me` 与 `teach-me` 的 frontmatter 都是 `disable-model-invocation: true`
（`skills/review-with-me/SKILL.md:4`），只经显式 slash 命令调用；`teaching`/`arch-code-review`
是模型自动触发型，因此才需要 trigger eval。**所以 review-with-me 的 trigger-set 价值有限。**

## 2. evals 文件结构与运行命令

两个文件（仓库内无运行文档，runner 来自 pi 的 `skill-creator` skill，
nix store 路径 `/nix/store/q3n1i887zrzp6y0mx2zs87810710lsbz-agent-skills-source/skill-creator/`）：

- **evals.json**：`{ "skill_name", "evals": [{ "id", "prompt", "expected_output", "files": [], "expectations": [...] }] }`
  示例 `skills/teaching/evals/evals.json:2-6`。schema 见 `skill-creator/references/schemas.md`（prompt + expected_output + files + expectations[]）。
  无独立运行脚本；按 `skill-creator/SKILL.md` Step 4 由 grader 子代理对每条 expectations 判分
  （`grading.json`，字段必须是 `text/passed/evidence`），再 `python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>`
  生成 `benchmark.json`，最后 `eval-viewer/generate_review.py` 起 viewer。
- **trigger-set.json**：`[{ "query", "should_trigger", "source" }]`，source 标注派生来源（如 "derived from evals.json #5"）。
  运行命令：`python scripts/run_eval.py --eval-set <skill>/evals/trigger-set.json --skill-path <skill>`
  （用 `claude -p` 逐 query 探测 Skill/Read 是否读取该 skill；默认 3 runs/query、0.5 阈值）。
  commit `232f3db` message 明确提到 trigger-set 是 "for run_eval.py (5 positive + 5 near-miss)"。
  `run_loop.py`（description 优化循环）消费同格式。

## 3. review-with-me 当前验证覆盖

**零覆盖**。`skills/review-with-me/` 只有 `SKILL.md`（`516f00c` 引入、`e565478` 重构为 code-slice 模型），
`git log --all` 下从无 evals 相关提交，目录内无 `evals/`。

## 4. 若修改其输出协议，最小应新增的 eval case

当前输出协议要点（`skills/review-with-me/SKILL.md`）：
- 三种 slice 标签：`Verify`/`Problem`/`Decision`（:42-44）
- slice 固定形状：`### [标签] <所控行为>` + 一两句 mental model + 代码块内 `// REVIEW ①:` 注解（:59）+ `**Review:**`（:62）+ `**Agent take:**`（:63）+ `Source: \`<path:start-end>\``（:64）
- `REVIEW` 注解只加在引用副本，**绝不改项目文件**（:67）
- 非机械改动必须 ≥1 个 slice；全机械才允许 0 slice 且须解释（:46）
- 每轮最多 5 个 slice，按后果排序（:91）
- 不给出 merge verdict（正文开头）
- 严重问题必须进 `Problem` slice，不做单独 findings dump（:93）

按 `teaching`/`arch-code-review` 惯例（正向 + 边界 + near-miss），最小新增：

**evals.json（输出协议，建议 3 正向 + 1 边界）：**
1. **正向 happy path** — prompt：请求 review 一个含非机械改动的连续范围；expectations：产生 ≥1 个 slice、标签 ∈ {Verify,Problem,Decision}、直接引用代码并带 `REVIEW` 注解、含 Review/Agent take/Source 三行、无 merge verdict、不修改项目文件。
2. **分类正确性** — 范围内含重大后果问题 → 必须呈现在 Problem slice 而非独立 findings 列表；意图/本地知识相关 → Decision slice。
3. **零-slice 边界** — 全机械范围 → 无 slice 且必须解释原因（对应 :46 规则）。
4. **轮次上限** — 超过 5 个候选 slice 时每轮最多呈现 5 个（对应 :91）。

**trigger-set.json（可选，最小 1–2 条）：**
- 因 `disable-model-invocation`，触发测试意义有限；若加，1 条 near-miss 即可：`"Review this PR and tell me if it can be merged."` → `should_trigger: false`（该语义属 arch-code-review，其 description 明说 "Not for ordinary coding…"，`skills/arch-code-review/SKILL.md:2`）。仓库惯例是每个 evals.json 固定带一条 near-miss case 并回填 trigger-set（teaching evals.json:55-63、arch-code-review evals.json:53-61，trigger-set source 标 "derived from evals.json #5"）。

## Start Here

`skills/review-with-me/SKILL.md`（全文 108 行，重点 :42-67 与 :89-97 的 slice 协议）——任何输出协议修改都要先对齐这里；evals 写入 `skills/review-with-me/evals/`（需新建目录）。
