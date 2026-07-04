"""Phase 164: substantiate Steps 6/6.5 invoke the seal-artifact generator.

Single structural regression lock replacing the 6 prose-pattern tests of
tests/test_substantiate_badge_currency_wiring.py (retired; generate-not-assert,
research entry #378 rec 2). Skill prose has no invokable unit; the behavioral
coverage lives in tests/test_seal_artifacts.py.
"""
from __future__ import annotations

import re
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[1]
    / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
)


def test_substantiate_steps_6_and_6_5_invoke_seal_artifacts():
    text = SKILL.read_text(encoding="utf-8")  # prose-lint: ok=wiring regression lock; skill prose has no invokable unit
    step6 = text[text.index("### Step 6: Sync System State"):text.index("### Step 6.5:")]
    step65_end = text.index("### Step 6.8")
    step65 = text[text.index("### Step 6.5:"):step65_end]
    assert re.search(r"seal_artifacts --write --phase", step6), (
        "Step 6 must regenerate seal artifacts via 'seal_artifacts --write --phase ...'"
    )
    assert re.search(r"seal_artifacts --check", step65), (
        "Step 6.5 must gate on 'seal_artifacts --check'"
    )
    assert re.search(r"ABORT", step65), "Step 6.5 must retain ABORT semantics"
    assert re.search(r"hotfix exempt", step65), "Step 6.5 must retain the hotfix exemption"
