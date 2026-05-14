"""Phase 73 P2: plan schema feature_inventory_touches field tests."""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMA_PATH = Path("qor/gates/schema/plan.schema.json")


def _validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema), schema


def _minimal_plan() -> dict:
    return {
        "phase": "plan",
        "ts": "2026-05-14T20:30:00Z",
        "session_id": "2026-05-14T2016-0a7b68",
        "plan_path": "docs/plan-qor-phase73-feature-inventory-tdd.md",
        "phases": ["Phase 1"],
        "ci_commands": ["python -m pytest"],
        "open_questions": [],
        "doc_tier": "standard",
        "terms": [],
        "boundaries": {"limitations": [], "non_goals": [], "exclusions": []},
        "high_risk_target": False,
        "change_class": "feature",
    }


def test_optional_field_validates():
    validator, _ = _validator()
    plan = _minimal_plan()
    plan["feature_inventory_touches"] = [
        {
            "entry_id": "FX001",
            "operation": "NEW",
            "test_path": "tests/test_foo.py",
            "test_descriptor": "POST /foo returns 200 + nonce",
        }
    ]
    validator.validate(plan)


def test_operation_enum_rejects_invalid():
    validator, _ = _validator()
    plan = _minimal_plan()
    plan["feature_inventory_touches"] = [
        {
            "entry_id": "FX001",
            "operation": "FROBNICATE",
            "test_path": "tests/test_foo.py",
            "test_descriptor": "x",
        }
    ]
    with pytest.raises(ValidationError) as exc:
        validator.validate(plan)
    assert "FROBNICATE" in str(exc.value) or "enum" in str(exc.value).lower()


def test_field_absent_is_valid():
    validator, _ = _validator()
    validator.validate(_minimal_plan())
