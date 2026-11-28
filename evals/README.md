# Skill evals

Inspect AI evaluations for the skills in this repository. The entry points
answer different questions:

| Entry | Task | What it tells you |
|---|---|---|
| `evals/smoke.py` | `wiring_smoke` | The chain works: sandbox starts, exec runs, staged files are readable, a model reply comes back. **Behavior is not assessed.** |
| `evals/task.py` | `skill_case` | Runs one behavior case under a `none`/`zh`/`en` condition and records a transcript for manual grading. Produces **no verdict**. |
| `evals/visual.py` | `visual_wiring_smoke` | Renders the dashboard fixture through the separate browser verifier. No model request or behavior verdict. |
| `evals/visual.py` | `visual_case` | Runs the dashboard visual pilot. The scorer checks retention and rendering; a blind human review compares the screenshots. |

Start with the corresponding smoke before running a behavior comparison.

## Setup

Prerequisites are a working rootless Podman plus Compose:

```bash
podman info
podman compose version        # or: podman-compose version
```

Then prepare the image the sandbox uses, once:

```bash
podman pull docker.io/library/python:3.12-slim
```

Finally create the environment (dependencies are pinned by `uv.lock`):

```bash
uv sync --locked --group dev
```

Credentials come from `DEEPSEEK_API_KEY`, which Inspect's built-in `deepseek`
provider reads itself (set `DEEPSEEK_BASE_URL` to point at another endpoint).
Nothing in `evals/` reads, copies, or logs the key.

## Wiring smoke

`evals/smoke.py` uses one synthetic sample to test the wiring, not Skill
behavior. The model may take several turns to make the tool calls and reply:

```bash
uv run --locked inspect eval evals/smoke.py --log-dir evals/.cache/logs
```

The smoke accepts `-T model_id=<id>` (default: `deepseek-flash`). It has no
`condition` parameter: Inspect silently ignores unrecognised task arguments, so
`-T condition=en` would still run the same wiring probe.

It scores 1.0 only if all three factual assertions hold:

| Assertion | Proves |
|---|---|
| `sandbox_exec_ran` | The Podman sandbox returned a successful `bash` tool result. |
| `staged_file_read` | A successful `read_file` result contained the probe text. The probe is staged under an absolute key because the provider resolves relative `Sample.files` keys against the container cwd (`/`), not the tool workdir. |
| `model_responded` | The model returned a non-empty reply. |

The log explanation always ends in `behavior not assessed`, so a green smoke can
never be read as evidence about Skill quality. Prerequisites are the same as
above: `DEEPSEEK_API_KEY` plus the pulled `python:3.12-slim` image.

## Paired behavior runs

`condition` selects what Skill text is staged. The case prompt, the system
guidance, the tool list, the model and the parameters are identical across
conditions, so the three runs below are paired — only the staged bytes differ:

```bash
uv run --locked inspect eval evals/task.py -T skill=refactor-ui -T case_id=1 -T condition=en   --log-dir evals/.cache/logs
uv run --locked inspect eval evals/task.py -T skill=refactor-ui -T case_id=1 -T condition=zh   --log-dir evals/.cache/logs
uv run --locked inspect eval evals/task.py -T skill=refactor-ui -T case_id=1 -T condition=none --log-dir evals/.cache/logs
```

| `condition` | What is staged |
|---|---|
| `en` | `skills/<name>/SKILL.md` and its package Markdown/assets |
| `zh` | the same sandbox paths, with `src/<name>/SPEC.zh.md` and `src/<name>/**/*.zh.md` overlaid |
| `none` | Only the case's input fixtures; no Skill package files — control run |

`en` and `zh` stage an **identical path set**; only contents differ. Files with no
Chinese translation (e.g. `frontend-slides` template assets) are copied unchanged
into both conditions, mirroring `scripts/skill_package.py`.

Repeat a comparison by running the three commands above and comparing the logs;
`--epochs N` repeats each arm if you want to average out sampling noise.

### How the treatment reaches the model

A tool call is not guaranteed, so `evals/loader.py` reads the staged
`/skill/SKILL.md` out of the container **before the first generation** and
prepends it to the system message. `none` finds nothing staged and adds no
document; the surrounding guidance is worded identically in every arm. This
happens in the host-side solver loop; the bytes come from the sandbox.

One case per run by default (`case_id` defaults to `1`). `model_id` defaults to
`deepseek-flash`; the log header records the model that ran.

## Sandbox boundary

| Concern | Runs where |
|---|---|
| Solver loop, DeepSeek request, scorer, document loading | Host process, outside any container |
| `read_file()`, `bash()` | Inside the Podman container from `evals/compose.yaml` |

Tools reach the sandbox only through `sandbox().read_file` / `sandbox().exec`.
Binding `sandbox=("podman", ...)` does not move the agent loop or model calls into
the container — only work a tool explicitly requests through `sandbox()` is
containerized.

Staging is absolute and computed by `evals/packages.py`:

```
/skill/SKILL.md             <- skills/<n>/SKILL.md | src/<n>/SPEC.zh.md
/skill/references/foo.md    <- skills/<n>/references/foo.md | src/<n>/references/foo.zh.md
/skill/evals/fixtures/...   <- the case's own input fixtures
```

`bash()` runs with cwd `/skill`, and `evals/compose.yaml` creates that directory
in every arm. Case fixtures are staged under `/skill/evals/fixtures/...` in all
three conditions, including `none`, so relative fixture paths resolve while the
control arm remains free of Skill package files.

Path handling is validated in both directions: `skill` must be a single directory
component, absolute or `..`-containing package paths are rejected, every staged
file is resolved and required to stay inside its skill package or `src/` root
(a symlinked package escaping `skills/`/`src/` fails), and eval definitions
(`evals.json`, `trigger-set.json`), rubrics, answers and grading files are
refused even when a case lists them inside `evals/fixtures/`.

## Scoring

`wiring_transcript` produces **no behavior verdict**. It returns `Score.unscored`
(excluded from metrics) and records the answer, the case's `expectations`,
`expected_output`, the document size and the tool calls, so a human — or an
explicitly opted-in grader — can rate the rubric from the log. No LLM grader runs
by default and no pass/fail is fabricated.

## Evidence status

Three distinct levels — do not collapse them:

* **Real model smoke, historical**: `evals/.cache/logs/2026-11-24T17-54-27-00-00_skill-case_C9xeaP9opfvXqWxu8RSWkU.eval`
  — one `deepseek/deepseek-flash` sample against Podman, score 1.0, tool calls
  `read_skill`, `bash`, `bash`. It ran an **earlier revision** (English-only
  staging, no document loading before generation), so it proves the Podman wiring
  at that time, not the current condition logic. It is kept as-is, not re-run.
* **`wiring_smoke`, current revision**: `evals/.cache/logs/2026-11-25T05-58-37-00-00_wiring-smoke_n4cWVWHsjt3PRYaEu4HKTm.eval`
  — one `deepseek/deepseek-flash` sample against Podman, status `success`, score
  `wiring_ok=1.0`; `sandbox_exec_ran`, `staged_file_read`, and `model_responded`
  were all true. This proves the current smoke wiring only; its explanation
  explicitly says **behavior not assessed**.
* **`skill_case`**: verified offline only — the staging/condition logic is covered
  by unit tests, no current-revision behavior run was performed. Its scorer
  records a transcript without a behavior verdict; any performance comparison
  still requires separate runs and grading.

## Dashboard visual pilot

This pilot covers **refactor-ui case 6 only**. It does not establish whole-Skill
release readiness. The next case to fixture is case 3 (preserve visual identity
while reducing competing decoration), after the case-6 chain is verified.

```bash
just eval-visual-image
just eval-visual-smoke
just eval-visual-pilot dashboard-01
```

The image command builds a local, versioned Playwright image; rebuild it after
changing the verifier. The smoke copies the original fixture to the output path
and exercises both Podman services and the scorer without making a model request.
The pilot needs `DEEPSEEK_API_KEY` for `https://api.deepseek.com`; it uses
`deepseek/deepseek-flash` by default. It runs nine fresh samples serially, rotating
condition order over three replicates. Use the checked-in launch command with
its fixed model configuration and message limit, not CLI overrides.

The model edits a single self-contained `/skill/output.html`. The evaluator
transfers only that HTML and the pristine fixture to a separate, networkless
browser container; model tools cannot select that container. Chromium captures
full-page screenshots with a 1440×1100 desktop viewport in both cases. The
scorer checks rendering, retention of the twelve metrics and event data, the
three daily filter controls, and the enabled `New incident` action. It does not
expect the static page to filter data or create incidents. It returns only the
automatic gate, never a visual score or a process grade. Missing or invalid
candidate HTML is a scored failure. Keep the `.eval` logs and their referenced
artifacts under `evals/.cache/visual/` together. Do not open generated HTML on
the host to review it; use the screenshot-only review page.

Inspect retries transient official API request failures (for example 429, 5xx,
connection failure or timeout) up to two times per request with backoff. It does
not retry invalid requests, bad credentials or insufficient balance. An API
error that cannot be retried or exhausts this budget stops the serial pilot.
There are no whole-sample retries. A completed candidate that fails the gate is
not a missing sample. If an API failure leaves cells missing, do not draw
conclusions; after service recovery, fill only the missing cells with the same
run ID, model and unchanged protocol. For example, for a missing English
replicate 2:

```bash
uv run --locked inspect eval evals/visual.py@visual_case -T run_id=dashboard-01 -T condition=en -T replicate=2 --retry-on-error=0 --log-dir evals/.cache/logs
```

Prepare the blinded bundle using every log for that run (`--log` is repeatable),
then start the local page:

```bash
uv run --locked python -m evals.review prepare --run-id dashboard-01 --log <pilot.eval> --out-dir evals/.cache/review-dashboard-01
uv run --locked python -m evals.review serve evals/.cache/review-dashboard-01
```

Open the printed `127.0.0.1` URL. Compare the original request, baseline and
anonymous A/B screenshots against the case criteria; pick A, B or tie and
optionally give a reason. No agent replies or process logs enter the review.
Stop with Ctrl-C and run `serve` on the same directory to resume saved votes.
Do not inspect the private mapping or raw logs during review. All nine cells
must be accounted for; only pairs with two passing candidates go to visual
review. The bundle rejects duplicate cells and changes to the recorded protocol.

The reveal reports wins/ties/losses for all three matchups and hard failures
separately. The English non-regression signal requires three comparable English
vs Chinese pairs, at most one English loss, and no new English hard failure.
Ties count as no observed decline. No-skill comparisons are diagnostic. This is
a pilot signal, not equivalence or whole-Skill certification. Good/bad visual
anchors may calibrate review after the first blind pilot; they are not scoring
targets.

## Tests

Offline only — no external network, no Podman, no model calls. Browser-side
regressions run if a local Chromium executable is available; otherwise they skip.

```bash
uv run --locked python -m pytest evals/tests -q
```

They cover condition selection, `en`/`zh` path parity, Chinese overlay mapping,
the translated-vs-copied asset distinction, fixture staging under the workdir,
exclusion of eval assets (including inside `evals/fixtures/`), skill-name
validation, symlink escapes, condition-agnostic prompt composition, and that
loading never mutates the case files.
