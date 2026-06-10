"""Phase 113 (#139): shadow-genome-graph doctrine + glossary."""
from __future__ import annotations

from pathlib import Path

from yaml import safe_load

_REPO = Path(__file__).resolve().parent.parent
_DOCTRINE = _REPO / "qor" / "references" / "doctrine-shadow-genome-graph.md"
_GLOSSARY = _REPO / "qor" / "references" / "glossary.md"


def test_doctrine_defines_types_and_scope_boundary():
    text = _DOCTRINE.read_text(encoding="utf-8")
    for node_type in ("checkpoint", "state", "failure", "governance"):
        assert node_type in text, f"missing node type {node_type}"
    for edge_type in ("produced", "occurred_during", "triggered_by", "applies_to"):
        assert edge_type in text, f"missing edge type {edge_type}"
    low = text.lower()
    # #213: the trust/federation/maturity surfaces are now in scope under an
    # emitter-API + derive model (consumer = FailSafe); the dashboard web API
    # stays a consumer concern.
    assert "emitter-api" in low
    assert "trust_transitions" in low and "federation_peers" in low
    assert "dashboard" in low and "federation" in low
    assert "trust-level" in low or "cbt/kbt/ibt" in low


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


def test_glossary_has_graph_terms():
    terms = _glossary_terms(_GLOSSARY.read_text(encoding="utf-8"))
    for name in ("Shadow Genome Graph", "Causal Chain"):
        assert name in terms, f"glossary missing '{name}'"
        assert terms[name]["home"] == "qor/references/doctrine-shadow-genome-graph.md"
