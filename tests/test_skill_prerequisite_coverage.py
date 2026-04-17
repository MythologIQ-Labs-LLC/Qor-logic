"""Phase 25 Phase 3: prerequisite coverage locks the autonomy inventory."""
from __future__ import annotations

from pathlib import Path

from yaml import safe_load


EXPECTED_AUTONOMY = {
    "qor-deep-audit": "autonomous",
    "qor-deep-audit-recon": "autonomous",
    "qor-deep-audit-remediate": "autonomous",
    "qor-audit": "interactive",
    "qor-validate": "interactive",
    "qor-substantiate": "interactive",
    "qor-implement": "interactive",
    "qor-document": "interactive",
    "qor-repo-release": "interactive",
    "qor-bootstrap": "interactive",
    "qor-organize": "interactive",
}

SKILL_PATHS = {
    "qor-deep-audit": "meta/qor-deep-audit/SKILL.md",
    "qor-deep-audit-recon": "meta/qor-deep-audit-recon/SKILL.md",
    "qor-deep-audit-remediate": "meta/qor-deep-audit-remediate/SKILL.md",
    "qor-audit": "governance/qor-audit/SKILL.md",
    "qor-validate": "governance/qor-validate/SKILL.md",
    "qor-substantiate": "governance/qor-substantiate/SKILL.md",
    "qor-implement": "sdlc/qor-implement/SKILL.md",
    "qor-document": "memory/qor-document/SKILL.md",
    "qor-repo-release": "meta/qor-repo-release/SKILL.md",
    "qor-bootstrap": "meta/qor-bootstrap/SKILL.md",
    "qor-organize": "memory/qor-organize/SKILL.md",
}


def _repo() -> Path:
    return Path(__file__).resolve().parent.parent


def _skills_root() -> Path:
    return _repo() / "qor" / "skills"


def _read_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    meta = safe_load(text[4:end]) or {}
    return meta if isinstance(meta, dict) else {}


def test_inventory_declares_expected_autonomy():
    for name, expected in EXPECTED_AUTONOMY.items():
        path = _skills_root() / SKILL_PATHS[name]
        assert path.exists(), f"skill file missing: {path}"
        meta = _read_frontmatter(path.read_text(encoding="utf-8"))
        assert meta.get("autonomy") == expected, (
            f"{name}: expected autonomy={expected!r}, got {meta.get('autonomy')!r}"
        )


def test_autonomous_skills_have_no_recovery_prompt():
    for name, mode in EXPECTED_AUTONOMY.items():
        if mode != "autonomous":
            continue
        text = (_skills_root() / SKILL_PATHS[name]).read_text(encoding="utf-8")
        assert "<!-- qor:recovery-prompt -->" not in text, (
            f"autonomous skill {name} must not contain qor:recovery-prompt"
        )


def test_interactive_skills_with_interdiction_have_recovery_marker():
    for name, mode in EXPECTED_AUTONOMY.items():
        if mode != "interactive":
            continue
        text = (_skills_root() / SKILL_PATHS[name]).read_text(encoding="utf-8")
        if "**INTERDICTION**" not in text:
            continue
        assert (
            "<!-- qor:recovery-prompt -->" in text
            or "<!-- qor:fail-fast-only" in text
        ), f"interactive skill {name} has INTERDICTION without recovery or fail-fast marker"


def test_doctrine_file_exists_and_lists_banned_phrases():
    doctrine = _repo() / "qor" / "references" / "doctrine-prompt-resilience.md"
    assert doctrine.exists()
    text = doctrine.read_text(encoding="utf-8")
    for phrase in [
        "wait for user", "confirm before", "pause here",
        "Ready to proceed?", "Continue?", "Ask the user to proceed",
    ]:
        assert phrase in text, f"doctrine missing banned phrase: {phrase!r}"
    assert "autonomous" in text and "interactive" in text


def test_skill_recovery_pattern_reference_exists_with_both_markers():
    ref = _repo() / "qor" / "references" / "skill-recovery-pattern.md"
    assert ref.exists()
    text = ref.read_text(encoding="utf-8")
    assert "qor:recovery-prompt" in text
    assert "qor:auto-heal" in text
    assert "qorlogic seed" in text


def test_every_skill_file_declares_autonomy_or_defaults_interactive():
    """Non-inventory skills default to interactive; we accept missing
    autonomy keys as an implicit interactive declaration.
    This test guards against a skill gaining 'autonomy: bogus-value'."""
    root = _skills_root()
    for skill_md in root.rglob("SKILL.md"):
        text = skill_md.read_text(encoding="utf-8")
        meta = _read_frontmatter(text)
        autonomy = meta.get("autonomy")
        if autonomy is None:
            continue
        assert autonomy in ("autonomous", "interactive"), (
            f"{skill_md}: invalid autonomy={autonomy!r}"
        )
