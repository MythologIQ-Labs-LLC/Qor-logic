"""Phase 56: doctrine round-trip integrity for secret-scanning gate."""
from __future__ import annotations

import re
from pathlib import Path

from qor.scripts.secret_scanner import PATTERNS

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-eu-ai-act.md"


def _section_body(text: str, heading: str) -> str:
    pattern = re.compile(rf"^{re.escape(heading)}\s*$\n(.*?)(?=^##\s|\Z)",
                         re.MULTILINE | re.DOTALL)
    m = pattern.search(text)
    return m.group(1) if m else ""


def test_doctrine_eu_ai_act_declares_secret_scanning_section_with_non_empty_body():
    text = DOCTRINE.read_text(encoding="utf-8")
    body = _section_body(text, "## Secret-scanning gate (Phase 56)")
    collapsed = re.sub(r"\s+", " ", body).strip()
    assert len(collapsed) >= 20, f"section body too thin: {collapsed!r}"
    for keyword in ("LLM06", "AI 600-1", "gitleaks"):
        assert keyword in body, f"doctrine body missing literal {keyword!r}"


def test_doctrine_round_trip_against_pattern_catalog():
    text = DOCTRINE.read_text(encoding="utf-8")
    body = _section_body(text, "## Secret-scanning gate (Phase 56)")
    if "see PATTERNS catalog" in body or "see `PATTERNS`" in body:
        return  # delegation marker present; round-trip waived
    missing = [p.name for p in PATTERNS if p.name not in body]
    assert not missing, (
        f"doctrine must mention each Pattern.name OR a 'see PATTERNS catalog' "
        f"delegation marker. Missing: {missing}"
    )
