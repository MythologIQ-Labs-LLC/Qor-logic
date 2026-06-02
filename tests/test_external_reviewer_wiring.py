"""Prompt-contract wiring tests for Phase 123 (GH #160)."""
from __future__ import annotations

from pathlib import Path

AUDIT = Path("qor/skills/governance/qor-audit/SKILL.md")
ADV_MODE = Path("qor/skills/governance/qor-audit/references/adversarial-mode.md")


def test_audit_references_bridge_with_fallback() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    idx = text.index("Identity Activation")
    region = text[idx:idx + 2500]
    assert "external_reviewer" in region  # prose-lint: ok=prompt-contract
    assert "capability_shortfall" in region  # prose-lint: ok=prompt-contract


def test_adversarial_mode_doc_marks_bridge_shipped() -> None:
    doc = ADV_MODE.read_text(encoding="utf-8")
    assert "Contract-only specification" not in doc  # prose-lint: ok=prompt-contract
    assert "qor.scripts.external_reviewer" in doc  # prose-lint: ok=prompt-contract
    assert "external_reviewer.command" in doc  # prose-lint: ok=prompt-contract
