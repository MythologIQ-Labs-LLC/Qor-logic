"""Phase 111 (#138 Layer 2): authoritative active-phase reporter."""
from __future__ import annotations

import json
import os

from qor.scripts.active_phase import latest_gate_phase


def _gate(tmp_path, sid, name, phase, mtime):
    d = tmp_path / ".qor" / "gates" / sid
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(json.dumps({"phase": phase, "ts": "2026-01-01T00:00:00Z"}), encoding="utf-8")
    os.utime(p, (mtime, mtime))
    return p


def test_returns_phase_of_newest_gate_artifact(tmp_path):
    sid = "2026-01-01T0000-bbbbbb"
    _gate(tmp_path, sid, "plan.json", "plan", mtime=1_000_000)
    _gate(tmp_path, sid, "audit.json", "audit", mtime=2_000_000)  # newer
    assert latest_gate_phase(sid, tmp_path) == "audit"


def test_returns_none_for_empty_session(tmp_path):
    assert latest_gate_phase("2026-01-01T0000-cccccc", tmp_path) is None
