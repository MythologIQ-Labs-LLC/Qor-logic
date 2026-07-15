"""Phase 93: behavior tests for qor.scripts.merge_velocity_check (GH #89).

Scratch-repo fixtures construct controlled merge-commit histories.
Per qor/references/doctrine-test-functionality.md, assertions verify
the returned VelocityAssessment fields and CLI exit codes — not header
presence.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qor.scripts.merge_velocity_check import (
    _git_log_merges_in_window,
    assess_merge_velocity,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str], cwd: Path, env: dict | None = None) -> str:
    result = subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, check=True, env=env,
    )
    return result.stdout


def _make_repo(tmp_path: Path) -> Path:
    """Initialize a scratch git repo with main branch and identity."""
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", "-b", "main"], cwd=repo)
    _run(["git", "config", "user.email", "test@example.com"], cwd=repo)
    _run(["git", "config", "user.name", "Test"], cwd=repo)
    # Initial commit so main exists
    (repo / "README.md").write_text("test\n", encoding="utf-8")
    _run(["git", "add", "."], cwd=repo)
    _run(["git", "commit", "-m", "initial"], cwd=repo)
    return repo


def _feat_suffix(subject: str) -> str:
    """Deterministic, collision-resistant name suffix for a merge subject.

    A pure function of ``subject`` (sha1, not the PYTHONHASHSEED-randomized
    builtin ``hash()``), so distinct subjects never collide into the same
    ``git checkout -b feat-<n>`` branch name across processes -- closing the
    exit-128 CI flake that mod-100000-truncated ``hash()`` produced.
    """
    return hashlib.sha1(subject.encode("utf-8")).hexdigest()[:8]


def _make_merge_commit(
    repo: Path,
    subject: str,
    files: dict[str, str] | None = None,
    days_ago: int = 0,
) -> None:
    """Create a feature branch, commit a file change, and merge with --no-ff
    (so the merge generates a merge commit that `--merges` will match)."""
    # Sanitize: filenames cannot contain ':' on Windows
    safe = re.sub(r"[^A-Za-z0-9_]", "_", subject)
    suffix = _feat_suffix(subject)
    files = files or {f"feature_{safe}_{suffix}.txt": subject}
    branch = f"feat-{suffix}"
    _run(["git", "checkout", "-b", branch], cwd=repo)
    for path, content in files.items():
        full = repo / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content + "\n", encoding="utf-8")
    _run(["git", "add", "."], cwd=repo)
    # The fixture tests merge-graph behavior, not tree-diff semantics. Allowing
    # an empty synthetic feature commit makes the DAG deterministic even if a
    # platform or filesystem reports an unchanged tree unexpectedly.
    _run(["git", "commit", "--allow-empty", "-m", f"feat: {subject}"], cwd=repo)
    _run(["git", "checkout", "main"], cwd=repo)
    # Set commit date via env var for the merge commit
    env = None
    if days_ago > 0:
        when = datetime.now(timezone.utc) - timedelta(days=days_ago)
        date_str = when.strftime("%Y-%m-%dT%H:%M:%S")
        import os
        env = {**os.environ, "GIT_AUTHOR_DATE": date_str, "GIT_COMMITTER_DATE": date_str}
    _run(["git", "merge", "--no-ff", branch, "-m", subject], cwd=repo, env=env)


# ---------------------------------------------------------------------------
# Grade thresholds
# ---------------------------------------------------------------------------


def test_assess_healthy_grade_for_low_pr_count(tmp_path):
    repo = _make_repo(tmp_path)
    for i in range(3):
        _make_merge_commit(repo, f"feature {i}")
    a = assess_merge_velocity(repo, window_days=7)
    assert a.stabilization_capacity == "healthy", (
        f"expected healthy with 3 merges; got {a.stabilization_capacity} (evidence={a.evidence})"
    )
    assert a.prs_merged_in_window == 3


def test_assess_strained_grade_for_moderate_pr_count(tmp_path):
    repo = _make_repo(tmp_path)
    for i in range(12):
        _make_merge_commit(repo, f"feature {i}")
    a = assess_merge_velocity(repo, window_days=7)
    assert a.stabilization_capacity == "strained", (
        f"expected strained with 12 merges; got {a.stabilization_capacity}"
    )


def test_assess_exceeded_grade_for_high_pr_count_and_repair_density(tmp_path):
    repo = _make_repo(tmp_path)
    # 25 merges total, with 9 having repair keywords (>= 20 PRs, >= 30% repair)
    repair_subjects = [
        "fix: A", "fix: B", "hotfix: C", "repair: D",
        "regression: E", "rollback: F", "revert: G", "fix: H", "fix: I",
    ]
    for s in repair_subjects:
        _make_merge_commit(repo, s)
    for i in range(16):
        _make_merge_commit(repo, f"feature {i}")
    a = assess_merge_velocity(repo, window_days=7)
    assert a.stabilization_capacity == "exceeded", (
        f"expected exceeded with 25 merges + 9 repair; got {a.stabilization_capacity} "
        f"(prs={a.prs_merged_in_window}, repair_density={a.repair_density})"
    )


def test_repair_density_classification_matches_keywords(tmp_path):
    repo = _make_repo(tmp_path)
    repair = ["fix: A", "hotfix: B", "repair: C", "regression: D", "rollback: E", "revert: F"]
    non_repair = ["seal: G", "seal: H", "seal: I"]
    for s in repair + non_repair:
        _make_merge_commit(repo, s)
    a = assess_merge_velocity(repo, window_days=30)
    assert a.repair_density == pytest.approx(6 / 9, abs=0.01)


# ---------------------------------------------------------------------------
# Shared-core touch counting
# ---------------------------------------------------------------------------


def test_shared_core_touch_counted_for_declared_paths(tmp_path):
    repo = _make_repo(tmp_path)
    # 3 merges touching core/ledger/, 2 touching other paths
    for i in range(3):
        _make_merge_commit(
            repo, f"core change {i}", files={f"core/ledger/file_{i}.py": f"x = {i}"},
        )
    for i in range(2):
        _make_merge_commit(
            repo, f"other change {i}", files={f"other/file_{i}.py": f"y = {i}"},
        )
    a = assess_merge_velocity(repo, window_days=30, shared_core_paths=("core/ledger/",))
    assert a.shared_core_touch_count == 3


# ---------------------------------------------------------------------------
# Window filtering
# ---------------------------------------------------------------------------


def test_merges_outside_window_excluded(tmp_path):
    repo = _make_repo(tmp_path)
    _make_merge_commit(repo, "recent feature")
    _make_merge_commit(repo, "old feature", days_ago=60)
    merges = _git_log_merges_in_window(repo, 30)
    subjects = [m.subject for m in merges]
    assert "recent feature" in subjects
    assert "old feature" not in subjects


# ---------------------------------------------------------------------------
# CLI behavior
# ---------------------------------------------------------------------------


def test_cli_healthy_exits_zero(tmp_path):
    repo = _make_repo(tmp_path)
    _make_merge_commit(repo, "feature one")
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.merge_velocity_check", "--repo", str(repo)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "healthy" in result.stdout


def test_cli_exceeded_exits_one(tmp_path):
    repo = _make_repo(tmp_path)
    for i in range(25):
        _make_merge_commit(repo, f"fix: issue {i}")
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.merge_velocity_check", "--repo", str(repo), "--window-days", "7"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "exceeded" in result.stdout
