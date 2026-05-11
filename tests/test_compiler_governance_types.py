"""Phase 51 governance type tests."""
from __future__ import annotations

import dataclasses

import pytest

from qor.compiler.governance.decisions import GovernanceDecision, RISK_LEVELS


def test_governance_decision_is_frozen():
    d = GovernanceDecision()
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.risk_level = "blocked"


def test_decision_default_allowed_true_risk_low():
    d = GovernanceDecision()
    assert d.allowed is True
    assert d.risk_level == "low"
    assert d.violations == ()
    assert d.warnings == ()


def test_risk_levels_is_closed_4_value_tuple():
    assert RISK_LEVELS == ("low", "medium", "high", "blocked")


def test_decision_blocked_when_violations_present():
    d = GovernanceDecision(allowed=False, risk_level="blocked", violations=("v1",))
    assert d.allowed is False
    assert d.risk_level == "blocked"
