"""Pytest config for qor-logic test suite."""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _qor_gate_provenance_optional(monkeypatch):
    """Phase 52: bypass write_gate_artifact provenance check for the test suite.

    Tests use monkeypatch.setattr(GATES_DIR, tmp_path) and direct helper calls
    that don't have QOR_SKILL_ACTIVE set. The provenance binding is for
    production skill invocations; tests opt out via this autouse fixture.

    Tests that EXERCISE the provenance check (test_gate_chain_provenance.py)
    explicitly delenv this var via monkeypatch.delenv(..., raising=False)
    inside the test body.
    """
    monkeypatch.setenv("QOR_GATE_PROVENANCE_OPTIONAL", "1")
    yield
