"""Phase 53 execution-mode tests."""
from __future__ import annotations

import dataclasses

import pytest

from qor.compiler.execution_modes import PlanResult, compile_compare, compile_plan
from qor.compiler.types import CompiledPrompt, TargetProfile


def test_plan_result_is_frozen():
    pr = PlanResult(mode="single_target", compiled=(), targets=())
    with pytest.raises(dataclasses.FrozenInstanceError):
        pr.mode = "compare"


def test_compile_plan_empty_targets_raises():
    with pytest.raises(ValueError):
        compile_plan("Draft x", ())


def test_compile_plan_single_target_returns_one_compiled():
    out = compile_plan("Draft x", (TargetProfile(provider="anthropic"),))
    assert out.mode == "execution_plan"
    assert len(out.compiled) == 1


def test_compile_plan_unsupported_provider_raises():
    with pytest.raises(ValueError):
        compile_plan("Draft x", (TargetProfile(provider="nonexistent"),))


def test_compile_plan_preserves_target_order(monkeypatch):
    seen: list[str] = []

    class FakeOpenAI:
        provider_name = "openai"
        def compile(self, prompt_ir, target):
            seen.append("openai")
            return CompiledPrompt(
                provider="openai", model=target.model,
                system_prompt="", user_prompt="", output_format="markdown",
            )

    from qor.compiler import compile as mod
    fake = dict(mod._PROVIDERS)
    fake["openai"] = FakeOpenAI
    monkeypatch.setattr(mod, "_PROVIDERS", fake)

    out = compile_plan("Draft x", (
        TargetProfile(provider="anthropic"),
        TargetProfile(provider="openai"),
    ))
    assert len(out.compiled) == 2
    assert out.compiled[0].provider == "anthropic"
    assert out.compiled[1].provider == "openai"
    assert seen == ["openai"]


def test_compile_compare_empty_providers_raises():
    with pytest.raises(ValueError):
        compile_compare("Draft x", ())


def test_compile_compare_runs_each_provider_once(monkeypatch):
    class FakeOpenAI:
        provider_name = "openai"
        def compile(self, prompt_ir, target):
            return CompiledPrompt(
                provider="openai", model=target.model,
                system_prompt="", user_prompt="", output_format="markdown",
            )

    from qor.compiler import compile as mod
    fake = dict(mod._PROVIDERS)
    fake["openai"] = FakeOpenAI
    monkeypatch.setattr(mod, "_PROVIDERS", fake)

    out = compile_compare("Draft x", ("anthropic", "openai"))
    assert out.mode == "compare"
    assert len(out.compiled) == 2
    providers = {c.provider for c in out.compiled}
    assert providers == {"anthropic", "openai"}


def test_compile_compare_labels_mode_as_compare():
    out = compile_compare("Draft x", ("anthropic",))
    assert out.mode == "compare"


def test_single_target_compile_prompt_unchanged_by_modes_module():
    """Importing execution_modes does not alter the single-target compile path."""
    from qor.compiler.compile import compile_prompt
    out = compile_prompt("Draft x", TargetProfile(provider="anthropic"))
    assert out.provider == "anthropic"
