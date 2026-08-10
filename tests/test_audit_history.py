"""Tests for qor/scripts/audit_history.py (Phase 37 B20 Part 1)."""
from __future__ import annotations

import json
import unittest.mock as mock

import pytest

from qor.scripts import audit_history


def _audit_payload(
    *,
    session_id: str = "s-hist",
    verdict: str = "VETO",
    target: str = "docs/plan.md",
    findings_categories: list[str] | None = None,
    ts: str = "2026-04-20T12:00:00Z",
) -> dict:
    p = {
        "phase": "audit",
        "ts": ts,
        "session_id": session_id,
        "target": target,
        "verdict": verdict,
    }
    if findings_categories is not None:
        p["findings_categories"] = findings_categories
    elif verdict == "VETO":
        # Schema requires findings_categories on VETO (Phase 37 B20b).
        p["findings_categories"] = ["specification-drift"]
    return p


def test_history_path_uses_gate_session_dir(tmp_path):
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        result = audit_history.history_path("s-abc")
    assert result == tmp_path / "s-abc" / "audit_history.jsonl"


def test_append_creates_jsonl_record(tmp_path):
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        path = audit_history.append(_audit_payload(session_id="s1", verdict="PASS"), session_id="s1")
    assert path.exists()
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["phase"] == "audit"
    assert record["verdict"] == "PASS"


def test_append_preserves_multiple_audit_passes(tmp_path):
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        sid = "s-multi"
        audit_history.append(_audit_payload(session_id=sid, verdict="VETO", ts="2026-04-20T12:00:00Z"), session_id=sid)
        audit_history.append(_audit_payload(session_id=sid, verdict="VETO", ts="2026-04-20T12:01:00Z"), session_id=sid)
        audit_history.append(_audit_payload(session_id=sid, verdict="PASS", ts="2026-04-20T12:02:00Z"), session_id=sid)
        records = audit_history.read(sid)
    assert len(records) == 3
    assert [r["verdict"] for r in records] == ["VETO", "VETO", "PASS"]


def test_read_absent_history_returns_empty(tmp_path):
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        records = audit_history.read("does-not-exist")
    assert records == []


def test_read_rejects_malformed_line_with_line_number(tmp_path):
    with mock.patch("qor.scripts.audit_history._workdir.gate_dir", return_value=tmp_path):
        path = audit_history.history_path("s-bad")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"phase":"audit","ts":"2026-04-20T12:00:00Z","session_id":"s-bad","target":"x","verdict":"PASS"}\n{"not-valid"\n', encoding="utf-8")
        with pytest.raises(ValueError, match="line 2"):
            audit_history.read("s-bad")
