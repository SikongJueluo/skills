---
name: jj-describe
description: Fill missing commit descriptions for Jujutsu (jj) commits, or rewrite a specified commit's description. Reads each change via git show/diff (jj's default diff is color-based and unreadable to the agent), drafts an English Conventional Commits message, and applies it with `jj desc`. Use whenever the user asks to write, fill, generate, or add commit messages/descriptions for jj commits, describe undescribed commits, or message a specific jj change/commit/revision — even without the word "skill".
argument-hint: "[optional change_id | commit_id | revset, e.g. @, @-, llvznuql]"
allowed-tools: Bash(jj *), Bash(git show *), Bash(git diff *), Bash(git log *)
---

# jj-describe

Write Conventional Commits descriptions for jj commits. Read changes with **git** (jj's default diff is color-based and unreadable to the agent); apply with `jj desc`.

## Safety

- Mutate descriptions only. **Never** `merge`, `rebase`, or `push` unless the user explicitly asks.
- Always pass `--no-pager` to jj and git so output doesn't hang the session.

## 1. Pick targets

- **User named a commit** (change_id / commit_id / revset like `@`, `@-`, `@--`): target **only** that one. Do not also sweep no-description commits.
- **Nothing specified**: target every non-empty, undescribed commit of yours:
  ```
  jj --no-pager log -r 'mine() & description(exact:"") & ~root() & ~empty()' --no-graph
  ```
  If empty, report "nothing to describe" and stop. If the list is long, show it and confirm before editing in bulk.

## 2. For each target

Read the change with git — the jj `commit_id` is the git hash in colocated repos:

```
git --no-pager show <commit_id>
```

If the repo isn't colocated (no `.git`), fall back to `jj --no-pager diff --git -r <change_id>`; its `--git` output is a plain unified diff, not color-based.

Draft a Conventional Commits message (https://www.conventionalcommits.org/en/v1.0.0/):

- **English, concise, plain text. No markdown** (no backticks, bold, or headers).
- Header: `type(scope): summary` — lowercase, imperative, no trailing period.
- Types: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`, `style`, `build`, `ci`. Add `(scope)` when a clear module/path exists.
- Body (optional): one `-` bullet per distinct change, **each starting with an imperative verb** (add, fix, remove, update, rename, extract, …).

Apply with the **change_id** (stable across rewrites):

```
jj desc -m "feat(auth): add login endpoint" -m "- validate email format
- return JWT on success" <change_id>
```

One `-m` per paragraph; keep bullets consecutive inside a single `-m` so they form one body block.

## 3. Verify

```
jj --no-pager log -r '<change_id> | @' --no-graph
```
