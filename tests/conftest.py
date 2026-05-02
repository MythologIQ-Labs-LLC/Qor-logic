"""Pytest config for qor-logic test suite."""
from __future__ import annotations

import shutil
from pathlib import Path

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


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_session_pollution():
    """Phase 58: sweep `.qor/gates/test*` directories at session-end.

    Some tests construct synthetic session IDs (e.g. ``test-session``,
    ``test-session-kb``, ``cli-test``) and call gate_chain.write_gate_artifact
    against them, which writes to the live `.qor/gates/<sid>/` tree rather
    than to a tmp_path. This fixture removes pollution at session-end so the
    repo stays clean.

    Pattern is conservative: matches `test*` and `cli-*` and `t1`-`t5`
    (Phase 58 fixture aliases); skips real session IDs (timestamp-prefixed
    `2026-...`) by name pattern. Idempotent; safe to re-run.
    """
    yield
    gates = Path(".qor") / "gates"
    if not gates.exists():
        return
    for entry in gates.iterdir():
        if not entry.is_dir():
            continue
        name = entry.name
        # Pollution patterns: test*, cli-*, t1-t9 single-letter-digit aliases
        is_pollution = (
            name.startswith("test")
            or name.startswith("cli-")
            or (len(name) <= 3 and name[0] == "t" and name[1:].isdigit())
        )
        if is_pollution:
            shutil.rmtree(entry, ignore_errors=True)
