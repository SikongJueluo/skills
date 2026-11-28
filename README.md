# Skills

A small collection of reusable skills for coding agents.

## Included skills

- [`arch-code-review`](skills/arch-code-review/SKILL.md) — Reviews a diff, PR, or branch from an architecture-first perspective and decides whether its minimum end-to-end loop is mergeable.
- [`code-craft`](skills/code-craft/SKILL.md) — Applies a contract-first standard while writing code: check the real interface contract, implement the current need, and trim unearned defensive branches, fallbacks, abstractions, and scope creep.
- [`code-craft-review`](skills/code-craft-review/SKILL.md) — Reviews a finished change for code-quality problems against the `code-craft` standard and reports actionable findings. Requires `code-craft`; not a merge or architecture decision.
- [`frontend-slides`](skills/frontend-slides/SKILL.md) — Builds and revises fixed-stage 16:9 HTML presentations, converts PPTX to HTML, and guides PDF or editable-PPTX export.
- [`jj-describe`](skills/jj-describe/SKILL.md) — Writes and applies concise, self-contained Conventional Commits descriptions to Jujutsu commits, on request or after completing a change.
- [`jj-desc`](skills/jj-desc/SKILL.md) — Provides a user-invoked alias that starts a `jj-describe` session.
- [`loop-discuss`](skills/loop-discuss/SKILL.md) — Cuts a vague idea down to the current minimum closed loop, fixes its endpoint and acceptance, and emits a contract that can be followed as written. Covers only this loop, not the whole design.
- [`loop-iterate`](skills/loop-iterate/SKILL.md) — Reviews a finished loop against its contract, fixes the friction it exposed in the environment and tooling, and connects to the next loop's discussion.
- [`loop-teach`](skills/loop-teach/SKILL.md) — Teaches along motive, intuition, and abstraction, one layer per turn, so the human can carry it elsewhere instead of receiving one large dump.
- [`refactor-ui`](skills/refactor-ui/SKILL.md) — Improves an existing UI or visual artifact from concrete feedback: diagnose the complaint, read design guidance on demand, make a bounded revision, and verify the original problem improved.
- [`review-with-me`](skills/review-with-me/SKILL.md) — Curates load-bearing code into focused slices for collaborative human review.

## Repository workflow

- `src/<skill>/SPEC.zh.md` is the authoritative Chinese specification. Nested authored references use `*.zh.md`; their reviewed English outputs live only in `skills/<skill>/` with the `.zh` suffix removed (the root spec maps to `SKILL.md`).
- `skills/` is the directly consumable runtime bundle. Generated English documents are tracked there, not duplicated under `src/`. `just skill-sync` copies non-language assets from `src/`; it does not translate, overwrite English outputs, or touch `evals/`.
- Translate manually with the [translation prompt](<compiler/translate_prompt.md>) and review the English against the Chinese source. `just skill-record <name> <generator>` records the model ID (or other truthful provenance) and the exact source/output hashes. `just skill-check` detects missing pairs, stale hashes, unpaired runtime files, and asset drift.
- A matching hash proves only that the recorded files have not changed; it is not human approval, semantic equivalence, or a performance result. English remains a candidate until controlled evaluation supports using it.
- `just test` runs deterministic workflow tests with Python 3.11+. `just eval-wiring-smoke` runs the single Inspect AI + Podman smoke case described in the [eval guide](<evals/README.md>); it requires model credentials and a working Podman setup. This smoke tests wiring, not task performance.
- The Nix deployment configuration is managed separately; this repository workflow does not update its source lock.

## License

[MIT](LICENSE)
