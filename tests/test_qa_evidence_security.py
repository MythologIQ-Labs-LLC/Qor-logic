"""Behavioral tests: SAST result flows into the qa.json security pillar (Phase 115, #167)."""
from __future__ import annotations

from pathlib import Path

from qor.scripts import qa_evidence, validate_gate_artifact
from qor.scripts.feature_index_verify import IndexSummary

ROOT = Path(__file__).resolve().parents[1]
DOCTRINE = ROOT / "qor" / "references" / "doctrine-verification-closure-integrity.md"


def _validate(payload):
    return validate_gate_artifact._validate_data("qa", payload)


def test_sast_fail_sets_verdict_fail():
    payload = qa_evidence.build_payload(
        IndexSummary(total=1, verified=1),
        security={"status": "fail", "metric": 2.0, "note": "2 HIGH findings"},
        session_id="sid-sec-1", ts="2026-05-29T12:00:00Z",
    )
    assert payload["pillars"]["security"]["status"] == "fail"
    assert payload["verdict"] == "FAIL"
    assert _validate(payload) == []


def test_sast_skip_keeps_verdict_pass():
    payload = qa_evidence.build_payload(
        IndexSummary(total=1, verified=1),
        security={"status": "skip", "note": "bandit backend unavailable"},
        session_id="sid-sec-1", ts="2026-05-29T12:00:00Z",
    )
    assert payload["pillars"]["security"]["status"] == "skip"
    assert payload["verdict"] == "PASS"
    assert _validate(payload) == []


def test_run_sast_returns_pillar_dict():
    # bandit absent in this env -> skip; present -> pass/fail. Either way a valid pillar.
    pillar = qa_evidence.run_sast(paths=("qor/scripts",))
    assert pillar["status"] in ("pass", "fail", "skip")


def test_doctrine_defines_sast_backend_term():
    text = DOCTRINE.read_text(encoding="utf-8").lower()
    assert "sast backend" in text
    assert "skip" in text and "bandit" in text
