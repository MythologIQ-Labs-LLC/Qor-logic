"""Phase 52: provider rulepacks. Frozen Python data; no YAML in V1."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderRulepack:
    provider: str
    version: str
    instruction_hierarchy: tuple[str, ...] = ()
    formatting_rules: tuple[str, ...] = ()
    anti_patterns: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()


from qor.compiler.rulepacks.registry import RulepackRegistry, registry

__all__ = ["ProviderRulepack", "RulepackRegistry", "registry"]
