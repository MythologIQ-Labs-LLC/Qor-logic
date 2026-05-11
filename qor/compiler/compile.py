"""Phase 50 V1: single-target compile API.

Parses raw prompt into ParsedIntent, builds PromptIR, dispatches to the
single registered provider compiler matching `target.provider`. Other
provider compilers are NEVER invoked when not targeted — this closes the
anti-pattern named in GH #39: "optimizing for OpenAI / Google when the
execution target is Claude is wasted work."

V1 supports `target.provider == "anthropic"` only. Adding a provider is a
one-line dictionary registration; the compile path is provider-agnostic.
"""
from __future__ import annotations

from qor.compiler.governance.gate import GovernanceGate, GovernanceViolation
from qor.compiler.intent_parser import parse_intent
from qor.compiler.protocol import ProviderCompiler
from qor.compiler.providers.anthropic import AnthropicCompiler
from qor.compiler.types import (
    CompiledPrompt,
    ContextContract,
    EvaluationContract,
    GovernanceContract,
    OutputContract,
    PromptIR,
    TargetProfile,
    ToolContract,
)


_PROVIDERS: dict[str, type] = {
    "anthropic": AnthropicCompiler,
}


def compile_prompt(
    raw_prompt: str,
    target: TargetProfile,
    *,
    output_format: str = "markdown",
    explicit_tools: tuple[str, ...] = (),
    denied_tools: tuple[str, ...] = (),
) -> CompiledPrompt:
    if target.provider not in _PROVIDERS:
        supported = ", ".join(sorted(_PROVIDERS))
        raise ValueError(
            f"unsupported provider: {target.provider!r}; supported: {supported}"
        )
    intent = parse_intent(raw_prompt)
    prompt_ir = PromptIR(
        intent=intent,
        output_contract=OutputContract(format=output_format),
        tool_contract=ToolContract(allowed=explicit_tools, denied=denied_tools),
    )
    decision = GovernanceGate().evaluate(prompt_ir)
    if not decision.allowed:
        raise GovernanceViolation(decision)
    prompt_ir = PromptIR(
        intent=prompt_ir.intent,
        output_contract=prompt_ir.output_contract,
        context_contract=prompt_ir.context_contract,
        tool_contract=prompt_ir.tool_contract,
        governance_contract=GovernanceContract(
            risk_level=decision.risk_level,
            required_controls=decision.required_controls,
        ),
        evaluation_contract=prompt_ir.evaluation_contract,
    )
    compiler_cls = _PROVIDERS[target.provider]
    compiler = compiler_cls()
    return compiler.compile(prompt_ir, target)
