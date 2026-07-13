"""Behavioral tests for the qa.json evidence artifact (Phase 114, #166).

Tests verify behavior, not presence: payloads are validated against the real
schema via validate_gate_artifact, and the regression pillar's status is
derived from an actual IndexSummary.
"""
from __future__ import annotations

import json

import pytest

from qor.scripts import qa_evidence, validate_gate_artifact
from qor.scripts.feature_index_verify import IndexSummary


def _validate(payload: dict) -> list[str]:
    return validate_gate_artifact._validate_data("qa", payload)


def test_payload_validates_against_schema():
    payload = qa_evidence.build_payload(
        regression_summary=IndexSummary(total=3, verified=3),
        session_id="test-sid-001",
        ts="2026-05-29T12:00:00Z",
    )
    assert _validate(payload) == []
    assert payload["phase"] == "qa"
    assert payload["verdict"] == "PASS"


def test_invalid_verdict_rejected():
    payload = qa_evidence.build_payload(
        regression_summary=IndexSummary(total=1, verified=1),
        session_id="test-sid-001",
        ts="2026-05-29T12:00:00Z",
    )
    payload["verdict"] = "MAYBE"
    assert _validate(payload) != []


def test_pillar_status_enum_enforced():
    payload = qa_evidence.build_payload(
        regression_summary=IndexSummary(total=1, verified=1),
        session_id="test-sid-001",
        ts="2026-05-29T12:00:00Z",
    )
    payload["pillars"]["regression"]["status"] = "bogus"
    assert _validate(payload) != []


def test_regression_pillar_fails_on_newly_unverified():
    payload = qa_evidence.build_payload(
        regression_summary=IndexSummary(total=2, verified=1, unverified=1,
                                        newly_unverified=("feat-x",)),
        session_id="test-sid-001",
        ts="2026-05-29T12:00:00Z",
    )
    assert payload["pillars"]["regression"]["status"] == "fail"
    assert payload["verdict"] == "FAIL"
    assert _validate(payload) == []


def test_partial_pillars_skip_with_note():
    payload = qa_evidence.build_payload(
        regression_summary=IndexSummary(total=1, verified=1),
        session_id="test-sid-001",
        ts="2026-05-29T12:00:00Z",
    )
    for pillar in ("security", "stability", "coverage"):
        assert payload["pillars"][pillar]["status"] == "skip"
        assert payload["pillars"][pillar].get("note", "").strip(), pillar
    assert _validate(payload) == []


# ----- Phase 177 (GH #269): production policy + required pillars -----

def _summary_pass():
    return IndexSummary(total=3, verified=3)


def test_adoption_default_output_unchanged():
    """Byte-compat lock: no new kwargs -> no policy keys, all-skip still PASS."""
    payload = qa_evidence.build_payload(
        regression_summary=_summary_pass(),
        session_id="test-sid-177", ts="2026-07-13T00:00:00Z",
    )
    assert "policy" not in payload and "required_pillars" not in payload
    assert payload["verdict"] == "PASS"
    assert all(payload["pillars"][n]["status"] == "skip"
               for n in ("security", "stability", "coverage"))


def test_production_required_skip_fails_verdict():
    """GH #269 acceptance: a required-but-skipped pillar cannot yield PASS."""
    payload = qa_evidence.build_payload(
        regression_summary=_summary_pass(),
        session_id="test-sid-177", ts="2026-07-13T00:00:00Z",
        policy="production", required_pillars={"security"},
    )
    assert payload["verdict"] == "FAIL"


def test_production_required_pass_passes():
    payload = qa_evidence.build_payload(
        regression_summary=_summary_pass(),
        security={"status": "pass", "note": "sast clean"},
        session_id="test-sid-177", ts="2026-07-13T00:00:00Z",
        policy="production", required_pillars={"security", "regression"},
    )
    assert payload["verdict"] == "PASS"
    assert payload["policy"] == "production"
    assert payload["required_pillars"] == ["regression", "security"]


def test_production_required_fail_fails():
    payload = qa_evidence.build_payload(
        regression_summary=_summary_pass(),
        security={"status": "fail", "note": "finding"},
        session_id="test-sid-177", ts="2026-07-13T00:00:00Z",
        policy="production", required_pillars={"security"},
    )
    assert payload["verdict"] == "FAIL"


def test_production_optional_skip_still_passes():
    payload = qa_evidence.build_payload(
        regression_summary=_summary_pass(),
        session_id="test-sid-177", ts="2026-07-13T00:00:00Z",
        policy="production", required_pillars={"regression"},
    )
    assert payload["verdict"] == "PASS"  # non-required skips stay skip-visible


def test_production_without_required_set_raises():
    with pytest.raises(ValueError):
        qa_evidence.build_payload(
            regression_summary=_summary_pass(),
            session_id="test-sid-177", ts="2026-07-13T00:00:00Z",
            policy="production",
        )
    with pytest.raises(ValueError):
        qa_evidence.build_payload(
            regression_summary=_summary_pass(),
            session_id="test-sid-177", ts="2026-07-13T00:00:00Z",
            policy="production", required_pillars=set(),
        )


def test_production_payload_validates_against_schema():
    production = qa_evidence.build_payload(
        regression_summary=_summary_pass(),
        security={"status": "pass"},
        session_id="test-sid-177", ts="2026-07-13T00:00:00Z",
        policy="production", required_pillars={"security"},
    )
    assert _validate(production) == []
    adoption = qa_evidence.build_payload(
        regression_summary=_summary_pass(),
        session_id="test-sid-177", ts="2026-07-13T00:00:00Z",
    )
    assert _validate(adoption) == []
