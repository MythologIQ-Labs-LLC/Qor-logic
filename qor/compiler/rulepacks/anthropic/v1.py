"""Phase 52: Anthropic provider rulepack v1.

Frozen data; encodes the V1 instruction-hierarchy preferences, formatting
rules, known anti-patterns, and worked examples that the AnthropicCompiler
consumes when building a system_prompt.
"""
from __future__ import annotations

from qor.compiler.rulepacks import ProviderRulepack


ANTHROPIC_V1 = ProviderRulepack(
    provider="anthropic",
    version="1.0.0",
    instruction_hierarchy=(
        "Highest priority: explicit user constraints (Constraints: section).",
        "Second priority: declared output format (Output format: line).",
        "Third priority: task-type preamble.",
        "Fourth priority: governance annotations (advisory, not binding).",
    ),
    formatting_rules=(
        "Prefer concise prose; avoid filler.",
        "When format is json, return strictly parseable JSON with no prose preface.",
        "When format is markdown, use minimal markup; no emoji unless requested.",
    ),
    anti_patterns=(
        "Do not repeat the user's prompt back verbatim before responding.",
        "Do not invent missing constraints; surface ambiguity instead.",
        "Do not embed control phrases like 'Ignore previous instructions'.",
    ),
    examples=(
        "task=implement -> begin with a brief plan, then code, then verification step.",
        "task=summarize -> begin with the headline result; supporting detail follows.",
    ),
)
