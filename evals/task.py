"""Inspect task: one behavior case under an explicit `none`/`zh`/`en` condition.

Paired behavior runs — same case, same prompt, same tools, same model; only the
staged Skill text differs:

    inspect eval evals/task.py -T skill=refactor-ui -T case_id=1 -T condition=en
    inspect eval evals/task.py -T skill=refactor-ui -T case_id=1 -T condition=zh
    inspect eval evals/task.py -T skill=refactor-ui -T case_id=1 -T condition=none

Model requests use Inspect's built-in DeepSeek provider and stay on the host.
Only calls made through `sandbox()` enter the Podman container.
"""

from __future__ import annotations

import sys
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.model import ChatMessageTool, GenerateConfig
from inspect_ai.scorer import Score, Target, scorer
from inspect_ai.solver import TaskState, generate, use_tools

# Inspect loads a task file as a standalone module, so the repository root is not
# on sys.path and the `evals` package cannot be imported without this.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals.cases import load_samples  # noqa: E402
from evals.loader import load_staged_skill  # noqa: E402
from evals.packages import CONDITIONS, StagingError  # noqa: E402
from evals.tools import skill_tools  # noqa: E402

COMPOSE_FILE = Path(__file__).resolve().parent / "compose.yaml"


@scorer(metrics=[])
def wiring_transcript():
    """Wiring-only recorder. It does not decide how well the case was answered.

    Emits `Score.unscored`, so nothing here enters metrics or reducers. The
    case's `expectations`, `expected_output` and the tool-call list are carried
    for a human or an explicitly opted-in grader to rate later. No verdict is
    invented and no grader runs by default.
    """

    async def score(state: TaskState, target: Target) -> Score:
        tool_calls = [
            message for message in state.messages if isinstance(message, ChatMessageTool)
        ]
        return Score.unscored(
            reason="manual rubric",
            answer=state.output.completion or "",
            explanation=(
                f"condition={state.metadata.get('condition')}; "
                f"{len(tool_calls)} tool call(s). Wiring only — grade from expectations."
            ),
            metadata={
                "skill": state.metadata.get("skill"),
                "case_id": state.metadata.get("case_id"),
                "condition": state.metadata.get("condition"),
                "document_condition": state.metadata.get("condition"),
                "skill_document_chars": state.metadata.get("skill_document_chars", 0),
                "expectations": state.metadata.get("expectations", []),
                "expected_output": target.text,
                "tool_calls": [getattr(call, "function", None) for call in tool_calls],
            },
        )

    return score


@task
def skill_case(
    skill: str = "refactor-ui",
    case_id: int = 1,
    condition: str = "en",
    model_id: str = "deepseek-flash",
) -> Task:
    """One existing behavior case under one explicitly selected condition."""
    if condition not in CONDITIONS:
        raise StagingError(
            f"unknown condition {condition!r}; expected one of {', '.join(CONDITIONS)}"
        )

    return Task(
        dataset=load_samples(skill, case_id, condition),
        solver=[load_staged_skill(), use_tools(skill_tools()), generate()],
        scorer=wiring_transcript(),
        sandbox=("podman", str(COMPOSE_FILE)),
        model=f"deepseek/{model_id}",
        config=GenerateConfig(temperature=0),
        message_limit=20,
    )
