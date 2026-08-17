"""Phase 231 (GH #332 Direction 3): the lock keeps the evidence it will be
asked about.

The lock stored hashes only, so a carry-forward drift's referent was
unrecoverable and every override rested on testimony. Capture now snapshots
the LF-normalized audited bytes; verify shows the bounded delta on DRIFT;
legacy records without snapshots behave exactly as before.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from qor.reliability import intent_lock


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Qor Test"], cwd=tmp_path, check=True)
    (tmp_path / "plan.md").write_text("alpha\nbeta\n", encoding="utf-8")
    (tmp_path / "audit.md").write_text("# AUDIT\n\nVerdict: PASS\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-m", "f"], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


def _capture(repo: Path, session: str = "sess-a") -> int:
    args = argparse.Namespace(
        repo=str(repo), plan=str(repo / "plan.md"), audit=str(repo / "audit.md"),
        session=session,
    )
    return intent_lock.capture(args)


def _verify(repo: Path, session: str = "sess-a", capsys=None) -> int:
    args = argparse.Namespace(repo=str(repo), session=session)
    return intent_lock.verify(args)


def test_capture_writes_selfconsistent_snapshots(tmp_path):
    repo = _repo(tmp_path)
    assert _capture(repo) == 0

    record = json.loads((repo / ".qor" / "intent-lock" / "sess-a.json").read_text())
    for kind, snap_name in (("plan", "sess-a.plan.snapshot"), ("audit", "sess-a.audit.snapshot")):
        snap = repo / ".qor" / "intent-lock" / snap_name
        assert snap.is_file(), snap_name
        digest = hashlib.sha256(snap.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        assert digest == record[f"{kind}_hash"], kind


def test_drift_prints_the_delta(tmp_path, capsys):
    repo = _repo(tmp_path)
    _capture(repo)
    (repo / "plan.md").write_text("alpha\nGAMMA\n", encoding="utf-8")

    rc = _verify(repo)

    err = capsys.readouterr().err
    assert rc == 1
    assert "DRIFT: plan" in err
    assert "+GAMMA" in err and "-beta" in err


def test_diff_is_bounded(tmp_path, capsys):
    repo = _repo(tmp_path)
    _capture(repo)
    (repo / "plan.md").write_text("\n".join(f"line-{i}" for i in range(200)), encoding="utf-8")

    rc = _verify(repo)

    err = capsys.readouterr().err
    assert rc == 1
    diff_lines = [ln for ln in err.splitlines() if ln.startswith(("+", "-", "@@"))]
    assert len(diff_lines) <= 40
    assert "truncated" in err


def test_legacy_record_without_snapshot_verifies_as_today(tmp_path, capsys):
    repo = _repo(tmp_path)
    _capture(repo)
    for snap in ("sess-a.plan.snapshot", "sess-a.audit.snapshot"):
        (repo / ".qor" / "intent-lock" / snap).unlink()

    assert _verify(repo) == 0

    (repo / "plan.md").write_text("alpha\nGAMMA\n", encoding="utf-8")
    rc = _verify(repo)
    err = capsys.readouterr().err
    assert rc == 1
    assert "DRIFT: plan" in err
    assert "+GAMMA" not in err  # the bare two-word report, exactly as before


def test_clean_verify_is_silent_about_snapshots(tmp_path, capsys):
    repo = _repo(tmp_path)
    _capture(repo)

    rc = _verify(repo)

    out = capsys.readouterr()
    assert rc == 0
    assert "@@" not in out.err and "@@" not in out.out
