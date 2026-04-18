"""Phase 30 Phase 1: session.rotate() writes a new session_id to the marker.

Closes the session-carry-over gap that let Phase 28/29 seals share a single
session directory, overwriting each phase's gate artifacts in turn.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import session  # noqa: E402


_SID_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}\d{2}-[0-9a-f]{6}$")


def test_rotate_returns_new_session_id(tmp_path, monkeypatch):
    marker = tmp_path / ".qor" / "session" / "current"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("2026-04-17T2335-f284b9", encoding="utf-8")
    monkeypatch.setattr(session, "MARKER_PATH", marker)

    new_sid = session.rotate()
    assert _SID_PATTERN.match(new_sid), f"Bad session_id format: {new_sid}"
    assert new_sid != "2026-04-17T2335-f284b9"


def test_rotate_changes_marker_file(tmp_path, monkeypatch):
    marker = tmp_path / ".qor" / "session" / "current"
    marker.parent.mkdir(parents=True, exist_ok=True)
    old = "2026-04-17T2335-f284b9"
    marker.write_text(old, encoding="utf-8")
    monkeypatch.setattr(session, "MARKER_PATH", marker)

    new_sid = session.rotate()
    assert marker.read_text(encoding="utf-8").strip() == new_sid
    assert marker.read_text(encoding="utf-8").strip() != old


def test_rotate_preserves_prior_session_dir(tmp_path, monkeypatch):
    """Prior .qor/gates/<old_sid>/ must NOT be deleted by rotation.
    Archaeology is preserved; operators can prune manually."""
    marker = tmp_path / ".qor" / "session" / "current"
    marker.parent.mkdir(parents=True, exist_ok=True)
    old = "2026-04-17T2335-f284b9"
    marker.write_text(old, encoding="utf-8")
    gates_old = tmp_path / ".qor" / "gates" / old
    gates_old.mkdir(parents=True, exist_ok=True)
    (gates_old / "substantiate.json").write_text('{"phase":"substantiate"}')
    monkeypatch.setattr(session, "MARKER_PATH", marker)

    session.rotate()
    assert (gates_old / "substantiate.json").exists(), (
        "Prior session's gate artifacts must be preserved"
    )
