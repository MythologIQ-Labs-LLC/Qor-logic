"""Phase 52 AnthropicCompiler + rulepack tests."""
from __future__ import annotations

from qor.compiler.compile import compile_prompt
from qor.compiler.providers.anthropic import AnthropicCompiler
from qor.compiler.rulepacks import ProviderRulepack
from qor.compiler.rulepacks.anthropic.v1 import ANTHROPIC_V1
from qor.compiler.types import OutputContract, ParsedIntent, PromptIR, TargetProfile


def _ir(user_goal="x"):
    return PromptIR(
        intent=ParsedIntent(task_type="draft", user_goal=user_goal),
        output_contract=OutputContract(format="markdown"),
    )


def test_default_rulepack_lookup_returns_v1():
    c = AnthropicCompiler()
    out = c.compile(_ir(), TargetProfile(provider="anthropic"))
    assert any("rulepack.version=1.0.0" in a for a in out.governance_annotations)


def test_system_prompt_includes_instruction_hierarchy():
    c = AnthropicCompiler()
    out = c.compile(_ir(), TargetProfile(provider="anthropic"))
    assert "Instruction hierarchy:" in out.system_prompt
    assert ANTHROPIC_V1.instruction_hierarchy[0] in out.system_prompt


def test_system_prompt_includes_formatting_rules():
    c = AnthropicCompiler()
    out = c.compile(_ir(), TargetProfile(provider="anthropic"))
    assert "Formatting rules:" in out.system_prompt


def test_explicit_rulepack_override_is_respected():
    c = AnthropicCompiler()
    custom = ProviderRulepack(
        provider="anthropic",
        version="9.9.9",
        instruction_hierarchy=("custom hierarchy line",),
        formatting_rules=("custom formatting rule",),
    )
    out = c.compile(_ir(), TargetProfile(provider="anthropic"), rulepack=custom)
    assert "custom hierarchy line" in out.system_prompt
    assert "custom formatting rule" in out.system_prompt
    assert any("rulepack.version=9.9.9" in a for a in out.governance_annotations)


def test_compile_prompt_uses_registry_lookup_by_default():
    out = compile_prompt("Draft a plan", TargetProfile(provider="anthropic"))
    assert any("rulepack.version=1.0.0" in a for a in out.governance_annotations)
