"""Phase 102 (GH #118 P1): pr-dependency-review.yml workflow assertions."""
from __future__ import annotations

import pathlib
import re

import yaml

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "pr-dependency-review.yml"
_KNOWN_GOVERNED = {
    "pyproject.toml",
    "requirements-release.in",
    "requirements-release.txt",
    "requirements-sbom.in",
    "requirements-sbom.txt",
}


def _governed_dependency_paths() -> set[str]:
    """Phase 298 (GH #511): root dependency surface, derived at test time."""
    names = {"pyproject.toml"}
    for pattern in ("requirements-*.in", "requirements-*.txt"):
        names.update(p.name for p in _REPO_ROOT.glob(pattern) if p.is_file())
    return names


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
        "dependency-review-action SHA pin must carry a '# vX.Y.Z' annotation comment"
    )


def test_workflow_triggers_on_dependency_paths():
    workflow = _load()
    # PyYAML parses 'on' as the boolean True due to YAML 1.1 spec; handle both.
    on_block = workflow.get("on") or workflow.get(True)
    assert on_block is not None, "workflow must declare an 'on' trigger block"
    pr_block = on_block.get("pull_request") or {}
    paths = pr_block.get("paths") or []
    governed = _governed_dependency_paths()
    assert _KNOWN_GOVERNED.issubset(governed), (
        f"derived governed set shrank; missing {_KNOWN_GOVERNED - governed}"
    )
    missing = governed - set(paths)
    assert not missing, (
        f"on.pull_request.paths must include every governed dependency path; "
        f"missing {sorted(missing)}; got {paths!r}"
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


def test_admission_lint_runs_for_every_governed_lockfile():
    """Phase 298 (GH #511): one hard-fail admission step per governed lockfile."""
    steps = _load()["jobs"]["dependency-review"]["steps"]
    lint_steps = [s for s in steps if "dependency_admission_lint" in (s.get("run") or "")]
    named: list[str] = []
    for step in lint_steps:
        run = step["run"]
        m = re.search(r"--lockfile\s+\"?([^\s\"]+)", run)
        assert m is not None, f"admission step must pass --lockfile: {run!r}"
        named.append(m.group(1))
        assert "--base" in run, f"admission step must pass --base: {run!r}"
        assert "|| true" not in run and "set +e" not in run, (
            f"admission step must stay hard-fail: {run!r}"
        )
        assert "if" not in step, f"admission step must not carry an if: guard: {step!r}"
        assert not step.get("continue-on-error"), (
            f"admission step must not set continue-on-error: {step!r}"
        )
    lockfiles = {p for p in _governed_dependency_paths() if p.endswith(".txt")}
    for lockfile in sorted(lockfiles):
        assert named.count(lockfile) == 1, (
            f"governed lockfile {lockfile} must be named by exactly one admission "
            f"step; named={named!r}"
        )
