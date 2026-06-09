"""Phase 138 (GH #196 V1): feature_index row schema accepts an optional
`surface` property without weakening additionalProperties:false.

Behavioral: run jsonschema validation over row dicts and assert validity/raising.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

_SCHEMA = json.loads(
    Path("qor/gates/schema/feature_index.schema.json").read_text(encoding="utf-8")
)


def _validate(row: dict) -> None:
    jsonschema.validate(instance=row, schema=_SCHEMA)


def test_schema_accepts_row_with_surface():
    _validate({"id": "FX001", "name": "Foo", "status": "verified", "surface": "route"})


def test_schema_accepts_row_without_surface():
    # surface stays optional: a row omitting it still validates.
    _validate({"id": "FX001", "name": "Foo", "status": "verified"})


def test_schema_still_rejects_unknown_property():
    with pytest.raises(jsonschema.ValidationError):
        _validate({"id": "FX001", "name": "Foo", "status": "verified", "bogus": "x"})
