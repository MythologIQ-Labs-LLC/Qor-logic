"""Phase 26 Phase 1: veto pattern detector pure function tests."""
from __future__ import annotations

from pathlib import Path

import pytest


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
