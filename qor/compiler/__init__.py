"""qor-logic prompt compiler. All 5 sub-phases (GH #39) delivered.

V1 scope:
- Phase 50: canonical IR + single-target compile + AnthropicCompiler.
- Phase 51: governance gate (4 deterministic policies; risk_level aggregation).
- Phase 52: rulepack registry (ProviderRulepack + auto-bootstrap anthropic v1).
- Phase 53: execution modes (compile_plan, compile_compare).
- Phase 54: evaluation loop (validate_output, compare_against_intent, record_feedback).

See `qor/references/doctrine-prompt-compilation.md` and `docs/roadmap-prompt-compiler.md`.
"""
from __future__ import annotations

from qor.compiler.compile import compile_prompt
from qor.compiler.evaluation import (
    EvaluationResult,
    compare_against_intent,
    record_feedback,
    validate_output,
)
from qor.compiler.execution_modes import PlanResult, compile_compare, compile_plan
from qor.compiler.governance import GovernanceDecision, GovernanceGate, GovernanceViolation
from qor.compiler.intent_parser import parse_intent
from qor.compiler.types import (
    CompiledPrompt,
    ContextContract,
    EvaluationContract,
    GovernanceContract,
    OutputContract,
    ParsedIntent,
    PromptIR,
    TargetProfile,
    ToolContract,
    TASK_TYPES,
)

__all__ = [
    "compile_prompt",
    "compile_plan",
    "compile_compare",
    "PlanResult",
    "GovernanceDecision",
    "GovernanceGate",
    "GovernanceViolation",
    "EvaluationResult",
    "validate_output",
    "compare_against_intent",
    "record_feedback",
    "parse_intent",
    "CompiledPrompt",
    "ContextContract",
    "EvaluationContract",
    "GovernanceContract",
    "OutputContract",
    "ParsedIntent",
    "PromptIR",
    "TargetProfile",
    "ToolContract",
    "TASK_TYPES",
]
