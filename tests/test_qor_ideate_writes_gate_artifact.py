"""Phase 59: end-to-end /qor-ideate gate-artifact write + schema validation."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from qor.scripts import gate_chain
from qor.scripts.validate_gate_artifact import validate_one


def _minimal_payload(sid: str) -> dict:
    return {
        "phase": "ideation",
        "session_id": sid,
        "ts": "2026-05-02T03:00:00Z",
        "concept_name": "test-concept",
        "spark": {"observation": "o", "initial_question": "q", "why_now": "n"},
        "problem_frame": {"affected_actors": ["a"], "failure_mode": "f", "cost_of_failure": "c"},
        "transformation_statement": "t moves from x to y without z",
        "boundaries": {"non_goals": ["ng"], "limitations": ["lim"], "exclusions": ["ex"]},
        "governance_profile": {"risk_grade": "L2", "evidence_required": ["repro"]},
        "readiness": {"status": "ready", "recommended_next_phase": "plan"},
        "ai_provenance": {
            "system": "Qor-logic", "version": "0.45.0", "host": "u", "model_family": "u",
            "human_oversight": "absent", "ts": "2026-05-02T03:00:00Z",
        },
    }


def test_skill_completes_writes_valid_ideation_json(tmp_path, monkeypatch):
    sid = "ideate-e2e"
    monkeypatch.setattr(gate_chain, "GATES_DIR", tmp_path / ".qor" / "gates")
    monkeypatch.setenv("QOR_SKILL_ACTIVE", "ideation")
    payload = _minimal_payload(sid)
    artifact_path = gate_chain.write_gate_artifact(
        phase="ideation", payload=payload, session_id=sid,
    )
    assert artifact_path.exists()
    written = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert written["phase"] == "ideation"
    # Schema-validate the written artifact
    errs = validate_one("ideation", artifact_path)
    assert errs == [], f"written artifact failed schema validation: {errs}"


def test_skill_writes_ai_provenance_field(tmp_path, monkeypatch):
    sid = "ideate-prov"
    monkeypatch.setattr(gate_chain, "GATES_DIR", tmp_path / ".qor" / "gates")
    monkeypatch.setenv("QOR_SKILL_ACTIVE", "ideation")
    payload = _minimal_payload(sid)
    artifact_path = gate_chain.write_gate_artifact(
        phase="ideation", payload=payload, session_id=sid,
    )
    written = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert "ai_provenance" in written
    assert written["ai_provenance"]["system"] == "Qor-logic"
