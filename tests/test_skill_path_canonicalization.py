"""Phase 53: skill path-canonicalization lint (DRIFT-1, DRIFT-2 closure).

Walks `qor/skills/**/*.md` and asserts no skill body still references the
legacy `.failsafe/governance/` directory or `memory/failsafe-bridge.md`. The
repo migrated to `docs/`-based governance and `.agent/staging/` for
transient working state; references to the legacy paths render the skill
unrunnable.

Behavior invariant: a regression that re-introduces either substring would
fail this test, naming the offending file path.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "qor" / "skills"
AGENTS_DIR = REPO_ROOT / "qor" / "agents"

_FORBIDDEN = (
    ".failsafe/governance/",
    "memory/failsafe-bridge.md",
)


def _walk_skill_md_files() -> list[Path]:
    skill_files = list(SKILLS_DIR.rglob("*.md"))
    agent_files = list(AGENTS_DIR.rglob("*.md")) if AGENTS_DIR.exists() else []
    return sorted(skill_files + agent_files)


def test_no_skill_references_failsafe_governance():
    violations: list[str] = []
    for path in _walk_skill_md_files():
        body = path.read_text(encoding="utf-8")
        if ".failsafe/governance/" in body:
            violations.append(str(path.relative_to(REPO_ROOT)))
    assert not violations, (
        ".failsafe/governance/ legacy path detected in skill bodies; "
        f"replace with current canonical paths: {violations}"
    )


def test_no_skill_references_failsafe_bridge_memory():
    violations: list[str] = []
    for path in _walk_skill_md_files():
        body = path.read_text(encoding="utf-8")
        if "memory/failsafe-bridge.md" in body:
            violations.append(str(path.relative_to(REPO_ROOT)))
    assert not violations, (
        "memory/failsafe-bridge.md legacy path detected in skill bodies; "
        f"replace with current canonical paths: {violations}"
    )


def test_lint_walks_at_least_one_skill():
    """Sanity: the lint walks a non-empty file set.

    Without this assertion the lint could be vacuously passing — if the
    rglob returned zero files, no violations would ever surface.
    """
    files = _walk_skill_md_files()
    assert len(files) >= 10, (
        f"expected >=10 skill markdown files; got {len(files)}. "
        "Lint may be walking the wrong directory."
    )
