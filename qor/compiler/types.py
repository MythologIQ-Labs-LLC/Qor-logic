"""Phase 50 (GH #39 sub-phase 1): canonical prompt-compiler types.

All types are frozen dataclasses. Collections are tuples (immutable). No
external dependencies; stdlib only. The IR is the stable source of truth
across the (future) governance gate, provider compiler, and evaluation loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field

TASK_TYPES: tuple[str, ...] = (
    "draft",
    "implement",
    "review",
    "analyze",
    "explain",
    "summarize",
)


@dataclass(frozen=True)
class OutputContract:
    format: str = "markdown"
    schema: str | None = None


@dataclass(frozen=True)
class ContextContract:
    must_include: tuple[str, ...] = ()
    must_exclude: tuple[str, ...] = ()


@dataclass(frozen=True)
class ToolContract:
    allowed: tuple[str, ...] = ()
    denied: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationContract:
    success_criteria: tuple[str, ...] = ()


@dataclass(frozen=True)
class GovernanceContract:
    risk_level: str = "unknown"
    required_controls: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParsedIntent:
    task_type: str
    user_goal: str
    explicit_constraints: tuple[str, ...] = ()
    implicit_constraints: tuple[str, ...] = ()
    required_outputs: tuple[str, ...] = ()
    context_dependencies: tuple[str, ...] = ()
    ambiguity_flags: tuple[str, ...] = ()
    risk_hints: tuple[str, ...] = ()


@dataclass(frozen=True)
class PromptIR:
    intent: ParsedIntent
    output_contract: OutputContract = field(default_factory=OutputContract)
    context_contract: ContextContract = field(default_factory=ContextContract)
    tool_contract: ToolContract = field(default_factory=ToolContract)
    governance_contract: GovernanceContract = field(default_factory=GovernanceContract)
    evaluation_contract: EvaluationContract = field(default_factory=EvaluationContract)


@dataclass(frozen=True)
class TargetProfile:
    provider: str
    model: str | None = None
    role: str | None = None


@dataclass(frozen=True)
class CompiledPrompt:
    provider: str
    model: str | None
    system_prompt: str
    user_prompt: str
    output_format: str
    tool_instructions: tuple[str, ...] = ()
    governance_annotations: tuple[str, ...] = ()
