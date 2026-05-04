"""Phase 59: /qor-research check_prior_artifact recognizes ideation."""
from __future__ import annotations

import json
import os
from pathlib import Path

from qor.scripts import gate_chain


def _write_ideation(repo_root: Path, sid: str) -> None:
    gates = repo_root / ".qor" / "gates" / sid
    gates.mkdir(parents=True, exist_ok=True)
    payload = {
        "phase": "ideation", "ts": "2026-05-02T03:00:00Z", "session_id": sid,
        "concept_name": "x", "spark": {"observation": "o", "initial_question": "q", "why_now": "n"},
        "problem_frame": {"affected_actors": ["a"], "failure_mode": "f", "cost_of_failure": "c"},
        "transformation_statement": "t",
        "boundaries": {"non_goals": [], "limitations": [], "exclusions": []},
        "governance_profile": {"risk_grade": "L1", "evidence_required": []},
        "readiness": {"status": "ready", "recommended_next_phase": "research"},
        "ai_provenance": {
            "system": "Qor-logic", "version": "0.45.0", "host": "u", "model_family": "u",
            "human_oversight": "absent", "ts": "2026-05-02T03:00:00Z",
        },
    }
    (gates / "ideation.json").write_text(json.dumps(payload), encoding="utf-8")


def test_check_prior_artifact_recognizes_ideation_for_research_phase(monkeypatch, tmp_path):
    sid = "ideation-research-test"
    _write_ideation(tmp_path, sid)
    # Repoint GATES_DIR at tmp_path
    monkeypatch.setattr(gate_chain, "GATES_DIR", tmp_path / ".qor" / "gates")
    result = gate_chain.check_prior_artifact("research", session_id=sid)
    assert result.found is True
    assert result.valid is True


def test_check_prior_artifact_research_succeeds_without_ideation(monkeypatch, tmp_path):
    """Backward compat: research with no prior at all still passes (legacy)."""
    monkeypatch.setattr(gate_chain, "GATES_DIR", tmp_path / ".qor" / "gates")
    result = gate_chain.check_prior_artifact("research", session_id="no-ideation")
    assert result.found is True
    assert result.valid is True
    assert result.path is None  # no prior expected
