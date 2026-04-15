"""GitHub Actions budget enforcement (Phase 12 Track A).

Static analysis over .github/workflows/*.yml. Tests pass vacuously when
no workflows exist (preventive infrastructure). When the first workflow
lands, all rules enforce automatically.

Source doctrine: qor/references/doctrine-ci-budget.md.

Per V-2 + V-C: regex parsing only; no pyyaml dep. Per V-4: combined
assertions split into separate tests. Per V-5: rule 4 narrowed to
setup-python users only.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def _workflow_files() -> list[Path]:
    if not WORKFLOWS_DIR.exists():
        return []
    return sorted(WORKFLOWS_DIR.glob("*.yml")) + sorted(WORKFLOWS_DIR.glob("*.yaml"))


# ----- V-4 split: workflow_dir_optional vs workflow_rules_enforced_when_present -----

def test_workflow_dir_optional():
    """Passes when .github/workflows/ is missing or empty (preventive infra)."""
    if not WORKFLOWS_DIR.exists():
        return  # vacuous pass; no workflows to audit
    assert WORKFLOWS_DIR.is_dir()


def test_workflow_rules_enforced_when_present():
    """Marker test: when workflows exist, the per-rule tests below enforce."""
    workflows = _workflow_files()
    if not workflows:
        pytest.skip("No workflows present; per-rule enforcement tests skip")
    # If we get here, workflows exist; per-rule tests will exercise them.
    assert all(f.suffix in (".yml", ".yaml") for f in workflows)


# ----- Rule 1: no schedule without justification -----

SCHEDULE_RE = re.compile(r"^\s*schedule:\s*$", re.MULTILINE)
COST_JUSTIFICATION_RE = re.compile(r"#.*cost justification:", re.IGNORECASE)


def test_no_unjustified_schedule():
    """Workflows with `schedule:` MUST contain `# cost justification:` comment."""
    failures = []
    for wf in _workflow_files():
        text = wf.read_text(encoding="utf-8")
        if SCHEDULE_RE.search(text) and not COST_JUSTIFICATION_RE.search(text):
            failures.append(str(wf.relative_to(REPO_ROOT)))
    if not _workflow_files():
        pytest.skip("No workflows; nothing to audit")
    assert not failures, "Workflows with schedule: but no cost justification:\n  " + "\n  ".join(failures)


# ----- Rule 2: paths filter mandatory -----

PATHS_FILTER_RE = re.compile(r"^\s*paths(-ignore)?:\s*$", re.MULTILINE)


def test_paths_ignore_present():
    """Every workflow MUST contain `paths-ignore:` or `paths:` filter."""
    failures = []
    for wf in _workflow_files():
        text = wf.read_text(encoding="utf-8")
        if not PATHS_FILTER_RE.search(text):
            failures.append(str(wf.relative_to(REPO_ROOT)))
    if not _workflow_files():
        pytest.skip("No workflows; nothing to audit")
    assert not failures, "Workflows missing paths-ignore: or paths: filter:\n  " + "\n  ".join(failures)


# ----- Rule 3: no matrix without justification -----

MATRIX_RE = re.compile(r"^\s*matrix:\s*$", re.MULTILINE)
MATRIX_JUSTIFICATION_RE = re.compile(r"#.*matrix justification:", re.IGNORECASE)


def test_no_matrix_without_justification():
    """Workflows with `matrix:` MUST contain `# matrix justification:` comment."""
    failures = []
    for wf in _workflow_files():
        text = wf.read_text(encoding="utf-8")
        if MATRIX_RE.search(text) and not MATRIX_JUSTIFICATION_RE.search(text):
            failures.append(str(wf.relative_to(REPO_ROOT)))
    if not _workflow_files():
        pytest.skip("No workflows; nothing to audit")
    assert not failures, "Workflows with matrix: but no matrix justification:\n  " + "\n  ".join(failures)


# ----- Rule 4: setup-python uses cache (V-5 narrowed: only direct setup-python users) -----

SETUP_PYTHON_RE = re.compile(r"actions/setup-python@", re.IGNORECASE)
SETUP_PYTHON_CACHE_RE = re.compile(r"actions/setup-python@.*?\n(?:\s+with:\s*\n)?(?:\s+\S.*\n)*?\s+cache:", re.MULTILINE)
ACTIONS_CACHE_RE = re.compile(r"^\s*-\s*uses:\s*actions/cache@", re.MULTILINE)


def test_setup_python_uses_cache():
    """Workflows that use actions/setup-python@ MUST declare `cache:` parameter
    OR explicitly use actions/cache@ for pip caching elsewhere."""
    failures = []
    for wf in _workflow_files():
        text = wf.read_text(encoding="utf-8")
        if SETUP_PYTHON_RE.search(text):
            has_setup_cache = SETUP_PYTHON_CACHE_RE.search(text)
            has_actions_cache = ACTIONS_CACHE_RE.search(text)
            if not (has_setup_cache or has_actions_cache):
                failures.append(str(wf.relative_to(REPO_ROOT)))
    if not _workflow_files():
        pytest.skip("No workflows; nothing to audit")
    assert not failures, "Workflows using setup-python@ without cache:\n  " + "\n  ".join(failures)


# ----- Rule 6: concurrency declared -----

CONCURRENCY_RE = re.compile(r"^\s*concurrency:\s*$", re.MULTILINE)


def test_concurrency_declared():
    """Every workflow MUST declare `concurrency:` to cancel superseded runs."""
    failures = []
    for wf in _workflow_files():
        text = wf.read_text(encoding="utf-8")
        if not CONCURRENCY_RE.search(text):
            failures.append(str(wf.relative_to(REPO_ROOT)))
    if not _workflow_files():
        pytest.skip("No workflows; nothing to audit")
    assert not failures, "Workflows missing concurrency: declaration:\n  " + "\n  ".join(failures)
