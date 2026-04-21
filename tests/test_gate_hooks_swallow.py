"""Swallow-log: a hook that raises must not abort write_gate_artifact.

The exception is recorded in .qor/hooks/hooks.log as a structured JSONL
line with status="error", and dispatch returns normally.
"""
from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path

from qor.scripts import gate_hooks


def _make_event(tmp_path: Path) -> gate_hooks.GateWrittenEvent:
    return gate_hooks.GateWrittenEvent(
        phase="plan",
        session_id="s1",
        artifact_path=tmp_path / ".qor" / "gates" / "s1" / "plan.json",
        payload_sha256="deadbeef",
        ts="2026-04-20T00:00:00Z",
    )


class _FakeEntryPoint:
    def __init__(self, name: str, target):
        self.name = name
        self._target = target
        self.group = gate_hooks.ENTRY_POINT_GROUP

    def load(self):
        return self._target


def test_raising_hook_is_swallowed_and_logged(monkeypatch, tmp_path):
    def bad_hook(event):
        raise RuntimeError("boom")

    ep = _FakeEntryPoint("bad-hook", bad_hook)
    monkeypatch.setattr(
        importlib.metadata, "entry_points",
        lambda group=None: [ep] if group == gate_hooks.ENTRY_POINT_GROUP else [],
    )
    gate_hooks.reload_entry_points()
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))

    # Dispatch must not raise.
    gate_hooks.dispatch_gate_written(_make_event(tmp_path))

    log_path = tmp_path / ".qor" / "hooks" / "hooks.log"
    assert log_path.exists()
    lines = [json.loads(line) for line in log_path.read_text().splitlines() if line]
    assert len(lines) == 1
    assert lines[0]["status"] == "error"
    assert lines[0]["hook"] == "bad-hook"
    assert "RuntimeError" in lines[0]["exception"]
    assert "boom" in lines[0]["exception"]
