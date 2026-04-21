"""Entry-point dispatch: registered callables fire once per gate write.

Cache behavior: `reload_entry_points()` is the explicit invalidation knob;
production never calls it. Second dispatch in a process reuses the cached
enumeration.
"""
from __future__ import annotations

import importlib.metadata
from pathlib import Path
from unittest.mock import patch

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


def test_entry_point_hook_invoked_once(monkeypatch, tmp_path):
    calls = []

    def hook(event):
        calls.append(event)

    ep = _FakeEntryPoint("test-hook", hook)
    monkeypatch.setattr(
        importlib.metadata, "entry_points",
        lambda group=None: [ep] if group == gate_hooks.ENTRY_POINT_GROUP else [],
    )
    gate_hooks.reload_entry_points()
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))

    event = _make_event(tmp_path)
    gate_hooks.dispatch_gate_written(event)

    assert len(calls) == 1
    assert calls[0] is event


def test_second_dispatch_uses_cached_entry_points(monkeypatch, tmp_path):
    call_log = []

    def hook(event):
        call_log.append(event.phase)

    ep = _FakeEntryPoint("cache-hook", hook)
    enumerate_calls = {"n": 0}

    def fake_entry_points(group=None):
        enumerate_calls["n"] += 1
        return [ep] if group == gate_hooks.ENTRY_POINT_GROUP else []

    monkeypatch.setattr(importlib.metadata, "entry_points", fake_entry_points)
    gate_hooks.reload_entry_points()
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))

    gate_hooks.dispatch_gate_written(_make_event(tmp_path))
    gate_hooks.dispatch_gate_written(_make_event(tmp_path))

    assert len(call_log) == 2
    # Cache should mean only one real enumeration call after reload.
    assert enumerate_calls["n"] == 1
