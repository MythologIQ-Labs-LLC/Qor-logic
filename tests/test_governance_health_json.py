"""Phase 193 (GH #278): structured governance-health output."""
from __future__ import annotations

import json
from pathlib import Path

from qor.scripts.governance_health import main


def _fixture(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text(
        "# Meta Ledger\n\n### Entry #1: GENESIS\n\ncontent\n", encoding="utf-8")
    return tmp_path


def test_json_findings_shape(tmp_path, capsys):
    repo = _fixture(tmp_path)
    main(["--repo-root", str(repo), "--profile", "skill-entry", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out.strip().splitlines()[-1])
    assert data["profile"] == "skill-entry"
    assert data["overall"] in ("ok", "blocked")
    assert isinstance(data["findings"], list) and data["findings"]
    for f in data["findings"]:
        assert set(f) >= {"path", "status", "reason", "legal_next"}


def test_exit_semantics_unchanged(tmp_path, capsys):
    repo = _fixture(tmp_path)
    rc_prose = main(["--repo-root", str(repo), "--profile", "skill-entry"])
    capsys.readouterr()
    rc_json = main(["--repo-root", str(repo), "--profile", "skill-entry",
                    "--format", "json"])
    capsys.readouterr()
    assert rc_json == rc_prose
