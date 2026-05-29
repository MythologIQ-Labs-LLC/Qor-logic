"""Phase 111 (#138): skill_active env-var management + doctrine note."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from qor.scripts import gate_chain


def test_env_unset_after_call_when_previously_unset(monkeypatch):
    monkeypatch.delenv("QOR_SKILL_ACTIVE", raising=False)
    with gate_chain.skill_active("plan"):
        assert os.environ["QOR_SKILL_ACTIVE"] == "plan"
    assert "QOR_SKILL_ACTIVE" not in os.environ


def test_env_restored_to_prior_value(monkeypatch):
    monkeypatch.setenv("QOR_SKILL_ACTIVE", "outer")
    with gate_chain.skill_active("inner"):
        assert os.environ["QOR_SKILL_ACTIVE"] == "inner"
    assert os.environ["QOR_SKILL_ACTIVE"] == "outer"


def test_skill_param_avoids_shell_prefix_provenance_error(tmp_path, monkeypatch):
    monkeypatch.delenv("QOR_GATE_PROVENANCE_OPTIONAL", raising=False)
    monkeypatch.delenv("QOR_SKILL_ACTIVE", raising=False)
    monkeypatch.setenv("QORLOGIC_PROJECT_DIR", str(tmp_path))
    payload = {"ts": "2026-01-01T00:00:00Z", "target": "x", "verdict": "PASS"}
    sid = "2026-01-01T0000-aaaaaa"
    # No ambient env + no skill= -> provenance gate fires.
    with pytest.raises(gate_chain.ProvenanceError):
        gate_chain.write_gate_artifact("audit", dict(payload), session_id=sid)
    # skill= self-manages the env: no error, artifact written, env restored.
    path = gate_chain.write_gate_artifact("audit", dict(payload), session_id=sid, skill="audit")
    assert path.exists()
    assert "QOR_SKILL_ACTIVE" not in os.environ


def test_doctrine_documents_env_management():
    doctrine = Path(__file__).resolve().parent.parent / "qor" / "references" / "doctrine-prompt-resilience.md"
    text = doctrine.read_text(encoding="utf-8")
    assert "skill_active" in text
    assert "qor.scripts.active_phase" in text
