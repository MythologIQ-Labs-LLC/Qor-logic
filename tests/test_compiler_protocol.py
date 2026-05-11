"""Phase 50 ProviderCompiler protocol tests."""
from __future__ import annotations

from qor.compiler.protocol import ProviderCompiler
from qor.compiler.types import CompiledPrompt, ParsedIntent, PromptIR, TargetProfile


class _FakeCompiler:
    provider_name = "fake"

    def compile(self, prompt_ir: PromptIR, target: TargetProfile) -> CompiledPrompt:
        return CompiledPrompt(
            provider=self.provider_name,
            model=target.model,
            system_prompt="sys",
            user_prompt=prompt_ir.intent.user_goal,
            output_format=prompt_ir.output_contract.format,
        )


def test_fake_compiler_satisfies_protocol_isinstance_check():
    f = _FakeCompiler()
    assert isinstance(f, ProviderCompiler)


def test_fake_compiler_compile_returns_compiled_prompt():
    f = _FakeCompiler()
    ir = PromptIR(intent=ParsedIntent(task_type="draft", user_goal="hi"))
    target = TargetProfile(provider="fake", model="x")
    out = f.compile(ir, target)
    assert isinstance(out, CompiledPrompt)
    assert out.provider == "fake"
    assert out.user_prompt == "hi"


def test_provider_compiler_protocol_requires_compile_attr():
    class MissingCompile:
        provider_name = "x"
    assert not isinstance(MissingCompile(), ProviderCompiler)
