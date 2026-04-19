"""Phase 30 Phase 1 + Phase 33 update: substantiate must call bump_version
at Step 7.5 and create_seal_tag at Step 9.5.5 (post-seal-commit).

Phase 29 hit an operator-level drift where create_seal_tag ran first, tag
got created at 0.20.0, and bump_version then interdicted because the tag
already existed -- forcing a manual pyproject.toml edit.

Phase 33 uncovered a separate bug: even after Phase 30's ordering fix,
create_seal_tag at Step 7.5 tagged the pre-seal HEAD (seal commit isn't
made until Step 9.5). So tagging was moved entirely to Step 9.5.5
post-commit. These tests lock both contracts.
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


def test_step_7_5_bumps_and_step_9_5_5_tags():
    body = SKILL_PATH.read_text(encoding="utf-8")
    step_75_start = body.find("### Step 7.5")
    step_76_start = body.find("### Step 7.6")
    step_955_start = body.find("### Step 9.5.5")
    step_96_start = body.find("### Step 9.6")
    assert step_75_start >= 0, "Step 7.5 section missing"
    assert step_76_start > step_75_start, "Step 7.6 must follow Step 7.5"
    assert step_955_start > step_76_start, "Step 9.5.5 must follow Step 7.5"
    assert step_96_start > step_955_start, "Step 9.6 must follow Step 9.5.5"

    step_75 = body[step_75_start:step_76_start]
    step_955 = body[step_955_start:step_96_start]

    assert "bump_version" in step_75, "Step 7.5 must call bump_version"
    assert "create_seal_tag" not in step_75, (
        "Step 7.5 must NOT call create_seal_tag (Phase 33: tagging moved to 9.5.5)"
    )
    assert "create_seal_tag" in step_955, "Step 9.5.5 must call create_seal_tag"
    assert "commit=" in step_955, (
        "Step 9.5.5 must pass commit= kwarg to create_seal_tag"
    )
