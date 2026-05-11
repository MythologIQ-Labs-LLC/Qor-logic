"""Phase 46 doctrine presence tests for feature-inventory."""
from __future__ import annotations

from pathlib import Path

PATH = (
    Path(__file__).resolve().parent.parent
    / "qor" / "references" / "doctrine-feature-inventory.md"
)


def _body():
    return PATH.read_text(encoding="utf-8")


def test_doctrine_feature_inventory_md_exists():
    assert PATH.exists()


def test_doctrine_states_status_enum_with_three_values():
    body = _body()
    assert "verified" in body
    assert "unverified" in body
    assert "n/a" in body


def test_doctrine_states_lifecycle_hooks_in_order():
    body = _body()
    start = body.find("## Lifecycle hooks")
    assert start >= 0, "missing Lifecycle hooks section"
    section = body[start:]
    pos_plan = section.find("/qor-plan")
    pos_audit = section.find("/qor-audit")
    pos_impl = section.find("/qor-implement")
    pos_subst = section.find("/qor-substantiate")
    assert pos_plan < pos_audit < pos_impl < pos_subst
