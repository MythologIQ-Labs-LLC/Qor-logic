"""Phase 57: Phase 52 provenance binding still fires before hook chain."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from qor.scripts import gate_chain, gate_hooks


@pytest.fixture(autouse=True)
def _reset(monkeypatch, tmp_path):
    gate_hooks.reload_entry_points()
    monkeypatch.setattr(gate_hooks._workdir, "root", lambda: tmp_path)
    # Explicitly clear bypass + skill-active env so Phase 52 check is enforced
    monkeypatch.delenv("QOR_GATE_PROVENANCE_OPTIONAL", raising=False)
    monkeypatch.delenv("QOR_SKILL_ACTIVE", raising=False)
    monkeypatch.chdir(tmp_path)
    yield
    gate_hooks.reload_entry_points()


def test_provenance_error_blocks_write_and_blocks_hook(monkeypatch):
    captured: list = []

    monkeypatch.setattr(gate_hooks, "dispatch_gate_written",
                        lambda e: captured.append(e))

    payload = {"phase": "plan", "session_id": "x", "ts": "2026-05-01T20:00:00Z"}

    with pytest.raises(gate_chain.ProvenanceError):
        gate_chain.write_gate_artifact("plan", payload, session_id="x")

    # Hook never fires; no artifact on disk
    assert captured == []
    artifact = Path(".qor") / "gates" / "x" / "plan.json"
    assert not artifact.exists()
