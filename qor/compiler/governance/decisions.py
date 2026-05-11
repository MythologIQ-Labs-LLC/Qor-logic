"""Phase 51: GovernanceDecision dataclass."""
from __future__ import annotations

from dataclasses import dataclass

RISK_LEVELS: tuple[str, ...] = ("low", "medium", "high", "blocked")


@dataclass(frozen=True)
class GovernanceDecision:
    allowed: bool = True
    risk_level: str = "low"
    violations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    required_controls: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
