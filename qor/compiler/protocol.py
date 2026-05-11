"""Phase 50: ProviderCompiler typing.Protocol."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from qor.compiler.types import CompiledPrompt, PromptIR, TargetProfile


@runtime_checkable
class ProviderCompiler(Protocol):
    provider_name: str

    def compile(self, prompt_ir: PromptIR, target: TargetProfile) -> CompiledPrompt: ...
