"""Phase 68 (#44): plan.schema.json declares originating_remediation.

Plans that introduce a discipline (e.g., a new lint or audit pass) MAY
declare which issue/incident their work remediates. The auditor reads
this field at Step 3.5 (Self-Application Sub-Pass) and applies the
to-be-introduced discipline against the plan's own content.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path("qor/gates/schema/plan.schema.json")


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _minimal_plan_payload(**overrides) -> dict:
    base = {
        "phase": "plan",
        "ts": "2026-05-14T18:00:00Z",
        "session_id": "fixture-session",
        "plan_path": "docs/plan-fixture.md",
        "phases": ["Phase 1: stub"],
        "ci_commands": ["python -m pytest"],
    }
    base.update(overrides)
    return base


def test_schema_accepts_originating_remediation_string():
    payload = _minimal_plan_payload(originating_remediation="GH #44")
    # Should validate without ValidationError.
    jsonschema.validate(payload, _schema())


def test_schema_accepts_originating_remediation_null():
    payload = _minimal_plan_payload(originating_remediation=None)
    jsonschema.validate(payload, _schema())


def test_schema_accepts_plan_without_originating_remediation():
    """Backward compat: pre-Phase-68 plans omit the field entirely."""
    payload = _minimal_plan_payload()
    assert "originating_remediation" not in payload
    jsonschema.validate(payload, _schema())
