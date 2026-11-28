# Skill repository context

## Source and runtime packages

- `src/<skill>/SPEC.zh.md` is the sole authority for each migrated Skill's behavior.
- `skills/<skill>/SKILL.md` is the English runtime candidate. Authored references follow the same rule: `src/.../name.zh.md` maps to `skills/.../name.md`.
- Scripts, templates, licenses, and other non-language assets are stored in `src/` and copied as ordinary files into `skills/`. `just skill-sync` leaves all `skills/*/evals/` directories alone and excludes `.zh.md` files.
- `compiler/lock.json` records source/output hashes and generator metadata. A matching hash means only that the recorded files have not changed; semantic equivalence and task performance require separate review/evaluation.
- Translation is a manual reviewed step. No model calls are part of sync, tests, or CI.

## Evaluation assets

The existing behavior evaluations use the skill-creator JSON shape: each case has a prompt, expected output, optional files, and expectations. Trigger sets contain queries with expected trigger decisions. Fixture paths may be relative to a Skill directory, so consumers must preserve or resolve that base correctly. Existing `skills/*/evals/` content is runtime-adjacent source data and is preserved during the source migration and asset sync.

Current tracked evaluation coverage is 32 behavior cases across four Skills and 35 trigger queries across three Skills. A Skill without cases is unvalidated, not passed. The `loop-discuss`, `loop-teach`, and `loop-iterate` set is deliberately uncovered for now: what makes it work is a stopping rule, and stopping only shows up across turns, which the single-turn solver cannot exercise. Treat them as unvalidated until a scripted-followup solver exists. These suites are regression material; they do not by themselves establish that English outperforms Chinese.

Use the repository's Inspect AI + Podman workflow in [`evals/README.md`](evals/README.md) for sandboxed evaluation. Execution tools must actually use Inspect's sandbox API; configuring a sandbox does not automatically contain arbitrary host-side code. Keep the evaluated model, exact runtime Skill files, tool set, and task fixtures fixed when comparing no-Skill, Chinese-source, and English-output conditions.

## Nix deployment boundary

The production Nix source lock is managed in the separate Nix configuration repository. This Skill repository's sync, hash checks, and Inspect evaluations do not update or activate that production pin.
