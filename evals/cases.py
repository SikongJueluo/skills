"""Load a skill's existing behavior case without rewriting it.

Cases live in `skills/<name>/evals/evals.json` in the schema those skills
already use:

    {"skill_name": str, "evals": [{"id": int, "prompt": str,
     "expected_output": str, "files": [...], "expectations": [str]}]}

This module only reads that schema. It never writes a case file, and it does not
depend on DeepSeek Harness. What actually gets staged into the sandbox is
decided by `evals/packages.py`.
"""

from __future__ import annotations

import json
from pathlib import Path

from inspect_ai.dataset import Sample

from evals.packages import (
    CONDITIONS,
    REPO_ROOT,
    SANDBOX_SKILL_MD,
    StagingError,
    fixture_plan,
    skill_dir,
    stage_plan,
)

SKILLS_ROOT = REPO_ROOT / "skills"


def case_file_for(skill: str) -> Path:
    return skill_dir(skill) / "evals" / "evals.json"


def discover_skills() -> list[str]:
    """Every skill that already ships a behavior-case file."""
    return sorted(path.parent.parent.name for path in SKILLS_ROOT.glob("*/evals/evals.json"))


def load_case(skill: str, case_id: int) -> dict:
    """The `evals.json` entry for one case id."""
    path = case_file_for(skill)
    if not path.is_file():
        available = ", ".join(discover_skills()) or "none"
        raise FileNotFoundError(
            f"{skill} has no behavior cases at {path} (skills with cases: {available})"
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    for entry in payload.get("evals") or []:
        if entry["id"] == case_id:
            return entry
    raise ValueError(f"{path} has no case with id={case_id!r}")


def to_sample(skill: str, entry: dict, condition: str) -> Sample:
    """One `evals.json` entry as an Inspect `Sample` for a given condition.

    `en`/`zh` stage the same package paths with different contents; `none`
    stages only the case fixtures.
    """
    if condition not in CONDITIONS:
        raise StagingError(f"unknown condition {condition!r}; expected one of {', '.join(CONDITIONS)}")

    files = {
        sandbox: str(host) for sandbox, host in stage_plan(skill, condition).items()
    } | {
        sandbox: str(host)
        for sandbox, host in fixture_plan(skill, list(entry.get("files") or [])).items()
    }

    return Sample(
        id=entry["id"],
        input=entry["prompt"],
        target=entry.get("expected_output", ""),
        files=files,
        metadata={
            "skill": skill,
            "case_id": entry["id"],
            "condition": condition,
            "skill_document": SANDBOX_SKILL_MD if condition != "none" else None,
            "case_file": str(case_file_for(skill)),
            "fixtures": list(entry.get("files") or []),
            "expectations": list(entry.get("expectations") or []),
        },
    )


def load_samples(skill: str, case_id: int, condition: str) -> list[Sample]:
    """Exactly one sample, so behavior runs stay paired and cheap."""
    return [to_sample(skill, load_case(skill, case_id), condition)]
