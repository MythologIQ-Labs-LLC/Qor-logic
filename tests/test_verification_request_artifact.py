"""Phase 58 verification request artifact tests."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from qor.capabilities.verification_request import (
    CONFIDENCE_LEVELS,
    build_verification_request,
    to_dict,
)

SCHEMA = (
    Path(__file__).resolve().parent.parent
    / "qor" / "gates" / "schema" / "verification_request.schema.json"
)


def test_verification_request_default_confidence_is_targeted():
    req = build_verification_request(".", "docs/plan-x.md")
    assert req.required_confidence == "targeted"


def test_verification_request_rejects_unknown_confidence():
    with pytest.raises(ValueError):
        build_verification_request(".", "x", required_confidence="vibes")


def test_verification_request_embeds_context_and_risk():
    req = build_verification_request(
        ".", "qor/skills/governance/qor-substantiate/SKILL.md",
    )
    assert req.context_packet.target == "qor/skills/governance/qor-substantiate/SKILL.md"
    assert req.risk_routing.risk_grade in ("L1", "L2", "L3")


def test_verification_request_target_substantiate_routes_to_hash_integrity():
    req = build_verification_request(
        ".", "qor/skills/governance/qor-substantiate/SKILL.md",
    )
    assert "hash-integrity" in req.requested_checks


def test_verification_request_aggregates_context_recommended_and_risk_required():
    req = build_verification_request(
        ".", "qor/skills/governance/qor-substantiate/SKILL.md",
        changed_files=("qor/skills/governance/qor-substantiate/SKILL.md",),
    )
    # both context.recommended_checks and risk.required_skills should contribute
    assert "hash-integrity" in req.requested_checks
    assert "ledger-verify" in req.requested_checks


def test_verification_request_extra_checks_are_appended():
    req = build_verification_request(
        ".", "x", extra_checks=("custom-check-X",),
    )
    assert "custom-check-X" in req.requested_checks


def test_to_dict_round_trip_validates_against_schema():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    req = build_verification_request(".", "docs/plan-x.md")
    payload = to_dict(req)
    jsonschema.validate(payload, schema)


def test_confidence_levels_is_closed_four_value_tuple():
    assert CONFIDENCE_LEVELS == ("targeted", "package", "workspace", "release")
