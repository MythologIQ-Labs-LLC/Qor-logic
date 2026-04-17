"""Phase 25 Phase 4: tone_aware frontmatter + rendering section enforcement.

Closes SG-Phase25-B (ghost feature via metadata-only declaration): every
`tone_aware: true` skill must contain a canonical rendering section with
per-tier instructions, not merely declare the flag.
"""
from __future__ import annotations

import re
from pathlib import Path

from yaml import safe_load


_TONE_OPEN = "<!-- qor:tone-aware-section -->"
_TONE_CLOSE = "<!-- /qor:tone-aware-section -->"
_TIERS = ("technical", "standard", "plain")

# Declarative list of skills that WRITE evidentiary artifacts. Must be
# tone_aware: false. Token-count heuristics conflate read with write and
# false-positive on skills that merely reference evidentiary files. The
# declarative list is the source of truth; plan-level discipline maintains it.
_EVIDENTIARY_WRITERS = frozenset({
    "qor-audit",
    "qor-substantiate",
    "qor-validate",
    "qor-implement",
    "qor-plan",
    "qor-research",
    "qor-bootstrap",
    "qor-refactor",
    "qor-remediate",
    "qor-deep-audit",
    "qor-deep-audit-recon",
    "qor-deep-audit-remediate",
    "qor-shadow-process",
    "qor-governance-compliance",
    "qor-process-review-cycle",
    "qor-meta-log-decision",
    "qor-meta-track-shadow",
    "qor-repo-release",
})


def _read_frontmatter(text: str) -> dict:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    meta = safe_load(text[4:end]) or {}
    return meta if isinstance(meta, dict) else {}


def _walk_skills() -> list[Path]:
    root = Path(__file__).resolve().parent.parent / "qor" / "skills"
    return list(root.rglob("SKILL.md"))


def _between_markers(text: str) -> str | None:
    start = text.find(_TONE_OPEN)
    if start < 0:
        return None
    end = text.find(_TONE_CLOSE, start)
    if end < 0:
        return None
    return text[start + len(_TONE_OPEN):end]


def test_every_skill_declares_tone_aware():
    for skill_md in _walk_skills():
        text = skill_md.read_text(encoding="utf-8")
        meta = _read_frontmatter(text)
        assert "tone_aware" in meta, f"{skill_md}: missing tone_aware frontmatter"
        assert meta["tone_aware"] in (True, False), (
            f"{skill_md}: tone_aware must be true or false, got {meta['tone_aware']!r}"
        )


def test_evidentiary_writer_skills_are_not_tone_aware():
    """Skills that write hash-chained / evidentiary artifacts must be tone_aware: false.

    Uses the declarative inventory above rather than a token heuristic so that
    status/help skills that merely READ evidentiary files (e.g., qor-status
    reads META_LEDGER to report chain status) can remain tone_aware: true.
    """
    for skill_md in _walk_skills():
        skill_name = skill_md.parent.name
        if skill_name not in _EVIDENTIARY_WRITERS:
            continue
        text = skill_md.read_text(encoding="utf-8")
        meta = _read_frontmatter(text)
        assert meta.get("tone_aware") is False, (
            f"{skill_md}: evidentiary-writer skill {skill_name!r} must be "
            f"tone_aware=false; got {meta.get('tone_aware')!r}"
        )


def test_tone_aware_skills_have_rendering_section():
    for skill_md in _walk_skills():
        text = skill_md.read_text(encoding="utf-8")
        meta = _read_frontmatter(text)
        if not meta.get("tone_aware"):
            continue
        body = _between_markers(text)
        assert body is not None, (
            f"{skill_md}: tone_aware=true but missing "
            f"{_TONE_OPEN} ... {_TONE_CLOSE} markers"
        )
        for tier in _TIERS:
            assert tier in body, f"{skill_md}: rendering section missing tier {tier!r}"
        # Non-empty content between tier headers
        lines = [l.strip() for l in body.splitlines() if l.strip()]
        assert len(lines) >= 6, (
            f"{skill_md}: rendering section too sparse "
            f"(expected >=6 non-blank lines for 3 tiers with instructions)"
        )
