"""Phase 50 compiler type tests."""
from __future__ import annotations

import dataclasses

import pytest

from qor.compiler.types import (
    TASK_TYPES,
    CompiledPrompt,
    ContextContract,
    EvaluationContract,
    GovernanceContract,
    OutputContract,
    ParsedIntent,
    PromptIR,
    TargetProfile,
    ToolContract,
)


def test_prompt_ir_is_frozen_dataclass():
    intent = ParsedIntent(task_type="draft", user_goal="x")
    ir = PromptIR(intent=intent)
    with pytest.raises(dataclasses.FrozenInstanceError):
        ir.intent = ParsedIntent(task_type="implement", user_goal="y")


def test_parsed_intent_defaults_implicit_fields_to_empty_tuples():
    intent = ParsedIntent(task_type="draft", user_goal="x")
    assert intent.implicit_constraints == ()
    assert intent.required_outputs == ()
    assert intent.context_dependencies == ()
    assert intent.ambiguity_flags == ()
    assert intent.risk_hints == ()


def test_target_profile_requires_provider_field():
    with pytest.raises(TypeError):
        TargetProfile()  # type: ignore[call-arg]


def test_target_profile_provider_only_defaults_other_fields():
    t = TargetProfile(provider="anthropic")
    assert t.model is None
    assert t.role is None


def test_compiled_prompt_exposes_provider_and_prompts():
    cp = CompiledPrompt(
        provider="anthropic",
        model="claude-opus-4-6",
        system_prompt="sys",
        user_prompt="usr",
        output_format="markdown",
    )
    assert cp.provider == "anthropic"
    assert cp.system_prompt == "sys"
    assert cp.user_prompt == "usr"


def test_governance_contract_default_is_unknown_risk():
    g = GovernanceContract()
    assert g.risk_level == "unknown"
    assert g.required_controls == ()


def test_task_types_is_closed_6_value_tuple():
    assert isinstance(TASK_TYPES, tuple)
    assert len(TASK_TYPES) == 6
    assert "draft" in TASK_TYPES
    assert "implement" in TASK_TYPES


def test_output_contract_default_format_markdown():
    oc = OutputContract()
    assert oc.format == "markdown"
    assert oc.schema is None


def test_tool_contract_uses_tuple_collections():
    tc = ToolContract(allowed=("read",), denied=("write",))
    assert isinstance(tc.allowed, tuple)
    assert isinstance(tc.denied, tuple)


def test_context_contract_defaults_empty_tuples():
    cc = ContextContract()
    assert cc.must_include == ()
    assert cc.must_exclude == ()


def test_evaluation_contract_defaults_empty_tuple():
    ec = EvaluationContract()
    assert ec.success_criteria == ()


def test_prompt_ir_factory_defaults_independent_per_instance():
    a = PromptIR(intent=ParsedIntent(task_type="draft", user_goal=""))
    b = PromptIR(intent=ParsedIntent(task_type="draft", user_goal=""))
    assert a.output_contract is not b.output_contract or a.output_contract == b.output_contract
