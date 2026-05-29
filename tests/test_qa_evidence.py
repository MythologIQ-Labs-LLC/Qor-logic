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
