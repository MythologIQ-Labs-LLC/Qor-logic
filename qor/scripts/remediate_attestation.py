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
import sys
from pathlib import Path
from typing import Mapping


class ReviewAttestationError(Exception):
    """Raised when a review-pass artifact fails verification during mark_addressed."""


class ClosureEnforcerError(Exception):
    """Raised when a closure lacks a valid executable enforcer (Phase 166; GH #249)."""


_BARE_MODULE_RE = re.compile(r"^qor\.(scripts|reliability)\.[a-z0-9_]+$")
_MODULE_CALLABLE_RE = re.compile(
    r"^(qor\.(?:scripts|reliability)\.[a-z0-9_]+):([A-Za-z_][A-Za-z0-9_]*)$"
)
_GATE_STEP_RE = re.compile(r"^/(qor-[a-z-]+) Step ([0-9]+(?:\.[0-9]+)*)$")
_CANNOT_AUTOMATE_PREFIX = "cannot-automate:"


def _validate_module_callable(module_name: str, callable_name: str, raw: str) -> None:
    """Resolve module_name and require a callable attribute named callable_name.

    GH #364: the prior module form validated importability alone, so any
    importable module -- including one unrelated to the pattern it claimed to
    guard -- satisfied the contract. Naming and resolving a specific callable
    does not prove semantic relevance (out of scope; no relevance classifier
    is introduced here), but it closes the mechanical gap: the cited name must
    resolve to something that actually exists and runs.
    """
    if importlib.util.find_spec(module_name) is None:
        raise ClosureEnforcerError(f"enforcer module is not importable: {raw}")
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        raise ClosureEnforcerError(f"enforcer module failed to import: {raw}: {exc}") from exc
    target = getattr(module, callable_name, None)
    if not callable(target):
        raise ClosureEnforcerError(
            f"enforcer module {module_name!r} has no callable named {callable_name!r}: {raw}"
        )


_STEP_HEADING_TEMPLATE = r"^#{{1,4}}\s*Step\s+{0}(?!\.\d)\b"


def _validate_gate_step(skill_name: str, step_num: str, root: Path, raw: str) -> None:
    """Resolve a '/qor-<skill> Step N[.M]' reference against installed skill docs.

    GH #364: the prior form validated on regex shape alone, so a step number
    that never existed still passed. A skill's Step headings may live in its
    SKILL.md or, under progressive disclosure, in one of its references/*.md
    files -- both are searched.
    """
    corpus = root / "qor" / "skills"
    if not corpus.is_dir():
        # Phase 243 iteration 2 (independent-audit V2): a consumer workspace
        # that pip-installed qor-logic has no <repo_root>/qor/skills tree --
        # skills install into host directories (.claude/skills/, ...), never
        # into the consumer repo. Heading resolution is impossible there, so
        # fall back to the pre-#364 shape-only acceptance as a DISCLOSED
        # degradation instead of rejecting every gate-step enforcer downstream.
        sys.stderr.write(
            f"INFO [closure_enforcer]: no skill corpus at {corpus}; gate-step "
            f"reference {raw!r} accepted on shape only (heading resolution "
            "requires the Qor-logic source tree)\n"
        )
        return
    matches = sorted(corpus.glob(f"*/{skill_name}"))
    if not matches:
        raise ClosureEnforcerError(f"no installed skill named {skill_name!r}: {raw}")
    skill_dir = matches[0]
    docs = [skill_dir / "SKILL.md", *sorted(skill_dir.glob("references/*.md"))]
    heading_re = re.compile(_STEP_HEADING_TEMPLATE.format(re.escape(step_num)), re.MULTILINE)
    for doc in docs:
        if doc.is_file() and heading_re.search(doc.read_text(encoding="utf-8")):
            return
    raise ClosureEnforcerError(
        f"skill {skill_name!r} has no 'Step {step_num}' heading in SKILL.md "
        f"or references/*.md: {raw}"
    )


def _validate_closure_enforcer(value: str, repo_root: Path | None = None) -> None:
    """Accept exactly four enforcer forms; raise ClosureEnforcerError otherwise.

    Forms: (1) existing tests/test_*.py path; (2) 'qor.scripts.*:<callable>' /
    'qor.reliability.*:<callable>' -- an importable module naming a resolvable
    callable attribute (Phase 166 accepted bare-module importability alone;
    GH #364 tightened this because any importable-but-irrelevant module
    satisfied it); (3) '/qor-<skill> Step N[.M]' gate reference, resolved
    against the named skill's actual SKILL.md/references Step headings (GH
    #364 tightened this from regex-shape-only); (4) 'cannot-automate:
    <justification >= 50 chars>'.
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
    if _BARE_MODULE_RE.fullmatch(value):
        raise ClosureEnforcerError(
            f"module enforcer must name a callable, e.g. {value}:<callable> "
            f"(GH #364: importability alone no longer suffices): {value!r}"
        )
    match = _MODULE_CALLABLE_RE.fullmatch(value)
    if match:
        _validate_module_callable(match.group(1), match.group(2), value)
        return
    match = _GATE_STEP_RE.fullmatch(value)
    if match:
        _validate_gate_step(match.group(1), match.group(2), root, value)
        return
    raise ClosureEnforcerError(
        f"closure_enforcer matches none of the four accepted forms: {value!r} "
        "(test path | 'qor module:callable' | '/qor-<skill> Step N' | "
        "'cannot-automate: <justification>')"
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
