"""Phase 59: doctrine ↔ schema round-trip integrity (Phase 50 model)."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = REPO_ROOT / "qor" / "gates" / "schema" / "ideation.schema.json"
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-ideation-readiness.md"


def test_every_required_schema_field_appears_in_doctrine_body():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    required = schema.get("required", [])
    body = DOCTRINE.read_text(encoding="utf-8")
    missing = [f for f in required if f not in body]
    assert not missing, f"doctrine body missing required field(s): {missing}"


def test_readiness_status_enum_appears_in_doctrine():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    enum = (schema["properties"]["readiness"]["properties"]
            ["status"]["enum"])
    body = DOCTRINE.read_text(encoding="utf-8")
    for value in enum:
        assert value in body, f"doctrine missing readiness.status enum value {value!r}"
