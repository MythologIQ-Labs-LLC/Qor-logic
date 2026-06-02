"""Detector: merge-pace throttle for stabilization-capacity governance (Phase 93).

Inspects ``origin/main``'s recent merge history via ``git log`` (offline-safe;
no GitHub API dependency) and computes a ``VelocityAssessment`` with three
stabilization-capacity grades: ``healthy``, ``strained``, ``exceeded``.

Invoked at ``/qor-substantiate`` Step 4.6.8 in WARN-only V1 contract; CLI exits
0 on healthy/strained and 1 on exceeded so V2 may convert to a hard ABORT by
removing the ``|| true`` wrap at the substantiate site.

Closes the detector half of GH #89; enforcement (hold-feature-merges,
require-stabilization-plan) is reserved for V2. Per
``qor/references/doctrine-shadow-genome-countermeasures.md`` SG-MergePaceThrottle-A.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from qor.scripts import shadow_process

# Threshold constants exposed at module scope for V1 transparency.
STRAINED_PR_COUNT = 10
EXCEEDED_PR_COUNT = 20
STRAINED_REPAIR_DENSITY = 0.20
EXCEEDED_REPAIR_DENSITY = 0.30
EXCEEDED_SHARED_CORE_TOUCHES = 10

_REPAIR_KEYWORDS = ("fix", "hotfix", "repair", "regression", "rollback", "revert")
# Match a leading repair keyword as the subject prefix (case-insensitive),
# allowing ``fix:`` / ``fix(scope):`` / ``Fix ``.
_REPAIR_SUBJECT_RE = re.compile(
    r"^\s*(" + "|".join(_REPAIR_KEYWORDS) + r")[:\s(]",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class VelocityAssessment:
    prs_merged_in_window: int
    additions_total: int
    repair_density: float
    shared_core_touch_count: int
    stabilization_capacity: str
    recommended_action: str
    evidence: tuple[str, ...]
    window_days: int


def _git_log_merges_in_window(repo_root: Path, window_days: int) -> list[tuple[str, str]]:
    """Return [(commit_sha, subject), ...] for merge commits within the window.

    Filters by committer date in Python rather than relying on
    ``git log --since``, which stops walking at the first ancestor older
    than the cutoff -- a behavior that drops valid in-window merges when
    the history is non-monotonic (e.g., a back-dated merge in the middle
    of the chain). Walks the full ``--merges`` log unbounded, then keeps
    commits whose committer date is within the window.
    """
    from datetime import datetime, timezone

    ref_check = subprocess.run(
        ["git", "rev-parse", "--verify", "origin/main"],
        cwd=str(repo_root), capture_output=True, text=True,
    )
    ref = "origin/main" if ref_check.returncode == 0 else "HEAD"
    result = subprocess.run(
        [
            "git", "log", ref, "--merges",
            "--pretty=format:%H%x00%cI%x00%s",
        ],
        cwd=str(repo_root), capture_output=True, text=True, check=True,
    )
    cutoff_epoch = datetime.now(timezone.utc).timestamp() - (window_days * 86400)
    out: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x00", 2)
        if len(parts) < 3:
            continue
        sha, iso_date, subject = parts
        try:
            commit_epoch = datetime.fromisoformat(iso_date).timestamp()
        except ValueError:
            continue
        if commit_epoch >= cutoff_epoch:
            out.append((sha, subject))
    return out


def _additions_for_commit(repo_root: Path, sha: str) -> int:
    """Return line-additions brought in by a commit. Uses ``git diff
    --shortstat <sha>^..<sha>`` so merge commits surface the line counts
    from the merged branch (``git show --shortstat`` returns empty for
    clean merges)."""
    result = subprocess.run(
        ["git", "diff", "--shortstat", f"{sha}^..{sha}"],
        cwd=str(repo_root), capture_output=True, text=True, check=True,
    )
    m = re.search(r"(\d+)\s+insertion", result.stdout)
    return int(m.group(1)) if m else 0


def _changed_paths_for_commit(repo_root: Path, sha: str) -> list[str]:
    """Return paths changed by a commit. Uses ``git diff --name-only
    <sha>^..<sha>`` so merge commits surface the files that the merge
    introduced relative to the first parent (``git show --name-only``
    returns empty for clean merges)."""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{sha}^..{sha}"],
        cwd=str(repo_root), capture_output=True, text=True, check=True,
    )
    return [p.strip() for p in result.stdout.splitlines() if p.strip()]


def _is_repair_subject(subject: str) -> bool:
    return bool(_REPAIR_SUBJECT_RE.match(subject))


def _touches_shared_core(paths: list[str], patterns: tuple[str, ...]) -> bool:
    if not patterns:
        return False
    return any(any(p.startswith(pat) for pat in patterns) for p in paths)


def _grade(prs: int, repair_density: float, shared_core_touches: int) -> str:
    if prs >= EXCEEDED_PR_COUNT and (
        repair_density >= EXCEEDED_REPAIR_DENSITY
        or shared_core_touches >= EXCEEDED_SHARED_CORE_TOUCHES
    ):
        return "exceeded"
    if prs >= STRAINED_PR_COUNT or repair_density >= STRAINED_REPAIR_DENSITY:
        return "strained"
    return "healthy"


_ACTION_FROM_GRADE = {
    "healthy": "merge_ok",
    "strained": "narrow_scope",
    "exceeded": "branch_only",
}


def _build_evidence(
    prs: int,
    additions: int,
    repair_density: float,
    shared_core_touches: int,
) -> tuple[str, ...]:
    out: list[str] = []
    if prs >= STRAINED_PR_COUNT:
        threshold = EXCEEDED_PR_COUNT if prs >= EXCEEDED_PR_COUNT else STRAINED_PR_COUNT
        out.append(f"prs_merged_in_window={prs} >= {threshold} threshold")
    if repair_density >= STRAINED_REPAIR_DENSITY:
        threshold = (
            EXCEEDED_REPAIR_DENSITY
            if repair_density >= EXCEEDED_REPAIR_DENSITY
            else STRAINED_REPAIR_DENSITY
        )
        out.append(f"repair_density={repair_density:.2f} >= {threshold} threshold")
    if shared_core_touches >= EXCEEDED_SHARED_CORE_TOUCHES:
        out.append(
            f"shared_core_touch_count={shared_core_touches} >= "
            f"{EXCEEDED_SHARED_CORE_TOUCHES} threshold"
        )
    if additions > 0:
        out.append(f"additions_total={additions}")
    return tuple(out)


def assess_merge_velocity(
    repo_root: Path,
    *,
    window_days: int = 7,
    shared_core_paths: tuple[str, ...] = (),
) -> VelocityAssessment:
    merges = _git_log_merges_in_window(repo_root, window_days)
    prs = len(merges)
    additions = sum(_additions_for_commit(repo_root, sha) for sha, _ in merges)
    repair_count = sum(1 for _, subj in merges if _is_repair_subject(subj))
    repair_density = (repair_count / prs) if prs > 0 else 0.0
    if shared_core_paths:
        shared_core_touches = sum(
            1 for sha, _ in merges
            if _touches_shared_core(_changed_paths_for_commit(repo_root, sha), shared_core_paths)
        )
    else:
        shared_core_touches = 0
    grade = _grade(prs, repair_density, shared_core_touches)
    action = _ACTION_FROM_GRADE[grade]
    evidence = _build_evidence(prs, additions, repair_density, shared_core_touches)
    return VelocityAssessment(
        prs_merged_in_window=prs,
        additions_total=additions,
        repair_density=round(repair_density, 4),
        shared_core_touch_count=shared_core_touches,
        stabilization_capacity=grade,
        recommended_action=action,
        evidence=evidence,
        window_days=window_days,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.merge_velocity_check")
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--window-days", type=int, default=7)
    parser.add_argument(
        "--shared-core-path", action="append", default=[],
        help="path prefix counted as shared-core (repeatable)",
    )
    parser.add_argument(
        "--override", action="store_true",
        help="accept an 'exceeded' grade for this seal; emit a logged "
             "gate_override event and pass (Phase 129 enforcer escape)",
    )
    args = parser.parse_args(argv)
    a = assess_merge_velocity(
        args.repo_root,
        window_days=args.window_days,
        shared_core_paths=tuple(args.shared_core_path),
    )
    print(
        f"merge_velocity_check: stabilization_capacity={a.stabilization_capacity} "
        f"action={a.recommended_action}"
    )
    print(f"  prs_merged_in_window={a.prs_merged_in_window} (window={a.window_days}d)")
    print(f"  additions_total={a.additions_total}")
    print(f"  repair_density={a.repair_density}")
    print(f"  shared_core_touch_count={a.shared_core_touch_count}")
    for line in a.evidence:
        print(f"  evidence: {line}")
    # Phase 129 (#153): enforce on exceeded. The substantiate Step 4.6.8 wiring
    # is now `|| ABORT`; --override is the logged operator escape.
    if a.stabilization_capacity != "exceeded":
        return 0
    if args.override:
        shadow_process.append_event({
            "ts": shadow_process.now_iso(),
            "skill": "qor-substantiate",
            "session_id": "merge-velocity-check",
            "event_type": "gate_override",
            "severity": 2,
            "details": {
                "gate": "merge_velocity_check",
                "grade": a.stabilization_capacity,
                "recommended_action": a.recommended_action,
            },
            "addressed": False, "issue_url": None, "addressed_ts": None,
            "addressed_reason": None, "source_entry_id": None,
        })
        print("merge_velocity_check: OVERRIDE (exceeded grade accepted; gate_override logged)")
        return 0
    print("merge_velocity_check: ABORT (stabilization capacity exceeded)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
