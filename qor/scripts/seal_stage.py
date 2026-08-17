"""Executable seal staging ceremony (Phase 229; GH #337).

The Step 9.5 enumeration drifted from reality for nine ceremony families and
staged a directory this repository does not have. The ceremony set is now a
constant exercised by tests/test_seal_stage.py; the skill invokes this module
instead of restating the list, so the document can no longer silently
understate what a seal commits.

Implementation files (source, tests, skills, references) remain the implement
phase's staging duty; this module stages ceremony artifacts only.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

#: Files every seal writes or may write. Absent paths are skipped, which also
#: retires the class of the old block's `git add src/` failure (no such tree).
CEREMONY_FILES = (
    "CHANGELOG.md",
    "README.md",
    "pyproject.toml",
    "docs/CONCEPT.md",
    "docs/ARCHITECTURE_PLAN.md",
    "docs/META_LEDGER.md",
    "docs/SYSTEM_STATE.md",
    "docs/BACKLOG.md",
    "docs/GOVERNANCE_INDEX.md",
    "docs/SHADOW_GENOME.md",
    "docs/PROCESS_SHADOW_GENOME.md",
    "docs/PROCESS_SHADOW_GENOME_UPSTREAM.md",
    ".agent/staging/AUDIT_REPORT.md",
)
#: The phase's plan and research briefs; the seal binds the plan by hash.
CEREMONY_GLOBS = (
    "docs/plan-qor-phase*.md",
    "docs/research-brief-*.md",
)
#: Trees the seal ceremony regenerates (Step 8.5 recompile; Step 7.9 specs).
CEREMONY_TREES = (
    "qor/dist",
    "qor/specs",
)


def _targets(session_id: str, repo_root: Path) -> list[str]:
    found: list[str] = []
    for rel in CEREMONY_FILES:
        if (repo_root / rel).is_file():
            found.append(rel)
    for pattern in CEREMONY_GLOBS:
        found.extend(sorted(p.relative_to(repo_root).as_posix()
                            for p in repo_root.glob(pattern)))
    for rel in CEREMONY_TREES:
        if (repo_root / rel).is_dir():
            found.append(rel)
    gate_dir = repo_root / ".qor" / "gates" / session_id
    if gate_dir.is_dir() and any(gate_dir.iterdir()):
        found.append(gate_dir.relative_to(repo_root).as_posix())
    return found


def stage(session_id: str, repo_root: Path | None = None) -> list[str]:
    """Stage the ceremony set for ``session_id``; return the staged targets.

    Only existing paths are passed to ``git add`` (list-form argv); paths
    outside the ceremony set are never touched.
    """
    root = repo_root or Path.cwd()
    targets = _targets(session_id, root)
    if targets:
        subprocess.run(["git", "add", "--"] + targets, cwd=root, check=True)
    return targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.seal_stage")
    parser.add_argument("--session", required=True)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    staged = stage(args.session, args.repo_root)
    print(f"seal-stage: {len(staged)} ceremony target(s) staged for {args.session}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
