# Translate a Chinese Skill specification into its English runtime output

Input: `src/<skill>/SPEC.zh.md` (and, when requested, one `src/<skill>/references/name.zh.md`). Output: replace the corresponding English runtime file in `skills/<skill>/` (`SKILL.md` for the root spec; `references/name.md` for a localized reference).

Treat the Chinese text as the only authoritative source. Translate faithfully into concise, direct English instructions. Preserve the Skill name, frontmatter keys, invocation flags, structure, code, paths, links, and every behavioral condition. Translate the description and prose; do not preserve Chinese-only phrasing in the English runtime copy. Do not add, remove, weaken, strengthen, or infer behavior. If the Chinese source is ambiguous, stop and ask for a source correction instead of resolving it in English.

Return only the complete English file, including frontmatter when present. Do not modify scripts, fixtures, evals, or other files. Review the output against the source before recording the exact pair with `just skill-record <name> <generator>`; the generator value is the actual model ID or other truthful provenance. Recording does not imply a human has approved the result.

The hash record detects later file changes; it does not prove that the English output is semantically equivalent to the Chinese source or performs better. Behavioral evidence comes from evaluation, not from translation, review metadata, or matching hashes.
