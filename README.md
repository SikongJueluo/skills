# Skills

A small collection of reusable skills for coding agents.

## Included skills

- [`arch-code-review`](skills/arch-code-review/SKILL.md) — Reviews a diff, PR, or branch from an architecture-first perspective and decides whether its minimum end-to-end loop is mergeable.
- [`code-craft`](skills/code-craft/SKILL.md) — Applies a contract-first standard while writing code: check the real interface contract, implement the current need, and trim unearned defensive branches, fallbacks, abstractions, and scope creep.
- [`code-craft-review`](skills/code-craft-review/SKILL.md) — Reviews a finished change for code-quality problems against the `code-craft` standard and reports actionable findings. Requires `code-craft`; not a merge or architecture decision.
- [`frontend-slides`](skills/frontend-slides/SKILL.md) — Builds, converts, and revises fixed-stage 16:9 HTML presentations with a large design template pack.
- [`jj-describe`](skills/jj-describe/SKILL.md) — Writes and applies concise, self-contained Conventional Commits descriptions to Jujutsu commits, on request or after completing a change.
- [`jj-desc`](skills/jj-desc/SKILL.md) — Provides a user-invoked alias that starts a `jj-describe` session.
- [`refactor-ui`](skills/refactor-ui/SKILL.md) — Improves an existing UI or visual artifact from concrete feedback: diagnose the complaint, read design guidance on demand, make a bounded revision, and verify the original problem improved.
- [`review-with-me`](skills/review-with-me/SKILL.md) — Curates load-bearing code into focused slices for collaborative human review.
- [`teaching`](skills/teaching/SKILL.md) — Intertwines teaching and co-design to build a shared technical model before implementing a maintainable change.
- [`teach-me`](skills/teach-me/SKILL.md) — Provides a user-invoked alias that starts a `teaching` session.

## License

[MIT](LICENSE)
