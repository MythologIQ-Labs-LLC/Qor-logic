"""Phase 64 (#48): dist variant SKILL.md carries Step 6.8 after dist_compile.

Phase 30 dist-drift contract requires variants to be regenerated from
source. These tests fail red until `python -m qor.scripts.dist_compile`
runs against the Phase 64 source change.
"""
from __future__ import annotations

from pathlib import Path

import pytest

VARIANT_PATHS = {
    "claude": Path("qor/dist/variants/claude/skills/qor-substantiate/SKILL.md"),
    "codex": Path("qor/dist/variants/codex/skills/qor-substantiate/SKILL.md"),
    "kilo-code": Path("qor/dist/variants/kilo-code/skills/qor-substantiate/SKILL.md"),
}

STEP_6_8_HEADING = "### Step 6.8: Seal Hash Integrity Gate"


def _assert_variant_carries_step(variant: str) -> None:
    path = VARIANT_PATHS[variant]
    assert path.exists(), f"variant {variant} skill file missing at {path}"
    text = path.read_text(encoding="utf-8")
    count = text.count(STEP_6_8_HEADING)
    assert count == 1, (
        f"variant {variant} ({path}) must carry exactly one '{STEP_6_8_HEADING}' "
        f"heading; found {count}. Run `python -m qor.scripts.dist_compile`."
    )


def test_claude_variant_carries_step_6_8():
    _assert_variant_carries_step("claude")


def test_codex_variant_carries_step_6_8():
    _assert_variant_carries_step("codex")


def test_kilo_code_variant_carries_step_6_8():
    _assert_variant_carries_step("kilo-code")
