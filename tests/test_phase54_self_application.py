"""Phase 54 self-application: AI provenance + new doctrines + new helpers
must scan clean against the canary scanner.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts.prompt_injection_canaries import mask_code_blocks, scan

REPO_ROOT = Path(__file__).resolve().parent.parent

PLAN_PATH = REPO_ROOT / "docs" / "plan-qor-phase54-ai-provenance-and-act-alignment.md"
EU_AI_ACT_DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-eu-ai-act.md"
AI_RMF_DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-ai-rmf.md"


def _hits(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    masked = mask_code_blocks(raw)
    return [
        f"{path.name}:{h.span[0]} [{h.canary.class_name}] {h.matched_text!r}"
        for h in scan(masked)
    ]


def test_phase54_plan_passes_canary_scan():
    assert _hits(PLAN_PATH) == []


def test_doctrine_eu_ai_act_passes_canary_scan():
    assert _hits(EU_AI_ACT_DOCTRINE) == []


def test_doctrine_ai_rmf_passes_canary_scan():
    assert _hits(AI_RMF_DOCTRINE) == []
