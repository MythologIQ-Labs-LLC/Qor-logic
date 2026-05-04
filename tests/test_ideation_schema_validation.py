"""Phase 59: ideation schema validation tests."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from qor.scripts.validate_gate_artifact import _registry

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "qor" / "gates" / "schema" / "ideation.schema.json"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validator():
    schema = _load_schema()
    return jsonschema.Draft202012Validator(schema, registry=_registry())


def _minimal_valid() -> dict:
    return {
        "phase": "ideation",
        "ts": "2026-05-02T03:00:00Z",
        "session_id": "test-sid",
        "concept_name": "test-concept",
        "spark": {
            "observation": "users hit the same error",
            "initial_question": "why does this recur?",
            "why_now": "third report this week",
        },
        "problem_frame": {
            "affected_actors": ["operators"],
            "failure_mode": "stale config",
            "cost_of_failure": "lost session work",
        },
        "transformation_statement": "operators move from manual reload to auto-refresh",
        "boundaries": {
            "non_goals": ["redesign config layer"],
            "limitations": ["read-only access"],
            "exclusions": ["mobile UX"],
            "forbidden_interpretations": [],
        },
        "governance_profile": {
            "risk_grade": "L2",
            "evidence_required": ["repro"],
            "escalation_triggers": ["3rd recurrence"],
        },
        "readiness": {
            "status": "ready",
            "blocking_reasons": [],
            "recommended_next_phase": "plan",
        },
        "ai_provenance": {
            "system": "Qor-logic", "version": "0.45.0",
            "host": "unknown", "model_family": "unknown",
            "human_oversight": "absent", "ts": "2026-05-02T03:00:00Z",
        },
    }


def test_validates_minimal_ideation_artifact():
    schema = _load_schema()
    payload = _minimal_valid()
    _validator().validate(payload)  # no exception


@pytest.mark.parametrize("missing_field", [
    "spark", "problem_frame", "transformation_statement",
    "boundaries", "governance_profile", "readiness",
])
def test_rejects_artifact_missing_required_field(missing_field):
    schema = _load_schema()
    payload = _minimal_valid()
    del payload[missing_field]
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(payload)


def test_readiness_status_enum_rejects_unknown_value():
    schema = _load_schema()
    payload = _minimal_valid()
    payload["readiness"]["status"] = "definitely_ready"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(payload)


def test_governance_profile_risk_grade_enum_rejects_L5():
    schema = _load_schema()
    payload = _minimal_valid()
    payload["governance_profile"]["risk_grade"] = "L5"
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(payload)


def test_failure_remediation_return_phase_enum_rejects_unknown():
    schema = _load_schema()
    payload = _minimal_valid()
    payload["failure_remediation"] = [{
        "failure_class": "config-drift",
        "detection_signal": "alert",
        "containment_action": "rollback",
        "return_phase": "deploy",  # not in enum
    }]
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(payload)


def test_assumptions_optional():
    schema = _load_schema()
    payload = _minimal_valid()
    # No "assumptions" key — must still validate
    assert "assumptions" not in payload
    _validator().validate(payload)


def test_validate_gate_artifact_recognizes_ideation_phase():
    """The validate_gate_artifact module's PHASES tuple must include 'ideation'."""
    from qor.scripts.validate_gate_artifact import PHASES
    assert "ideation" in PHASES
