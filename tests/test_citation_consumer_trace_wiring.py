"""Prompt-contract wiring test for Phase 126 (GH #157)."""
from __future__ import annotations

from pathlib import Path

_DOC = Path("qor/skills/governance/qor-audit/references/phase37-subpasses.md")


def test_phase37_names_runnable_trace() -> None:
    text = _DOC.read_text(encoding="utf-8")
    assert "citation_consumer_trace" in text  # prose-lint: ok=prompt-contract
    assert "--entry" in text and "--symbol" in text  # prose-lint: ok=prompt-contract
