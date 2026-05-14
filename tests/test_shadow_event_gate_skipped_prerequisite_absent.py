"""Phase 75 P3: shadow_event schema gains gate_skipped_prerequisite_absent."""
import json
import hashlib
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


SCHEMA = json.loads(Path("qor/gates/schema/shadow_event.schema.json").read_text(encoding="utf-8"))


def _event(event_type: str) -> dict:
    return {
        "ts": "2026-05-14T22:00:00Z",
        "skill": "qor-substantiate",
        "session_id": "2026-05-14T2216-a5f692",
        "event_type": event_type,
        "severity": 1,
        "details": {"step_id": "7.5", "requires": "file:pyproject.toml"},
        "source_entry_id": None,
        "addressed": False,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
    }


def test_schema_accepts_new_event_type():
    validator = Draft202012Validator(SCHEMA)
    event = _event("gate_skipped_prerequisite_absent")
    validator.validate(event)


def test_schema_still_rejects_unknown_event_type():
    validator = Draft202012Validator(SCHEMA)
    event = _event("fabricated_event_not_in_enum")
    with pytest.raises(ValidationError):
        validator.validate(event)
