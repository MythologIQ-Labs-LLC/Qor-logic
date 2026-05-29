"""Behavioral tests for the FEATURE_INDEX regression ABORT CLI (Phase 114, #155/#40).

Verifies exit codes, not prose: the deferred PASS-blocking ABORT now exits
non-zero on an outside-scope verified->unverified regression.
"""
from __future__ import annotations

import json
from pathlib import Path

from qor.scripts import feature_index_verify as fiv

_INDEX_HEADER = (
    "| ID | Name | Source | Doc | Test | Verification status |\n"
    "|----|------|--------|-----|------|---------------------|\n"
)


def _write_index(root: Path, rows: list[tuple[str, str]]) -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    body = _INDEX_HEADER + "".join(
        f"| {fid} | {fid} | s | d | t | {status} |\n" for fid, status in rows
    )
    (root / "docs" / "FEATURE_INDEX.md").write_text(body, encoding="utf-8")


def _write_snapshot(root: Path, sid: str, snap: dict[str, str]) -> None:
    d = root / ".qor" / "feature_index_snapshots"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{sid}.json").write_text(json.dumps(snap), encoding="utf-8")


def test_exit_zero_no_regression(tmp_path):
    _write_index(tmp_path, [("feat-x", "verified")])
    rc = fiv.main(["--repo-root", str(tmp_path)])
    assert rc == 0


def test_exit_nonzero_on_newly_unverified(tmp_path):
    sid = "sess-1"
    _write_snapshot(tmp_path, sid, {"feat-x": "verified"})
    _write_index(tmp_path, [("feat-x", "unverified")])
    rc = fiv.main(["--repo-root", str(tmp_path), "--snapshot", sid])
    assert rc == 1


def test_warn_only_suppresses_exit(tmp_path):
    sid = "sess-1"
    _write_snapshot(tmp_path, sid, {"feat-x": "verified"})
    _write_index(tmp_path, [("feat-x", "unverified")])
    rc = fiv.main(["--repo-root", str(tmp_path), "--snapshot", sid, "--warn-only"])
    assert rc == 0


def test_missing_index_skips(tmp_path):
    rc = fiv.main(["--repo-root", str(tmp_path)])
    assert rc == 0
