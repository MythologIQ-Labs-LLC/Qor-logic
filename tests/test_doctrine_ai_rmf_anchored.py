"""Phase 54: doctrine round-trip integrity for AI RMF + AI 600-1 mapping."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE_PATH = REPO_ROOT / "qor" / "references" / "doctrine-ai-rmf.md"

_RMF_FUNCTIONS: tuple[str, ...] = ("GOVERN", "MAP", "MEASURE", "MANAGE")
_GENAI_SECTIONS: tuple[str, ...] = ("2.4", "2.7", "2.8", "2.10", "2.12")

_HEADING_RE = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)


def _section_body(content: str, heading_pattern: str) -> str:
    match = re.search(heading_pattern, content, re.MULTILINE)
    assert match, f"missing heading matching {heading_pattern!r}"
    rest = content[match.end():]
    next_h = _HEADING_RE.search(rest)
    return rest[: next_h.start()].strip() if next_h else rest.strip()


def test_doctrine_round_trip_against_functions():
    content = DOCTRINE_PATH.read_text(encoding="utf-8")
    for func in _RMF_FUNCTIONS:
        body = _section_body(content, rf"^##\s+{func}\b")
        assert body, f"{func} section has empty body"
        compact = re.sub(r"\s+", " ", body).strip()
        assert len(compact) >= 30, f"{func} body too short: {compact!r}"


def test_doctrine_round_trip_against_genai_profile_sections():
    """Each cited GenAI profile section must appear in the §2 table with a status marker."""
    content = DOCTRINE_PATH.read_text(encoding="utf-8")
    genai_body = _section_body(content, r"^##\s+NIST AI 600-1.*Generative AI Profile")
    assert genai_body, "GenAI profile section has empty body"
    for sec in _GENAI_SECTIONS:
        assert f"| {sec} |" in genai_body, (
            f"GenAI section §{sec} missing from profile table"
        )


def test_doctrine_declares_canonical_sections():
    content = DOCTRINE_PATH.read_text(encoding="utf-8")
    for canonical in (
        "## Framework summary",
        "## GOVERN",
        "## MAP",
        "## MEASURE",
        "## MANAGE",
        "## Evidence-collection contract",
    ):
        assert canonical in content, f"missing canonical section: {canonical}"


def test_doctrine_evidence_contract_cites_phase54_provenance():
    content = DOCTRINE_PATH.read_text(encoding="utf-8")
    body = _section_body(content, r"^##\s+Evidence-collection contract")
    assert "ai_provenance" in body, "evidence contract must cite ai_provenance field"
    assert "MEASURE-2.1" in body, "evidence contract must cite MEASURE-2.1"
    assert "MANAGE-1.1" in body, "evidence contract must cite MANAGE-1.1"
