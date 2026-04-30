"""Phase 53 self-application: the system that defends against prompt
injection must not itself contain a prompt injection.

The doctrine documents canary classes via worked examples written inside
backtick-delimited spans. Production scanning at `/qor-audit` consumes
governance markdown verbatim; this test masks fenced and inline backtick
content before scanning to mirror how operators would author governance
markdown that *describes* canaries without *embedding* them.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts.prompt_injection_canaries import mask_code_blocks, scan

REPO_ROOT = Path(__file__).resolve().parent.parent

PLAN_PATH = REPO_ROOT / "docs" / "plan-qor-phase53-prompt-injection-defense.md"
RESEARCH_BRIEF_PATH = (
    REPO_ROOT / "docs" / "research-brief-prompt-logic-frameworks-2026-04-30.md"
)
DOCTRINE_PATH = (
    REPO_ROOT / "qor" / "references" / "doctrine-prompt-injection.md"
)


def _hits_in_prose(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    masked = mask_code_blocks(raw)
    hits = scan(masked)
    return [
        f"{path.name}:{h.span[0]} [{h.canary.class_name}] {h.matched_text!r}"
        for h in hits
    ]


def test_phase53_plan_passes_canary_scan():
    """The Phase 53 plan must not embed prompt-injection canaries in prose."""
    hits = _hits_in_prose(PLAN_PATH)
    assert not hits, f"plan contains canary triggers in prose: {hits}"


def test_research_brief_passes_canary_scan():
    """The research brief that motivated Phase 53 must scan clean."""
    hits = _hits_in_prose(RESEARCH_BRIEF_PATH)
    assert not hits, f"research brief contains canary triggers in prose: {hits}"


def test_doctrine_prompt_injection_passes_canary_scan():
    """The doctrine itself must scan clean once worked examples are masked.

    Mirrors how `/qor-audit` will treat doctrine content: production scan
    runs against the raw file, but the doctrine narrative outside its
    backtick-delimited worked examples is the meaningful surface to verify.
    """
    hits = _hits_in_prose(DOCTRINE_PATH)
    assert not hits, f"doctrine contains canary triggers in prose: {hits}"
