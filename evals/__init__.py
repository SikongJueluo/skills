"""Inspect AI evaluations for the skills in this repository.

Read a skill's existing `evals.json` behavior case as a dataset sample, run a
tool-using agent against it, and execute that agent's tools inside a Podman
container via the `inspect-podman` sandbox provider.
"""
