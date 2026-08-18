"""Phase 233 (GH #352): CI sees the lock.

Before this, intent_lock was the one ladder gate with no CI enforcement --
its ABORT was always resolvable by the person it constrains (#16798). Sealed
sessions commit their lock evidence since Phase 231; this checker makes a
merge that loses or tampers with that evidence fail CI.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from qor.reliability import intent_lock_committed as subject


def _ledger(phase: int, session: str) -> str:
    return (f"# Ledger\n\n"
            f"### Entry #1: SESSION SEAL -- Phase {phase} widget (v9.9.9)\n\n"
            f"**Session**: `{session}`\n")


def _repo(tmp_path: Path, phase: int = 300, session: str = "sess-a") -> Path:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Qor Test"], cwd=tmp_path, check=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text(_ledger(phase, session), encoding="utf-8")
    plan = tmp_path / "docs" / "plan.md"
    plan.write_text("alpha\nbeta\n", encoding="utf-8")
    audit_body = b"# AUDIT\n\nVerdict: PASS\n"
    lock_dir = tmp_path / ".qor" / "intent-lock"
    lock_dir.mkdir(parents=True)
    plan_bytes = plan.read_bytes().replace(b"\r\n", b"\n")
    (lock_dir / f"{session}.plan.snapshot").write_bytes(plan_bytes)
    (lock_dir / f"{session}.audit.snapshot").write_bytes(audit_body)
    record = {
        "session": session,
        "plan_path": "docs/plan.md",
        "plan_hash": hashlib.sha256(plan_bytes).hexdigest(),
        "audit_path": ".agent/staging/AUDIT_REPORT.md",
        "audit_hash": hashlib.sha256(audit_body).hexdigest(),
        "head_commit": "0" * 40,
        "captured_ts": "2026-01-01T00:00:00Z",
    }
    (lock_dir / f"{session}.json").write_text(json.dumps(record), encoding="utf-8")
    subprocess.run(["git", "add", "-A", "-f"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "f"], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


def test_valid_session_verifies_clean(tmp_path):
    repo = _repo(tmp_path)
    assert subject.check(repo, phase_min=231) == []


def test_tampered_snapshot_is_named(tmp_path):
    repo = _repo(tmp_path)
    snap = repo / ".qor" / "intent-lock" / "sess-a.plan.snapshot"
    snap.write_bytes(snap.read_bytes() + b"tampered\n")

    failures = subject.check(repo, phase_min=231)

    assert any("sess-a" in f.detail and f.kind == "snapshot-mismatch" for f in failures)


def test_missing_family_is_named(tmp_path):
    repo = _repo(tmp_path)
    (repo / ".qor" / "intent-lock" / "sess-a.json").unlink()

    failures = subject.check(repo, phase_min=231)

    assert any(f.kind == "missing-evidence" for f in failures)


def test_plan_referent_mismatch_is_named(tmp_path):
    repo = _repo(tmp_path)
    (repo / "docs" / "plan.md").write_text("alpha\nEDITED\n", encoding="utf-8")

    failures = subject.check(repo, phase_min=231)

    kinds = {f.kind for f in failures}
    assert "plan-referent-mismatch" in kinds
    assert "snapshot-mismatch" not in kinds  # distinct failure classes


def test_grandfather_boundary_skips_old_sessions(tmp_path):
    repo = _repo(tmp_path, phase=200)
    for f in (repo / ".qor" / "intent-lock").iterdir():
        f.unlink()

    assert subject.check(repo, phase_min=231) == []


def test_the_real_ledger_verifies_clean_at_the_boundary():
    """The anti-recurrence binding: the repo's own committed evidence must
    verify -- the first check of the lock's guarantee by something other than
    the person it constrains."""
    repo = Path(__file__).resolve().parents[1]
    assert subject.check(repo, phase_min=231) == []
