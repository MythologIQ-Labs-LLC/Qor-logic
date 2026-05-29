"""Skill-integrity grep-lints for Phase 37 B21 wiring."""
from __future__ import annotations

import importlib.util
import json
import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_QOR_PLAN = pathlib.Path("qor/skills/sdlc/qor-plan/SKILL.md")
_QOR_AUDIT = pathlib.Path("qor/skills/governance/qor-audit/SKILL.md")
_DELEGATION = pathlib.Path("qor/gates/delegation-table.md")
_AUDIT_SCHEMA = pathlib.Path("qor/gates/schema/audit.schema.json")


def test_qor_plan_skill_calls_cycle_count_check():
    prose = _QOR_PLAN.read_text(encoding="utf-8")
    assert "cycle_count_escalator" in prose  # prose-lint: ok=prompt-citation paired with existence check
    assert importlib.util.find_spec("qor.scripts.cycle_count_escalator") is not None
    assert "cce.check" in prose or "cycle_count_escalator.check" in prose


def test_qor_audit_skill_calls_cycle_count_check():
    prose = _QOR_AUDIT.read_text(encoding="utf-8")
    assert "cycle_count_escalator" in prose  # prose-lint: ok=prompt-citation paired with existence check
    assert importlib.util.find_spec("qor.scripts.cycle_count_escalator") is not None


def test_qor_audit_has_infrastructure_alignment_pass():
    prose = _QOR_AUDIT.read_text(encoding="utf-8")
    assert "Infrastructure Alignment Pass" in prose  # prose-lint: ok=prompt-contract: audit pass name
    assert "infrastructure-mismatch" in prose  # prose-lint: ok=prompt-citation paired with existence check
    schema = json.loads((REPO_ROOT / _AUDIT_SCHEMA).read_text(encoding="utf-8"))
    assert "infrastructure-mismatch" in json.dumps(schema)


def test_delegation_table_lists_cycle_count_escalation():
    prose = _DELEGATION.read_text(encoding="utf-8")
    assert "cycle-count escalation" in prose
    assert "orchestration_override" in prose
