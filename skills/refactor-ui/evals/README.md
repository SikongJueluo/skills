# Evaluation notes

- `evals.json` holds behavior cases in the skill-creator format: prompt, expected output, and checkable expectations.
- `trigger-set.json` holds description-trigger checks: five positives and five near-misses.
- `fixtures/dense-dashboard/index.html` is a static, deliberately busy but legitimate operations dashboard. It is the anti-minimalism case: all twelve metrics, the event table, and the three daily filters are load-bearing.

## Running

No runner is vendored in this repository. Use the host's skill-creator evaluation flow: give each prompt and its fixture to a fresh agent with the skill available, then grade each expectation from the final response and the artifact state. Use the host's trigger evaluator for `trigger-set.json`.

The fixture opens directly in a browser. For screenshot comparison, use any headless Chromium at the same viewport for the before and after states.

## Recorded trials

See [trials.md](trials.md) for the runs performed on 2026-10-28 and their limits.
