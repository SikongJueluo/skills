"""Tools that reach into the sandbox, and the guidance shared by all conditions.

Every tool here goes through `sandbox()`, so nothing in this module can run on
the host. The model request, the solver loop and scoring stay outside.
"""

from __future__ import annotations

from inspect_ai.tool import Tool, ToolError, tool
from inspect_ai.util import sandbox

# The one directory every condition works in. `evals/compose.yaml` creates it
# before the container idles, so `none` has it too.
SANDBOX_WORKDIR = "/skill"
SANDBOX_SKILL_MD = f"{SANDBOX_WORKDIR}/SKILL.md"

# Deliberately condition-agnostic: whether a skill document exists is stated in
# the same words for every arm, and the staged text itself is inserted ahead of
# it by `evals/loader.py` when the condition provides one.
SYSTEM_PROMPT = (
    "You are working in a Linux container. Relative paths in the request are "
    f"relative to {SANDBOX_WORKDIR}. "
    "Answer the user's request directly."
)


@tool
def read_file() -> Tool:
    async def execute(path: str) -> str:
        """Read a file inside the sandbox.

        Args:
            path: Path of the file to read; relative paths resolve to the workdir.

        Returns:
            The contents of the file.
        """
        target = path if path.startswith("/") else f"{SANDBOX_WORKDIR}/{path}"
        try:
            return await sandbox().read_file(target)
        except FileNotFoundError as ex:
            raise ToolError(f"no file at {target}: {ex}") from ex

    return execute


@tool
def bash() -> Tool:
    async def execute(command: str, timeout: int = 60) -> str:
        """Run a shell command inside the sandbox.

        Args:
            command: Shell command to run.
            timeout: Seconds before the command is abandoned.

        Returns:
            Combined stdout and stderr of the command.
        """
        result = await sandbox().exec(
            ["sh", "-c", command], cwd=SANDBOX_WORKDIR, timeout=timeout
        )
        output = (result.stdout + result.stderr).strip()
        if not result.success:
            raise ToolError(f"command exited {result.returncode}:\n{output}")
        return output

    return execute


def skill_tools() -> list[Tool]:
    """The same tools in every arm, so only staged text differs."""
    return [read_file(), bash()]
