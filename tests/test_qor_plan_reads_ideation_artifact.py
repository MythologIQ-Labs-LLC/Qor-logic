"""Phase 59: /qor-plan check_prior_artifact accepts ideation OR research."""
from __future__ import annotations

import json
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
        "readiness": {"status": "ready", "recommended_next_phase": "plan"},
        "ai_provenance": {
            "system": "Qor-logic", "version": "0.45.0", "host": "u", "model_family": "u",
            "human_oversight": "absent", "ts": "2026-05-02T03:00:00Z",
        },
    }
    (gates / "ideation.json").write_text(json.dumps(payload), encoding="utf-8")


def test_check_prior_artifact_recognizes_ideation_for_plan_phase(monkeypatch, tmp_path):
    """When ideation.json exists but research.json does not, plan check accepts ideation."""
    sid = "ideation-plan-test"
    _write_ideation(tmp_path, sid)
    monkeypatch.setattr(gate_chain, "GATES_DIR", tmp_path / ".qor" / "gates")
    result = gate_chain.check_prior_artifact("plan", session_id=sid)
    assert result.found is True
    assert result.valid is True
    # path should point at the ideation artifact since that's what was found
    assert result.path is not None
    assert result.path.name == "ideation.json"


def test_check_prior_artifact_plan_falls_back_when_neither_present(monkeypatch, tmp_path):
    """Backward compat: plan check with no research AND no ideation reports prior missing."""
    monkeypatch.setattr(gate_chain, "GATES_DIR", tmp_path / ".qor" / "gates")
    result = gate_chain.check_prior_artifact("plan", session_id="empty")
    assert result.found is False
