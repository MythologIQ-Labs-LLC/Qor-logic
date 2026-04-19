"""Governance helpers for Phase 13 v4 (branching + versioning + tagging).

Pure functions; all git interactions isolated to module-level helpers
(`_current_branch`, `_list_tags`) so tests can monkeypatch them.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path


class InterdictionError(RuntimeError):
    """Raised when a governance precondition blocks an operation (V-4)."""


_PHASE_FILENAME_RE = re.compile(r"^plan-qor-phase(\d+)-([a-z0-9-]+)\.md$")
_CHANGE_CLASS_RE = re.compile(
    r"^\*\*change_class\*\*:\s+(hotfix|feature|breaking)\s*$",
    re.MULTILINE,
)
_BRANCH_PHASE_RE = re.compile(r"^phase/(\d+)-")
_VERSION_RE = re.compile(r'^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', re.MULTILINE)


def _current_branch() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def _list_tags() -> list[str]:
    result = subprocess.run(
        ["git", "tag", "--list", "v*"],
        capture_output=True, text=True, check=True,
    )
    return [t.strip() for t in result.stdout.splitlines() if t.strip()]


def current_branch() -> str:
    return _current_branch()


def derive_phase_metadata(plan_path: Path) -> tuple[int, str]:
    m = _PHASE_FILENAME_RE.match(Path(plan_path).name)
    if not m:
        raise ValueError(
            f"Plan filename must match plan-qor-phase<digits>-<slug>.md (got {plan_path.name!r}); "
            f"letter-suffix legacy (e.g. 11d) is grandfathered and rejected here."
        )
    return int(m.group(1)), m.group(2)


def current_phase_plan_path(docs_dir: Path | None = None) -> Path:
    docs_dir = Path(docs_dir) if docs_dir else Path("docs")
    branch = _current_branch()
    m = _BRANCH_PHASE_RE.match(branch)
    if not m:
        raise InterdictionError(f"Not on a phase branch: {branch!r}")
    nn = int(m.group(1))
    candidates = sorted(docs_dir.glob(f"plan-qor-phase{nn}*.md"))
    if not candidates:
        raise FileNotFoundError(f"No plan for phase {nn} in {docs_dir}")
    return candidates[-1]


def parse_change_class(plan_path: Path) -> str:
    text = Path(plan_path).read_text(encoding="utf-8")
    m = _CHANGE_CLASS_RE.search(text)
    if not m:
        raise ValueError(
            f"{plan_path} header missing canonical `**change_class**: "
            f"<hotfix|feature|breaking>` (bold required per V-2)."
        )
    return m.group(1)


def _parse_version(text: str) -> tuple[int, int, int]:
    m = _VERSION_RE.search(text)
    if not m:
        raise ValueError("pyproject.toml missing [project] version")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _compute_new(major: int, minor: int, patch: int, change_class: str) -> tuple[int, int, int]:
    if change_class == "hotfix":
        return major, minor, patch + 1
    if change_class == "feature":
        return major, minor + 1, 0
    if change_class == "breaking":
        return major + 1, 0, 0
    raise ValueError(f"unknown change_class: {change_class!r}")


def _highest_tag(tags: list[str]) -> tuple[int, int, int] | None:
    parsed: list[tuple[int, int, int]] = []
    for t in tags:
        m = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", t)
        if m:
            parsed.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    return max(parsed) if parsed else None


def bump_version(change_class: str, pyproject_path: Path | None = None) -> str:
    pyproject_path = Path(pyproject_path) if pyproject_path else Path("pyproject.toml")
    text = pyproject_path.read_text(encoding="utf-8")
    cur = _parse_version(text)
    new = _compute_new(*cur, change_class)
    new_str = f"{new[0]}.{new[1]}.{new[2]}"
    tags = _list_tags()
    if f"v{new_str}" in tags:
        raise InterdictionError(f"tag v{new_str} already exists")
    highest = _highest_tag(tags)
    if highest is not None and new <= highest:
        raise InterdictionError(
            f"target v{new_str} <= current highest tag v{highest[0]}.{highest[1]}.{highest[2]} (downgrade guard)"
        )
    new_text = _VERSION_RE.sub(f'version = "{new_str}"', text, count=1)
    tmp = pyproject_path.with_suffix(pyproject_path.suffix + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    os.replace(tmp, pyproject_path)
    return new_str


def create_seal_tag(
    version: str, seal: str, entry: int, phase: int, klass: str, commit: str,
) -> str:
    tag = f"v{version}"
    message = (
        f"v{version}\n\n"
        f"Merkle seal: {seal}\n"
        f"Ledger entry: #{entry}\n"
        f"Phase: {phase}\n"
        f"Class: {klass}\n"
    )
    subprocess.run(
        ["git", "tag", "-a", tag, commit, "-m", message], check=True,
    )
    return tag


def create_phase_branch(phase: int, slug: str) -> str:
    status = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, check=True,
    )
    if status.stdout.strip():
        raise InterdictionError("working tree dirty; stash/commit/abandon before branching")
    branch = f"phase/{phase:02d}-{slug}"
    subprocess.run(["git", "checkout", "-b", branch], check=True)
    return branch
