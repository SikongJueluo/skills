"""Offline tests for condition staging. No network, no Podman, no model call.

Run with: `uv run --locked python -m pytest evals/tests -q`
"""

from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from evals import packages as P  # noqa: E402
from evals.cases import load_case, load_samples  # noqa: E402
from evals.loader import compose_system_prompt  # noqa: E402
from evals.tools import SANDBOX_SKILL_MD, SANDBOX_WORKDIR  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_conditions_are_the_three_documented():
    assert P.CONDITIONS == ("none", "zh", "en")


@pytest.mark.parametrize("skill", ["code-craft", "frontend-slides", "refactor-ui"])
def test_en_and_zh_stage_identical_paths(skill):
    en = P.stage_plan(skill, "en")
    zh = P.stage_plan(skill, "zh")

    assert set(en) == set(zh), "paired runs must stage the same sandbox paths"
    assert SANDBOX_SKILL_MD in en


def test_none_stages_no_skill_text():
    assert P.stage_plan("refactor-ui", "none") == {}


def test_zh_overlays_chinese_sources_at_mapped_paths():
    plan = P.package_plan("refactor-ui")
    en = P.stage_plan("refactor-ui", "en")
    zh = P.stage_plan("refactor-ui", "zh")

    nested = f"{SANDBOX_WORKDIR}/references/surface.md"
    assert nested in plan
    assert zh[nested].relative_to(REPO_ROOT).as_posix() == "src/refactor-ui/references/surface.zh.md"
    assert en[nested].relative_to(REPO_ROOT).as_posix() == "skills/refactor-ui/references/surface.md"
    assert digest(zh[nested]) != digest(en[nested])


def test_translated_and_copied_assets_are_distinguished():
    plan = P.package_plan("frontend-slides")
    translated, copied = [], []
    for sandbox, (english, chinese) in plan.items():
        (translated if digest(english) != digest(chinese) else copied).append(sandbox)

    assert translated, "frontend-slides should have translated Markdown"
    assert copied, "frontend-slides ships static assets with no Chinese counterpart"
    for sandbox in copied:
        english, chinese = plan[sandbox]
        assert digest(english) == digest(chinese), f"{sandbox} copied asset drifted"


def test_system_prompt_is_condition_agnostic():
    """Only the staged document block may differ; the guidance never does."""
    none_prompt = compose_system_prompt(None)
    en_prompt = compose_system_prompt("# Skill\nbody")
    zh_prompt = compose_system_prompt("# 技能\n正文")

    assert en_prompt.startswith(none_prompt)
    assert zh_prompt.startswith(none_prompt)
    assert "SKILL.md" not in none_prompt, "control arm must not be primed about a document"


def test_case_fixtures_land_under_sandbox_workdir():
    staged = P.fixture_plan(
        "frontend-slides",
        ["evals/fixtures/image-truth/deck/index.html"],
    )
    assert staged == {
        f"{SANDBOX_WORKDIR}/evals/fixtures/image-truth/deck/index.html":
            REPO_ROOT / "skills/frontend-slides/evals/fixtures/image-truth/deck/index.html"
    }


def test_case_prompts_resolve_relative_to_workdir():
    """Regression: fixtures must be reachable from the shell cwd."""
    entry = load_case("frontend-slides", 11)
    staged = P.fixture_plan("frontend-slides", entry["files"])
    for sandbox_path in staged:
        assert sandbox_path.startswith(f"{SANDBOX_WORKDIR}/"), (
            "a relative path in the prompt can only resolve if fixtures sit under the workdir"
        )


def test_eval_assets_are_never_staged():
    for skill in ("code-craft", "frontend-slides", "refactor-ui"):
        staged = dict(P.stage_plan(skill, "en")) | dict(P.fixture_plan(skill, []))
        for sandbox in staged:
            relative = sandbox.removeprefix(f"{SANDBOX_WORKDIR}/")
            assert not relative.startswith("evals/") or relative.startswith("evals/fixtures/")


def test_excluded_names_rejected_even_inside_fixtures():
    for bad in (
        "evals/fixtures/rubric.json",
        "evals/fixtures/answers.json",
        "evals/fixtures/grading.json",
        "evals/fixtures/nested/rubric.md",
    ):
        with pytest.raises(P.StagingError):
            P.fixture_plan("refactor-ui", [bad])


def test_package_plan_excludes_evals_directory():
    staged = set(P.package_plan("frontend-slides"))
    assert not any(path.startswith(f"{SANDBOX_WORKDIR}/evals/") for path in staged)


@pytest.mark.parametrize("bad", ["/etc/passwd", "../escape.md", "a/../../b.md"])
def test_escaping_package_paths_are_rejected(bad):
    with pytest.raises(P.StagingError):
        P.sandbox_path(bad)


@pytest.mark.parametrize("bad", ["", ".", "..", "a/b", "../refactor-ui"])
def test_skill_name_must_be_one_component(bad):
    with pytest.raises(P.StagingError):
        P.validate_skill_name(bad)


def test_symlinked_package_escaping_skills_root_is_rejected(tmp_path, monkeypatch):
    """A package directory that is a symlink out of `skills/` must fail."""
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "SKILL.md").write_text("# escaped\n", encoding="utf-8")

    fake_root = tmp_path / "skills"
    fake_root.mkdir()
    (fake_root / "escape").symlink_to(outside)

    monkeypatch.setattr(P, "SKILLS_ROOT", fake_root)
    with pytest.raises(P.StagingError):
        P.ensure_package_root("escape")


def test_unknown_condition_is_rejected():
    with pytest.raises(P.StagingError):
        P.stage_plan("refactor-ui", "EN")


@pytest.mark.parametrize("skill", ["teaching", "teach-me", "no-such-skill"])
def test_unknown_skill_is_rejected(skill):
    with pytest.raises(P.StagingError):
        P.stage_plan(skill, "en")


def test_alias_skills_without_chinese_source_fail_loudly():
    with pytest.raises(P.StagingError):
        P.stage_plan("jj-desc", "zh")


def test_sample_metadata_records_condition_without_verdict():
    for condition in P.CONDITIONS:
        sample = load_samples("refactor-ui", 1, condition)[0]
        assert sample.metadata["condition"] == condition
        assert "staged_correctly" not in sample.metadata
    assert load_samples("refactor-ui", 1, "none")[0].metadata["skill_document"] is None
    assert load_samples("refactor-ui", 1, "zh")[0].metadata["skill_document"] == SANDBOX_SKILL_MD


def test_missing_case_id_fails_loudly():
    with pytest.raises(ValueError):
        load_case("refactor-ui", 999)


def test_existing_case_file_is_untouched_by_loading():
    path = P.skill_dir("refactor-ui") / "evals" / "evals.json"
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    load_samples("refactor-ui", 1, "en")
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


def test_compose_creates_the_workdir_for_every_arm():
    """`none` has no fixtures, so the container itself must create the cwd."""
    compose = (REPO_ROOT / "evals" / "compose.yaml").read_text(encoding="utf-8")
    assert SANDBOX_WORKDIR in compose, "compose must guarantee the tool working directory"
    assert "mkdir -p" in compose


def test_smoke_probe_path_is_absolute_and_matches_its_prompt():
    """Regression: relative `Sample.files` keys resolve against the container cwd.

    The provider writes relative keys under `/`, not under the tool workdir, so a
    `probe.txt` key would land at `/probe.txt` while the prompt asked for
    `/skill/probe.txt` and the assertion read the wrong place.

    Constructing the Task would initialise the model client, so this checks the
    task source instead of instantiating it — the suite stays credential-free.
    """
    from evals.smoke import PROBE_CONTENT, PROBE_PATH

    assert PROBE_PATH.startswith(f"{SANDBOX_WORKDIR}/"), "staged key must be absolute"

    source = (REPO_ROOT / "evals" / "smoke.py").read_text(encoding="utf-8")
    assert "files={PROBE_PATH: PROBE_CONTENT}" in source, "sample must stage PROBE_PATH"
    assert "call read_file on " in source and "{PROBE_PATH}" in source, (
        "prompt must name the same path the sample stages"
    )
    assert PROBE_CONTENT.strip() == "wiring-probe"


def test_behaviour_samples_stage_absolute_sandbox_paths_only():
    """Same class of bug for the behaviour runner, across all conditions."""
    for condition in P.CONDITIONS:
        sample = load_samples("frontend-slides", 11, condition)[0]
        for sandbox_path in sample.files:
            assert sandbox_path.startswith("/"), (
                f"{condition} stages a relative key {sandbox_path!r}, "
                "which the provider would write outside the workdir"
            )
