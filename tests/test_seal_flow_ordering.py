"""Phase 30 Phase 1: substantiate Step 7.5 must call bump_version before create_seal_tag.

Phase 29 hit an operator-level drift where create_seal_tag ran first, tag
got created at 0.20.0, and bump_version then interdicted because the tag
already existed -- forcing a manual pyproject.toml edit. Skill text is
already correct; these tests lock the contract and prevent regression.
"""
from __future__ import annotations

from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
)


def test_constraints_section_names_bump_before_tag():
    body = SKILL_PATH.read_text(encoding="utf-8")
    constraints_idx = body.find("## Constraints")
    assert constraints_idx >= 0, "Constraints section missing"
    constraints_body = body[constraints_idx:]
    assert "bump_version" in constraints_body, (
        "Constraints must name bump_version ordering rule (SG-Phase30 wiring)"
    )
    assert "create_seal_tag" in constraints_body, (
        "Constraints must name create_seal_tag ordering rule"
    )


def test_step_7_5_calls_bump_version_first():
    body = SKILL_PATH.read_text(encoding="utf-8")
    step_75_start = body.find("### Step 7.5")
    step_76_start = body.find("### Step 7.6")
    assert step_75_start >= 0, "Step 7.5 section missing"
    assert step_76_start > step_75_start, "Step 7.6 must follow Step 7.5"
    step_75 = body[step_75_start:step_76_start]
    bump_idx = step_75.find("bump_version")
    tag_idx = step_75.find("create_seal_tag")
    assert bump_idx >= 0, "Step 7.5 must call bump_version"
    assert tag_idx >= 0, "Step 7.5 must call create_seal_tag"
    assert bump_idx < tag_idx, (
        f"bump_version must appear before create_seal_tag in Step 7.5 source "
        f"(got bump at {bump_idx}, tag at {tag_idx})"
    )
