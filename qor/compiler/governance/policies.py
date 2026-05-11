"""Phase 51: V1 deterministic policy functions.

Each policy returns (violations, warnings) tuples. The gate aggregates.
"""
from __future__ import annotations

import re

from qor.compiler.types import PromptIR

_ALLOWED_FORMATS: frozenset[str] = frozenset({"markdown", "json", "text"})
_SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "ssn", "social security", "credit card", "api key", "api_key",
    "private key", "password", "secret_key", "secret key",
)
_INJECTION_PREFIXES: tuple[str, ...] = (
    "ignore previous", "ignore all previous", "disregard above",
    "disregard previous", "forget previous instructions",
    "ignore your instructions",
)


def policy_denied_tools(ir: PromptIR) -> tuple[tuple[str, ...], tuple[str, ...]]:
    overlap = set(ir.tool_contract.allowed) & set(ir.tool_contract.denied)
    if not overlap:
        return ((), ())
    violations = tuple(f"tool {t!r} appears in both allowed and denied lists" for t in sorted(overlap))
    return (violations, ())


def policy_output_format(ir: PromptIR) -> tuple[tuple[str, ...], tuple[str, ...]]:
    fmt = ir.output_contract.format
    if fmt in _ALLOWED_FORMATS:
        return ((), ())
    return ((f"output format {fmt!r} not in allowed set {sorted(_ALLOWED_FORMATS)}",), ())


def policy_sensitive_data_hint(ir: PromptIR) -> tuple[tuple[str, ...], tuple[str, ...]]:
    text = ir.intent.user_goal.lower()
    hits = [kw for kw in _SENSITIVE_KEYWORDS if kw in text]
    if not hits:
        return ((), ())
    warnings = tuple(f"user_goal references sensitive keyword: {kw!r}" for kw in hits)
    return ((), warnings)


def policy_prompt_injection_hint(ir: PromptIR) -> tuple[tuple[str, ...], tuple[str, ...]]:
    text = ir.intent.user_goal.lower()
    hits = [pref for pref in _INJECTION_PREFIXES if pref in text]
    if not hits:
        return ((), ())
    warnings = tuple(f"user_goal contains injection-style prefix: {pref!r}" for pref in hits)
    return ((), warnings)


ALL_POLICIES = (
    policy_denied_tools,
    policy_output_format,
    policy_sensitive_data_hint,
    policy_prompt_injection_hint,
)
