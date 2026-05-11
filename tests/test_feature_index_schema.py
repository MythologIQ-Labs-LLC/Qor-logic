"""Phase 46 feature_index.schema.json tests."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA = (
    Path(__file__).resolve().parent.parent
    / "qor" / "gates" / "schema" / "feature_index.schema.json"
)


def _schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_feature_index_schema_file_exists():
    assert SCHEMA.exists()


def test_schema_accepts_minimal_verified_row():
    row = {
        "id": "FX001",
        "name": "Marketplace install endpoint",
        "test_path": "tests/test_marketplace_route.py",
        "status": "verified",
    }
    jsonschema.validate(row, _schema())


def test_schema_accepts_n_a_row_with_rationale():
    row = {
        "id": "FX004",
        "name": "Brainstorm UI",
        "status": "n/a",
        "n_a_rationale": "Human-judgment surface; manual QA only.",
    }
    jsonschema.validate(row, _schema())


def test_schema_rejects_unknown_status_value():
    row = {"id": "FX001", "name": "X", "status": "maybe"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(row, _schema())


def test_schema_rejects_n_a_row_without_rationale():
    row = {"id": "FX004", "name": "X", "status": "n/a"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(row, _schema())


def test_schema_rejects_missing_required_fields():
    for missing in ("id", "name", "status"):
        row = {"id": "FX001", "name": "x", "status": "verified"}
        del row[missing]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(row, _schema())
