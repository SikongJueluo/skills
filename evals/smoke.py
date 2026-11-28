"""Wiring smoke task — NOT a behavior case.

Proves the chain end to end with one tiny sample: the Podman sandbox starts, a
file staged through `Sample.files` is readable inside it, `sandbox().exec` runs,
and a model reply comes back. It scores only those wiring facts, so it never
claims anything about Skill behavior. The behavior runner lives in
`evals/task.py` and deliberately produces no verdict.

    uv run --locked inspect eval evals/smoke.py --log-dir evals/.cache/logs
"""

from __future__ import annotations

import sys
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import ChatMessageTool, GenerateConfig
from inspect_ai.scorer import Score, Target, accuracy, scorer
from inspect_ai.solver import TaskState, generate, use_tools

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals.tools import SANDBOX_WORKDIR, bash, skill_tools  # noqa: E402

COMPOSE_FILE = Path(__file__).resolve().parent / "compose.yaml"

PROBE_CONTENT = "wiring-probe\n"
# Absolute, because the provider resolves relative `Sample.files` keys against
# the container working directory (which is `/` for this image).
PROBE_PATH = f"{SANDBOX_WORKDIR}/probe.txt"
PROBE_PROMPT = (
    "Call the bash tool once to run `pwd`, then call read_file on "
    f"{PROBE_PATH} and reply with the working directory and the file contents."
)


@scorer(metrics=[accuracy()])
def wiring_ok():
    """1.0 only when the sandbox actually ran and served a staged file."""

    async def score(state: TaskState, target: Target) -> Score:
        tool_calls = [
            message
            for message in state.messages
            if isinstance(message, ChatMessageTool)
        ]
        succeeded = {call.function for call in tool_calls if call.error is None}
        bash_pwd = next(
            (
                call
                for call in tool_calls
                if call.function == "bash" and call.error is None
            ),
            None,
        )
        read_probe = next(
            (
                call
                for call in tool_calls
                if call.function == "read_file"
                and call.error is None
                and PROBE_CONTENT.strip() in str(call.content)
            ),
            None,
        )

        checks = {
            "model_responded": bool((state.output.completion or "").strip()),
            "sandbox_exec_ran": bash_pwd is not None,
            "staged_file_read": read_probe is not None,
            "tools_succeeded": sorted(succeeded),
        }
        passed = all(
            checks[key] for key in ("model_responded", "sandbox_exec_ran", "staged_file_read")
        )

        return Score(
            value=1.0 if passed else 0.0,
            answer=state.output.completion or "",
            explanation=(
                "wiring "
                + ("ok" if passed else "FAILED")
                + f"; sandbox exec={checks['sandbox_exec_ran']}, "
                f"staged read={checks['staged_file_read']}, "
                f"model reply={checks['model_responded']} — behavior not assessed"
            ),
            metadata=checks,
        )

    return score


@task
def wiring_smoke(model_id: str = "deepseek-flash") -> Task:
    """One sample that exercises sandbox start, exec, staged read and a reply."""
    return Task(
        dataset=[
            Sample(
                id="wiring",
                input=PROBE_PROMPT,
                target=PROBE_CONTENT.strip(),
                files={PROBE_PATH: PROBE_CONTENT},
            )
        ],
        solver=[use_tools(skill_tools()), generate()],
        scorer=wiring_ok(),
        sandbox=("podman", str(COMPOSE_FILE)),
        model=f"deepseek/{model_id}",
        config=GenerateConfig(temperature=0),
        message_limit=6,
    )
