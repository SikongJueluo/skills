"""Load the staged skill document into the system prompt before generating.

The treatment must reach the model whether or not it chooses to call a tool, so
the document is read out of the sandbox with a privileged `exec`/`read_file` and
prepended to the system message. `none` simply finds nothing staged and adds no
document.

This runs on the host inside the solver loop; the bytes come from the container.
"""

from __future__ import annotations

from inspect_ai.model import ChatMessageSystem
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox

from evals.tools import SYSTEM_PROMPT

DOCUMENT_HEADER = "The skill document (`/skill/SKILL.md`) follows:"


async def staged_document(path: str | None) -> str | None:
    """Read the staged skill document, or None when this arm stages none."""
    if path is None:
        return None
    result = await sandbox().exec(["sh", "-c", f"cat {path}"], cwd="/skill")
    if not result.success:
        raise RuntimeError(f"condition declares {path} but it could not be read: {result.stderr}")
    return result.stdout


def compose_system_prompt(document: str | None) -> str:
    """Identical guidance in every arm; only the document block differs."""
    if document is None:
        return SYSTEM_PROMPT
    return f"{SYSTEM_PROMPT}\n\n{DOCUMENT_HEADER}\n\n{document}"


@solver
def load_staged_skill() -> Solver:
    """Put the staged skill text in the system message before the first turn."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        document = await staged_document(state.metadata.get("skill_document"))
        state.metadata["skill_document_chars"] = len(document or "")
        prompt = compose_system_prompt(document)
        state.messages = [
            message for message in state.messages if not isinstance(message, ChatMessageSystem)
        ]
        state.messages.insert(0, ChatMessageSystem(content=prompt))
        return state

    return solve
