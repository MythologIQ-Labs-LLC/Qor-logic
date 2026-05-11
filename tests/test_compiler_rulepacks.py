"""Phase 52 rulepack + registry tests."""
from __future__ import annotations

import dataclasses

import pytest

from qor.compiler.rulepacks import ProviderRulepack, registry
from qor.compiler.rulepacks.anthropic.v1 import ANTHROPIC_V1
from qor.compiler.rulepacks.registry import RulepackRegistry


def test_provider_rulepack_is_frozen():
    p = ProviderRulepack(provider="x", version="1.0.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.version = "1.1.0"


def test_anthropic_v1_loads_with_expected_provider_and_version():
    assert ANTHROPIC_V1.provider == "anthropic"
    assert ANTHROPIC_V1.version == "1.0.0"


def test_anthropic_v1_has_at_least_one_formatting_rule():
    assert len(ANTHROPIC_V1.formatting_rules) >= 1


def test_anthropic_v1_has_instruction_hierarchy():
    assert len(ANTHROPIC_V1.instruction_hierarchy) >= 1


def test_registry_get_returns_registered_rulepack():
    p = registry.get("anthropic")
    assert p is ANTHROPIC_V1


def test_registry_get_raises_on_unknown_provider():
    with pytest.raises(KeyError):
        registry.get("nonexistent")


def test_registry_list_providers_includes_anthropic():
    assert "anthropic" in registry.list_providers()


def test_register_isolated_registry_adds_pack():
    r = RulepackRegistry()
    p = ProviderRulepack(provider="fake", version="0.1.0")
    r.register(p)
    assert r.get("fake") is p
    assert "fake" in r.list_providers()
