"""Phase 176 (GH #262): the documented seal staging list must include the
sealed session's gate artifacts.

Step 7.8 and the required CI job (gate_chain_completeness) make the committed
`.qor/gates/<sid>/` files load-bearing for every sealed phase >= 52; a Step
9.5 block that omits them ships a seal whose CI completeness gate fails.
These are prose-contract tests: the SKILL.md block IS the operator-facing
procedure under test.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CANONICAL = REPO / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
VARIANTS = [
    REPO / "qor" / "dist" / "variants" / host / "skills" / "qor-substantiate" / "SKILL.md"
    for host in ("claude", "codex", "kilo-code")
]

EXCEEDED_BYTES = 40 * 1024  # mirrors qor/scripts/skill_size_budget_lint.py


def _step_9_5_bash(text: str) -> str:
    """The first fenced bash block inside the Step 9.5 section."""
    section = re.search(r"### Step 9\.5:.*?(?=\n### Step)", text, re.DOTALL)
    assert section, "Step 9.5 section not found"
    block = re.search(r"```bash\n(.*?)```", section.group(0), re.DOTALL)
    assert block, "Step 9.5 bash block not found"
    return block.group(1)


def test_step_9_5_stages_the_sealed_gate_dir():
    # prose-lint: ok=Step 9.5's git-add block IS the operator procedure under
    # test; GH #262 is exactly this block omitting the load-bearing gate dir.
    bash = _step_9_5_bash(CANONICAL.read_text(encoding="utf-8"))
    add_lines = [ln for ln in bash.splitlines() if "git add" in ln]
    assert any(".qor/gates/" in ln and "$SESSION_ID" in ln for ln in add_lines), (
        "Step 9.5 must stage the sealed session's gate artifacts "
        f"(.qor/gates/$SESSION_ID/); got: {add_lines}"
    )


def test_skill_stays_under_exceeded_budget():
    # Locks plan LD-2: the GH #262 amendment must pay for itself in bytes so a
    # seal cannot be blocked by the size-budget EXCEEDED threshold.
    size = os.path.getsize(CANONICAL)
    assert size < EXCEEDED_BYTES, (
        f"qor-substantiate SKILL.md is {size} bytes; EXCEEDED at {EXCEEDED_BYTES}"
    )


@pytest.mark.parametrize("variant", VARIANTS, ids=lambda p: p.parts[-4])
def test_variants_match_canonical_step_9_5(variant):
    # prose-lint: ok=variant-vs-canonical equality of the same operator
    # procedure block; regression lock on dist regeneration.
    canonical_block = _step_9_5_bash(CANONICAL.read_text(encoding="utf-8"))
    variant_block = _step_9_5_bash(variant.read_text(encoding="utf-8"))
    assert variant_block == canonical_block
