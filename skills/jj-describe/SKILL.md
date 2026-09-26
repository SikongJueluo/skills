---
name: jj-describe
description: Write and apply concise, self-contained Conventional Commits descriptions for Jujutsu commits. Use when the user asks to describe a jj commit, and after completing a cohesive code or documentation change in a jj repository when the current non-empty commit is undescribed. Explain what changed and why without context-only planning labels such as P0 or P1.
argument-hint: "[optional change_id | commit_id | revset, e.g. @, @-, llvznuql]"
allowed-tools: Bash(jj *), Bash(git show *), Bash(git diff *), Bash(git log *)
---

# jj-describe

Write Conventional Commits descriptions for jj commits. Read changes with **git** (jj's default diff is color-based and unreadable to the agent); apply with `jj desc`.

## Safety

- Mutate descriptions only. **Never** `merge`, `rebase`, or `push` unless the user explicitly asks.
- Treat each repository as a **single-writer** for jj: issue at most one jj command, wait for it to exit, then issue the next. Never put multiple jj commands in parallel tool calls; even read-only jj commands may snapshot the working copy. Pure git reads may run in parallel.
- If jj reports concurrent modification, divergence, or a failed Git HEAD update, stop and report it. Do not run `jj abandon`, `jj new`, or `jj rebase` as automatic recovery.
- Always pass `--no-pager` to jj and git so output doesn't hang the session.

## 1. Pick targets

- **Automatic completion trigger** (the user did not ask for a description): inspect only `@`. Target it only when it is non-empty and undescribed. If its diff includes unrelated pre-existing work or its intent is unclear, leave it untouched and report why.
- **User named a commit** (change_id / commit_id / revset like `@`, `@-`, `@--`): target **only** that one. Do not also sweep no-description commits.
- **User asked without naming a commit**: target every non-empty, undescribed commit of yours:
  ```
  jj --no-pager --color=never log -r 'mine() & description(exact:"") & ~root() & ~empty()' --no-graph -T 'change_id.short() ++ " " ++ commit_id.short() ++ "\n"'
  ```
  If empty, report "nothing to describe" and stop. If the list is long, show it and confirm before editing in bulk.

## 2. Inspect and draft

Read every target before mutating anything. These pure git reads may run in parallel. The jj `commit_id` is the git hash in colocated repos:

```
git --no-pager show <commit_id>
```

If the repo isn't colocated (no `.git`), fall back to `jj --no-pager diff --git -r <change_id>`; its `--git` output is a plain unified diff, not color-based.

Draft a Conventional Commits message (https://www.conventionalcommits.org/en/v1.0.0/):

- **English, concise, plain text. No markdown** (no backticks, bold, or headers).
- Header: `type(scope): summary` — lowercase, imperative, no trailing period. Say **what** changed.
- Types: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`, `style`, `build`, `ci`. Add `(scope)` when a clear module/path exists.
- Make the message understandable without the task conversation. Replace temporary planning labels (`P0`, `P1`, phase names, option letters) with the concrete behavior, problem, or constraint they represent.
- For non-trivial changes, add one short body paragraph explaining **why** the change was needed. Omit it only when the reason is already obvious from the header.
- When several distinct changes need listing, add one `-` bullet per change, each starting with an imperative verb (add, fix, remove, update, rename, extract, …).

## 3. Apply serially

Apply with the **change_id** (stable across rewrites) and the exact `--stdin` + quoted-heredoc pattern below. It safely preserves blank lines and body bullets beginning with `-`:

```bash
jj --no-pager desc --stdin <change_id> <<'JJ_DESCRIPTION'
feat(auth): add login endpoint

Enable stateless API access while rejecting malformed identities.

- validate email format
- return JWT on success
JJ_DESCRIPTION
```

For multiple targets, run one `jj desc`, wait for exit code 0, then run the next in a later tool call. Stop the batch on the first failure. Use this transport rather than repeated `-m` flags or guessed file-input flags.

### Few-shot: two targets

First assistant tool call — and the only jj call in that turn:

```bash
jj --no-pager desc --stdin mrpyxtqq <<'JJ_DESCRIPTION'
refactor(theme): source shell colors from catppuccin

Keep starship and Home Manager on one palette instead of maintaining duplicated color constants.

- enable the catppuccin Home Manager module
- replace hardcoded starship colors
JJ_DESCRIPTION
```

After that tool result exits successfully, the next assistant tool call:

```bash
jj --no-pager desc --stdin ysxvxtlo <<'JJ_DESCRIPTION'
chore(flake): drop upstreamed patches

Use maintained upstream fixes so local overrides no longer drift across dependency updates.

- remove obsolete build overrides
- update locked dependencies
JJ_DESCRIPTION
```

## 4. Verify

After all writes finish, run one serial jj command containing every target and `@`:

```bash
jj --no-pager log -r 'mrpyxtqq | ysxvxtlo | @' --no-graph
```

Done means the command exits successfully and every target shows its intended description. A divergence error is a failure: stop and report it without cleanup mutations.
