"""Tests for audit gate emission of findings_categories (Phase 37 B20b)."""
from __future__ import annotations

import pathlib
import pytest

from qor.scripts import validate_gate_artifact as vga


_QOR_AUDIT_SKILL = pathlib.Path("qor/skills/governance/qor-audit/SKILL.md")
_QOR_AUDIT_TEMPLATES = pathlib.Path(
    "qor/skills/governance/qor-audit/references/qor-audit-templates.md"
)


def _veto_payload(**overrides):
    payload = {
        "phase": "audit",
        "ts": "2026-04-20T12:00:00Z",
        "session_id": "s-veto",
        "target": "docs/plan.md",
        "verdict": "VETO",
        "findings_categories": ["specification-drift"],
    }
    payload.update(overrides)
    return payload


def _pass_payload(**overrides):
    payload = {
        "phase": "audit",
        "ts": "2026-04-20T12:00:00Z",
        "session_id": "s-pass",
        "target": "docs/plan.md",
        "verdict": "PASS",
    }
    payload.update(overrides)
    return payload


def test_veto_audit_schema_requires_categories():
    # VETO without findings_categories -> validation fails
    payload = _veto_payload()
    payload.pop("findings_categories")
    errs = vga._validate_data("audit", payload)
    assert errs, "VETO without findings_categories must fail schema"


def test_pass_audit_schema_allows_missing_categories():
    # PASS without findings_categories -> validates
    errs = vga._validate_data("audit", _pass_payload())
    assert errs == []


def test_pass_audit_schema_allows_empty_categories():
    errs = vga._validate_data("audit", _pass_payload(findings_categories=[]))
    assert errs == []


def test_schema_rejects_unknown_category():
    errs = vga._validate_data("audit", _veto_payload(findings_categories=["fictional-cat"]))
    assert errs, "Unknown category value must fail schema enum"


def test_qor_audit_skill_names_findings_categories_slot():
    prose = _QOR_AUDIT_SKILL.read_text(encoding="utf-8")
    assert "findings_categories" in prose, \
        "/qor-audit skill must reference findings_categories field"


def test_qor_audit_skill_names_unmapped_category_error():
    prose = _QOR_AUDIT_SKILL.read_text(encoding="utf-8")
    assert "UnmappedCategoryError" in prose, \
        "/qor-audit skill must cite UnmappedCategoryError discipline"


def test_qor_audit_template_has_findings_categories_slot():
    prose = _QOR_AUDIT_TEMPLATES.read_text(encoding="utf-8")
    assert "findings_categories" in prose, \
        "audit template must declare a findings_categories slot"


def test_schema_accepts_prompt_injection_category():
    """Phase 53: prompt-injection is a valid VETO category."""
    errs = vga._validate_data(
        "audit", _veto_payload(findings_categories=["prompt-injection"])
    )
    assert errs == [], (
        f"prompt-injection must be in audit.schema.json findings_categories enum; "
        f"got errors: {errs}"
    )
