"""Phase 52: RulepackRegistry."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qor.compiler.rulepacks import ProviderRulepack


class RulepackRegistry:
    def __init__(self) -> None:
        self._by_provider: dict[str, "ProviderRulepack"] = {}

    def register(self, rulepack: "ProviderRulepack") -> None:
        self._by_provider[rulepack.provider] = rulepack

    def get(self, provider: str) -> "ProviderRulepack":
        if provider not in self._by_provider:
            raise KeyError(f"no rulepack registered for provider {provider!r}")
        return self._by_provider[provider]

    def list_providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_provider))


registry = RulepackRegistry()


def _bootstrap() -> None:
    from qor.compiler.rulepacks.anthropic.v1 import ANTHROPIC_V1
    registry.register(ANTHROPIC_V1)


_bootstrap()
