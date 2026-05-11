"""Phase 54: prompt compiler evaluation loop.

V1 deterministic evaluation: format validation + word-overlap drift detection
+ optional JSONL feedback record. No LLM-as-judge in V1.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from qor.compiler.types import OutputContract, ParsedIntent

_WORD = re.compile(r"\b[a-zA-Z][a-zA-Z0-9_-]*\b")


@dataclass(frozen=True)
class EvaluationResult:
    format_valid: bool
    format_error: str | None
    drift_score: float
    drift_detected: bool
    matched_tokens: tuple[str, ...]
    missing_tokens: tuple[str, ...]


def validate_output(output_text: str, contract: OutputContract) -> tuple[bool, str | None]:
    fmt = contract.format
    if fmt == "json":
        try:
            json.loads(output_text)
        except (json.JSONDecodeError, ValueError) as exc:
            return False, f"json parse error: {exc}"
    return True, None


def _tokens(text: str) -> tuple[str, ...]:
    return tuple(t.lower() for t in _WORD.findall(text) if len(t) > 3)


def compare_against_intent(
    output_text: str,
    intent: ParsedIntent,
    *,
    threshold: float = 0.3,
) -> EvaluationResult:
    goal_tokens = set(_tokens(intent.user_goal))
    output_lower = output_text.lower()
    matched = tuple(sorted(t for t in goal_tokens if t in output_lower))
    missing = tuple(sorted(goal_tokens - set(matched)))
    score = (len(missing) / len(goal_tokens)) if goal_tokens else 0.0
    drift_detected = score > (1.0 - threshold) if goal_tokens else False
    return EvaluationResult(
        format_valid=True,
        format_error=None,
        drift_score=round(score, 4),
        drift_detected=drift_detected,
        matched_tokens=matched,
        missing_tokens=missing,
    )


def record_feedback(
    session_id: str,
    result: EvaluationResult,
    repo_root: str | Path = ".",
) -> Path:
    path = Path(repo_root) / ".qor" / "evaluation" / f"{session_id}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(asdict(result), sort_keys=True) + "\n")
    return path
