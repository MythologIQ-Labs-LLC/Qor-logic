"""Phase 288 Phase 1: a stale session marker is not the same as an absent one.

GH #483: session.current()/get_or_create() collapsed "stale" (marker exists,
content valid, mtime aged past SESSION_TTL) and "absent" (no marker file) into
one boolean, silently rotating/reporting-missing a session whose gate
directory still held unsealed, in-flight phase artifacts.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import session  # noqa: E402


def _write_marker(marker: Path, sid: str, *, age: timedelta) -> None:
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(sid + "\n", encoding="utf-8")
    stale_time = (datetime.now(timezone.utc) - age).timestamp()
    import os
    os.utime(marker, (stale_time, stale_time))


def test_stale_valid_marker_with_unsealed_gate_dir_is_still_current(tmp_path, monkeypatch):
    sid = "2026-04-17T2335-f284b9"
    marker = tmp_path / ".qor" / "session" / "current"
    _write_marker(marker, sid, age=timedelta(hours=25))
    gate_dir = tmp_path / ".qor" / "gates" / sid
    gate_dir.mkdir(parents=True)
    (gate_dir / "plan.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    assert session.current() == sid


def test_get_or_create_reuses_stale_valid_marker_with_unsealed_gate_dir(tmp_path, monkeypatch):
    sid = "2026-04-17T2335-f284b9"
    marker = tmp_path / ".qor" / "session" / "current"
    _write_marker(marker, sid, age=timedelta(hours=25))
    gate_dir = tmp_path / ".qor" / "gates" / sid
    gate_dir.mkdir(parents=True)
    (gate_dir / "plan.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    assert session.get_or_create() == sid


def test_get_or_create_refreshes_marker_mtime_on_reuse(tmp_path, monkeypatch):
    sid = "2026-04-17T2335-f284b9"
    marker = tmp_path / ".qor" / "session" / "current"
    _write_marker(marker, sid, age=timedelta(hours=25))
    gate_dir = tmp_path / ".qor" / "gates" / sid
    gate_dir.mkdir(parents=True)
    (gate_dir / "plan.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    session.get_or_create()

    mtime = datetime.fromtimestamp(marker.stat().st_mtime, tz=timezone.utc)
    assert (datetime.now(timezone.utc) - mtime) < session.SESSION_TTL


def test_stale_valid_marker_with_sealed_gate_dir_still_rotates(tmp_path, monkeypatch):
    sid = "2026-04-17T2335-f284b9"
    marker = tmp_path / ".qor" / "session" / "current"
    _write_marker(marker, sid, age=timedelta(hours=25))
    gate_dir = tmp_path / ".qor" / "gates" / sid
    gate_dir.mkdir(parents=True)
    (gate_dir / "plan.json").write_text("{}", encoding="utf-8")
    (gate_dir / "substantiate.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    assert session.current() is None
    new_sid = session.get_or_create()
    assert new_sid != sid
    assert marker.read_text(encoding="utf-8").strip() == new_sid


def test_stale_valid_marker_with_no_gate_dir_still_rotates(tmp_path, monkeypatch):
    sid = "2026-04-17T2335-f284b9"
    marker = tmp_path / ".qor" / "session" / "current"
    _write_marker(marker, sid, age=timedelta(hours=25))
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    assert session.current() is None
    new_sid = session.get_or_create()
    assert new_sid != sid


def test_absent_marker_is_unaffected(tmp_path, monkeypatch):
    marker = tmp_path / ".qor" / "session" / "current"
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    assert session.current() is None
    new_sid = session.get_or_create()
    assert marker.read_text(encoding="utf-8").strip() == new_sid


def test_fresh_marker_is_unaffected(tmp_path, monkeypatch):
    sid = "2026-04-17T2335-f284b9"
    marker = tmp_path / ".qor" / "session" / "current"
    _write_marker(marker, sid, age=timedelta(hours=1))
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    assert session.current() == sid
    assert session.get_or_create() == sid
