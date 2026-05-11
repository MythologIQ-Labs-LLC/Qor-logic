"""Phase 50: stdlib regex heuristic intent parser.

V1 contract:
- task_type: first word match against TASK_TYPES; falls back to "draft".
- user_goal: prompt with the leading task-type verb stripped (if matched).
- explicit_constraints: sentences beginning with must / do not / no / avoid
  / cannot (case-insensitive).
- All other ParsedIntent fields populated as empty tuples in V1.
"""
from __future__ import annotations

import re

from qor.compiler.types import TASK_TYPES, ParsedIntent

_LEADING_VERB = re.compile(r"^\s*([A-Za-z]+)", re.MULTILINE)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_CONSTRAINT_PREFIX = re.compile(
    r"^(must(\s+not)?|do(\s+not|n't)?|no\s|avoid\s|cannot\s|can't\s)",
    re.IGNORECASE,
)


def _detect_task_type(raw_prompt: str) -> tuple[str, int]:
    match = _LEADING_VERB.match(raw_prompt)
    if not match:
        return "draft", 0
    verb = match.group(1).lower()
    if verb in TASK_TYPES:
        return verb, match.end()
    return "draft", 0


def _extract_constraints(raw_prompt: str) -> tuple[str, ...]:
    sentences = _SENTENCE_SPLIT.split(raw_prompt)
    constraints: list[str] = []
    for sentence in sentences:
        stripped = sentence.strip()
        if not stripped:
            continue
        if _CONSTRAINT_PREFIX.match(stripped):
            constraints.append(stripped.rstrip(".!?"))
    return tuple(constraints)


def parse_intent(raw_prompt: str) -> ParsedIntent:
    task_type, verb_end = _detect_task_type(raw_prompt)
    body = raw_prompt[verb_end:].strip() if verb_end else raw_prompt.strip()
    constraints = _extract_constraints(raw_prompt)
    return ParsedIntent(
        task_type=task_type,
        user_goal=body,
        explicit_constraints=constraints,
    )
