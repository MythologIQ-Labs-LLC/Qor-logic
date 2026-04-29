"""Cedar-inspired policy engine for Qor-logic governance.

Public API::

    from qor.policy import evaluate, Decision, Request, EntityUID
    result = evaluate(request, policies)
    assert result.decision == Decision.ALLOW
"""
from __future__ import annotations

from qor.policy.evaluator import EvalResult, evaluate
from qor.policy.types import (
    Condition,
    Constraint,
    Decision,
    EntityUID,
    Policy,
    Request,
)

__all__ = [
    "Condition",
    "Constraint",
    "Decision",
    "EntityUID",
    "EvalResult",
    "Policy",
    "Request",
    "evaluate",
]
