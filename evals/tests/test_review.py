from __future__ import annotations

import base64
import http.client
import json
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from inspect_ai.log import EvalConfig, EvalDataset, EvalLog, EvalSample, EvalSpec, read_eval_log
from inspect_ai.scorer import Score

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evals.review import Review, make_server, prepare  # noqa: E402

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jKeQAAAAASUVORK5CYII="
)
PROMPT = "Simplify this dashboard without removing its content."


@pytest.fixture
def log_samples(tmp_path):
    samples = []
    for replicate in range(1, 4):
        for condition in ("none", "zh", "en"):
            artifact = tmp_path / f"artifact-{replicate}-{condition}"
            artifact.mkdir()
            (artifact / "baseline.png").write_bytes(PNG)
            (artifact / "final.png").write_bytes(PNG)
            (artifact / "gate.json").write_text(json.dumps({"passed": True, "checks": []}))
            (artifact / "final.html").write_text("<script>never serve me</script>")
            metadata = {
                "run_id": "unit-run", "skill": "refactor-ui", "case_id": 6,
                "condition": condition, "replicate": replicate, "protocol_digest": "same-digest",
                "model_id": "deepseek-flash", "hard_gate_passed": True, "artifact_dir": str(artifact),
            }
            samples.append(EvalSample(id=f"{replicate}-{condition}", epoch=1, input=PROMPT,
                                      target="", scores={"visual_gate": Score(
                                          value=1, metadata={"visual_eval": metadata})}))
    return samples


def write_log(path, samples, model="deepseek/deepseek-flash"):
    log = EvalLog(eval=EvalSpec(created="2026-11-25T00:00:00Z", task="offline",
                               dataset=EvalDataset(), model=model, config=EvalConfig()),
                  samples=samples)
    path.write_text(log.model_dump_json())
    return path


def metadata(sample):
    return sample.scores["visual_gate"].metadata["visual_eval"]


def fail(sample):
    cell = metadata(sample)
    cell["hard_gate_passed"] = False
    sample.scores["visual_gate"].value = 0
    artifact = Path(cell["artifact_dir"])
    (artifact / "final.png").unlink()
    (artifact / "gate.json").write_text(json.dumps({"passed": False, "reason": "missing output"}))


def complete(review, en_losses=0):
    for pair in review.bundle["pairs"]:
        cells = review.bundle["cells"]
        sides = {side: cells[pair[side]]["condition"] for side in ("A", "B")}
        choice = "tie"
        if set(sides.values()) == {"en", "zh"} and en_losses:
            choice = next(side for side, condition in sides.items() if condition == "zh")
            en_losses -= 1
        review.judge(pair["id"], choice, "offline reason")
    return review.state()["summary"]


def test_prepare_reads_real_inspect_logs_and_builds_all_matched_pairs(tmp_path, log_samples):
    first = write_log(tmp_path / "first.json", log_samples[:4])
    second = write_log(tmp_path / "second.json", log_samples[4:])
    assert len(read_eval_log(first).samples) == 4
    bundle = prepare("unit-run", [first, second], tmp_path / "review")
    assert len(bundle["cells"]) == len(bundle["pairs"]) == 9
    seen = set()
    for pair in bundle["pairs"]:
        a, b = (bundle["cells"][pair[side]] for side in ("A", "B"))
        assert a["replicate"] == b["replicate"]
        seen.add((a["replicate"], frozenset((a["condition"], b["condition"]))))
        assert len(pair["id"]) == 32
    assert len(seen) == 9
    images = list((tmp_path / "review/images").iterdir())
    assert len(images) == 18
    assert all(len(image.stem) == 32 and image.suffix == ".png" for image in images)
    assert not list((tmp_path / "review").rglob("*.html"))
    other = prepare("unit-run", [first, second], tmp_path / "other")
    assert set(bundle["cells"]).isdisjoint(other["cells"])
    assert {pair["id"] for pair in bundle["pairs"]}.isdisjoint(pair["id"] for pair in other["pairs"])


@pytest.mark.parametrize("problem", ["missing", "duplicate", "digest", "case", "prompt", "replicate", "key", "model"])
def test_incomplete_or_unmatched_runs_rejected_before_writing(tmp_path, log_samples, problem):
    if problem == "missing":
        log_samples.pop()
    elif problem == "duplicate":
        log_samples.append(log_samples[0])
    elif problem == "digest":
        metadata(log_samples[-1])["protocol_digest"] = "different"
    elif problem == "case":
        metadata(log_samples[-1])["case_id"] = 7
    elif problem == "prompt":
        log_samples[-1].input = "different prompt"
    elif problem == "replicate":
        metadata(log_samples[-1])["replicate"] = True
    elif problem == "model":
        metadata(log_samples[-1])["model_id"] = "different"
    else:
        del metadata(log_samples[-1])["artifact_dir"]
    log = write_log(tmp_path / "log.json", log_samples)
    with pytest.raises(ValueError):
        prepare("unit-run", [log], tmp_path / "review")
    assert not (tmp_path / "review").exists()


@pytest.mark.parametrize("model", ["openai/deepseek-flash", "deepseek/different", "deepseek-flash"])
def test_recorded_log_model_cannot_override_metadata(tmp_path, log_samples, model):
    log = write_log(tmp_path / "log.json", log_samples, model=model)
    with pytest.raises(ValueError, match="model"):
        prepare("unit-run", [log], tmp_path / "review")


def test_other_uniform_deepseek_models_allowed_but_not_mixed_runs(tmp_path, log_samples):
    for sample in log_samples[3:]:
        metadata(sample)["model_id"] = "deepseek-other"
    first = write_log(tmp_path / "first.json", log_samples[:3])
    second = write_log(tmp_path / "second.json", log_samples[3:], model="deepseek/deepseek-other")
    with pytest.raises(ValueError, match="model_id"):
        prepare("unit-run", [first, second], tmp_path / "review")
    for sample in log_samples[:3]:
        metadata(sample)["model_id"] = "deepseek-other"
    first = write_log(first, log_samples[:3], model="deepseek/deepseek-other")
    assert prepare("unit-run", [first, second], tmp_path / "review")["model_id"] == "deepseek-other"


def test_failed_gate_is_a_present_cell_not_a_missing_sample(tmp_path, log_samples):
    fail(log_samples[-1])
    log = write_log(tmp_path / "log.json", log_samples)
    bundle = prepare("unit-run", [log], tmp_path / "review")
    assert len(bundle["cells"]) == 9
    assert len(bundle["pairs"]) == 7
    failed = next(cell for cell in bundle["cells"].values() if not cell["passed"])
    assert "final" not in failed
    assert all(failed["id"] not in (pair["A"], pair["B"]) for pair in bundle["pairs"])
    summary = complete(Review(tmp_path / "review"))
    assert summary["hard_failures"] == [{"condition": "en", "replicate": 3,
                                          "gate": {"passed": False, "reason": "missing output"}}]
    assert sum(summary["comparisons"]["en vs zh"].values()) == 2
    assert summary["en_vs_zh_pilot_signal"] is False


@pytest.mark.parametrize("problem", ["baseline", "pass-final", "gate", "mismatch", "not-png"])
def test_required_artifacts_and_gate_consistency(tmp_path, log_samples, problem):
    artifact = Path(metadata(log_samples[0])["artifact_dir"])
    if problem in ("baseline", "pass-final", "gate"):
        filename = {"baseline": "baseline.png", "pass-final": "final.png", "gate": "gate.json"}[problem]
        (artifact / filename).unlink()
    elif problem == "mismatch":
        (artifact / "gate.json").write_text('{"passed":false}')
    else:
        (artifact / "final.png").write_text("<html>not an image</html>")
    log = write_log(tmp_path / "log.json", log_samples)
    with pytest.raises((ValueError, FileNotFoundError)):
        prepare("unit-run", [log], tmp_path / "review")


@pytest.mark.parametrize("losses,signal", [(0, True), (1, True), (2, False), (3, False)])
def test_pilot_signal_is_only_three_comparisons_and_at_most_one_loss(tmp_path, log_samples, losses, signal):
    log = write_log(tmp_path / "log.json", log_samples)
    prepare("unit-run", [log], tmp_path / "review")
    summary = complete(Review(tmp_path / "review"), losses)
    assert summary["en_vs_zh_pilot_signal"] is signal
    assert summary["comparisons"]["en vs zh"] == {"wins": 0, "ties": 3 - losses, "losses": losses}


def test_control_hard_failure_does_not_remove_en_zh_comparisons(tmp_path, log_samples):
    fail(log_samples[0])
    log = write_log(tmp_path / "log.json", log_samples)
    prepare("unit-run", [log], tmp_path / "review")
    review = Review(tmp_path / "review")
    for pair in review.bundle["pairs"]:
        en_side = next((side for side in ("A", "B")
                        if review.bundle["cells"][pair[side]]["condition"] == "en"), "tie")
        review.judge(pair["id"], en_side)
    summary = review.state()["summary"]
    assert summary["en_vs_zh_pilot_signal"] is True
    assert summary["comparisons"]["en vs zh"] == {"wins": 3, "ties": 0, "losses": 0}
    assert len(summary["hard_failures"]) == 1


def test_failed_persistence_does_not_advance_in_memory(tmp_path, log_samples, monkeypatch):
    log = write_log(tmp_path / "log.json", log_samples)
    prepare("unit-run", [log], tmp_path / "review")
    review = Review(tmp_path / "review")
    before = review.state()

    def reject_replace(*args):
        raise OSError("disk unavailable")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "replace", reject_replace)
        with pytest.raises(OSError, match="disk unavailable"):
            review.judge(before["pair"]["id"], "tie")
    assert review.state() == before
    assert Review(tmp_path / "review").state() == before


def test_all_failed_cells_complete_without_inventing_comparisons(tmp_path, log_samples):
    for sample in log_samples:
        fail(sample)
    log = write_log(tmp_path / "log.json", log_samples)
    prepare("unit-run", [log], tmp_path / "review")
    state = Review(tmp_path / "review").state()
    assert state["complete"] and state["total"] == 0
    assert len(state["summary"]["hard_failures"]) == 9
    assert not state["summary"]["en_vs_zh_pilot_signal"]


class RunningServer:
    def __init__(self, directory):
        self.server = make_server(directory, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()

    def request(self, path, body=None, headers=None):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        connection.request("GET" if body is None else "POST", path, body,
                           headers=headers or {"Content-Type": "application/json"})
        response = connection.getresponse()
        result = response.status, response.read()
        connection.close()
        return result

    def state(self):
        status, content = self.request("/state")
        assert status == 200
        return json.loads(content)


def test_server_blinds_restricts_routes_and_persists_across_restarts(tmp_path, log_samples):
    log = write_log(tmp_path / "log.json", log_samples)
    directory = tmp_path / "review"
    prepare("unit-run", [log], directory)
    with RunningServer(directory) as server:
        assert server.server.server_address[0] == "127.0.0.1"
        state = server.state()
        assert set(state) == {"complete", "completed", "total", "pair"}
        assert set(state["pair"]) == {"id", "prompt", "baseline", "A", "B"}
        assert state["pair"]["prompt"] == PROMPT
        for secret in (b"unit-run", b"refactor-ui", b"replicate", b"condition", b"same-digest", b"artifact-", b"deepseek-flash"):
            assert secret not in json.dumps(state).encode()
        status, template = server.request("/")
        assert status == 200
        assert all(criterion in template for criterion in (
            b"all twelve metrics", b"event table", b"three daily filters", b"New incident",
            b"grouping, hierarchy", b"faster to scan", b"Do not delete data"))
        assert server.request(state["pair"]["A"]) == (200, PNG)
        for path in ("/private.json", "/judgments.json", "/final.html", "/images/../private.json",
                     "/images/baseline.png", "/images/final.html", "/reveal", "/%2e%2e/private.json"):
            assert server.request(path)[0] == 404
        assert server.request("/state", headers={"Host": "attacker.example"})[0] == 403
        vote = json.dumps({"id": state["pair"]["id"], "choice": "A", "reason": "readable"})
        assert server.request("/judge", vote, {"Content-Type": "application/json", "Origin": "https://evil.example"})[0] == 403
        assert server.request("/judge", '{"id":"wrong","choice":"A"}')[0] == 400
        assert server.request("/judge", vote)[0] == 200
        assert server.request("/judge", vote)[0] == 400
        resumed_pair = server.state()["pair"]
    with RunningServer(directory) as restarted:
        state = restarted.state()
        assert state["completed"] == 1
        assert state["pair"] == resumed_pair
        assert "summary" not in state
        while not state["complete"]:
            status, content = restarted.request("/judge", json.dumps({"id": state["pair"]["id"], "choice": "tie"}))
            assert status == 200
            state = json.loads(content)
        assert state["summary"]["run_id"] == "unit-run"
        assert len(state["summary"]["judgments"]) == 9
        assert sum(sum(counts.values()) for counts in state["summary"]["comparisons"].values()) == 9
    assert Review(directory).state() == state
    votes = json.loads((directory / "judgments.json").read_text())
    assert len(votes) == 9
    assert any(vote["reason"] == "readable" for vote in votes.values())


def test_cli_accepts_multiple_logs_offline(tmp_path, log_samples):
    first = write_log(tmp_path / "first.json", log_samples[:3])
    second = write_log(tmp_path / "second.json", log_samples[3:])
    output = subprocess.run([sys.executable, "-m", "evals.review", "prepare", "--run-id", "unit-run",
                             "--log", str(first), "--log", str(second), "--out-dir", str(tmp_path / "review")],
                            cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
    assert output.returncode == 0, output.stderr
    assert "Prepared 9 blind pairs" in output.stdout
