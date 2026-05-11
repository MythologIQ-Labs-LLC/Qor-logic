"""Phase 58 (operator-raised): governance capability surface.

Local-only V1 — Python APIs, CLI output, gate artifacts. No network service;
no remote documentation fetch. Aggregates the disciplines matured across
Phases 45-57 + 59 into a reporting layer that agents and operators consult
before planning or auditing.
"""
from qor.capabilities.types import Capability
from qor.capabilities.inventory import KNOWN_CAPABILITIES, build_inventory
from qor.capabilities.context import GovernanceContextPacket, build_context_packet
from qor.capabilities.risk import RiskRoutingReport, route_risk
from qor.capabilities.verification_request import (
    VerificationRequest,
    build_verification_request,
)

__all__ = [
    "Capability",
    "KNOWN_CAPABILITIES",
    "build_inventory",
    "GovernanceContextPacket",
    "build_context_packet",
    "RiskRoutingReport",
    "route_risk",
    "VerificationRequest",
    "build_verification_request",
]
