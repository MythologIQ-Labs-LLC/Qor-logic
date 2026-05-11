"""Phase 61 audit_triggers tests."""
from __future__ import annotations

from qor.scripts.audit_triggers import (
    ADVERSARIAL_REVIEW_TRIGGERS,
    AdversarialTrigger,
    matches_any_trigger,
    requires_adversarial_review,
)


def test_trigger_list_is_non_empty():
    assert len(ADVERSARIAL_REVIEW_TRIGGERS) >= 5


def test_every_trigger_has_label_prefixes_reason():
    for t in ADVERSARIAL_REVIEW_TRIGGERS:
        assert isinstance(t, AdversarialTrigger)
        assert t.label
        assert t.prefixes
        assert t.reason


def test_governance_skills_trigger_fires_on_qor_skills_governance():
    fired = matches_any_trigger(("qor/skills/governance/qor-substantiate/SKILL.md",))
    labels = {t.label for t in fired}
    assert "governance-skills" in labels
    assert "substantiate-core" in labels  # also fires (overlapping prefix)


def test_ledger_trigger_fires_on_meta_ledger():
    fired = matches_any_trigger(("docs/META_LEDGER.md",))
    assert any(t.label == "ledger" for t in fired)


def test_ledger_trigger_fires_on_ledger_hash():
    fired = matches_any_trigger(("qor/scripts/ledger_hash.py",))
    assert any(t.label == "ledger" for t in fired)


def test_ledger_trigger_fires_on_hash_guard():
    fired = matches_any_trigger(("qor/scripts/hash_guard.py",))
    assert any(t.label == "ledger" for t in fired)


def test_schemas_trigger_fires_on_qor_gates_schema():
    fired = matches_any_trigger(("qor/gates/schema/plan.schema.json",))
    assert any(t.label == "schemas" for t in fired)


def test_no_trigger_fires_on_unrelated_path():
    fired = matches_any_trigger(("docs/random.md",))
    assert fired == ()


def test_no_trigger_fires_on_sibling_lookalike():
    """The M1 regression: `ledger_hash_validation.py` must NOT trigger the
    ledger class (the prefix `qor/scripts/ledger_hash` has a path boundary)."""
    fired = matches_any_trigger(("qor/scripts/ledger_hash_validation.py",))
    assert fired == ()


def test_requires_adversarial_review_returns_true_when_any_trigger_fires():
    assert requires_adversarial_review(("qor/skills/governance/qor-audit/SKILL.md",)) is True


def test_requires_adversarial_review_returns_false_for_l1_path():
    assert requires_adversarial_review(("docs/random.md",)) is False


def test_matches_any_trigger_returns_all_overlapping_classes():
    """A qor-substantiate change fires both `governance-skills` (parent
    directory) AND `substantiate-core` (specific path)."""
    fired = matches_any_trigger(("qor/skills/governance/qor-substantiate/SKILL.md",))
    labels = {t.label for t in fired}
    assert {"governance-skills", "substantiate-core"}.issubset(labels)
