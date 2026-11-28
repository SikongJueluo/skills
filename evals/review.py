"""Offline, blinded pairwise review of one complete nine-cell visual pilot."""

from __future__ import annotations

import argparse
import itertools
import json
import random
import shutil
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

CONDITIONS = ("none", "zh", "en")
COMBINATIONS = (("zh", "none"), ("en", "none"), ("en", "zh"))
KEYS = {"run_id", "skill", "case_id", "condition", "replicate", "protocol_digest",
        "model_id", "hard_gate_passed", "artifact_dir"}


def prepare(run_id, logs, out_dir):
    from inspect_ai.log import read_eval_log

    cells = {}
    identity = None
    for log in logs:
        evaluation = read_eval_log(log)
        for sample in evaluation.samples or []:
            for score in (sample.scores or {}).values():
                metadata = (score.metadata or {}).get("visual_eval")
                if not metadata or metadata.get("run_id") != run_id:
                    continue
                if KEYS - metadata.keys():
                    raise ValueError(f"missing visual_eval keys: {KEYS - metadata.keys()}")
                condition, replicate = metadata["condition"], metadata["replicate"]
                if condition not in CONDITIONS or type(replicate) is not int or replicate not in range(1, 4):
                    raise ValueError("expected conditions none/zh/en and replicates 1..3")
                key = (replicate, condition)
                if key in cells:
                    raise ValueError(f"duplicate cell: {key}")
                if not isinstance(sample.input, str) or not metadata["protocol_digest"]:
                    raise ValueError("a text prompt and protocol_digest are required")
                model_id = metadata["model_id"]
                if not isinstance(model_id, str) or not model_id or "/" in model_id or evaluation.eval.model != f"deepseek/{model_id}":
                    raise ValueError("log model must match the bare DeepSeek model_id")
                current = (metadata["skill"], metadata["case_id"], metadata["protocol_digest"], sample.input, model_id)
                if identity is not None and current != identity:
                    raise ValueError("skill, case, protocol_digest, prompt and model_id must match")
                identity = current
                passed = metadata["hard_gate_passed"]
                artifact = Path(metadata["artifact_dir"])
                gate = json.loads((artifact / "gate.json").read_text(encoding="utf-8"))
                if type(passed) is not bool or type(gate.get("passed")) is not bool or gate["passed"] != passed:
                    raise ValueError(f"gate verdict mismatch: {key}")
                for filename in ("baseline.png", "final.png") if passed else ("baseline.png",):
                    with (artifact / filename).open("rb") as image:
                        if image.read(8) != b"\x89PNG\r\n\x1a\n":
                            raise ValueError(f"not a PNG: {artifact / filename}")
                cells[key] = {"id": uuid.uuid4().hex, "condition": condition,
                              "replicate": replicate, "passed": passed, "gate": gate,
                              "artifact": artifact}
    expected = set(itertools.product(range(1, 4), CONDITIONS))
    if cells.keys() != expected:
        raise ValueError(f"missing cells: {sorted(expected - cells.keys())}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True)
    images = out_dir / "images"
    images.mkdir()
    for cell in cells.values():
        artifact = cell.pop("artifact")
        if cell["passed"]:
            for kind in ("baseline", "final"):
                cell[kind] = uuid.uuid4().hex + ".png"
                shutil.copyfile(artifact / f"{kind}.png", images / cell[kind])
    pairs = []
    rng = random.SystemRandom()
    for replicate in range(1, 4):
        for left, right in COMBINATIONS:
            sides = [cells[replicate, left], cells[replicate, right]]
            if all(cell["passed"] for cell in sides):
                rng.shuffle(sides)
                pairs.append({"id": uuid.uuid4().hex, "A": sides[0]["id"], "B": sides[1]["id"]})
    rng.shuffle(pairs)
    skill, case_id, digest, prompt, model_id = identity
    bundle = {"run_id": run_id, "skill": skill, "case_id": case_id,
              "protocol_digest": digest, "prompt": prompt, "model_id": model_id,
              "cells": {cell["id"]: cell for cell in cells.values()}, "pairs": pairs}
    (out_dir / "private.json").write_text(json.dumps(bundle), encoding="utf-8")
    return bundle


class Review:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.bundle = json.loads((self.directory / "private.json").read_text(encoding="utf-8"))
        self.path = self.directory / "judgments.json"
        self.judgments = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        self.images = {cell[kind] for cell in self.bundle["cells"].values()
                       for kind in ("baseline", "final") if kind in cell}

    def state(self):
        pairs, cells = self.bundle["pairs"], self.bundle["cells"]
        pending = next((pair for pair in pairs if pair["id"] not in self.judgments), None)
        state = {"complete": pending is None, "completed": len(self.judgments), "total": len(pairs)}
        if pending is None:
            state["summary"] = self.summary()
        else:
            a, b = cells[pending["A"]], cells[pending["B"]]
            state["pair"] = {"id": pending["id"], "prompt": self.bundle["prompt"],
                             "baseline": "/images/" + a["baseline"],
                             "A": "/images/" + a["final"], "B": "/images/" + b["final"]}
        return state

    def judge(self, pair_id, choice, reason=""):
        pending = self.state().get("pair")
        if not pending or pair_id != pending["id"] or choice not in ("A", "B", "tie"):
            raise ValueError("choose A, B or tie for the current pair")
        if not isinstance(reason, str) or len(reason) > 2000:
            raise ValueError("reason must be text, at most 2000 characters")
        judgments = self.judgments | {pair_id: {"choice": choice, "reason": reason}}
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(judgments), encoding="utf-8")
        temporary.replace(self.path)
        self.judgments = judgments
        return self.state()

    def summary(self):
        cells = self.bundle["cells"]
        results = {f"{left} vs {right}": {"wins": 0, "ties": 0, "losses": 0}
                   for left, right in COMBINATIONS}
        judgments = []
        for pair in self.bundle["pairs"]:
            a, b = cells[pair["A"]], cells[pair["B"]]
            vote = self.judgments[pair["id"]]
            winner = None if vote["choice"] == "tie" else cells[pair[vote["choice"]]]["condition"]
            left, right = next(combo for combo in COMBINATIONS
                               if set(combo) == {a["condition"], b["condition"]})
            outcome = "ties" if winner is None else "wins" if winner == left else "losses"
            results[f"{left} vs {right}"][outcome] += 1
            judgments.append({"id": pair["id"], "replicate": a["replicate"],
                              "A": a["condition"], "B": b["condition"], **vote})
        failures = [{"condition": cell["condition"], "replicate": cell["replicate"], "gate": cell["gate"]}
                    for cell in cells.values() if not cell["passed"]]
        matched_failure = any(failure["condition"] == "en" and any(
            cell["condition"] == "zh" and cell["replicate"] == failure["replicate"] and cell["passed"]
            for cell in cells.values()) for failure in failures)
        en_zh = results["en vs zh"]
        return {key: self.bundle[key] for key in ("run_id", "skill", "case_id", "protocol_digest", "model_id")} | {
            "comparisons": results, "hard_failures": failures, "judgments": judgments,
            "en_vs_zh_pilot_signal": sum(en_zh.values()) == 3 and en_zh["losses"] <= 1 and not matched_failure,
            "interpretation": "Pilot signal only; not a statistical or general skill-quality claim."}


def make_server(directory, port=8079):
    review = Review(directory)
    template = Path(__file__).with_suffix(".html").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, content, content_type="application/json"):
            if not isinstance(content, bytes):
                content = json.dumps(content).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; img-src 'self'; connect-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(content)

        def local_request(self):
            host = f"127.0.0.1:{self.server.server_port}"
            return self.headers.get("Host") == host and self.headers.get("Origin", "http://" + host) == "http://" + host

        def do_GET(self):
            if not self.local_request():
                return self.reply(403, {"error": "loopback origin required"})
            path = urlsplit(self.path).path
            if path == "/":
                return self.reply(200, template, "text/html; charset=utf-8")
            if path == "/state":
                return self.reply(200, review.state())
            if path.startswith("/images/") and path[8:] in review.images:
                return self.reply(200, (review.directory / "images" / path[8:]).read_bytes(), "image/png")
            self.reply(404, {"error": "not found"})

        def do_POST(self):
            if not self.local_request():
                return self.reply(403, {"error": "loopback origin required"})
            if self.path != "/judge":
                return self.reply(404, {"error": "not found"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if self.headers.get("Content-Type") != "application/json" or not 0 < size <= 16384:
                    raise ValueError("send a JSON judgment, at most 16384 bytes")
                vote = json.loads(self.rfile.read(size))
                if not isinstance(vote, dict):
                    raise ValueError("expected a judgment object")
                state = review.judge(vote.get("id"), vote.get("choice"), vote.get("reason", ""))
            except (ValueError, TypeError) as error:
                return self.reply(400, {"error": str(error)})
            self.reply(200, state)

        def log_message(self, format, *args):
            pass

    return HTTPServer(("127.0.0.1", port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("--run-id", required=True)
    prepare_parser.add_argument("--log", action="append", required=True)
    prepare_parser.add_argument("--out-dir", required=True)
    serve_parser = commands.add_parser("serve")
    serve_parser.add_argument("directory")
    serve_parser.add_argument("--port", type=int, default=8079)
    args = parser.parse_args()
    if args.command == "prepare":
        bundle = prepare(args.run_id, args.log, args.out_dir)
        print(f"Prepared {len(bundle['pairs'])} blind pairs in {args.out_dir}; private.json is not served.")
    else:
        with make_server(args.directory, args.port) as server:
            print(f"Review: http://127.0.0.1:{server.server_port}", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()
