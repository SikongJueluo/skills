from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx
import openai
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from inspect_ai.model import GenerateConfig, get_model  # noqa: E402
from inspect_ai.model._model import init_active_model  # noqa: E402
from inspect_ai.solver import TaskState  # noqa: E402

from evals.visual import (  # noqa: E402
    MESSAGE_LIMIT,
    MODEL_CONFIG,
    pilot_samples,
    protocol_guard,
    visual_case,
)

OFFICIAL = "https://api.deepseek.com"


@pytest.fixture(autouse=True)
def _deepseek_credentials(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-offline-test")
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)


def _model(**kwargs):
    return get_model("deepseek/deepseek-flash", config=GenerateConfig(), **kwargs, memoize=False)


def _activate(model, config=MODEL_CONFIG):
    init_active_model(model, config)


def _state(model_id="deepseek-flash", message_limit=MESSAGE_LIMIT):
    return TaskState(
        model=f"deepseek/{model_id}",
        sample_id="1-none",
        epoch=1,
        input="prompt",
        messages=[],
        message_limit=message_limit,
        metadata={"model_id": model_id},
    )


def _guard(model_id="deepseek-flash", message_limit=MESSAGE_LIMIT):
    asyncio.run(protocol_guard()(_state(model_id, message_limit), None))


def test_pilot_samples_are_nine_matched_cells_with_balanced_condition_order():
    samples = pilot_samples("unit-run", "deepseek-flash")

    assert len(samples) == 9
    assert [sample.metadata["condition"] for sample in samples] == [
        "none", "zh", "en", "zh", "en", "none", "en", "none", "zh"
    ]
    assert {(sample.metadata["replicate"], sample.metadata["condition"]) for sample in samples} == {
        (replicate, condition)
        for replicate in range(1, 4)
        for condition in ("none", "zh", "en")
    }
    assert {sample.metadata["protocol_digest"] for sample in samples}.__len__() == 1
    assert all(sample.input.endswith("1440×1100 desktop viewport.") for sample in samples)
    assert all(sample.input.startswith("Our operations dashboard is too busy.") for sample in samples)


def test_pilot_samples_can_select_only_a_missing_cell_without_changing_protocol():
    all_samples = pilot_samples("unit-run", "deepseek-flash")
    missing = pilot_samples("unit-run", "deepseek-flash", condition="en", replicate=2)

    assert len(missing) == 1
    assert missing[0].metadata["condition"] == "en"
    assert missing[0].metadata["replicate"] == 2
    assert missing[0].metadata["protocol_digest"] == all_samples[0].metadata["protocol_digest"]


def test_subset_requires_the_original_run_id():
    with pytest.raises(ValueError, match="run_id"):
        pilot_samples("", "deepseek-flash", condition="en", replicate=2)


def test_model_request_retry_budget_is_three_attempts_and_no_sample_retry():
    assert MODEL_CONFIG.max_retries == 2
    assert MODEL_CONFIG.temperature == 0


def test_provider_retries_only_transient_request_failures():
    model = _model()
    request = httpx.Request("POST", f"{OFFICIAL}/chat/completions")

    def status(code):
        return openai.APIStatusError(
            "boom", response=httpx.Response(code, request=request), body={"error": {"message": "boom"}}
        )

    for code in (400, 401, 402, 403, 404):
        assert model.api.should_retry(status(code)).retry is False
    for code in (429, 500, 503):
        assert model.api.should_retry(status(code)).retry is True
    assert model.api.should_retry(openai.APIConnectionError(request=request)).retry is True
    assert model.api.should_retry(openai.APITimeoutError(request=request)).retry is True


def test_invalid_run_ids_and_cells_fail_before_eval():
    with pytest.raises(ValueError, match="run_id"):
        pilot_samples("../escape", "deepseek-flash")
    with pytest.raises(ValueError, match="condition"):
        pilot_samples("unit-run", "deepseek-flash", condition="es")
    with pytest.raises(ValueError, match="replicate"):
        pilot_samples("unit-run", "deepseek-flash", condition="en", replicate=4)
    with pytest.raises(ValueError, match="model_id"):
        pilot_samples("unit-run", "deepseek/flash")


def test_protocol_guard_accepts_the_declared_run():
    _activate(_model())
    _guard()


def test_protocol_guard_accepts_the_official_endpoint_spelled_with_a_slash(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_BASE_URL", OFFICIAL + "/")
    _activate(_model())
    _guard()


def test_protocol_guard_rejects_an_endpoint_override():
    _activate(_model(base_url="https://api.deepseek.example"))
    with pytest.raises(ValueError, match="endpoint"):
        _guard()


def test_protocol_guard_rejects_a_generation_config_override():
    _activate(_model(), MODEL_CONFIG.merge(GenerateConfig(temperature=0.7)))
    with pytest.raises(ValueError, match="generation config"):
        _guard()


def test_protocol_guard_rejects_a_model_override():
    model = get_model(
        "deepseek/deepseek-reasoner", config=GenerateConfig(), memoize=False
    )
    _activate(model)
    with pytest.raises(ValueError, match="model is deepseek/deepseek-reasoner"):
        _guard()


def test_protocol_guard_rejects_model_args():
    _activate(_model(organization="org-test"))
    with pytest.raises(ValueError, match="model args"):
        _guard()


def test_protocol_guard_rejects_a_message_limit_override():
    _activate(_model())
    with pytest.raises(ValueError, match="message limit"):
        _guard(message_limit=MESSAGE_LIMIT + 1)


def test_visual_case_rejects_a_non_official_endpoint_environment(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.example")
    with pytest.raises(ValueError, match="official DeepSeek endpoint"):
        visual_case("unit-run")


def test_visual_case_freezes_protocol_and_fails_fast():
    task = visual_case("unit-run")

    assert task.fail_on_error is True
    assert task.max_samples == 1
    assert task.message_limit == MESSAGE_LIMIT
    assert task.config.model_dump(exclude_none=True) == MODEL_CONFIG.model_dump(exclude_none=True)
    assert callable(task.setup)


def test_visual_case_setup_guard_runs_before_generation():
    task = visual_case("unit-run")
    _activate(_model(base_url="https://api.deepseek.example"))

    with pytest.raises(ValueError, match="endpoint"):
        asyncio.run(task.setup(_state(), None))
