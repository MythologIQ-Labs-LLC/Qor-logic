"""Phase 58 types."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    id: str
    skill: str
    phase: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    risk_level: str
