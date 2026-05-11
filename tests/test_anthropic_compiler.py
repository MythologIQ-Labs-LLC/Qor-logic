"""Phase 50 AnthropicCompiler behavior tests."""
from __future__ import annotations

import sys

import pytest

from qor.compiler.providers.anthropic import AnthropicCompiler
from qor.compiler.types import (
    GovernanceContract,
    OutputContract,
    ParsedIntent,
    PromptIR,
    TargetProfile,
)


def _ir(task_type="draft", user_goal="x", constraints=(), output_format="markdown", risk="unknown"):
    return PromptIR(
        intent=ParsedIntent(task_type=task_type, user_goal=user_goal, explicit_constraints=constraints),
        output_contract=OutputContract(format=output_format),
        governance_contract=GovernanceContract(risk_level=risk),
    )


def test_anthropic_provider_name_is_anthropic_literal():
    assert AnthropicCompiler.provider_name == "anthropic"


def test_anthropic_compile_returns_compiled_prompt_with_provider_set():
    c = AnthropicCompiler()
    out = c.compile(_ir(), TargetProfile(provider="anthropic", model="m"))
    assert out.provider == "anthropic"


def test_anthropic_compile_model_propagates_from_target():
    c = AnthropicCompiler()
    out = c.compile(_ir(), TargetProfile(provider="anthropic", model="claude-opus-4-6"))
    assert out.model == "claude-opus-4-6"


def test_anthropic_compile_model_none_when_target_unset():
    c = AnthropicCompiler()
    out = c.compile(_ir(), TargetProfile(provider="anthropic"))
    assert out.model is None


def test_anthropic_system_prompt_includes_task_type_preamble():
    c = AnthropicCompiler()
    out = c.compile(_ir(task_type="implement"), TargetProfile(provider="anthropic"))
    assert "implement" in out.system_prompt.lower()


def test_anthropic_system_prompt_lists_explicit_constraints():
    c = AnthropicCompiler()
    ir = _ir(constraints=("Must use stdlib only", "Do not introduce new deps"))
    out = c.compile(ir, TargetProfile(provider="anthropic"))
    assert "Constraints:" in out.system_prompt
    assert "Must use stdlib only" in out.system_prompt
    assert "Do not introduce new deps" in out.system_prompt


def test_anthropic_system_prompt_omits_constraints_when_none():
    c = AnthropicCompiler()
    out = c.compile(_ir(), TargetProfile(provider="anthropic"))
    # Phase 52: instruction_hierarchy may reference "Constraints:" as a string
    # in its prose. Assert the actual standalone Constraints section header is
    # NOT present (i.e., the section was not emitted because there were no
    # explicit constraints to list).
    assert "\nConstraints:\n" not in out.system_prompt


def test_anthropic_system_prompt_includes_output_format_line():
    c = AnthropicCompiler()
    out = c.compile(_ir(output_format="json"), TargetProfile(provider="anthropic"))
    assert "Output format: json" in out.system_prompt


def test_anthropic_user_prompt_equals_intent_user_goal_verbatim():
    c = AnthropicCompiler()
    out = c.compile(_ir(user_goal="the original goal text"), TargetProfile(provider="anthropic"))
    assert out.user_prompt == "the original goal text"


def test_anthropic_governance_annotation_cites_risk_level():
    c = AnthropicCompiler()
    out = c.compile(_ir(risk="medium"), TargetProfile(provider="anthropic"))
    assert any("medium" in a for a in out.governance_annotations)


def test_anthropic_governance_annotation_cites_unknown_for_v1_default():
    c = AnthropicCompiler()
    out = c.compile(_ir(), TargetProfile(provider="anthropic"))
    assert any("unknown" in a for a in out.governance_annotations)


def test_anthropic_tool_instructions_empty_in_v1():
    c = AnthropicCompiler()
    out = c.compile(_ir(), TargetProfile(provider="anthropic"))
    assert out.tool_instructions == ()


def test_anthropic_compiler_does_not_import_anthropic_sdk():
    assert "anthropic" not in sys.modules, (
        "AnthropicCompiler must remain pure; the anthropic SDK was imported "
        "(somewhere in the call chain). V1 compiler emits prompts only — "
        "execution is the caller's concern."
    )
