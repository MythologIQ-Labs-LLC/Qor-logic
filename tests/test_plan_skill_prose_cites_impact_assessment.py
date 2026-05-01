"""Phase 54: schema-anchored round-trip integrity for Step 1c subfields.

Reads the plan schema's `impact_assessment` required subfield names, then
asserts every name appears in the qor-plan SKILL.md Step 1c section body
with a non-empty body. Drift between schema and SKILL.md prose surfaces
immediately.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "qor" / "gates" / "schema" / "plan.schema.json"
SKILL_PATH = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-plan" / "SKILL.md"

_HEADING_RE = re.compile(r"^#{1,6}\s+.+$", re.MULTILINE)


def _section_body(content: str, heading_pattern: str) -> str:
    match = re.search(heading_pattern, content, re.MULTILINE)
    assert match, f"missing heading matching {heading_pattern!r}"
    rest = content[match.end():]
    next_h = _HEADING_RE.search(rest)
    return rest[: next_h.start()].strip() if next_h else rest.strip()


def _impact_subfields_from_schema() -> tuple[str, ...]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    impact = schema["properties"]["impact_assessment"]
    required = tuple(impact.get("required", []))
    assert required, "schema must declare impact_assessment required subfields"
    return required


def test_plan_skill_step_1c_round_trips_impact_assessment_subfields():
    content = SKILL_PATH.read_text(encoding="utf-8")
    body = _section_body(content, r"^###\s+Step 1c:.*Impact assessment")
    assert body, "Step 1c section body must be non-empty"
    compact = re.sub(r"\s+", " ", body).strip()
    assert len(compact) >= 50, f"Step 1c body too short: {compact!r}"

    subfields = _impact_subfields_from_schema()
    missing = [f for f in subfields if f not in body]
    assert not missing, (
        f"qor-plan Step 1c body must mention every impact_assessment subfield "
        f"declared in plan.schema.json; missing: {missing}; subfields: {subfields}"
    )


def test_step_1c_references_high_risk_target_flag():
    content = SKILL_PATH.read_text(encoding="utf-8")
    body = _section_body(content, r"^###\s+Step 1c:.*Impact assessment")
    assert "high_risk_target" in body, (
        "Step 1c body must reference the high_risk_target trigger flag"
    )


def test_step_1c_references_eu_ai_act_doctrine():
    content = SKILL_PATH.read_text(encoding="utf-8")
    body = _section_body(content, r"^###\s+Step 1c:.*Impact assessment")
    assert "doctrine-eu-ai-act.md" in body or "doctrine-ai-rmf.md" in body, (
        "Step 1c body must cross-link the AI Act / AI RMF doctrine"
    )
