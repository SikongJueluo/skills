"""Inspect tasks for the refactor-ui dashboard pilot and its model-free smoke."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path
from tempfile import mkdtemp

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import GenerateConfig, Model, get_model
from inspect_ai.model._generate_config import active_generate_config
from inspect_ai.scorer import Score, Target, accuracy, scorer
from inspect_ai.solver import Generate, TaskState, generate, solver, use_tools
from inspect_ai.util import sandbox

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals.cases import load_case, to_sample  # noqa: E402
from evals.loader import load_staged_skill  # noqa: E402
from evals.packages import REPO_ROOT, sandbox_path  # noqa: E402
from evals.tools import skill_tools  # noqa: E402

SKILL = "refactor-ui"
CASE_ID = 6
CONDITIONS = ("none", "zh", "en")
ROUNDS = (("none", "zh", "en"), ("zh", "en", "none"), ("en", "none", "zh"))
MODEL_ID = "deepseek-flash"
API_URL = "https://api.deepseek.com"
MODEL_CONFIG = GenerateConfig(
    temperature=0,
    max_retries=2,
    attempt_timeout=120,
    max_connections=1,
    adaptive_connections=False,
)
MESSAGE_LIMIT = 24
PROTOCOL_ENDPOINT = API_URL.rstrip("/")
PROTOCOL_CONFIG = MODEL_CONFIG.model_dump(exclude_none=True)
COMPOSE = Path(__file__).with_name("visual_compose.yaml")
ARTIFACT_ROOT = REPO_ROOT / "evals/.cache/visual"
OUTPUT = "/skill/output.html"
ARTIFACT_REQUEST = (
    "\n\nEdit the supplied dashboard and write the final page to `/skill/output.html`. "
    "Deliver a single self-contained HTML file (inline CSS and scripts; no external assets "
    "or network dependencies). The input page is `{fixture}`. "
    "The final page will be opened at a 1440×1100 desktop viewport."
)


def _run_id(value: str, condition: str, replicate: int) -> str:
    if not value:
        if condition != "all" or replicate:
            raise ValueError("run_id is required when selecting a subset of a run")
        return uuid.uuid4().hex
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise ValueError("run_id must be 1–64 letters, digits, hyphens or underscores")
    return value


def _protocol_digest(samples: list[Sample], model_id: str) -> str:
    protocol = {
        "model": f"deepseek/{model_id}",
        "base_url": API_URL,
        "config": PROTOCOL_CONFIG,
        "message_limit": MESSAGE_LIMIT,
        "inputs": [
            (sample.id, sample.input, {
                target: hashlib.sha256(Path(source).read_bytes()).hexdigest()
                for target, source in sample.files.items()
            })
            for sample in samples
        ],
        "harness": {
            filename: hashlib.sha256((REPO_ROOT / filename).read_bytes()).hexdigest()
            for filename in (
                "evals/visual.py", "evals/visual_compose.yaml", "evals/browser_runner.py",
                "evals/browser/Dockerfile", "evals/tools.py", "evals/loader.py", "uv.lock",
            )
        },
    }
    return hashlib.sha256(json.dumps(protocol, sort_keys=True).encode()).hexdigest()


def pilot_samples(
    run_id: str,
    model_id: str,
    *,
    condition: str = "all",
    replicate: int = 0,
) -> list[Sample]:
    if condition not in ("all", *CONDITIONS):
        raise ValueError(f"condition must be 'all' or one of {', '.join(CONDITIONS)}")
    if not 0 <= replicate <= 3:
        raise ValueError("replicate must be 0 (all) or 1–3")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", model_id):
        raise ValueError("model_id must be one bare DeepSeek model name")
    run_id = _run_id(run_id, condition, replicate)

    case = load_case(SKILL, CASE_ID)
    (fixture,) = case["files"]
    samples = []
    for round_number, order in enumerate(ROUNDS, start=1):
        for selected_condition in order:
            sample = to_sample(SKILL, case, selected_condition)
            sample.id = f"{round_number}-{selected_condition}"
            sample.input = case["prompt"] + ARTIFACT_REQUEST.format(fixture=fixture)
            sample.metadata.update(
                run_id=run_id,
                replicate=round_number,
                model_id=model_id,
                baseline_path=sample.files[sandbox_path(fixture)],
            )
            samples.append(sample)

    digest = _protocol_digest(samples, model_id)
    for sample in samples:
        sample.metadata["protocol_digest"] = digest
    return [
        sample for sample in samples
        if (condition == "all" or sample.metadata["condition"] == condition)
        and (not replicate or sample.metadata["replicate"] == replicate)
    ]


def _protocol_problems(
    model: Model, model_id: str, message_limit: int | None
) -> list[str]:
    """Describe every way the resolved run differs from the declared digest."""
    problems = []
    expected_model = f"deepseek/{model_id}"
    if str(model) != expected_model:
        problems.append(f"model is {model}, not {expected_model}")
    endpoint = (model.api.base_url or "").rstrip("/")
    if endpoint != PROTOCOL_ENDPOINT:
        problems.append(f"endpoint must be {PROTOCOL_ENDPOINT}")
    if model.model_args:
        problems.append("model args are outside the protocol")
    effective = model.config.merge(active_generate_config()).model_dump(exclude_none=True)
    if effective != PROTOCOL_CONFIG:
        problems.append("generation config differs from the pilot defaults")
    if message_limit != MESSAGE_LIMIT:
        problems.append(f"message limit is {message_limit}, not {MESSAGE_LIMIT}")
    return problems


@solver
def protocol_guard():
    """Stop the sample before generation when the effective protocol was overridden."""

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        problems = _protocol_problems(
            get_model(), state.metadata["model_id"], state.message_limit
        )
        if problems:
            raise ValueError(
                "the visual pilot protocol was overridden: " + "; ".join(problems)
            )
        return state

    return solve


@scorer(metrics=[accuracy()])
def visual_gate(reviewable: bool = True):
    async def score(state: TaskState, target: Target) -> Score:
        metadata = state.metadata
        try:
            candidate = await sandbox().read_file(OUTPUT, text=False)
        except (FileNotFoundError, IsADirectoryError, PermissionError):
            candidate = None

        verifier = sandbox("verifier")
        await verifier.write_file(
            "/input/baseline.html", Path(metadata["baseline_path"]).read_bytes()
        )
        if candidate is not None:
            await verifier.write_file("/input/candidate.html", candidate)
        check = await verifier.exec(
            [
                "python", "/opt/ui-eval/browser_runner.py",
                "--baseline", "/input/baseline.html",
                "--candidate", "/input/candidate.html",
                "--output-dir", "/output",
            ],
            timeout=75,
            timeout_retry=False,
        )
        if not check.success:
            raise RuntimeError(f"visual verifier exited {check.returncode}: {check.stderr}")
        gate_text = await verifier.read_file("/output/gate.json")
        gate = json.loads(gate_text)
        passed = gate["passed"]
        if type(passed) is not bool:
            raise ValueError("visual verifier must return a boolean 'passed'")

        run_dir = ARTIFACT_ROOT / metadata["run_id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        artifact_dir = Path(mkdtemp(prefix="cell-", dir=run_dir))
        (artifact_dir / "baseline.png").write_bytes(
            await verifier.read_file("/output/baseline.png", text=False)
        )
        (artifact_dir / "gate.json").write_text(gate_text, encoding="utf-8")
        if passed:
            (artifact_dir / "final.png").write_bytes(
                await verifier.read_file("/output/final.png", text=False)
            )
            if candidate is None:
                raise AssertionError("a passing candidate must exist")
        if candidate is not None:
            (artifact_dir / "final.html").write_bytes(candidate)

        evidence = {
            **{key: metadata[key] for key in (
                "run_id", "skill", "case_id", "condition", "replicate", "protocol_digest", "model_id",
            )},
            "hard_gate_passed": passed,
            "hard_gate": gate,
            "artifact_dir": str(artifact_dir),
        }
        return Score(
            value=float(passed),
            explanation="Automatic artifact gate only; visual preference requires blind review.",
            metadata={"visual_eval" if reviewable else "visual_smoke": evidence},
        )

    return score


@task
def visual_case(
    run_id: str = "",
    model_id: str = MODEL_ID,
    condition: str = "all",
    replicate: int = 0,
) -> Task:
    """Run case 6 in matched arms; the score is not an aesthetic rating.

    Inspect retries transient request failures up to `max_retries=2` (three
    attempts total) and does not retry permanent 4xx/config errors. Either way
    the resulting sample error aborts the remaining serial batch instead of
    sending more requests; sample-level retries stay off, so a failed cell is
    refilled later with the same run ID and protocol.
    """
    if os.getenv("DEEPSEEK_BASE_URL", API_URL).rstrip("/") != API_URL:
        raise ValueError("the visual pilot requires the official DeepSeek endpoint")
    return Task(
        dataset=pilot_samples(
            run_id, model_id, condition=condition, replicate=replicate
        ),
        # setup always runs, including when a CLI --solver replaces the solver
        setup=protocol_guard(),
        solver=[load_staged_skill(), use_tools(skill_tools()), generate()],
        scorer=visual_gate(),
        sandbox=("podman", str(COMPOSE)),
        model=f"deepseek/{model_id}",
        config=MODEL_CONFIG,
        message_limit=MESSAGE_LIMIT,
        max_samples=1,
        fail_on_error=True,
    )


@solver
def copy_baseline():
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        await sandbox().write_file(
            OUTPUT, Path(state.metadata["baseline_path"]).read_bytes()
        )
        return state

    return solve


@task
def visual_wiring_smoke(run_id: str = "wiring") -> Task:
    """Exercise the real browser verifier without making a model API call."""
    return Task(
        dataset=pilot_samples(run_id, MODEL_ID)[:1],
        solver=copy_baseline(),
        scorer=visual_gate(reviewable=False),
        sandbox=("podman", str(COMPOSE)),
    )
