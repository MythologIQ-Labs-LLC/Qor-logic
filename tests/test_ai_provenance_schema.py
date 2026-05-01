"""Phase 54: AI provenance schema validation tests."""
from __future__ import annotations

from copy import deepcopy

import pytest

from qor.scripts import validate_gate_artifact as vga


def _audit_payload(provenance: dict | None = None) -> dict:
    payload = {
        "phase": "audit",
        "ts": "2026-04-30T18:00:00Z",
        "session_id": "test-sess-aiprov",
        "target": "docs/plan.md",
        "verdict": "PASS",
    }
    if provenance is not None:
        payload["ai_provenance"] = provenance
    return payload


def _full_provenance() -> dict:
    return {
        "system": "Qor-logic",
        "version": "0.39.0",
        "host": "claude-code",
        "model_family": "claude-opus-4-7",
        "human_oversight": "pass",
        "ts": "2026-04-30T18:00:00Z",
    }


def test_schema_validates_full_manifest():
    errs = vga._validate_data("audit", _audit_payload(_full_provenance()))
    assert errs == [], f"valid manifest must validate: {errs}"


def test_schema_rejects_unknown_human_oversight_value():
    bad = _full_provenance()
    bad["human_oversight"] = "maybe"
    errs = vga._validate_data("audit", _audit_payload(bad))
    assert errs, "unknown human_oversight value must fail enum"


def test_schema_optional_in_phase_schemas():
    errs = vga._validate_data("audit", _audit_payload(provenance=None))
    assert errs == [], f"audit without ai_provenance must validate: {errs}"


@pytest.mark.parametrize("missing", [
    "system", "version", "host", "model_family", "human_oversight", "ts",
])
def test_schema_required_fields(missing: str):
    bad = _full_provenance()
    bad.pop(missing)
    errs = vga._validate_data("audit", _audit_payload(bad))
    assert errs, f"missing {missing} must fail validation"


def test_schema_system_field_must_be_qor_logic():
    bad = _full_provenance()
    bad["system"] = "Other-System"
    errs = vga._validate_data("audit", _audit_payload(bad))
    assert errs, "system field must be const Qor-logic"


def test_schema_ts_pattern_enforced():
    bad = _full_provenance()
    bad["ts"] = "2026-04-30 18:00:00"
    errs = vga._validate_data("audit", _audit_payload(bad))
    assert errs, "ts must match ISO 8601 UTC pattern"


@pytest.mark.parametrize("phase", ["research", "plan", "audit", "implement", "substantiate", "validate"])
def test_provenance_optional_across_all_six_phases(phase: str):
    """Every phase schema must accept ai_provenance and accept its absence."""
    base = {"phase": phase, "ts": "2026-04-30T18:00:00Z", "session_id": "s-x"}
    if phase == "research":
        base.update({"questions": [], "findings": []})
    elif phase == "plan":
        base.update({"plan_path": "p.md", "phases": ["a"], "ci_commands": ["c"]})
    elif phase == "audit":
        base.update({"target": "p.md", "verdict": "PASS"})
    elif phase == "implement":
        base.update({"files_touched": ["a.py"]})
    elif phase == "substantiate":
        base.update({"verdict": "PASS", "merkle_seal": "0" * 64})
    elif phase == "validate":
        base.update({"overall": "PASS", "criteria_results": []})

    # Without provenance
    assert vga._validate_data(phase, base) == []
    # With provenance
    base_with = deepcopy(base)
    base_with["ai_provenance"] = _full_provenance()
    assert vga._validate_data(phase, base_with) == []
