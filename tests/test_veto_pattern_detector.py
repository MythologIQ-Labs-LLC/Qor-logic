"""Phase 26 Phase 1: veto pattern detector pure function tests."""
from __future__ import annotations

from pathlib import Path



FIXTURES = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_no_pattern_returns_single_pass_per_phase():
    from qor.scripts.veto_pattern import parse_phase_audit_counts
    counts = parse_phase_audit_counts(_read("ledger_no_pattern.md"))
    assert counts == {10: 1, 11: 1}


def test_parse_pattern_fires_returns_multi_pass_counts():
    from qor.scripts.veto_pattern import parse_phase_audit_counts
    counts = parse_phase_audit_counts(_read("ledger_pattern_fires.md"))
    assert counts == {24: 3, 25: 3}


def test_parse_pattern_clears_includes_reset_phase():
    from qor.scripts.veto_pattern import parse_phase_audit_counts
    counts = parse_phase_audit_counts(_read("ledger_pattern_clears.md"))
    assert counts == {24: 3, 25: 3, 26: 1}


def test_detector_no_pattern():
    from qor.scripts.veto_pattern import detect_repeated_veto_pattern
    result = detect_repeated_veto_pattern({10: 1, 11: 1}, window=2)
    assert result.detected is False
    assert result.recent_phases == []


def test_detector_pattern_fires_on_two_consecutive_multi_pass():
    from qor.scripts.veto_pattern import detect_repeated_veto_pattern
    result = detect_repeated_veto_pattern({24: 3, 25: 3}, window=2)
    assert result.detected is True
    assert result.recent_phases == [24, 25]
    assert result.max_pass_count == 3


def test_detector_resets_when_clean_phase_follows():
    from qor.scripts.veto_pattern import detect_repeated_veto_pattern
    result = detect_repeated_veto_pattern({24: 3, 25: 3, 26: 1}, window=2)
    assert result.detected is False
    assert result.recent_phases == []


def test_detector_single_sealed_phase_not_enough():
    from qor.scripts.veto_pattern import detect_repeated_veto_pattern
    result = detect_repeated_veto_pattern({24: 1}, window=2)
    assert result.detected is False


def test_detector_one_phase_many_passes_is_not_the_pattern():
    """B18 is CROSS-phase; a single phase with many passes does not fire."""
    from qor.scripts.veto_pattern import detect_repeated_veto_pattern
    result = detect_repeated_veto_pattern({24: 5}, window=2)
    assert result.detected is False


def test_detector_window_3_requires_three_consecutive():
    from qor.scripts.veto_pattern import detect_repeated_veto_pattern
    # Two consecutive multi-pass -- not enough for window=3
    assert detect_repeated_veto_pattern({24: 3, 25: 3}, window=3).detected is False
    # Three consecutive multi-pass -- detected
    assert detect_repeated_veto_pattern({24: 3, 25: 3, 26: 2}, window=3).detected is True


def test_pattern_result_namedtuple_shape():
    from qor.scripts.veto_pattern import PatternResult
    r = PatternResult(detected=True, recent_phases=[1, 2], max_pass_count=3)
    assert r.detected is True
    assert r.recent_phases == [1, 2]
    assert r.max_pass_count == 3


def test_parse_ignores_non_audit_entries_in_counts():
    """IMPLEMENT, REFACTOR, SEAL entries should not count as audit passes."""
    from qor.scripts.veto_pattern import parse_phase_audit_counts
    text = """
### Entry #1: AUDIT -- Phase 5 plan review
**Verdict**: PASS

### Entry #2: REFACTOR -- Phase 5 extract module
**Verdict**: PASS

### Entry #3: IMPLEMENT -- Phase 5 build
**Verdict**: PASS

### Entry #4: SESSION SEAL -- Phase 5 substantiated
**Verdict**: PASS
"""
    counts = parse_phase_audit_counts(text)
    assert counts == {5: 1}


def test_parse_skips_unsealed_phase():
    """A phase without a SEAL entry should not appear in counts (in-flight work)."""
    from qor.scripts.veto_pattern import parse_phase_audit_counts
    text = """
### Entry #1: AUDIT -- Phase 5 plan review
**Verdict**: PASS

### Entry #2: SESSION SEAL -- Phase 5 substantiated

### Entry #3: AUDIT -- Phase 6 plan review
**Verdict**: VETO

### Entry #4: AUDIT -- Phase 6 plan review (Pass 2)
**Verdict**: PASS
"""
    counts = parse_phase_audit_counts(text)
    assert counts == {5: 1}  # Phase 6 not sealed yet


# --- Phase 227 (GH #342): the detector reads the ledger that exists ----------

_GATE_TRIBUNAL_LEDGER = """
### Entry #10: GATE TRIBUNAL -- Phase 300 widget driver, iteration 1 (VETO)
**Verdict**: VETO

### Entry #11: GATE TRIBUNAL -- Phase 300 widget driver, iteration 2 (PASS)
**Verdict**: PASS

### Entry #12: SESSION SEAL -- Phase 300 widget driver (v9.9.9)
**Verdict**: PASS

### Entry #13: GATE TRIBUNAL -- Phase 301 gadget driver, iteration 1 (VETO)
**Verdict**: VETO

### Entry #14: GATE TRIBUNAL -- Phase 301 gadget driver, iteration 2 (PASS)
**Verdict**: PASS

### Entry #15: SESSION SEAL -- Phase 301 gadget driver (v9.9.10)
**Verdict**: PASS
"""


def test_gate_tribunal_entries_are_counted():
    """The ledger has written GATE TRIBUNAL since Entry #86; the detector must
    count the convention that exists, not the one retired at phase 27."""
    from qor.scripts.veto_pattern import parse_phase_audit_counts
    counts = parse_phase_audit_counts(_GATE_TRIBUNAL_LEDGER)
    assert counts == {300: 2, 301: 2}


def test_audit_entries_still_counted():
    """The grandfathered convention (entries 1-85, existing fixtures) keeps parsing."""
    from qor.scripts.veto_pattern import parse_phase_audit_counts
    counts = parse_phase_audit_counts(_read("ledger_pattern_fires.md"))
    assert counts == {24: 3, 25: 3}


def test_in_flight_phase_joins_the_window():
    """A live multi-pass phase is visible BEFORE its seal: the detector must not
    be structurally one phase late."""
    from qor.scripts.veto_pattern import detect_repeated_veto_pattern
    result = detect_repeated_veto_pattern({24: 3}, window=2, in_flight=(25, 2))
    assert result.detected is True
    assert result.recent_phases == [24, 25]
    assert result.max_pass_count == 3


def test_in_flight_single_pass_does_not_fire():
    """One audit pass in the live phase is normal; only a multi-pass in-flight
    phase may join the window."""
    from qor.scripts.veto_pattern import detect_repeated_veto_pattern
    result = detect_repeated_veto_pattern({24: 3}, window=2, in_flight=(25, 1))
    assert result.detected is False


def test_stale_older_unsealed_phase_never_joins_the_window():
    """Ordering guard: an abandoned unsealed phase OLDER than the newest sealed
    phase must not compose the window out of temporal order."""
    from qor.scripts.veto_pattern import detect_repeated_veto_pattern
    result = detect_repeated_veto_pattern({24: 3, 26: 3}, window=2, in_flight=(25, 2))
    assert result.detected is False or 25 not in result.recent_phases


def test_the_real_ledger_parses_to_nonempty_counts_above_phase_200():
    """The anti-recurrence binding: the parser recognizes the repo's own ledger.

    Asserts a monotone structural property (sealed phases cannot unseal; the
    ledger is append-only), never specific values -- the deliberate opposite of
    the synthetic-only suite that concealed eight phases of blindness.
    """
    from qor.scripts.veto_pattern import parse_phase_audit_counts
    ledger = Path(__file__).resolve().parents[1] / "docs" / "META_LEDGER.md"
    counts = parse_phase_audit_counts(ledger.read_text(encoding="utf-8"))
    assert any(phase > 200 for phase in counts), (
        "the detector cannot see any sealed phase above 200 -- the recognition "
        "defect (veto_pattern blindness) has recurred"
    )
