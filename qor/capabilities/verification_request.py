"""Phase 58: verification request artifact."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

from qor.capabilities.context import GovernanceContextPacket, build_context_packet
from qor.capabilities.risk import RiskRoutingReport, route_risk


CONFIDENCE_LEVELS: tuple[str, ...] = ("targeted", "package", "workspace", "release")


@dataclass(frozen=True)
class VerificationRequest:
    target: str
    required_confidence: str
    requested_checks: tuple[str, ...]
    context_packet: GovernanceContextPacket
    risk_routing: RiskRoutingReport


def build_verification_request(
    repo_root: Path | str,
    target: str,
    *,
    required_confidence: str = "targeted",
    changed_files: tuple[str, ...] = (),
    extra_checks: tuple[str, ...] = (),
) -> VerificationRequest:
    if required_confidence not in CONFIDENCE_LEVELS:
        raise ValueError(
            f"required_confidence must be one of {CONFIDENCE_LEVELS}, got {required_confidence!r}"
        )
    context = build_context_packet(repo_root, target)
    risk = route_risk(repo_root, changed_files or (target,))
    checks: list[str] = list(context.recommended_checks)
    for c in risk.required_skills:
        if c not in checks:
            checks.append(c)
    for c in extra_checks:
        if c not in checks:
            checks.append(c)
    return VerificationRequest(
        target=target,
        required_confidence=required_confidence,
        requested_checks=tuple(checks),
        context_packet=context,
        risk_routing=risk,
    )


def to_dict(req: VerificationRequest) -> dict:
    return {
        "target": req.target,
        "required_confidence": req.required_confidence,
        "requested_checks": list(req.requested_checks),
        "context_packet": asdict(req.context_packet),
        "risk_routing": asdict(req.risk_routing),
    }
