"""Phase 54: tests for `qor-logic compliance ai-provenance` subcommand."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write_gate(session_dir: Path, phase: str, payload: dict) -> None:
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / f"{phase}.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


@pytest.fixture
def fixture_session(tmp_path):
    """Create an isolated workdir with synthetic session gates.

    Uses ``QOR_ROOT`` to redirect the workdir resolver at the subprocess
    boundary; gate dir then derives as ``<QOR_ROOT>/.qor/gates``.
    """
    session_id = "2026-04-30T0000-fixture"
    qor_root = tmp_path / "fakeroot"
    gates_dir = qor_root / ".qor" / "gates" / session_id

    provenance = {
        "system": "Qor-logic", "version": "0.39.0",
        "host": "claude-code", "model_family": "claude-opus-4-7",
        "ts": "2026-04-30T18:00:00Z",
    }

    _write_gate(gates_dir, "research", {
        "phase": "research", "ts": "2026-04-30T18:00:00Z",
        "session_id": session_id, "questions": [], "findings": [],
        "ai_provenance": {**provenance, "human_oversight": "absent"},
    })
    _write_gate(gates_dir, "audit", {
        "phase": "audit", "ts": "2026-04-30T18:01:00Z",
        "session_id": session_id, "target": "p.md", "verdict": "PASS",
        "ai_provenance": {**provenance, "human_oversight": "pass"},
    })
    _write_gate(gates_dir, "implement", {
        "phase": "implement", "ts": "2026-04-30T18:02:00Z",
        "session_id": session_id, "files_touched": ["a.py"],
    })
    return session_id, qor_root


def test_cli_aggregates_session_provenance(fixture_session):
    session_id, qor_root = fixture_session
    env = {**os.environ, "QOR_ROOT": str(qor_root)}
    proc = subprocess.run(
        [sys.executable, "-m", "qor.cli", "compliance", "ai-provenance",
         "--session", session_id],
        cwd=str(REPO_ROOT), capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads(proc.stdout)
    assert manifest["session_id"] == session_id
    assert "research" in manifest["phases"]
    assert manifest["phases"]["research"]["human_oversight"] == "absent"
    assert manifest["phases"]["audit"]["human_oversight"] == "pass"
    assert manifest["phases"]["implement"] is None  # missing provenance -> null


def test_cli_handles_missing_session(tmp_path):
    env = {**os.environ, "QOR_ROOT": str(tmp_path / "empty")}
    (tmp_path / "empty").mkdir()
    proc = subprocess.run(
        [sys.executable, "-m", "qor.cli", "compliance", "ai-provenance",
         "--session", "nonexistent-sid"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 1
    assert "no gate artifacts" in proc.stderr.lower()
