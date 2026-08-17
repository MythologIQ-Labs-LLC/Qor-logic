"""Phase 228 (GH #342): the reviewer-toolset contract exists where cited.

The Phase 223 recurrence: a mandated Option B reviewer had no shell across four
iterations while a content-hash freeze attestation was pinned as
reviewer-verified. The contract that closes it must live in the adversarial-mode
reference and be anchored in the Step 1 region the closure citation
(`/qor-audit Step 1`) names.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE = REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "references" / "adversarial-mode.md"
SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"


def test_the_reference_carries_the_toolset_contract():
    body = REFERENCE.read_text(encoding="utf-8")
    assert "## Reviewer toolset declaration" in body
    assert "declares its available toolset" in body
    assert "may not pin" in body


def test_step_1_anchors_the_toolset_contract():
    """The gate-step citation `/qor-audit Step 1` must resolve to a step that
    carries the contract."""
    body = SKILL.read_text(encoding="utf-8")
    match = re.search(
        r"^### Step 1: Identity Activation.*?(?=^### Step \d)",
        body, re.MULTILINE | re.DOTALL,
    )
    assert match, "Step 1 region not found"
    assert "Reviewer toolset declaration" in match.group(0)
