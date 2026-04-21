"""No hooks registered or configured: dispatch is a no-op.

No .qor/hooks/ directory is created when nothing fires.
"""
from __future__ import annotations

import importlib.metadata
from pathlib import Path

from qor.scripts import gate_hooks


def test_no_hooks_is_noop(monkeypatch, tmp_path):
    monkeypatch.setattr(
        importlib.metadata, "entry_points", lambda group=None: [],
    )
    gate_hooks.reload_entry_points()
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))

    event = gate_hooks.GateWrittenEvent(
        phase="plan",
        session_id="s1",
        artifact_path=tmp_path / ".qor" / "gates" / "s1" / "plan.json",
        payload_sha256="x",
        ts="2026-04-20T00:00:00Z",
    )

    gate_hooks.dispatch_gate_written(event)

    assert not (tmp_path / ".qor" / "hooks").exists()
