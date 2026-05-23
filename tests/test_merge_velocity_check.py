"""Phase 93: behavior tests for qor.scripts.merge_velocity_check (GH #89).

Scratch-repo fixtures construct controlled merge-commit histories.
Per qor/references/doctrine-test-functionality.md, assertions verify
the returned VelocityAssessment fields and CLI exit codes — not header
presence.
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qor.scripts.merge_velocity_check import (
    VelocityAssessment,
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
    files = files or {f"feature_{safe}_{abs(hash(subject)) % 100000}.txt": subject}
    branch = f"feat-{abs(hash(subject)) % 100000}"
    _run(["git", "checkout", "-b", branch], cwd=repo)
    for path, content in files.items():
        full = repo / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content + "\n", encoding="utf-8")
    _run(["git", "add", "."], cwd=repo)
    _run(["git", "commit", "-m", f"feat: {subject}"], cwd=repo)
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
    assert a.shared_core_touch_count == 3, (
        f"expected 3 shared-core touches; got {a.shared_core_touch_count}"
    )


def test_shared_core_touch_zero_when_no_patterns_declared(tmp_path):
    repo = _make_repo(tmp_path)
    _make_merge_commit(repo, "feature")
    a = assess_merge_velocity(repo, window_days=7)
    assert a.shared_core_touch_count == 0


# ---------------------------------------------------------------------------
# Recommended action mapping
# ---------------------------------------------------------------------------


def test_recommended_action_maps_from_grade(tmp_path):
    # healthy
    repo_h = _make_repo(tmp_path / "h")
    _make_merge_commit(repo_h, "feature")
    a_h = assess_merge_velocity(repo_h, window_days=7)
    assert a_h.recommended_action == "merge_ok"

    # strained
    repo_s = _make_repo(tmp_path / "s")
    for i in range(12):
        _make_merge_commit(repo_s, f"feature {i}")
    a_s = assess_merge_velocity(repo_s, window_days=7)
    assert a_s.recommended_action == "narrow_scope"

    # exceeded
    repo_e = _make_repo(tmp_path / "e")
    for i in range(25):
        _make_merge_commit(repo_e, f"fix: {i}")
    a_e = assess_merge_velocity(repo_e, window_days=7)
    assert a_e.recommended_action == "branch_only"


# ---------------------------------------------------------------------------
# Evidence list
# ---------------------------------------------------------------------------


def test_evidence_list_names_threshold_in_each_fired_signal(tmp_path):
    repo = _make_repo(tmp_path)
    for i in range(15):
        _make_merge_commit(repo, f"feature {i}")
    a = assess_merge_velocity(repo, window_days=7)
    # 15 >= strained threshold 10; the evidence list must name the threshold
    assert any("10" in e and ">=" in e for e in a.evidence), (
        f"expected evidence string naming the 10-threshold; got: {a.evidence}"
    )


# ---------------------------------------------------------------------------
# Window filtering
# ---------------------------------------------------------------------------


def test_window_days_arg_filters_merges(tmp_path):
    repo = _make_repo(tmp_path)
    # 3 recent + 3 old (15 days ago)
    for i in range(3):
        _make_merge_commit(repo, f"recent {i}")
    for i in range(3):
        _make_merge_commit(repo, f"old {i}", days_ago=15)
    a_narrow = assess_merge_velocity(repo, window_days=7)
    a_wide = assess_merge_velocity(repo, window_days=30)
    assert a_narrow.prs_merged_in_window == 3
    assert a_wide.prs_merged_in_window == 6


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_main_cli_exits_zero_on_healthy(tmp_path):
    repo = _make_repo(tmp_path)
    _make_merge_commit(repo, "feature")
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.merge_velocity_check",
         "--repo-root", str(repo), "--window-days", "7"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"healthy should exit 0; got {result.returncode} stderr={result.stderr!r}"
    )


def test_main_cli_exits_one_on_exceeded(tmp_path):
    repo = _make_repo(tmp_path)
    for i in range(25):
        _make_merge_commit(repo, f"fix: {i}")
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.merge_velocity_check",
         "--repo-root", str(repo), "--window-days", "7"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 1, (
        f"exceeded should exit 1; got {result.returncode} stdout={result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Canonical-repo forward-only guard
# ---------------------------------------------------------------------------


def test_assess_velocity_on_qor_logic_main():
    """Run the detector on Qor-logic's own main; assert it returns a valid
    grade and a positive PR count. Does NOT assert a specific grade (data-
    driven; will shift over time)."""
    a = assess_merge_velocity(REPO_ROOT, window_days=30)
    assert a.stabilization_capacity in {"healthy", "strained", "exceeded"}, (
        f"invalid grade: {a.stabilization_capacity}"
    )
    assert a.prs_merged_in_window > 0, (
        f"canonical repo must have at least one merge in 30-day window; got {a.prs_merged_in_window}"
    )
