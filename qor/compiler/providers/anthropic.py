"""Phase 50 V1 / Phase 52 rulepack-aware: AnthropicCompiler. Pure; no API I/O."""
from __future__ import annotations

from qor.compiler.rulepacks import ProviderRulepack, registry
from qor.compiler.types import CompiledPrompt, PromptIR, TargetProfile


_TASK_PREAMBLES: dict[str, str] = {
    "draft": "Draft the requested artifact.",
    "implement": "Implement the requested feature with precise, working code.",
    "review": "Review the supplied material and report findings.",
    "analyze": "Analyze the supplied material and surface relevant observations.",
    "explain": "Explain the supplied subject in clear, accurate prose.",
    "summarize": "Summarize the supplied material concisely.",
}


class AnthropicCompiler:
    provider_name = "anthropic"

    def compile(
        self,
        prompt_ir: PromptIR,
        target: TargetProfile,
        rulepack: ProviderRulepack | None = None,
    ) -> CompiledPrompt:
        pack = rulepack if rulepack is not None else registry.get("anthropic")
        intent = prompt_ir.intent
        preamble = _TASK_PREAMBLES.get(intent.task_type, _TASK_PREAMBLES["draft"])
        lines = [preamble]
        if pack.instruction_hierarchy:
            lines.append("Instruction hierarchy:")
            for h in pack.instruction_hierarchy:
                lines.append(f"- {h}")
        if intent.explicit_constraints:
            lines.append("Constraints:")
            for c in intent.explicit_constraints:
                lines.append(f"- {c}")
        if pack.formatting_rules:
            lines.append("Formatting rules:")
            for r in pack.formatting_rules:
                lines.append(f"- {r}")
        fmt = prompt_ir.output_contract.format
        lines.append(f"Output format: {fmt}.")
        system_prompt = "\n".join(lines)
        user_prompt = intent.user_goal
        risk = prompt_ir.governance_contract.risk_level
        annotations = (
            f"governance.risk_level={risk}",
            f"rulepack.version={pack.version}",
        )
        return CompiledPrompt(
            provider=self.provider_name,
            model=target.model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_format=fmt,
            tool_instructions=(),
            governance_annotations=annotations,
        )
