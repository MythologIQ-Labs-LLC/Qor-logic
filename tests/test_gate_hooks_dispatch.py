"""Phase 57: gate_hooks.dispatch_gate_written behavior tests."""
from __future__ import annotations

import json
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
    # Pin workdir to tmp_path so log file goes there
    monkeypatch.setattr(gate_hooks._workdir, "root", lambda: tmp_path)
    yield
    gate_hooks.reload_entry_points()


def test_dispatch_with_no_hooks_is_noop(tmp_path, monkeypatch):
    monkeypatch.setattr(gate_hooks.importlib.metadata, "entry_points", lambda group=None: [])
    event = _event(tmp_path)
    gate_hooks.dispatch_gate_written(event)
    log = tmp_path / ".qor" / "hooks" / "hooks.log"
    assert not log.exists()


def test_dispatch_invokes_entry_point_callable_once(tmp_path, monkeypatch):
    invocations: list = []

    def hook(event):
        invocations.append(event)

    fake_ep = SimpleNamespace(name="test-hook", load=lambda: hook)
    monkeypatch.setattr(gate_hooks.importlib.metadata, "entry_points",
                        lambda group=None: [fake_ep])
    event = _event(tmp_path)
    gate_hooks.dispatch_gate_written(event)
    assert len(invocations) == 1
    assert invocations[0] is event


def test_dispatch_caches_entry_points(tmp_path, monkeypatch):
    call_count = {"n": 0}

    def fake_entry_points(group=None):
        call_count["n"] += 1
        return []

    monkeypatch.setattr(gate_hooks.importlib.metadata, "entry_points", fake_entry_points)
    gate_hooks.dispatch_gate_written(_event(tmp_path))
    gate_hooks.dispatch_gate_written(_event(tmp_path))
    assert call_count["n"] == 1


def test_reload_entry_points_invalidates_cache(tmp_path, monkeypatch):
    call_count = {"n": 0}

    def fake_entry_points(group=None):
        call_count["n"] += 1
        return []

    monkeypatch.setattr(gate_hooks.importlib.metadata, "entry_points", fake_entry_points)
    gate_hooks.dispatch_gate_written(_event(tmp_path))
    gate_hooks.reload_entry_points()
    gate_hooks.dispatch_gate_written(_event(tmp_path))
    assert call_count["n"] == 2


def test_dispatch_runs_entry_points_before_config_hooks(tmp_path, monkeypatch):
    order: list[str] = []

    def ep_hook(event):
        order.append("entry-point")

    def config_hook(event):
        order.append("config-file")

    fake_ep = SimpleNamespace(name="ep", load=lambda: ep_hook)
    monkeypatch.setattr(gate_hooks.importlib.metadata, "entry_points",
                        lambda group=None: [fake_ep])

    # Stub _import_dotted to return our config_hook
    monkeypatch.setattr(gate_hooks, "_import_dotted", lambda d: config_hook)

    yaml_text = "gate_written:\n  - module: fake_pkg:hook\n"
    (tmp_path / ".qor").mkdir()
    (tmp_path / ".qor" / "hooks.yaml").write_text(yaml_text, encoding="utf-8")

    gate_hooks.dispatch_gate_written(_event(tmp_path))
    assert order == ["entry-point", "config-file"]
