"""Inline detector: workspace fragility / stabilization-capacity (Phase 94; GH #90).

Inspects local workspace signals (untracked file count, dirty gate artifacts,
ledger chain failures, branch count, branch-diff size) and computes a
``FragilityAssessment`` with three grades (``low`` / ``medium`` / ``high``).

Companion to Phase 93's ``merge_velocity_check`` (macro merge-pace at
substantiate); Phase 94 runs INLINE at ``/qor-audit`` Step 0.6 so the signal
surfaces before the cycle commits to scope. Per
``qor/references/doctrine-shadow-genome-countermeasures.md``
SG-MergePaceThrottle-A inline-companion sub-paragraph.

V1 WARN-only at substantiate-site via ``|| true``; CLI exits 1 on ``high`` so
V2 can convert to a hard ABORT.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


MEDIUM_UNTRACKED = 15
HIGH_UNTRACKED = 50
MEDIUM_DIRTY_GATES = 3
MEDIUM_BRANCHES = 10
MEDIUM_DIFF_LINES = 1500
HIGH_DIFF_LINES = 5000


@dataclass(frozen=True)
class FragilityAssessment:
    untracked_count: int
    dirty_gate_artifact_count: int
    ledger_chain_failure_count: int
    active_branch_count: int
    recent_commit_diff_lines: int
    workspace_fragility: str  # 'low' | 'medium' | 'high'
    stabilization_capacity: str   # Phase 129 (#154): merge_velocity vocab mirror
    shared_surface_risk: str      # Phase 129 (#154): 'low' | 'medium' | 'high'
    recommended_action: str   # 'merge_ok' | 'narrow_scope' | 'hardening_only' | 'branch_only'
    evidence: tuple[str, ...]


# Phase 129 (#154): restore #90's dropped contract.
_CAPACITY_FROM_GRADE = {"low": "healthy", "medium": "strained", "high": "exceeded"}


def _capacity_for(grade: str) -> str:
    """Re-express the fragility grade in merge_velocity's stabilization vocab."""
    return _CAPACITY_FROM_GRADE.get(grade, "healthy")


def _shared_surface_risk(active_branch_count: int, recent_commit_diff_lines: int) -> str:
    """Shared-surface churn proxy from concurrent branches + recent diff size."""
    if active_branch_count >= 10 or recent_commit_diff_lines >= 1500:
        return "high"
    if active_branch_count >= 5 or recent_commit_diff_lines >= 750:
        return "medium"
    return "low"


def _recommended_action(grade: str, shared_surface_risk: str) -> str:
    """`branch_only` (isolate) when shared-surface risk is high; else grade-based."""
    if shared_surface_risk == "high":
        return "branch_only"
    return _ACTION_FROM_GRADE[grade]


_ACTION_FROM_GRADE = {
    "low": "merge_ok",
    "medium": "narrow_scope",
    "high": "hardening_only",
}


def _git_status_untracked(repo_root: Path) -> int:
    """Count ``??`` lines from ``git status --short``."""
    result = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=str(repo_root), capture_output=True, text=True, check=False,
    )
    return sum(
        1 for line in result.stdout.splitlines()
        if line.startswith("?? ")
    )


def _dirty_gate_artifacts(repo_root: Path) -> int:
    """Count gate sessions under ``.qor/gates/`` whose session_id has no
    SESSION SEAL entry in META_LEDGER. Sessions sealed at HEAD are clean."""
    gates_root = repo_root / ".qor" / "gates"
    if not gates_root.is_dir():
        return 0
    ledger = repo_root / "docs" / "META_LEDGER.md"
    sealed_sids: set[str] = set()
    if ledger.is_file():
        text = ledger.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\*\*Session\*\*:\s*`([^`]+)`", text):
            sealed_sids.add(m.group(1))
    dirty = 0
    for session_dir in gates_root.iterdir():
        if not session_dir.is_dir():
            continue
        if session_dir.name not in sealed_sids:
            dirty += 1
    return dirty


def _ledger_chain_failures(repo_root: Path) -> int:
    """Count chain-math failures in META_LEDGER (excluding grandfathered
    residuals per Phase 91). Invokes ``verify-ledger`` with the tolerance
    flag so the SG-ConcurrentLedgerRace-A duplicates are not counted."""
    ledger = repo_root / "docs" / "META_LEDGER.md"
    if not ledger.is_file():
        return 0
    from qor.scripts.ledger_hash import verify
    import io
    from contextlib import redirect_stderr, redirect_stdout
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            verify(ledger, tolerate_known_grandfathered=True)
        except Exception:
            return 1
    return sum(1 for line in err.getvalue().splitlines() if line.startswith("FAIL "))


def _active_branch_count(repo_root: Path) -> int:
    """Count local branches via ``git branch``."""
    result = subprocess.run(
        ["git", "branch", "--list"],
        cwd=str(repo_root), capture_output=True, text=True, check=False,
    )
    return sum(1 for line in result.stdout.splitlines() if line.strip())


def _recent_commit_diff_lines(repo_root: Path) -> int:
    """Sum of added + deleted lines on the current branch since divergence
    from origin/main. Returns 0 when origin/main is absent or no divergence."""
    ref_check = subprocess.run(
        ["git", "rev-parse", "--verify", "origin/main"],
        cwd=str(repo_root), capture_output=True, text=True,
    )
    if ref_check.returncode != 0:
        return 0
    result = subprocess.run(
        ["git", "diff", "--shortstat", "origin/main..HEAD"],
        cwd=str(repo_root), capture_output=True, text=True, check=False,
    )
    text = result.stdout
    ins = re.search(r"(\d+)\s+insertion", text)
    dels = re.search(r"(\d+)\s+deletion", text)
    return (int(ins.group(1)) if ins else 0) + (int(dels.group(1)) if dels else 0)


def _grade(
    untracked: int,
    dirty_gates: int,
    ledger_failures: int,
    branches: int,
    diff_lines: int,
) -> str:
    if (
        ledger_failures > 0
        or untracked >= HIGH_UNTRACKED
        or diff_lines >= HIGH_DIFF_LINES
    ):
        return "high"
    if (
        untracked >= MEDIUM_UNTRACKED
        or dirty_gates >= MEDIUM_DIRTY_GATES
        or branches >= MEDIUM_BRANCHES
        or diff_lines >= MEDIUM_DIFF_LINES
    ):
        return "medium"
    return "low"


def _build_evidence(
    untracked: int,
    dirty_gates: int,
    ledger_failures: int,
    branches: int,
    diff_lines: int,
) -> tuple[str, ...]:
    out: list[str] = []
    if untracked >= MEDIUM_UNTRACKED:
        threshold = HIGH_UNTRACKED if untracked >= HIGH_UNTRACKED else MEDIUM_UNTRACKED
        out.append(f"untracked_count={untracked} >= {threshold} threshold")
    if dirty_gates >= MEDIUM_DIRTY_GATES:
        out.append(f"dirty_gate_artifact_count={dirty_gates} >= {MEDIUM_DIRTY_GATES}")
    if ledger_failures > 0:
        out.append(f"ledger_chain_failure_count={ledger_failures} > 0 (HIGH integrity signal)")
    if branches >= MEDIUM_BRANCHES:
        out.append(f"active_branch_count={branches} >= {MEDIUM_BRANCHES}")
    if diff_lines >= MEDIUM_DIFF_LINES:
        threshold = HIGH_DIFF_LINES if diff_lines >= HIGH_DIFF_LINES else MEDIUM_DIFF_LINES
        out.append(f"recent_commit_diff_lines={diff_lines} >= {threshold} threshold")
    return tuple(out)


def assess_workspace_fragility(repo_root: Path) -> FragilityAssessment:
    untracked = _git_status_untracked(repo_root)
    dirty_gates = _dirty_gate_artifacts(repo_root)
    ledger_failures = _ledger_chain_failures(repo_root)
    branches = _active_branch_count(repo_root)
    diff_lines = _recent_commit_diff_lines(repo_root)
    grade = _grade(untracked, dirty_gates, ledger_failures, branches, diff_lines)
    ssr = _shared_surface_risk(branches, diff_lines)
    return FragilityAssessment(
        untracked_count=untracked,
        dirty_gate_artifact_count=dirty_gates,
        ledger_chain_failure_count=ledger_failures,
        active_branch_count=branches,
        recent_commit_diff_lines=diff_lines,
        workspace_fragility=grade,
        stabilization_capacity=_capacity_for(grade),
        shared_surface_risk=ssr,
        recommended_action=_recommended_action(grade, ssr),
        evidence=_build_evidence(untracked, dirty_gates, ledger_failures, branches, diff_lines),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.workspace_fragility_check")
    parser.add_argument("--repo-root", required=True, type=Path)
    args = parser.parse_args(argv)
    a = assess_workspace_fragility(args.repo_root)
    print(
        f"workspace_fragility_check: fragility={a.workspace_fragility} "
        f"action={a.recommended_action}"
    )
    print(f"  untracked_count={a.untracked_count}")
    print(f"  dirty_gate_artifact_count={a.dirty_gate_artifact_count}")
    print(f"  ledger_chain_failure_count={a.ledger_chain_failure_count}")
    print(f"  active_branch_count={a.active_branch_count}")
    print(f"  recent_commit_diff_lines={a.recent_commit_diff_lines}")
    for line in a.evidence:
        print(f"  evidence: {line}")
    return 1 if a.workspace_fragility == "high" else 0


if __name__ == "__main__":
    sys.exit(main())
