"""Phase 112 (#140): governance-index doctrine + glossary terms."""
from __future__ import annotations

from pathlib import Path

from yaml import safe_load

_REPO = Path(__file__).resolve().parent.parent
_DOCTRINE = _REPO / "qor" / "references" / "doctrine-governance-index.md"
_GLOSSARY = _REPO / "qor" / "references" / "glossary.md"


def test_doctrine_defines_six_tiers():
    text = _DOCTRINE.read_text(encoding="utf-8")
    for tier in ("Canonical Source", "Doctrine & Policy", "Active Initiative",
                 "Per-Plan Artifact", "Reference Material", "Archived"):
        assert tier in text, f"doctrine missing tier '{tier}'"
    assert "Governance Index Drift" in text
    assert "stale-tier1" in text


def _glossary_terms(text):
    terms = {}
    for block in text.split("```yaml"):
        body = block.split("```", 1)[0]
        if "term:" not in body:
            continue
        try:
            data = safe_load(body)
        except Exception:
            continue
        if isinstance(data, dict) and "term" in data:
            terms[data["term"]] = data
    return terms


def test_glossary_has_governance_index_terms():
    terms = _glossary_terms(_GLOSSARY.read_text(encoding="utf-8"))
    for name in ("Governance Index", "Governance Freshness Tier", "Governance Index Drift"):
        assert name in terms, f"glossary missing '{name}'"
        assert terms[name]["home"] == "qor/references/doctrine-governance-index.md"
