"""Phase 124 (release pipeline fix): structural assertions that release.yml's
tag trigger is no longer path-filtered, exposes a workflow_dispatch tag input,
and both jobs build the resolved ref. Parses the actual workflow YAML.
"""
from __future__ import annotations

import pathlib
import re

import yaml

_RELEASE = pathlib.Path(".github/workflows/release.yml")


def _load() -> dict:
    return yaml.safe_load(_RELEASE.read_text(encoding="utf-8"))


def _on_block(wf: dict) -> dict:
    # PyYAML parses the bare key `on:` as the boolean True.
    return wf.get(True, wf.get("on"))


def _first_checkout(job: dict) -> dict:
    for step in job.get("steps", []):
        if "uses" in step and "actions/checkout" in step["uses"]:
            return step
    return {}


def test_tag_trigger_has_no_paths_ignore() -> None:
    on = _on_block(_load())
    assert "tags" in on["push"], "tag trigger must remain"
    assert "paths-ignore" not in on["push"], (
        "paths-ignore on a tag push makes GitHub skip the Release workflow"
    )
    assert "paths" not in on["push"]


def test_workflow_dispatch_with_tag_input() -> None:
    on = _on_block(_load())
    assert "workflow_dispatch" in on
    tag = on["workflow_dispatch"]["inputs"]["tag"]
    assert tag["required"] is True


def test_both_jobs_checkout_resolved_ref() -> None:
    jobs = _load()["jobs"]
    for name in ("build", "publish"):
        step = _first_checkout(jobs[name])
        ref = step.get("with", {}).get("ref", "")
        assert "inputs.tag" in ref, f"{name} checkout must build the resolved ref, got {ref!r}"


def test_reachability_guard_uses_checked_out_head() -> None:
    jobs = _load()["jobs"]
    for name in ("build", "publish"):
        runs = "\n".join(s.get("run", "") for s in jobs[name].get("steps", []))
        assert "merge-base --is-ancestor" in runs, f"{name} missing reachability guard"
        assert "git rev-parse HEAD" in runs, (
            f"{name} guard must validate the checked-out tag (git rev-parse HEAD)"
        )


def test_actions_still_sha_pinned() -> None:
    wf = _load()
    sha_re = re.compile(r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")
    for job in wf["jobs"].values():
        for step in job.get("steps", []):
            uses = step.get("uses")
            if uses:
                assert sha_re.match(uses), f"action not SHA-pinned: {uses}"


def test_ci_coverage_lint_treats_dispatch_release_as_tag_only() -> None:
    """Adding workflow_dispatch to the release workflow must not reclassify it
    as a CI gate (Phase 124 regression guard for ci_coverage_lint)."""
    from qor.scripts.ci_coverage_lint import _is_tag_only_workflow
    on_value = {"push": {"tags": ["v*.*.*"]}, "workflow_dispatch": {"inputs": {"tag": {}}}}
    assert _is_tag_only_workflow(on_value) is True
    # A branch-push workflow is still a CI gate (not tag-only).
    assert _is_tag_only_workflow({"push": {"branches": ["main"]}}) is False
