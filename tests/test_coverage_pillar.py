"""Behavioral tests for the qa.json coverage pillar (Phase 116, #168)."""
from __future__ import annotations

from qor.scripts import qa_evidence


def test_pass_at_or_above_threshold():
    p = qa_evidence.coverage_pillar(91.0, min_pct=80.0)
    assert p["status"] == "pass"
    assert p["metric"] == 91.0


def test_fail_below_threshold():
    p = qa_evidence.coverage_pillar(70.0, min_pct=80.0)
    assert p["status"] == "fail"
    assert p["metric"] == 70.0


def test_run_coverage_skips_without_data(tmp_path):
    p = qa_evidence.run_coverage(data_file=str(tmp_path / ".coverage-absent"), min_pct=80.0)
    assert p["status"] == "skip"
