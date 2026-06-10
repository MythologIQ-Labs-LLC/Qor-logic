"""Phase 150 (GAP-GOV-04): the QOR_GATE_PROVENANCE_OPTIONAL bypass is honored
only under pytest. In any non-pytest process the provenance binding is enforced
regardless of the env var, so it cannot be used to forge gate artifacts.
"""
from __future__ import annotations

import pytest

from qor.scripts import gate_chain


def test_bypass_ignored_outside_pytest(monkeypatch):
    # Simulate a non-pytest process: _pytest_active() -> False. With the bypass
    # env set but no skill provenance, the write must still be refused.
    monkeypatch.setattr(gate_chain, "_pytest_active", lambda: False)
    monkeypatch.setenv("QOR_GATE_PROVENANCE_OPTIONAL", "1")
    monkeypatch.delenv("QOR_SKILL_ACTIVE", raising=False)
    with pytest.raises(gate_chain.ProvenanceError):
        gate_chain.write_gate_artifact(
            "plan", {"phase": "plan"}, session_id="2026-01-01T0000-aaaaaa"
        )


def test_bypass_honored_under_pytest(monkeypatch):
    # Under pytest the bypass is honored: no ProvenanceError (a later schema
    # error is acceptable -- we assert only that provenance did not block it).
    monkeypatch.setattr(gate_chain, "_pytest_active", lambda: True)
    monkeypatch.setenv("QOR_GATE_PROVENANCE_OPTIONAL", "1")
    monkeypatch.delenv("QOR_SKILL_ACTIVE", raising=False)
    try:
        gate_chain.write_gate_artifact(
            "plan", {"phase": "plan"}, session_id="2026-01-01T0000-aaaaaa"
        )
    except gate_chain.ProvenanceError:
        pytest.fail("provenance bypass must be honored under pytest")
    except Exception:
        pass  # schema/other errors are fine; only ProvenanceError is under test


def test_pytest_active_true_in_this_process():
    # Sanity: PYTEST_CURRENT_TEST is set while a test runs.
    assert gate_chain._pytest_active() is True
