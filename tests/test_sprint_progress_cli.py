"""Phase 54: sprint-progress CLI tests."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from qor.scripts import sprint_progress

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write_brief(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _write_ledger(path: Path, sealed_phases: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for n, phase in enumerate(sealed_phases, start=1):
        lines.append(f"### Entry #{100 + n}: SESSION SEAL -- Phase {phase} feature substantiated\n")
        lines.append("body...\n\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def test_compute_progress_reads_priorities_and_sealed_phases(tmp_path):
    repo = tmp_path / "repo"
    docs = repo / "docs"
    _write_brief(docs / "research-brief-test-2026-05-01.md", """
### Priority 1 — Phase 60 candidate: Foo
### Priority 2 — Phase 61 candidate: Bar
### Priority 3 — Phase 62 candidate (optional): Baz
""")
    _write_ledger(docs / "META_LEDGER.md", sealed_phases=[60, 61])
    brief, entries = sprint_progress.compute_progress(repo)
    assert brief is not None
    assert brief.name.endswith("2026-05-01.md")
    assert len(entries) == 3
    statuses = {(e.priority.number, e.sealed) for e in entries}
    assert statuses == {(1, True), (2, True), (3, False)}


def test_compute_progress_handles_no_brief(tmp_path):
    brief, entries = sprint_progress.compute_progress(tmp_path)
    assert brief is None
    assert entries == []


def test_render_progress_emits_priority_status_table(tmp_path):
    repo = tmp_path / "repo"
    docs = repo / "docs"
    _write_brief(docs / "research-brief-x-2026-05-02.md", """
### Priority 1 — Phase 70 candidate: Alpha
### Priority 2 — Phase 71 candidate: Beta
""")
    _write_ledger(docs / "META_LEDGER.md", sealed_phases=[70])
    output = sprint_progress.render_progress(repo)
    assert "Priority 1 (Phase 70): SEALED" in output
    assert "Priority 2 (Phase 71): PENDING" in output
    assert "1/2 priorities sealed" in output


def test_render_progress_handles_missing_brief(tmp_path):
    output = sprint_progress.render_progress(tmp_path)
    assert "no sprint in progress" in output.lower()


def test_cli_emits_priority_status_table(tmp_path):
    repo = tmp_path / "repo"
    docs = repo / "docs"
    _write_brief(docs / "research-brief-cli-2026-05-03.md",
                 "### Priority 1 — Phase 80 candidate: Gamma\n")
    _write_ledger(docs / "META_LEDGER.md", sealed_phases=[80])
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.sprint_progress", "--repo-root", str(repo)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0
    assert "Priority 1 (Phase 80): SEALED" in proc.stdout


def test_cli_handles_missing_brief(tmp_path):
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.sprint_progress", "--repo-root", str(tmp_path)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0
    assert "no sprint in progress" in proc.stdout.lower()


def test_compliance_subcommand_invokes_sprint_progress(tmp_path):
    repo = tmp_path / "repo"
    docs = repo / "docs"
    _write_brief(docs / "research-brief-c-2026-05-04.md",
                 "### Priority 1 — Phase 90 candidate: Delta\n")
    _write_ledger(docs / "META_LEDGER.md", sealed_phases=[])
    proc = subprocess.run(
        [sys.executable, "-m", "qor.cli", "compliance", "sprint-progress",
         "--repo-root", str(repo)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0
    assert "Priority 1 (Phase 90): PENDING" in proc.stdout
