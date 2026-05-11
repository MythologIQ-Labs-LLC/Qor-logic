"""Phase 46 doctrine presence tests for per-feature TDD."""
from __future__ import annotations

from pathlib import Path

PATH = (
    Path(__file__).resolve().parent.parent
    / "qor" / "references" / "doctrine-feature-tdd.md"
)


def _body():
    return PATH.read_text(encoding="utf-8")


def test_doctrine_feature_tdd_md_exists():
    assert PATH.exists()


def test_doctrine_distinguishes_per_unit_from_per_feature():
    body = _body()
    assert "Per-unit" in body or "per-unit" in body
    assert "Per-feature" in body or "per-feature" in body


def test_doctrine_states_acceptance_question_with_sg_035_anchor():
    body = _body()
    assert "SG-035" in body
    assert "acceptance question" in body.lower()
    assert "silently broken" in body
