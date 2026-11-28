set positional-arguments

skill-sync:
    python3 scripts/skill_package.py sync

skill-check:
    python3 scripts/skill_package.py check

skill-record skill generator:
    python3 scripts/skill_package.py record "$1" --generator "$2"

test:
    python3 -B -m unittest discover -s tests -v

eval-wiring-smoke:
    uv run --locked inspect eval evals/smoke.py --log-dir evals/.cache/logs

eval-visual-image:
    podman build -f evals/browser/Dockerfile -t localhost/skills-ui-verifier:playwright-1.58.0 evals

eval-visual-smoke:
    uv run --locked inspect eval evals/visual.py@visual_wiring_smoke --model mockllm/model --log-dir evals/.cache/logs

eval-visual-pilot run:
    uv run --locked inspect eval evals/visual.py@visual_case -T "run_id=$1" --retry-on-error=0 --log-dir evals/.cache/logs
