"""Attestation and enforcer validation for the two-stage remediation flip.

Extracted from ``remediate_mark_addressed`` (Phase 226; GH #333) so the
contract checks -- what counts as a valid closure enforcer, what counts as a
PASS review attestation -- live apart from the durable event mutation they
gate. ``remediate_mark_addressed`` imports from here and re-exports the two
exception classes; nothing here imports back.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Mapping


class ReviewAttestationError(Exception):
    """Raised when a review-pass artifact fails verification during mark_addressed."""


class ClosureEnforcerError(Exception):
    """Raised when a closure lacks a valid executable enforcer (Phase 166; GH #249)."""


_MODULE_RE = re.compile(r"^qor\.(scripts|reliability)\.[a-z0-9_]+$")
_GATE_STEP_RE = re.compile(r"^/qor-[a-z-]+ Step [0-9]+(\.[0-9]+)*$")
_CANNOT_AUTOMATE_PREFIX = "cannot-automate:"


def _validate_closure_enforcer(value: str, repo_root: Path | None = None) -> None:
    """Accept exactly four enforcer forms; raise ClosureEnforcerError otherwise.

    Forms: (1) existing tests/test_*.py path; (2) importable qor.scripts.* /
    qor.reliability.* module; (3) '/qor-<skill> Step N[.M]' gate reference;
    (4) 'cannot-automate: <justification >= 50 chars>'.
    """
    root = repo_root or Path.cwd()
    if not value or not value.strip():
        raise ClosureEnforcerError("closure_enforcer is required and cannot be empty")
    if value.startswith(_CANNOT_AUTOMATE_PREFIX):
        justification = value[len(_CANNOT_AUTOMATE_PREFIX):].strip()
        if len(justification) < 50:
            raise ClosureEnforcerError(
                "cannot-automate justification must be >= 50 characters "
                f"(got {len(justification)})"
            )
        return
    if re.fullmatch(r"tests/test_[a-z0-9_]+\.py", value):
        if not (root / value).is_file():
            raise ClosureEnforcerError(f"enforcer test file does not exist: {value}")
        return
    if _MODULE_RE.fullmatch(value):
        if importlib.util.find_spec(value) is None:
            raise ClosureEnforcerError(f"enforcer module is not importable: {value}")
        return
    if _GATE_STEP_RE.fullmatch(value):
        return
    raise ClosureEnforcerError(
        f"closure_enforcer matches none of the four accepted forms: {value!r} "
        "(test path | qor module | '/qor-<skill> Step N' | 'cannot-automate: <justification>')"
    )


def _verify_review_pass_artifact(
    review_pass_artifact_path: str,
    remediate_gate_path: str,
) -> None:
    """Verify the audit artifact is a legitimate PASS review of the named remediate gate.

    Raises ReviewAttestationError on any failure. No return value.
    """
    artifact_path = Path(review_pass_artifact_path)
    if not artifact_path.is_file():
        raise ReviewAttestationError(
            f"review-pass artifact not found: {review_pass_artifact_path}"
        )
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewAttestationError(
            f"review-pass artifact unreadable: {review_pass_artifact_path}: {exc}"
        ) from exc
    if payload.get("phase") != "audit":
        raise ReviewAttestationError(
            f"review-pass artifact is not an audit gate (phase={payload.get('phase')!r})"
        )
    if payload.get("verdict") != "PASS":
        raise ReviewAttestationError(
            f"review-pass artifact verdict is not PASS: {payload.get('verdict')!r}"
        )
    declared_gate = payload.get("reviews_remediate_gate")
    if not declared_gate:
        raise ReviewAttestationError(
            "review-pass artifact missing 'reviews_remediate_gate' field "
            "(operator must pass reviews-remediate:<path> to /qor-audit)"
        )
    if Path(declared_gate).resolve() != Path(remediate_gate_path).resolve():
        raise ReviewAttestationError(
            f"review-pass artifact reviews_remediate_gate mismatch: "
            f"declared={declared_gate!r} expected={remediate_gate_path!r}"
        )


def _normalized_enforcers(
    event_ids: list[str] | Mapping[str, str],
    closure_enforcer: str | None,
    repo_root: Path | None,
) -> tuple[list[str], dict[str, str] | None]:
    """Validate shared or per-event enforcers without mutating durable state."""
    if isinstance(event_ids, Mapping):
        if closure_enforcer is not None:
            raise ClosureEnforcerError(
                "closure_enforcer must be omitted when event_ids is an event-to-enforcer mapping"
            )
        mapping = dict(event_ids)
        if not mapping:
            raise ClosureEnforcerError("event-to-enforcer mapping cannot be empty")
        for value in mapping.values():
            _validate_closure_enforcer(value, repo_root=repo_root)
        return list(mapping), mapping

    if closure_enforcer is None:
        raise ClosureEnforcerError("closure_enforcer is required for a list of event IDs")
    _validate_closure_enforcer(closure_enforcer, repo_root=repo_root)
    return list(event_ids), None
