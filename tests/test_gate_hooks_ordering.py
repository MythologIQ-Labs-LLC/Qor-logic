"""Ordering: entry-points run first (registration order), then config-file
entries (file order). Captured in a shared list.
"""
from __future__ import annotations

import importlib.metadata
from pathlib import Path

from qor.scripts import gate_hooks


_order: list[str] = []


def _ep1(event): _order.append("ep1")
def _ep2(event): _order.append("ep2")
def _cfg1(event): _order.append("cfg1")
def _cfg2(event): _order.append("cfg2")


class _FakeEntryPoint:
    def __init__(self, name, target):
        self.name = name
        self._target = target
        self.group = gate_hooks.ENTRY_POINT_GROUP

    def load(self):
        return self._target


def _make_event(tmp_path: Path) -> gate_hooks.GateWrittenEvent:
    return gate_hooks.GateWrittenEvent(
        phase="plan",
        session_id="s1",
        artifact_path=tmp_path / ".qor" / "gates" / "s1" / "plan.json",
        payload_sha256="beef",
        ts="2026-04-20T00:00:00Z",
    )


def test_entry_points_before_config_file(monkeypatch, tmp_path):
    _order.clear()
    eps = [_FakeEntryPoint("ep1", _ep1), _FakeEntryPoint("ep2", _ep2)]
    monkeypatch.setattr(
        importlib.metadata, "entry_points",
        lambda group=None: eps if group == gate_hooks.ENTRY_POINT_GROUP else [],
    )
    gate_hooks.reload_entry_points()
    monkeypatch.setenv("QOR_ROOT", str(tmp_path))

    hooks_yaml = tmp_path / ".qor" / "hooks.yaml"
    hooks_yaml.parent.mkdir(parents=True, exist_ok=True)
    hooks_yaml.write_text(
        f"gate_written:\n"
        f"  - module: {__name__}:_cfg1\n"
        f"  - module: {__name__}:_cfg2\n",
        encoding="utf-8",
    )

    gate_hooks.dispatch_gate_written(_make_event(tmp_path))

    assert _order == ["ep1", "ep2", "cfg1", "cfg2"]
