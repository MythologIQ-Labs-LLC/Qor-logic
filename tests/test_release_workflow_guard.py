"""Tests for release.yml main-reachability guard (Phase 40 hotfix).

Prevents the pre-merge publish class of failure that shipped v0.24.1, v0.25.0,
and v0.28.0 to PyPI from open-PR branches before they were merged to main.
"""
from __future__ import annotations

import pathlib

import yaml


_WORKFLOW = pathlib.Path(".github/workflows/release.yml")


def _load_job_steps() -> list[dict]:
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    return workflow["jobs"]["build-and-publish"]["steps"]


def _guard_step_index(steps: list[dict]) -> int | None:
    for idx, step in enumerate(steps):
        run = step.get("run", "")
        if "merge-base --is-ancestor" in run and "origin/main" in run:
            return idx
    return None


def _publish_step_index(steps: list[dict]) -> int | None:
    for idx, step in enumerate(steps):
        uses = step.get("uses", "")
        if uses.startswith("pypa/gh-action-pypi-publish"):
            return idx
    return None


def test_release_workflow_has_main_reachability_guard():
    """release.yml must contain a step that runs git merge-base --is-ancestor against origin/main."""
    steps = _load_job_steps()
    idx = _guard_step_index(steps)
    assert idx is not None, (
        "release.yml is missing the main-reachability guard step. "
        "Expected a run block containing 'git merge-base --is-ancestor' and 'origin/main'."
    )


def test_release_workflow_guard_runs_before_publish():
    """The guard must precede the PyPI publish step so a failing guard blocks upload."""
    steps = _load_job_steps()
    guard = _guard_step_index(steps)
    publish = _publish_step_index(steps)
    assert guard is not None, "guard step absent"
    assert publish is not None, "publish step absent"
    assert guard < publish, (
        f"Guard step (index {guard}) must precede publish step (index {publish}). "
        "Otherwise a failing guard does not block the upload."
    )
