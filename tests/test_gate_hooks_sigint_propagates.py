"""Phase 57: SIGINT/SystemExit must propagate through dispatch (VETO-remediation regression)."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from qor.scripts import gate_hooks


def _event(tmp_path: Path) -> gate_hooks.GateWrittenEvent:
    artifact = tmp_path / "art.json"
    artifact.write_text("{}", encoding="utf-8")
    return gate_hooks.GateWrittenEvent(
        phase="plan", session_id="test-sid",
        artifact_path=artifact, payload_sha256="a" * 64,
        ts="2026-05-01T20:00:00Z",
    )


@pytest.fixture(autouse=True)
def _reset_cache(monkeypatch, tmp_path):
    gate_hooks.reload_entry_points()
    monkeypatch.setattr(gate_hooks._workdir, "root", lambda: tmp_path)
    yield
    gate_hooks.reload_entry_points()


def test_keyboard_interrupt_in_callable_hook_propagates(tmp_path, monkeypatch):
    def interruptible_hook(event):
        raise KeyboardInterrupt("operator pressed Ctrl-C")

    fake_ep = SimpleNamespace(name="kb-hook", load=lambda: interruptible_hook)
    monkeypatch.setattr(gate_hooks.importlib.metadata, "entry_points",
                        lambda group=None: [fake_ep])

    with pytest.raises(KeyboardInterrupt):
        gate_hooks.dispatch_gate_written(_event(tmp_path))


def test_system_exit_in_callable_hook_propagates(tmp_path, monkeypatch):
    def exiting_hook(event):
        raise SystemExit(42)

    fake_ep = SimpleNamespace(name="exit-hook", load=lambda: exiting_hook)
    monkeypatch.setattr(gate_hooks.importlib.metadata, "entry_points",
                        lambda group=None: [fake_ep])

    with pytest.raises(SystemExit):
        gate_hooks.dispatch_gate_written(_event(tmp_path))
