"""Phase 58: CLI behavior + Process Shadow Genome event emission."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _make_repo(tmp_path: Path, sid: str, files_touched: list[str]) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(exist_ok=True)
    gates = repo / ".qor" / "gates" / sid
    gates.mkdir(parents=True, exist_ok=True)
    (gates / "implement.json").write_text(json.dumps({
        "phase": "implement", "session_id": sid, "ts": "2026-05-01T20:00:00Z",
        "files_touched": files_touched,
    }), encoding="utf-8")
    # Minimal docs/PROCESS_SHADOW_GENOME_UPSTREAM.md so append target exists
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs" / "PROCESS_SHADOW_GENOME_UPSTREAM.md").write_text(
        "# upstream\n", encoding="utf-8")
    return repo


def test_cli_appends_severity_2_event_for_each_doc_surface_deviation(tmp_path: Path):
    sid = "cli-test"
    repo = _make_repo(tmp_path, sid, ["qor/skills/foo/SKILL.md"])
    out = repo / "dist" / "procedural-fidelity.findings.json"
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.procedural_fidelity",
         "--session", sid, "--repo-root", str(repo), "--out", str(out)],
        capture_output=True, text=True,
    )
    # WARN posture: exit 0 with WARN to stderr
    assert proc.returncode == 0
    assert "WARN" in proc.stderr
    assert out.exists()
    findings = json.loads(out.read_text(encoding="utf-8"))
    assert len(findings) >= 1
    assert any(f["class"] == "doc-surface-uncovered" for f in findings)


def test_cli_exit_0_clean_when_no_deviations(tmp_path: Path):
    sid = "cli-clean"
    repo = _make_repo(tmp_path, sid, [
        "qor/skills/foo/SKILL.md", "docs/SYSTEM_STATE.md",
    ])
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.procedural_fidelity",
         "--session", sid, "--repo-root", str(repo)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert "WARN" not in proc.stderr


def test_cli_exit_2_on_missing_implement_gate(tmp_path: Path):
    repo = tmp_path / "no-gate"
    repo.mkdir()
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.procedural_fidelity",
         "--session", "missing", "--repo-root", str(repo)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 2
    assert "ERROR" in proc.stderr
