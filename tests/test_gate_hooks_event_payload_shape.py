"""Phase 57: GateWrittenEvent frozen-dataclass shape lock."""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from qor.scripts import gate_hooks


def test_gate_written_event_is_frozen_dataclass():
    assert dataclasses.is_dataclass(gate_hooks.GateWrittenEvent)
    event = gate_hooks.GateWrittenEvent(
        phase="plan", session_id="sid",
        artifact_path=Path("/tmp/x.json"),
        payload_sha256="0" * 64, ts="2026-05-01T20:00:00Z",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.phase = "audit"  # type: ignore[misc]


def test_gate_written_event_field_set():
    fields = {f.name for f in dataclasses.fields(gate_hooks.GateWrittenEvent)}
    assert fields == {"phase", "session_id", "artifact_path", "payload_sha256", "ts"}


def test_gate_written_event_field_types():
    types = {f.name: f.type for f in dataclasses.fields(gate_hooks.GateWrittenEvent)}
    # Frozen dataclass field types are stored as either the class or the string representation
    # depending on `from __future__ import annotations`. Accept both.
    expected = {
        "phase": (str, "str"),
        "session_id": (str, "str"),
        "artifact_path": (Path, "Path"),
        "payload_sha256": (str, "str"),
        "ts": (str, "str"),
    }
    for name, candidates in expected.items():
        assert types[name] in candidates, f"{name} type was {types[name]!r}, expected one of {candidates}"


def test_constants_present():
    assert gate_hooks.ENTRY_POINT_GROUP == "qor_logic.events.gate_written"
    assert gate_hooks.HOOK_TIMEOUT_SECONDS == 30
