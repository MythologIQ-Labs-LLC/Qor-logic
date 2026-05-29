"""Tests for plan.schema.json ci_commands slot (Phase 38 B22)."""
from __future__ import annotations

import json
import pathlib
import re

import pytest

from qor.scripts import validate_gate_artifact as vga


_SKILL = pathlib.Path("qor/skills/sdlc/qor-plan/SKILL.md")
_PLANS_DIR = pathlib.Path("docs")


def _base_plan_payload(**overrides):
    payload = {
        "phase": "plan",
        "ts": "2026-04-20T12:00:00Z",
        "session_id": "s-ci-test",
        "plan_path": "docs/plan-qor-phaseXX.md",
        "phases": ["Phase 1: thing"],
        "ci_commands": ["pytest"],
    }
    payload.update(overrides)
    return payload


def test_plan_schema_requires_ci_commands_for_phase_38_plus():
    payload = _base_plan_payload()
    payload.pop("ci_commands")
    errs = vga._validate_data("plan", payload)
    assert errs, "plan without ci_commands must fail schema"


def test_plan_schema_rejects_empty_ci_commands():
    errs = vga._validate_data("plan", _base_plan_payload(ci_commands=[]))
    assert errs, "empty ci_commands must fail minItems:1"


def test_plan_schema_rejects_empty_command_string():
    errs = vga._validate_data("plan", _base_plan_payload(ci_commands=[""]))
    assert errs, "empty-string command must fail minLength:1"


def test_plan_schema_accepts_valid_ci_commands():
    errs = vga._validate_data("plan", _base_plan_payload(
        ci_commands=["pytest tests/foo.py", "pytest", "python -m qor.reliability.gate_skill_matrix"]
    ))
    assert errs == [], f"valid ci_commands should pass: {errs}"


def test_qor_plan_skill_template_has_ci_commands_section():
    prose = _SKILL.read_text(encoding="utf-8")
    assert "## CI Commands" in prose or "CI Commands" in prose
    assert "ci_commands" in prose  # prose-lint: ok=prompt-contract: plan-template field label


def test_pre_phase_38_plans_grandfathered():
    """Plans with phase number < 38 are grandfathered; phase >= 38 must validate."""
    pattern = re.compile(r"plan-qor-phase(\d+)-.*\.md$")
    for plan_path in _PLANS_DIR.glob("plan-qor-phase*.md"):
        match = pattern.search(plan_path.name)
        if not match:
            continue
        phase_num = int(match.group(1))
        # Grandfathering: skip plans authored before Phase 38.
        if phase_num < 38:
            continue
        # Plans authored Phase 38 and later must declare a ci_commands section.
        prose = plan_path.read_text(encoding="utf-8")
        assert "## CI Commands" in prose, \
            f"Plan {plan_path.name} (phase {phase_num}) missing '## CI Commands' section"
