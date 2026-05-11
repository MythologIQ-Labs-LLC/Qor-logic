"""Phase 51: GovernanceGate + GovernanceViolation."""
from __future__ import annotations

from qor.compiler.governance.decisions import GovernanceDecision
from qor.compiler.governance.policies import ALL_POLICIES
from qor.compiler.types import PromptIR


class GovernanceViolation(Exception):
    def __init__(self, decision: GovernanceDecision):
        super().__init__(f"governance blocked: {list(decision.violations)}")
        self.decision = decision


def _aggregate_risk(violations: tuple[str, ...], warnings: tuple[str, ...]) -> str:
    if violations:
        return "blocked"
    if len(warnings) >= 2:
        return "high"
    if len(warnings) == 1:
        return "medium"
    return "low"


class GovernanceGate:
    def evaluate(self, prompt_ir: PromptIR) -> GovernanceDecision:
        all_violations: list[str] = []
        all_warnings: list[str] = []
        for policy in ALL_POLICIES:
            v, w = policy(prompt_ir)
            all_violations.extend(v)
            all_warnings.extend(w)
        violations = tuple(all_violations)
        warnings = tuple(all_warnings)
        risk = _aggregate_risk(violations, warnings)
        return GovernanceDecision(
            allowed=not bool(violations),
            risk_level=risk,
            violations=violations,
            warnings=warnings,
        )
