"""Tests for release.yml main-reachability guard (Phase 40 hotfix + Phase 101 split-job amendment).

Prevents the pre-merge publish class of failure that shipped v0.24.1, v0.25.0,
and v0.28.0 to PyPI from open-PR branches before they were merged to main.

Phase 101 (GH #118 P0) split the single `build-and-publish` job into separate
`build` and `publish` jobs. The tag-ancestry guard now runs in BOTH jobs
(early fail in build, enforcement gate in publish) -- load-bearing-gate
preservation per qor-substantiate Constraints.
"""
from __future__ import annotations

import pathlib

import yaml


_WORKFLOW = pathlib.Path(".github/workflows/release.yml")


def _load_workflow() -> dict:
    return yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))


def _job_steps(job_name: str) -> list[dict]:
    return _load_workflow()["jobs"][job_name]["steps"]


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
    """The guard must exist in the publish job (the enforcement gate)."""
    steps = _job_steps("publish")
    idx = _guard_step_index(steps)
    assert idx is not None, (
        "release.yml publish job is missing the main-reachability guard step. "
        "Expected a run block containing 'git merge-base --is-ancestor' and 'origin/main'."
    )


def test_release_workflow_guard_runs_before_publish():
    """The guard must precede the PyPI publish step so a failing guard blocks upload."""
    steps = _job_steps("publish")
    guard = _guard_step_index(steps)
    publish = _publish_step_index(steps)
    assert guard is not None, "guard step absent from publish job"
    assert publish is not None, "publish step absent"
    assert guard < publish, (
        f"Guard step (index {guard}) must precede publish step (index {publish}). "
        "Otherwise a failing guard does not block the upload."
    )


def test_tag_ancestry_guard_present_in_both_jobs():
    """Phase 101: load-bearing-gate preservation. The guard runs in BOTH jobs.

    Build job: early-fail gate (cheap, avoids wasted build).
    Publish job: enforcement gate (the actual decision point).
    Two cheap checks beat one because cache invalidation or artifact
    misdelivery cannot bypass both.
    """
    build_guard = _guard_step_index(_job_steps("build"))
    publish_guard = _guard_step_index(_job_steps("publish"))
    assert build_guard is not None, (
        "Phase 101 P0: build job must also carry the tag-ancestry guard (early fail). "
        "Removing it would degrade the defense-in-depth posture."
    )
    assert publish_guard is not None, (
        "Phase 101 P0: publish job must carry the tag-ancestry guard (enforcement gate)."
    )
