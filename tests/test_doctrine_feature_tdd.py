"""Phase 73 P1: doctrine-feature-tdd.md tests."""
from pathlib import Path

DOCTRINE = Path("qor/references/doctrine-feature-tdd.md")


def test_documents_three_upstream_gates():
    text = DOCTRINE.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "/qor-plan" in text and "feature inventory touches" in lowered, (
        "must name /qor-plan + Feature Inventory Touches declaration gate"
    )
    assert "/qor-audit" in text and "feature test coverage pass" in lowered, (
        "must name /qor-audit + Feature Test Coverage Pass gate"
    )
    assert "/qor-implement" in text and "per-feature" in lowered, (
        "must name /qor-implement + per-feature TDD gate"
    )
    assert "feature-test-undeclared" in text, "must name VETO category"


def test_documents_acceptance_question():
    text = DOCTRINE.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "silently broken" in lowered and "would this" in lowered and "fail" in lowered, (
        "must inherit SG-035 acceptance question form"
    )
    assert "sg-035" in lowered, "must cross-reference SG-035 inheritance"
