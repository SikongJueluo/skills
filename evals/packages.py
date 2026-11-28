"""Condition-aware staging plan for paired behavior runs.

A behavior run compares the same case under an explicitly selected condition:

* ``en``   — the repo's English runtime skill package.
* ``zh``   — the Chinese sources overlaid onto the *same* sandbox paths.
* ``none`` — no skill text at all (control).

The path set is derived from the English package and is identical for ``en``
and ``zh``; only the file contents differ. That is what makes the comparison
paired. ``none`` stages the case fixtures only.

Layout produced for ``en``/``zh``:

    /skill/SKILL.md              <- skills/<n>/SKILL.md  | src/<n>/SPEC.zh.md
    /skill/references/foo.md     <- skills/<n>/references/foo.md
                                    | src/<n>/references/foo.zh.md

Everything is staged under an absolute sandbox root so the result cannot depend
on the container working directory. Case fixtures go to
``/skill/evals/fixtures/...`` and are the only files taken from ``evals/``;
``evals.json``, ``trigger-set.json``, rubrics, answers and grading files are
never staged.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "skills"
SOURCE_ROOT = REPO_ROOT / "src"

SANDBOX_ROOT = "/skill"
SANDBOX_SKILL_MD = f"{SANDBOX_ROOT}/SKILL.md"

CONDITIONS = ("none", "zh", "en")

# The Chinese source for a runtime Markdown file.
SPEC_NAME = "SPEC.zh.md"

# Never staged even when a case lists them: these hold the eval definitions or
# would give the answer away. Checked by name anywhere in a path, including
# inside `evals/fixtures/`.
EXCLUDED_NAMES = frozenset(
    {"evals.json", "trigger-set.json", "rubric.json", "rubric.md", "answers.json", "grading.json"}
)


class StagingError(ValueError):
    """A path could not be staged faithfully."""


def validate_skill_name(skill: str) -> str:
    """Require `skill` to be exactly one directory component of `skills/`."""
    if not skill or skill in {".", ".."} or "/" in skill or "\\" in skill:
        raise StagingError(f"skill must be a single directory name: {skill!r}")
    return skill


def skill_dir(skill: str) -> Path:
    return SKILLS_ROOT / validate_skill_name(skill)


def source_dir(skill: str) -> Path:
    return SOURCE_ROOT / validate_skill_name(skill)


def ensure_within(path: Path, root: Path) -> Path:
    """Resolve `path` and require it to stay inside `root`.

    Guards both directions: a trusted repo path may point outside its skill
    package (symlink, stray `..`), and a fixture may try to escape.
    """
    resolved = path.resolve()
    root_resolved = root.resolve()
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise StagingError(f"{path} resolves outside {root}: {resolved}")
    return resolved


def ensure_package_root(skill: str) -> tuple[Path, Path]:
    """Resolved (English, Chinese) package roots, refusing symlinked escapes."""
    return (
        ensure_within(skill_dir(skill), SKILLS_ROOT),
        ensure_within(source_dir(skill), SOURCE_ROOT),
    )


def sandbox_path(relative: str) -> str:
    """Absolute sandbox path for a package-relative path, rejecting escapes."""
    candidate = Path(relative)
    if candidate.is_absolute():
        raise StagingError(f"package path must be relative: {relative}")
    if ".." in candidate.parts:
        raise StagingError(f"package path must not contain '..': {relative}")
    return f"{SANDBOX_ROOT}/{candidate.as_posix()}"


def _is_private(relative: Path) -> bool:
    """Eval assets, caches and VCS metadata are never part of a skill package."""
    parts = relative.parts
    if "__pycache__" in parts or ".venv" in parts:
        return True
    if parts and parts[0] == "evals":
        return True
    return any(part in EXCLUDED_NAMES for part in parts)


def _package_assets(skill: str) -> list[Path]:
    """Non-Markdown files of the runtime package (identical in zh and en)."""
    root = skill_dir(skill)
    if not root.is_dir():
        raise StagingError(f"unknown skill: {skill}")
    return [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.suffix != ".md" and not _is_private(path.relative_to(root))
    ]


def _chinese_counterpart(skill: str, relative: Path) -> Path:
    """The `src/<skill>` file that stands in for a runtime Markdown file.

    Mirrors `scripts/skill_package.py`: a runtime `foo.md` is a *translation
    pair* when `src/<skill>/foo.zh.md` exists, otherwise a *copied asset*
    (`src/<skill>/foo.md`) that is byte-identical in both conditions.
    """
    if relative.as_posix() == "SKILL.md":
        return source_dir(skill) / SPEC_NAME

    if relative.suffix != ".md":
        raise StagingError(f"not a Markdown path: {relative}")

    chinese = (source_dir(skill) / relative).with_name(relative.name[: -len(".md")] + ".zh.md")
    if chinese.is_file():
        return chinese

    asset = source_dir(skill) / relative
    if asset.is_file():
        return asset

    raise StagingError(
        f"{skill}: {relative} has neither a .zh.md translation nor a copied "
        f"src/{skill}/{relative} asset"
    )


def package_plan(skill: str) -> dict[str, tuple[Path, Path]]:
    """Sandbox path -> (English source, Chinese source) for one skill package."""
    root, source_root = ensure_package_root(skill)
    if not root.is_dir():
        raise StagingError(f"unknown skill: {skill}")

    markdown = [
        path
        for path in sorted(root.rglob("*.md"))
        if path.is_file() and not _is_private(path.relative_to(root))
    ]
    if not (root / "SKILL.md").is_file():
        raise StagingError(f"{skill} has no SKILL.md")
    if not (source_root / SPEC_NAME).is_file():
        raise StagingError(f"{skill}: missing src/{skill}/{SPEC_NAME}")

    plan: dict[str, tuple[Path, Path]] = {}
    for english in markdown:
        relative = english.relative_to(root)
        chinese = _chinese_counterpart(skill, relative)
        key = sandbox_path(relative.as_posix())
        plan[key] = (
            ensure_within(english, root),
            ensure_within(chinese, source_root),
        )

    for asset in _package_assets(skill):
        resolved = ensure_within(asset, root)
        plan[sandbox_path(asset.relative_to(root).as_posix())] = (resolved, resolved)

    return plan


def stage_plan(skill: str, condition: str) -> dict[str, Path]:
    """Sandbox path -> host file to stage, for one condition."""
    if condition not in CONDITIONS:
        raise StagingError(f"unknown condition {condition!r}; expected one of {', '.join(CONDITIONS)}")
    if condition == "none":
        return {}

    index = 0 if condition == "en" else 1
    return {sandbox: sources[index] for sandbox, sources in package_plan(skill).items()}


def fixture_plan(skill: str, fixtures: list[str]) -> dict[str, Path]:
    """Stage the case's own input fixtures, and nothing else from `evals/`."""
    fixtures_root = ensure_within(skill_dir(skill) / "evals" / "fixtures", SKILLS_ROOT)
    staged: dict[str, Path] = {}
    for fixture in fixtures:
        relative = Path(fixture)
        if relative.parts[:2] != ("evals", "fixtures"):
            raise StagingError(f"case fixture must live under evals/fixtures/: {fixture}")
        if any(part in EXCLUDED_NAMES or part == "__pycache__" for part in relative.parts):
            raise StagingError(f"refusing to stage eval asset: {fixture}")

        resolved = ensure_within(skill_dir(skill) / relative, fixtures_root)
        if not resolved.is_file():
            raise StagingError(f"{skill}: case references a missing fixture: {fixture}")
        staged[sandbox_path(relative.as_posix())] = resolved
    return staged
