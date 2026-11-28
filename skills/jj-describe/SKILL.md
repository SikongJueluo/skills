---
name: jj-describe
description: Write and apply concise, self-contained Conventional Commits descriptions for Jujutsu commits. Use when the user asks to describe a jj commit, and after finishing a cohesive code or documentation change in a jj repository whose current non-empty commit has no description. State what changed and why, with no context-only planning labels such as P0 or P1.
argument-hint: "[optional change_id | commit_id | revset, e.g. @, @-, llvznuql]"
allowed-tools: Bash(jj *), Bash(git show *), Bash(git diff *), Bash(git log *)
---

# jj-describe

Write Conventional Commits descriptions for jj commits. Read the changes with **git** (jj's default diff is color-based and unreadable to an agent); apply the description with `jj desc`.

## Safety

- Change descriptions only. **Never** `merge`, `rebase`, or `push` unless the user asks for it explicitly.
- **Never rewrite a layer that another writer has already recorded.** Targeting a revision other than your own blank `@` (for example `jj desc -r @-`, a change-id, or a revset) rewrites that commit and rebases its descendants. Before running `jj desc -r <rev>`, `jj squash`, `jj abandon`, or `jj restore` against such a revision, inspect it with a single read-only log: `jj --no-pager --color=never log -r '<rev>' --no-graph -T 'change_id.short() ++ " | empty=" ++ empty ++ " | " ++ description.first_line() ++ "\n"'`. If it is **non-empty and already carries a description**, stop and report it — that layer records another writer's work, not yours. Do not describe, squash, or abandon it; record your own work on a fresh `jj new` layer instead (the normal way to start work, not error recovery). Override this only on an explicit user instruction that names the revision and asks to change its existing description, and warn that doing so rewrites the revision and rebases its descendants.
- Treat each repository as having a **single writer** for jj: run one jj command, wait for it to exit, then run the next. Never issue several jj commands in parallel tool calls; even read-only jj commands can snapshot the working copy. Pure git reads may run in parallel.
- If jj reports concurrent modification, divergence, or a failed Git HEAD update, stop and report it. Do not reach for `jj abandon`, `jj new`, or `jj rebase` as automatic recovery.
- Always pass `--no-pager` to jj and git so the output cannot hang the session.

## 1. Choose the targets

- **Automatic completion trigger** (the user did not ask for a description): inspect `@` only. Target it only when it is non-empty and has no description. If its diff contains unrelated pre-existing work, or its intent is unclear, leave it alone and explain why.
- **The user named a commit** (change_id / commit_id / revset such as `@`, `@-`, `@--`): target **only** that commit. Do not additionally sweep for commits without descriptions. When the target is not your own blank `@`, run the recorded-layer check from Safety first.
- **The user asked without naming a commit**: target each of your own commits that is non-empty and has no description:
  ```
  jj --no-pager --color=never log -r 'mine() & description(exact:"") & ~root() & ~empty()' --no-graph -T 'change_id.short() ++ " " ++ commit_id.short() ++ "\n"'
  ```
  If that returns nothing, report "nothing to describe" and stop. If the list is long, show it and confirm before editing in bulk.

## 2. Inspect and draft

Read every target before mutating anything. These pure git reads may run in parallel. In a colocated repository, jj's `commit_id` is the git hash:

```
git --no-pager show <commit_id>
```

If the repository is not colocated (there is no `.git`), fall back to `jj --no-pager diff --git -r <change_id>`; its `--git` output is a plain unified diff rather than a color-based one.

Draft a Conventional Commits message (https://www.conventionalcommits.org/en/v1.0.0/):

- **English, concise, plain text. No markdown** (no backticks, bold, or headers).
- Header: `type(scope): summary` — lowercase, imperative, no trailing period. State **what** changed.
- Types: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`, `style`, `build`, `ci`. Add `(scope)` when there is a clear module or path.
- Make the message intelligible without the task conversation. Replace temporary planning labels (`P0`, `P1`, phase names, option letters) with the concrete behavior, problem, or constraint they represent.
- Body (**why**): one short paragraph recording the **decision** — the approach taken, and the constraint or trade-off that forced it, naming the alternative you rejected when one was genuinely in play. Write down what the diff cannot show, so a reader who never saw this task still understands the choice. Omit the body when the header already carries the reason.
- Hold the why to **3 lines of at most 100 characters**, rewrapping the text to fit. When the decision does not fit, the layer is too big — split it instead of trimming or padding the reason.
- List distinct changes one `-` bullet per change, each starting with an imperative verb (add, fix, remove, update, rename, extract, …), one line of at most 100 characters. The bullets carry the per-change detail; the why paragraph stays separate.

Body shape — the decision first, the diff never:

    Good: "Pin nixpkgs per host: torch regressed on gfx1103 in the 2025-09 unstable bump."
    Bad:  "Change the nixpkgs input to an older revision and update flake.lock."

## 3. Apply serially

Apply with the **change_id** (stable across rewrites) using the exact `--stdin` + quoted-heredoc pattern below. It preserves blank lines and body bullets that start with `-`:

```bash
jj --no-pager desc --stdin <change_id> <<'JJ_DESCRIPTION'
feat(auth): add login endpoint

Enable stateless API access while rejecting malformed identities.

- validate email format
- return JWT on success
JJ_DESCRIPTION
```

For several targets, run one `jj desc`, wait for exit code 0, then run the next one in a later tool call. Stop the batch at the first failure. Use this transport instead of repeated `-m` flags or guessed file-input flags.

### Few-shot: two targets

The first assistant tool call — and the only jj call in that turn:

```bash
jj --no-pager desc --stdin mrpyxtqq <<'JJ_DESCRIPTION'
refactor(theme): source shell colors from catppuccin

Keep starship and Home Manager on one palette instead of maintaining duplicated color constants.

- enable the catppuccin Home Manager module
- replace hardcoded starship colors
JJ_DESCRIPTION
```

Once that tool result exits successfully, the next assistant tool call:

```bash
jj --no-pager desc --stdin ysxvxtlo <<'JJ_DESCRIPTION'
chore(flake): drop upstreamed patches

Use maintained upstream fixes so local overrides no longer drift across dependency updates.

- remove obsolete build overrides
- update locked dependencies
JJ_DESCRIPTION
```

## 4. Verify

After all writes finish, run a single serial jj command containing every target and `@`:

```bash
jj --no-pager log -r 'mrpyxtqq | ysxvxtlo | @' --no-graph
```

Done means the command exits successfully, every target shows the description you intended, and each body respects the 3-line, 100-character bound. A divergence error is a failure: stop and report it, without cleanup mutations.
