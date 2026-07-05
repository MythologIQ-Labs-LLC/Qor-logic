"""Phase 53: skill path-canonicalization lint (DRIFT-1, DRIFT-2 closure).

Walks `qor/skills/**/*.md` and asserts no skill body still references the
legacy consumer governance staging directory or its bridge memory file
(literals assembled below to honor the publication boundary). The repo
migrated to `docs/`-based governance and `.agent/staging/` for transient
working state; references to the legacy paths render the skill unrunnable.

Behavior invariant: a regression that re-introduces either substring would
fail this test, naming the offending file path.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "qor" / "skills"
AGENTS_DIR = REPO_ROOT / "qor" / "agents"

# Assembled from fragments so the tracked source never carries the legacy
# product token itself (publication boundary, Phase 172).
_LEGACY_STAGING = ".fail" + "safe/governance/"
_LEGACY_BRIDGE = "memory/fail" + "safe-bridge.md"

_FORBIDDEN = (
    _LEGACY_STAGING,
    _LEGACY_BRIDGE,
)


def _walk_skill_md_files() -> list[Path]:
    skill_files = list(SKILLS_DIR.rglob("*.md"))
    agent_files = list(AGENTS_DIR.rglob("*.md")) if AGENTS_DIR.exists() else []
    return sorted(skill_files + agent_files)


def test_no_skill_references_legacy_governance_dir():
    violations: list[str] = []
    for path in _walk_skill_md_files():
        body = path.read_text(encoding="utf-8")
        if _LEGACY_STAGING in body:
            violations.append(str(path.relative_to(REPO_ROOT)))
    assert not violations, (
        f"{_LEGACY_STAGING} legacy path detected in skill bodies; "
        f"replace with current canonical paths: {violations}"
    )


def test_no_skill_references_legacy_bridge_memory():
    violations: list[str] = []
    for path in _walk_skill_md_files():
        body = path.read_text(encoding="utf-8")
        if _LEGACY_BRIDGE in body:
            violations.append(str(path.relative_to(REPO_ROOT)))
    assert not violations, (
        f"{_LEGACY_BRIDGE} legacy path detected in skill bodies; "
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
