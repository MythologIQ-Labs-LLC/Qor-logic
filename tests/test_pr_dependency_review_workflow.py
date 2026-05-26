"""Phase 102 (GH #118 P1): pr-dependency-review.yml workflow assertions."""
from __future__ import annotations

import pathlib
import re

import yaml

_WORKFLOW = pathlib.Path(".github/workflows/pr-dependency-review.yml")


def _load() -> dict:
    return yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))


def test_workflow_file_exists():
    assert _WORKFLOW.is_file(), ".github/workflows/pr-dependency-review.yml must be committed"


def test_workflow_uses_dependency_review_action_sha_pinned():
    workflow = _load()
    steps = workflow["jobs"]["dependency-review"]["steps"]
    review_step = next(
        (s for s in steps if s.get("uses", "").startswith("actions/dependency-review-action@")),
        None,
    )
    assert review_step is not None, (
        "workflow must include actions/dependency-review-action step"
    )
    uses = review_step["uses"]
    m = re.match(r"^actions/dependency-review-action@([0-9a-f]{40})$", uses)
    assert m is not None, (
        f"dependency-review-action must be SHA-pinned; got {uses!r}"
    )
    # Annotation comment must appear on the same line in the source YAML
    text = _WORKFLOW.read_text(encoding="utf-8")
    sha = m.group(1)
    annotated = any(
        sha in line and re.search(r"#\s*v[0-9]+\.[0-9]+", line)
        for line in text.splitlines()
    )
    assert annotated, (
        f"dependency-review-action SHA pin must carry a '# vX.Y.Z' annotation comment"
    )


def test_workflow_triggers_on_dependency_paths():
    workflow = _load()
    # PyYAML parses 'on' as the boolean True due to YAML 1.1 spec; handle both.
    on_block = workflow.get("on") or workflow.get(True)
    assert on_block is not None, "workflow must declare an 'on' trigger block"
    pr_block = on_block.get("pull_request") or {}
    paths = pr_block.get("paths") or []
    required_paths = {"pyproject.toml", "requirements-release.txt"}
    assert required_paths.issubset(set(paths)), (
        f"on.pull_request.paths must include {required_paths}; got {paths!r}"
    )
    workflow_glob_present = any(p.startswith(".github/workflows/") for p in paths)
    assert workflow_glob_present, (
        "on.pull_request.paths must include a glob covering .github/workflows/**"
    )


def test_lint_step_does_not_have_or_true_wrap():
    """Phase 107 D-107.1: the cooling-period lint step exits non-zero on violation."""
    text = _WORKFLOW.read_text(encoding="utf-8")
    # The lint step is the one containing 'dependency_admission_lint'
    lines = text.splitlines()
    in_lint_step = False
    lint_step_lines: list[str] = []
    for line in lines:
        if "dependency_admission_lint" in line:
            in_lint_step = True
        if in_lint_step:
            lint_step_lines.append(line)
            # Step boundary heuristic: next step starts at the next "- name:" at same indent
            if line.strip().startswith("- ") and "dependency_admission_lint" not in line and "name:" in line:
                break
    block = "\n".join(lint_step_lines)
    assert "|| true" not in block, (
        "Phase 107 flipped the WARN→hard-fail; the cooling-period lint step must "
        "exit non-zero on violations. Found `|| true` wrap still present:\n" + block
    )


def test_workflow_fails_on_high_severity():
    workflow = _load()
    steps = workflow["jobs"]["dependency-review"]["steps"]
    review_step = next(
        (s for s in steps if s.get("uses", "").startswith("actions/dependency-review-action@")),
        None,
    )
    with_kwargs = (review_step or {}).get("with") or {}
    assert with_kwargs.get("fail-on-severity") == "high", (
        f"fail-on-severity must be 'high'; got {with_kwargs.get('fail-on-severity')!r}"
    )
