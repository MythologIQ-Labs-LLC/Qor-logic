"""Phase 25 Phase 4: canonical tone-aware rendering example.

Pins qor/skills/memory/qor-status/SKILL.md as the reference. Anchors the
doctrine in at least one skill whose rendering section passes tier-register
heuristics, closing the SG-Phase25-B ghost-feature pattern.
"""
from __future__ import annotations

import re
from pathlib import Path


CANONICAL = Path(__file__).resolve().parent.parent / "qor" / "skills" / "memory" / "qor-status" / "SKILL.md"

_TONE_OPEN = "<!-- qor:tone-aware-section -->"
_TONE_CLOSE = "<!-- /qor:tone-aware-section -->"

_TECHNICAL_REGISTER = re.compile(r"SG-[A-Za-z0-9-]+|OWASP|A0[0-9]|Merkle|sha256|SHA256|hash chain|verdict", re.IGNORECASE)
_HASH_TOKEN = re.compile(r"\b[a-f0-9]{8,}\b")


def _extract_tier_block(section: str, tier: str) -> str:
    """Return the text of one tier's sub-section."""
    pattern = re.compile(
        rf"###\s*{re.escape(tier)}\s*\n(.*?)(?=\n###\s|$)",
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(section)
    return match.group(1).strip() if match else ""


def test_canonical_skill_exists():
    assert CANONICAL.exists(), f"canonical tone example missing: {CANONICAL}"


def test_canonical_skill_has_tone_section():
    text = CANONICAL.read_text(encoding="utf-8")
    assert _TONE_OPEN in text, f"{CANONICAL}: missing {_TONE_OPEN}"
    assert _TONE_CLOSE in text, f"{CANONICAL}: missing {_TONE_CLOSE}"


def test_canonical_tiers_have_register_fragments():
    text = CANONICAL.read_text(encoding="utf-8")
    start = text.index(_TONE_OPEN) + len(_TONE_OPEN)
    end = text.index(_TONE_CLOSE)
    section = text[start:end]

    technical_block = _extract_tier_block(section, "technical")
    standard_block = _extract_tier_block(section, "standard")
    plain_block = _extract_tier_block(section, "plain")

    assert technical_block, "canonical skill: technical tier block empty"
    assert standard_block, "canonical skill: standard tier block empty"
    assert plain_block, "canonical skill: plain tier block empty"

    assert _TECHNICAL_REGISTER.search(technical_block), (
        "technical tier must contain a technical register token (SG, OWASP, Merkle, sha256, verdict, ...)"
    )
    assert not _TECHNICAL_REGISTER.search(plain_block), (
        "plain tier must avoid technical jargon; register heuristic hit"
    )
    assert not _HASH_TOKEN.search(plain_block), (
        "plain tier must avoid hash-looking tokens in body"
    )
