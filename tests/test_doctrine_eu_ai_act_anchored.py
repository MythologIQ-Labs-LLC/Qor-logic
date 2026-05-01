"""Phase 54: doctrine round-trip integrity for EU AI Act mapping."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE_PATH = REPO_ROOT / "qor" / "references" / "doctrine-eu-ai-act.md"

_CITED_ARTICLES: tuple[int, ...] = (9, 10, 12, 13, 14, 15, 50, 72)
_HEADING_RE = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)


def _section_body(content: str, heading_pattern: str) -> str:
    match = re.search(heading_pattern, content, re.MULTILINE)
    assert match, f"missing heading matching {heading_pattern!r}"
    rest = content[match.end():]
    next_h = _HEADING_RE.search(rest)
    return rest[: next_h.start()].strip() if next_h else rest.strip()


def test_doctrine_round_trip_against_articles():
    content = DOCTRINE_PATH.read_text(encoding="utf-8")
    for art in _CITED_ARTICLES:
        body = _section_body(content, rf"^###\s+Art\.\s+{art}\b.*$")
        assert body, f"Art. {art} section has empty body"
        compact = re.sub(r"\s+", " ", body).strip()
        assert len(compact) >= 30, f"Art. {art} body is too short: {compact!r}"


def test_doctrine_classifies_qor_logic_under_applicability_section_with_non_empty_body():
    content = DOCTRINE_PATH.read_text(encoding="utf-8")
    body = _section_body(content, r"^##\s+Applicability classification")
    assert body, "Applicability classification section has empty body"
    compact = re.sub(r"\s+", " ", body).strip()
    assert len(compact) >= 20, f"applicability body too short: {compact!r}"
    assert "Annex III" in body, "applicability body must mention Annex III"
    assert ("not high-risk" in body or "not classified as high-risk" in body), (
        "applicability body must declare the not-high-risk classification literally"
    )


def test_doctrine_declares_canonical_sections():
    content = DOCTRINE_PATH.read_text(encoding="utf-8")
    for canonical in (
        "## Applicability classification",
        "## Article-by-article mapping",
        "## Annex IV (Technical documentation) guidance",
        "## Limitations",
    ):
        assert canonical in content, f"missing canonical section: {canonical}"
