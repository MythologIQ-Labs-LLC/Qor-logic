"""Phase 28 Phase 1: plan.schema.json accepts new optional doc-integrity fields.

Existing plan schema is untouched for legacy plans (additionalProperties: true
already). These tests confirm the new optional fields validate when declared.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest


SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "qor" / "gates" / "schema" / "plan.schema.json"
)


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _base_payload(**overrides):
    payload = {
        "phase": "plan",
        "ts": "2026-04-17T23:35:05Z",
        "session_id": "2026-04-17T2335-f284b9",
        "plan_path": "docs/plan-qor-phase28.md",
        "phases": ["Phase 1"],
    }
    payload.update(overrides)
    return payload


def test_plan_schema_accepts_absence_of_new_fields():
    jsonschema.validate(_base_payload(), _schema())


def test_plan_schema_accepts_doc_tier_standard():
    jsonschema.validate(_base_payload(doc_tier="standard"), _schema())


def test_plan_schema_accepts_all_new_optional_fields():
    payload = _base_payload(
        doc_tier="system",
        terms=[{"term": "Foo", "home": "README.md"}],
        boundaries={
            "limitations": ["a"],
            "non_goals": ["b"],
            "exclusions": ["c"],
        },
    )
    jsonschema.validate(payload, _schema())


def test_plan_schema_rejects_invalid_doc_tier():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_base_payload(doc_tier="bogus"), _schema())


def test_plan_schema_terms_requires_term_and_home():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_payload(terms=[{"term": "Foo"}]),  # missing home
            _schema(),
        )
