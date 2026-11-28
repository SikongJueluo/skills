---
name: jj-describe
description: 为 Jujutsu 提交撰写并应用简洁、自包含的 Conventional Commits 描述。用于用户要求描述某个 jj 提交时，以及在 jj 仓库中完成一段连贯的代码或文档改动后、当前非空提交尚无描述时。说明改了什么、为什么改，不使用 P0、P1 之类的纯上下文计划标签。
argument-hint: "[可选 change_id | commit_id | revset，例如 @, @-, llvznuql]"
allowed-tools: Bash(jj *), Bash(git show *), Bash(git diff *), Bash(git log *)
---

# jj-describe

为 jj 提交撰写 Conventional Commits 描述。用 **git** 读取改动（jj 默认 diff 基于颜色，Agent 无法阅读）；用 `jj desc` 应用描述。

## 安全

- 只修改描述。除非用户明确要求，**绝不** `merge`、`rebase` 或 `push`。
- **绝不改写其他写入者已记录的层。** 以非自己的空白 `@` 为目标（例如 `jj desc -r @-`、某个 change-id、某个 revset）会重写该提交并对其后代做 rebase。在对这类 revision 执行 `jj desc -r <rev>`、`jj squash`、`jj abandon` 或 `jj restore` 之前，先用一条只读日志检查：`jj --no-pager --color=never log -r '<rev>' --no-graph -T 'change_id.short() ++ " | empty=" ++ empty ++ " | " ++ description.first_line() ++ "\n"'`。若它**非空且已有描述**，停下来并报告——那一层记录的是其他写入者的工作，不是你的。不要描述、squash 或 abandon 它；改为在一个新的 `jj new` 层上记录自己的工作（这是正常的开工路径，不是错误恢复）。只有当用户明确指示、点名该 revision 且要求修改其现有描述时才覆盖，并警告这会重写该 revision 并对其后代做 rebase。
- 把每个仓库视为 jj 的**单写入者**：一次只发一条 jj 命令，等它退出后再发下一条。绝不把多条 jj 命令放进并行的工具调用；即便是只读 jj 命令也可能快照工作副本。纯 git 读取可以并行。
- 若 jj 报告并发修改、分叉或 Git HEAD 更新失败，停下来并报告。不要把 `jj abandon`、`jj new` 或 `jj rebase` 当作自动恢复手段。
- 始终给 jj 和 git 传 `--no-pager`，以免输出挂住会话。

## 1. 选定目标

- **自动完成触发**（用户没有要求描述）：只检查 `@`。仅当它非空且无描述时才以它为目标。若其 diff 包含无关的既有工作或其意图不明，保持不动并说明原因。
- **用户点名了提交**（change_id / commit_id / revset，如 `@`、`@-`、`@--`）：**只**以那一个为目标。不要顺便扫一遍无描述的提交。当目标不是自己的空白 `@` 时，先执行“安全”一节中的已记录层检查。
- **用户要求但未点名提交**：以自己的每个非空、无描述的提交为目标：
  ```
  jj --no-pager --color=never log -r 'mine() & description(exact:"") & ~root() & ~empty()' --no-graph -T 'change_id.short() ++ " " ++ commit_id.short() ++ "\n"'
  ```
  若结果为空，报告“没有可描述的内容”并停止。若列表很长，先展示它并在批量编辑前确认。

## 2. 检查并起草

在修改任何内容之前读取每个目标。这些纯 git 读取可以并行。在 co-located 仓库中，jj 的 `commit_id` 就是 git 哈希：

```
git --no-pager show <commit_id>
```

若仓库不是 co-located（无 `.git`），回退到 `jj --no-pager diff --git -r <change_id>`；它的 `--git` 输出是普通 unified diff，而非基于颜色。

起草 Conventional Commits 信息（https://www.conventionalcommits.org/en/v1.0.0/）：

- **英文、简洁、纯文本。不用 markdown**（不用反引号、粗体或标题）。
- 标题：`type(scope): summary` —— 小写、祈使语气、结尾不加句号。说明**改了什么**。
- 类型：`feat`、`fix`、`docs`、`refactor`、`perf`、`test`、`chore`、`style`、`build`、`ci`。当存在明确的模块/路径时加 `(scope)`。
- 让信息不依赖任务对话即可理解。把临时计划标签（`P0`、`P1`、阶段名、选项字母）替换为它们所代表的具体行为、问题或约束。
- 正文（**为什么**）：用一小段记录**决策**——采取的做法，以及迫使这样做的约束或权衡；当确实存在被放弃的替代方案时点名它。写出 diff 无法呈现的内容，使从未见过该任务的读者也能理解这个选择。当标题已承载原因时省略正文。
- 将“为什么”限制为**最多 3 行、每行不超过 100 字符**，通过重排换行来适配。当决策无法容纳时，说明该层太大——拆分它，而不是删减或填充理由。
- 把不同改动列为每条一个 `-` 项目符号，以祈使动词开头（add、fix、remove、update、rename、extract……），每行最多 100 字符。项目符号承载逐项细节；“为什么”段落保持独立。

正文形态——决策优先，绝不写 diff：

    好："Pin nixpkgs per host: torch regressed on gfx1103 in the 2025-09 unstable bump."
    坏："Change the nixpkgs input to an older revision and update flake.lock."

## 3. 串行应用

用 **change_id**（在重写之间保持稳定）以及下面精确的 `--stdin` + 带引号 heredoc 模式应用。它安全地保留空行和以 `-` 开头的正文项目符号：

```bash
jj --no-pager desc --stdin <change_id> <<'JJ_DESCRIPTION'
feat(auth): add login endpoint

Enable stateless API access while rejecting malformed identities.

- validate email format
- return JWT on success
JJ_DESCRIPTION
```

对多个目标，先运行一条 `jj desc`，等退出码为 0，然后在后续工具调用中运行下一条。首个失败即停止整批。使用这种传输方式，而不是重复的 `-m` 参数或猜测的文件输入参数。

### 少样本：两个目标

第一次助手工具调用——也是该轮中唯一的 jj 调用：

```bash
jj --no-pager desc --stdin mrpyxtqq <<'JJ_DESCRIPTION'
refactor(theme): source shell colors from catppuccin

Keep starship and Home Manager on one palette instead of maintaining duplicated color constants.

- enable the catppuccin Home Manager module
- replace hardcoded starship colors
JJ_DESCRIPTION
```

在该工具结果成功退出后，下一次助手工具调用：

```bash
jj --no-pager desc --stdin ysxvxtlo <<'JJ_DESCRIPTION'
chore(flake): drop upstreamed patches

Use maintained upstream fixes so local overrides no longer drift across dependency updates.

- remove obsolete build overrides
- update locked dependencies
JJ_DESCRIPTION
```

## 4. 验证

所有写入完成后，运行一条包含全部目标与 `@` 的串行 jj 命令：

```bash
jj --no-pager log -r 'mrpyxtqq | ysxvxtlo | @' --no-graph
```

完成意味着：命令成功退出，每个目标都显示预期的描述，且每个正文都遵守 3 行、100 字符的界限。分叉错误即失败：停下来报告，不做清理性变更操作。
