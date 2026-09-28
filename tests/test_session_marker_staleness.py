"""Phase 299 Phase 1: a stale session marker is not the same as an absent one.

GH #483: session.current()/get_or_create() collapsed "stale" (marker exists,
content valid, mtime aged past SESSION_TTL) and "absent" (no marker file) into
one boolean, silently rotating/reporting-missing a session whose gate
directory still held unsealed, in-flight phase artifacts.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qor.scripts import gate_chain

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


def test_stale_valid_marker_with_empty_gate_dir_still_rotates(tmp_path, monkeypatch):
    sid = "2026-04-17T2335-f284b9"
    marker = tmp_path / ".qor" / "session" / "current"
    _write_marker(marker, sid, age=timedelta(hours=25))
    (tmp_path / ".qor" / "gates" / sid).mkdir(parents=True)
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    assert session.current() is None
    new_sid = session.get_or_create()
    assert new_sid != sid
    assert marker.read_text(encoding="utf-8").strip() == new_sid


@pytest.mark.parametrize("age_h", [25, 1], ids=["stale", "fresh"])
@pytest.mark.parametrize("kind", ["traversal", "absolute", "empty", "wrong-format"])
def test_marker_with_malformed_content_rotates_to_fresh_id(tmp_path, monkeypatch, kind, age_h):
    content = {"traversal": "../../evil", "absolute": str(tmp_path / "abs"), "empty": "",
               "wrong-format": "2026-04-17T2335-F284B9"}[kind]
    marker = tmp_path / ".qor" / "session" / "current"
    _write_marker(marker, content, age=timedelta(hours=age_h))
    gates = tmp_path / ".qor" / "gates"
    gates.mkdir(parents=True)
    (gates / content).mkdir(parents=True, exist_ok=True)
    (gates / content / "plan.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    assert session.current() is None
    new_sid = session.get_or_create()
    assert new_sid != content and session.SESSION_ID_PATTERN.match(new_sid)
    assert marker.read_text(encoding="utf-8").strip() == new_sid


def test_stale_valid_marker_with_ideation_only_gate_dir_is_still_current(tmp_path, monkeypatch):
    sid = "2026-04-17T2335-f284b9"
    marker = tmp_path / ".qor" / "session" / "current"
    _write_marker(marker, sid, age=timedelta(hours=25))
    gate_dir = tmp_path / ".qor" / "gates" / sid
    gate_dir.mkdir(parents=True)
    (gate_dir / "ideation.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    assert session.current() == sid
    assert session.get_or_create() == sid
    assert marker.read_text(encoding="utf-8").strip() == sid


def _live(root: Path, name: str, monkeypatch) -> bool:
    """True if a 25 h marker whose gate dir holds only ``name`` stays current."""
    sid = "2026-04-17T2335-f284b9"
    marker = root / ".qor" / "session" / "current"
    _write_marker(marker, sid, age=timedelta(hours=25))
    gate_dir = root / ".qor" / "gates" / sid
    gate_dir.mkdir(parents=True)
    (gate_dir / name).write_text("{}", encoding="utf-8")
    monkeypatch.setattr(session._workdir, "root", lambda: root)
    return session.current(marker=marker) == sid


@pytest.mark.parametrize(
    "phase",
    [gate_chain.IDEATION_PHASE, *gate_chain.CHAIN[: gate_chain.CHAIN.index("substantiate")]],
)
def test_stale_marker_liveness_covers_every_pre_seal_chain_phase(tmp_path, monkeypatch, phase):
    assert _live(tmp_path, f"{phase}.json", monkeypatch)


def test_stale_marker_liveness_set_equals_pre_seal_chain_phases(tmp_path, monkeypatch):
    phases = [gate_chain.IDEATION_PHASE, *gate_chain.CHAIN[: gate_chain.CHAIN.index("substantiate")]]
    expected = {f"{p}.json" for p in phases}
    assert sorted(session._GATE_PHASE_ARTIFACTS) == sorted(expected)
    names = sorted(expected | set(session._GATE_PHASE_ARTIFACTS))
    live = {name for name in names if _live(tmp_path / name, name, monkeypatch)}
    assert live == expected


@pytest.mark.parametrize("name", ["remediate.json", "validate.json", "audit_history.jsonl", "notes.json"])
def test_stale_marker_with_only_non_pre_seal_artifacts_rotates(tmp_path, monkeypatch, name):
    sid = "2026-04-17T2335-f284b9"
    marker = tmp_path / ".qor" / "session" / "current"
    _write_marker(marker, sid, age=timedelta(hours=25))
    gate_dir = tmp_path / ".qor" / "gates" / sid
    gate_dir.mkdir(parents=True)
    (gate_dir / name).write_text("{}", encoding="utf-8")
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    assert session.current() is None
    new_sid = session.get_or_create()
    assert new_sid != sid
    assert marker.read_text(encoding="utf-8").strip() == new_sid


def test_reads_of_a_fresh_marker_do_not_refresh_it(tmp_path, monkeypatch):
    sid = "2026-04-17T2335-f284b9"
    marker = tmp_path / ".qor" / "session" / "current"
    _write_marker(marker, sid, age=timedelta(hours=1))
    before = marker.stat().st_mtime
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    assert session.current() == sid
    assert session.get_or_create() == sid
    assert marker.stat().st_mtime == before


def test_current_on_a_stale_live_marker_does_not_refresh_it(tmp_path, monkeypatch):
    sid = "2026-04-17T2335-f284b9"
    marker = tmp_path / ".qor" / "session" / "current"
    _write_marker(marker, sid, age=timedelta(hours=25))
    gate_dir = tmp_path / ".qor" / "gates" / sid
    gate_dir.mkdir(parents=True)
    (gate_dir / "plan.json").write_text("{}", encoding="utf-8")
    before = marker.stat().st_mtime
    monkeypatch.setattr(session, "MARKER_PATH", marker)
    monkeypatch.setattr(session._workdir, "root", lambda: tmp_path)

    assert session.current() == sid
    assert marker.stat().st_mtime == before
