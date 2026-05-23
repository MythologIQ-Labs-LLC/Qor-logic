"""Phase 94: behavior tests for qor.scripts.workspace_fragility_check (GH #90).

Scratch-repo fixtures + canonical-repo forward-only guard.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qor.scripts.workspace_fragility_check import (
    FragilityAssessment,
    assess_workspace_fragility,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str], cwd: Path) -> str:
    return subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, check=True,
    ).stdout


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", "-b", "main"], cwd=repo)
    _run(["git", "config", "user.email", "t@e.com"], cwd=repo)
    _run(["git", "config", "user.name", "T"], cwd=repo)
    (repo / "README.md").write_text("x\n")
    _run(["git", "add", "."], cwd=repo)
    _run(["git", "commit", "-m", "init"], cwd=repo)
    return repo


def test_assess_low_grade_for_clean_workspace(tmp_path):
    repo = _make_repo(tmp_path)
    a = assess_workspace_fragility(repo)
    assert a.workspace_fragility == "low", (
        f"expected low; got {a.workspace_fragility} (evidence={a.evidence})"
    )


def test_assess_medium_grade_when_untracked_count_at_threshold(tmp_path):
    repo = _make_repo(tmp_path)
    for i in range(16):
        (repo / f"untracked_{i}.txt").write_text("x")
    a = assess_workspace_fragility(repo)
    assert a.workspace_fragility == "medium", (
        f"expected medium with 16 untracked; got {a.workspace_fragility}"
    )
    assert a.untracked_count == 16


def test_assess_high_grade_for_ledger_chain_failure(tmp_path):
    repo = _make_repo(tmp_path)
    docs = repo / "docs"
    docs.mkdir()
    # Build a META_LEDGER with a deliberately bad chain hash.
    (docs / "META_LEDGER.md").write_text(
        "# META_LEDGER\n\n"
        "### Entry #1: TEST\n\n"
        "**Content Hash**: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`\n\n"
        "**Previous Hash**: `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`\n\n"
        "**Chain Hash**: `ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff`\n",
        encoding="utf-8",
    )
    a = assess_workspace_fragility(repo)
    assert a.workspace_fragility == "high", (
        f"expected high on chain-failure ledger; got {a.workspace_fragility} "
        f"(chain_failures={a.ledger_chain_failure_count})"
    )
    assert a.ledger_chain_failure_count > 0


def test_active_branch_count_counts_local_branches(tmp_path):
    repo = _make_repo(tmp_path)
    for i in range(5):
        _run(["git", "branch", f"feat-{i}"], cwd=repo)
    a = assess_workspace_fragility(repo)
    # main + 5 feature branches = 6
    assert a.active_branch_count == 6, (
        f"expected 6 branches; got {a.active_branch_count}"
    )


def test_dirty_gate_artifact_count_finds_unsealed_sessions(tmp_path):
    repo = _make_repo(tmp_path)
    gates = repo / ".qor" / "gates" / "test-session-X"
    gates.mkdir(parents=True)
    (gates / "plan.json").write_text("{}")
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs" / "META_LEDGER.md").write_text("# empty\n", encoding="utf-8")
    a = assess_workspace_fragility(repo)
    assert a.dirty_gate_artifact_count >= 1, (
        f"expected at least 1 dirty session; got {a.dirty_gate_artifact_count}"
    )


def test_recommended_action_maps_from_grade(tmp_path):
    repo = _make_repo(tmp_path)
    a_low = assess_workspace_fragility(repo)
    assert a_low.recommended_action == "merge_ok"

    # medium via untracked
    for i in range(16):
        (repo / f"u_{i}.txt").write_text("x")
    a_med = assess_workspace_fragility(repo)
    assert a_med.recommended_action == "narrow_scope"


def test_evidence_list_names_threshold_for_each_fired_signal(tmp_path):
    repo = _make_repo(tmp_path)
    for i in range(20):
        (repo / f"u_{i}.txt").write_text("x")
    a = assess_workspace_fragility(repo)
    assert any("untracked_count=20" in e for e in a.evidence), (
        f"expected untracked_count evidence; got: {a.evidence}"
    )


def test_main_cli_exits_zero_on_low_or_medium(tmp_path):
    repo = _make_repo(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.workspace_fragility_check",
         "--repo-root", str(repo)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0


def test_main_cli_exits_one_on_high(tmp_path):
    repo = _make_repo(tmp_path)
    docs = repo / "docs"
    docs.mkdir()
    (docs / "META_LEDGER.md").write_text(
        "# META_LEDGER\n\n"
        "### Entry #1: TEST\n\n"
        "**Content Hash**: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`\n\n"
        "**Previous Hash**: `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`\n\n"
        "**Chain Hash**: `ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff`\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.workspace_fragility_check",
         "--repo-root", str(repo)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 1, (
        f"expected exit 1 on high; got {result.returncode}; stdout={result.stdout!r}"
    )


def test_assess_fragility_on_qor_logic_main():
    """Canonical-repo forward-only guard."""
    a = assess_workspace_fragility(REPO_ROOT)
    assert a.workspace_fragility in {"low", "medium", "high"}
    assert a.active_branch_count > 0
