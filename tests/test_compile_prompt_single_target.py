"""Phase 50 compile_prompt single-target API tests."""
from __future__ import annotations

import pytest

from qor.compiler.compile import _PROVIDERS, compile_prompt
from qor.compiler.types import CompiledPrompt, ParsedIntent, PromptIR, TargetProfile


def test_compile_prompt_with_anthropic_target_returns_compiled_prompt():
    out = compile_prompt("Draft a migration plan", TargetProfile(provider="anthropic"))
    assert isinstance(out, CompiledPrompt)
    assert out.provider == "anthropic"


def test_compile_prompt_propagates_user_goal_into_user_prompt():
    out = compile_prompt(
        "Implement a parser using stdlib only.",
        TargetProfile(provider="anthropic"),
    )
    assert "a parser using stdlib only" in out.user_prompt.lower()


def test_compile_prompt_default_output_format_is_markdown():
    out = compile_prompt("Draft x", TargetProfile(provider="anthropic"))
    assert out.output_format == "markdown"


def test_compile_prompt_respects_output_format_override():
    out = compile_prompt("Draft x", TargetProfile(provider="anthropic"), output_format="json")
    assert out.output_format == "json"
    assert "Output format: json" in out.system_prompt


def test_compile_prompt_raises_value_error_on_unknown_provider():
    with pytest.raises(ValueError) as exc:
        compile_prompt("hi", TargetProfile(provider="openai"))
    assert "openai" in str(exc.value)
    assert "anthropic" in str(exc.value)


def test_compile_prompt_does_not_invoke_other_provider_compilers(monkeypatch):
    """The anti-pattern named in GH #39: optimizing across providers when only
    one is targeted. compile_prompt MUST NOT call a non-targeted compiler."""
    other_called = {"count": 0}

    class FakeOpenAICompiler:
        provider_name = "openai"
        def compile(self, prompt_ir, target):
            other_called["count"] += 1
            raise AssertionError("non-targeted compiler must not run")

    fake_providers = dict(_PROVIDERS)
    fake_providers["openai"] = FakeOpenAICompiler
    monkeypatch.setattr("qor.compiler.compile._PROVIDERS", fake_providers)

    compile_prompt("Draft a plan", TargetProfile(provider="anthropic"))
    assert other_called["count"] == 0


def test_compile_prompt_attaches_tool_contract_when_explicit_tools_provided():
    out = compile_prompt(
        "Implement a feature",
        TargetProfile(provider="anthropic"),
        explicit_tools=("read", "write"),
    )
    # V1: tool_instructions is intentionally empty (deferred); the ToolContract
    # lives on the IR but does not flow into emitted prompts yet. This locks
    # the V1 boundary documented in plan §boundaries.
    assert out.tool_instructions == ()


def test_compile_prompt_includes_task_type_specific_preamble():
    out = compile_prompt("Implement the parser", TargetProfile(provider="anthropic"))
    assert "implement" in out.system_prompt.lower()


def test_compile_prompt_governance_annotation_carries_default_risk_level():
    # Phase 51: gate replaces the Phase 50 "unknown" default with the gate's
    # aggregated risk level. A clean prompt produces "low".
    out = compile_prompt("Draft x", TargetProfile(provider="anthropic"))
    assert any("low" in a for a in out.governance_annotations)


def test_compile_prompt_supported_providers_is_anthropic_only_in_v1():
    assert set(_PROVIDERS.keys()) == {"anthropic"}
