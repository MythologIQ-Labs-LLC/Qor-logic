"""Portable governed-procedure execution evidence semantics (Phase 242).

The evaluator decides whether a policy-derived required-procedure set is
satisfied by execution evidence. It does not verify signatures or run a signer.
A trusted host boundary verifies concrete attestations and passes claim-bound
verification facts into this deterministic core.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable

import jsonschema

from qor import resources

CONTRACT_VERSION = "1"
INDEPENDENT_CLASSES = frozenset({"wrapper-observed", "ci-attested"})


class ProcedureEvidenceError(ValueError):
    """Malformed or internally ambiguous procedure-evidence contract."""


@dataclass(frozen=True)
class VerifiedClaim:
    """Trusted-boundary fact binding a principal to one exact evidence claim."""

    evidence_id: str
    claim_sha256: str
    principal_id: str


@dataclass(frozen=True)
class RequirementResult:
    requirement_id: str
    status: str
    evidence_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvaluationResult:
    status: str
    requirements: tuple[RequirementResult, ...]

    @property
    def satisfied(self) -> bool:
        return self.status == "satisfied"


def _schema() -> dict[str, Any]:
    with resources.schema("procedure_execution_evidence.schema.json").open(
        "r", encoding="utf-8"
    ) as handle:
        return json.load(handle)


def _require_unique(records: list[dict[str, Any]], key: str, label: str) -> None:
    values = [item[key] for item in records]
    if len(values) != len(set(values)):
        raise ProcedureEvidenceError(f"duplicate {label} {key}")


def _validate_independent_requirements(requirements: list[dict[str, Any]]) -> None:
    for req in requirements:
        classes = set(req["acceptedEvidenceClasses"])
        if classes & INDEPENDENT_CLASSES and not req.get("trustedPrincipals"):
            raise ProcedureEvidenceError(
                f"{req['requirementId']}: independent evidence requires trustedPrincipals"
            )


def validate_contract(contract: dict[str, Any]) -> None:
    """Validate shape plus cross-record invariants JSON Schema cannot express."""
    try:
        jsonschema.Draft202012Validator(_schema()).validate(contract)
    except jsonschema.ValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path)
        detail = f"{path}: {exc.message}" if path else exc.message
        raise ProcedureEvidenceError(detail) from exc
    _require_unique(contract["requirements"], "requirementId", "requirement")
    _require_unique(contract["evidence"], "evidenceId", "evidence")
    _validate_independent_requirements(contract["requirements"])


def canonical_claim_digest(evidence: dict[str, Any]) -> str:
    """Digest the exact evidence claim verified by an external trust boundary."""
    raw = json.dumps(
        evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _binding_reasons(req: dict[str, Any], ev: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if ev["procedure"] != req["procedure"]:
        reasons.append("procedure_binding_mismatch")
    if ev["subject"] != req["subject"]:
        reasons.append("subject_binding_mismatch")
    expected_input = req.get("inputSha256")
    if expected_input is not None and ev.get("inputSha256") != expected_input:
        reasons.append("input_digest_mismatch")
    return reasons


def _class_reasons(req: dict[str, Any], ev: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if ev["evidenceClass"] not in req["acceptedEvidenceClasses"]:
        reasons.append("evidence_class_not_accepted")
    if ev["status"] != "completed":
        reasons.append("execution_not_completed")
    return reasons


def _verification_reasons(
    req: dict[str, Any],
    ev: dict[str, Any],
    verified: tuple[VerifiedClaim, ...],
) -> list[str]:
    if ev["evidenceClass"] not in INDEPENDENT_CLASSES:
        return []
    observer = ev.get("observerId")
    if not observer:
        return ["observer_required"]
    if observer not in req.get("trustedPrincipals", []):
        return ["untrusted_observer"]
    digest = canonical_claim_digest(ev)
    matched = any(
        item.evidence_id == ev["evidenceId"]
        and item.claim_sha256 == digest
        and item.principal_id == observer
        for item in verified
    )
    return [] if matched else ["claim_not_independently_verified"]


def _candidate_reasons(
    req: dict[str, Any],
    ev: dict[str, Any],
    verified: tuple[VerifiedClaim, ...],
) -> list[str]:
    reasons = _binding_reasons(req, ev)
    reasons.extend(_class_reasons(req, ev))
    reasons.extend(_verification_reasons(req, ev, verified))
    return reasons


def _evaluate_requirement(
    req: dict[str, Any],
    evidence: list[dict[str, Any]],
    verified: tuple[VerifiedClaim, ...],
) -> RequirementResult:
    candidates = [
        item for item in evidence
        if item["procedure"]["name"] == req["procedure"]["name"]
    ]
    if not candidates:
        return RequirementResult(
            req["requirementId"], "unsatisfied", reasons=("missing_evidence",)
        )
    accepted = [
        item["evidenceId"]
        for item in candidates
        if not _candidate_reasons(req, item, verified)
    ]
    if accepted:
        return RequirementResult(
            req["requirementId"], "satisfied", tuple(sorted(accepted))
        )
    reasons = {
        reason
        for item in candidates
        for reason in _candidate_reasons(req, item, verified)
    }
    return RequirementResult(
        req["requirementId"], "unsatisfied", reasons=tuple(sorted(reasons))
    )


def evaluate_contract(
    contract: dict[str, Any],
    verified_claims: Iterable[VerifiedClaim] = (),
) -> EvaluationResult:
    """Evaluate every requirement; externally verified claims stay a separate input."""
    validate_contract(contract)
    verified = tuple(verified_claims)
    results = tuple(
        _evaluate_requirement(req, contract["evidence"], verified)
        for req in contract["requirements"]
    )
    status = "satisfied" if all(
        item.status == "satisfied" for item in results
    ) else "failed"
    return EvaluationResult(status, results)
