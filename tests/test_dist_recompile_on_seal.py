"""Phase 30 Phase 1: substantiate Step 8.5 must invoke dist_compile.

Phase 28/29 dist drift happened because variants were not rebuilt on seal.
Step 8.5 (new) rebuilds them mechanically. These tests lock the contract.
"""
from __future__ import annotations

from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parent.parent
    / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
)


def test_step_85_section_present():
    body = SKILL_PATH.read_text(encoding="utf-8")
    assert "### Step 8.5:" in body, "Step 8.5 (Dist Recompile) section missing"


def test_step_85_invokes_dist_compile():
    body = SKILL_PATH.read_text(encoding="utf-8")
    step_start = body.find("### Step 8.5:")
    step_end = body.find("### Step 9", step_start)
    assert step_start >= 0, "Step 8.5 missing"
    assert step_end > step_start, "Step 9 must follow Step 8.5"
    section = body[step_start:step_end]
    assert "qor.scripts.dist_compile" in section, (
        "Step 8.5 must invoke python -m qor.scripts.dist_compile"
    )
