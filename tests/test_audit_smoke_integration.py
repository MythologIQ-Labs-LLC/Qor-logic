"""Phase 26 Phase 3: smoke integration -- detector + advisory rendering."""
from __future__ import annotations

from pathlib import Path


FIXTURES = Path(__file__).parent / "fixtures"


def test_pattern_fires_end_to_end():
    from qor.scripts.veto_pattern import check, render_advisory_text
    ledger = FIXTURES / "ledger_pattern_fires.md"
    result = check(ledger_path=ledger)
    assert result.detected is True
    advisory = render_advisory_text(result)
    assert "/qor-remediate" in advisory
    assert "24" in advisory and "25" in advisory
    assert "non-blocking" in advisory.lower()


def test_no_pattern_advisory_says_none_detected():
    from qor.scripts.veto_pattern import check, render_advisory_text
    ledger = FIXTURES / "ledger_no_pattern.md"
    result = check(ledger_path=ledger)
    assert result.detected is False
    advisory = render_advisory_text(result)
    assert "No repeated-VETO pattern detected" in advisory
    assert "/qor-remediate" not in advisory


def test_pattern_clears_after_clean_phase():
    """Regression guard: a clean phase between multi-pass ones resets streak."""
    from qor.scripts.veto_pattern import check, render_advisory_text
    ledger = FIXTURES / "ledger_pattern_clears.md"
    result = check(ledger_path=ledger)
    assert result.detected is False
    advisory = render_advisory_text(result)
    assert "/qor-remediate" not in advisory


def test_advisory_text_ready_for_template_slot():
    """Confirm the rendered text drops cleanly under the qor:veto-pattern-advisory marker."""
    from qor.scripts.veto_pattern import PatternResult, render_advisory_text
    fired = PatternResult(detected=True, recent_phases=[40, 41], max_pass_count=2)
    text = render_advisory_text(fired)
    # Text is a single paragraph, no markdown headers; the template already
    # provides the `## Process Pattern Advisory` header and the marker.
    assert not text.startswith("#")
    assert text.strip() == text
