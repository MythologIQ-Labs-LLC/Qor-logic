"""Phase 167 (GH #250 part b): dry-run modes for the mutating CLI surfaces.

Contract under test, per surface: reads/rendering/validation execute exactly
as in wet mode; every write/unlink is suppressed; one '[dry] would <action>'
line per suppressed mutation; validation failures surface identically.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

_PREV = "a" * 64
_CHAIN = "b" * 64

_LEDGER = f"""# META LEDGER

### Entry #1: GENESIS

**Previous Hash**: `{_PREV}`
**Chain Hash (Merkle seal)**: `{_CHAIN}`

### Entry #2: SOMETHING

**Previous Hash**: `{_PREV}`
**Chain Hash (Merkle seal)**: `{_CHAIN}`
"""

_README = (
    '<img src="https://img.shields.io/badge/Tests-10%20passing-brightgreen" alt="Tests: 10 passing">\n'
    '<img src="https://img.shields.io/badge/Skills-3-blue" alt="Skills: 3">\n'
    '<img src="https://img.shields.io/badge/Agents-1-blue" alt="Agents: 1">\n'
    '<img src="https://img.shields.io/badge/Doctrines-2-blue" alt="Doctrines: 2">\n'
    '<img src="https://img.shields.io/badge/Ledger-1%20entries%20sealed-green" alt="Ledger: 1 entries sealed">\n'
)

_SYSTEM_STATE = "# State\n\n**Snapshot**: 2026-01-01\n**Phase**: Phase 1 (x).\n"


def test_seal_artifacts_dry_run_previews_without_writing(tmp_path, capsys):
    from qor.scripts import seal_artifacts

    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text(_README, encoding="utf-8")
    (tmp_path / "docs" / "SYSTEM_STATE.md").write_text(_SYSTEM_STATE, encoding="utf-8")
    (tmp_path / "docs" / "META_LEDGER.md").write_text(_LEDGER, encoding="utf-8")
    before_readme = (tmp_path / "README.md").read_bytes()
    before_state = (tmp_path / "docs" / "SYSTEM_STATE.md").read_bytes()
    rc = seal_artifacts.main(["--write", "--dry-run", "--phase", "2",
                              "--snapshot", "2026-07-04", "--repo-root", str(tmp_path),
                              "--skip-tests"])
    out = capsys.readouterr().out
    assert rc == 0
    assert out.count("[dry] would write") == 2
    assert (tmp_path / "README.md").read_bytes() == before_readme
    assert (tmp_path / "docs" / "SYSTEM_STATE.md").read_bytes() == before_state
    rc = seal_artifacts.main(["--write", "--phase", "2", "--snapshot", "2026-07-04",
                              "--repo-root", str(tmp_path), "--skip-tests"])
    assert rc == 0
    assert (tmp_path / "README.md").read_bytes() != before_readme


def test_reconcile_propose_and_authorize_dry_run(tmp_path, capsys):
    from qor.cli_handlers import reconcile as handlers
    from qor.scripts import reconcile

    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(_LEDGER, encoding="utf-8")
    out_path = tmp_path / "proposal.json"
    args = argparse.Namespace(ledger=str(ledger), out=str(out_path), dry_run=True)
    rc = handlers.do_propose(args)
    assert rc == 0
    assert not out_path.exists()
    assert "[dry] would write proposal" in capsys.readouterr().out
    # wet propose, then dry authorize
    args = argparse.Namespace(ledger=str(ledger), out=str(out_path), dry_run=False)
    assert handlers.do_propose(args) == 0
    before_ledger = ledger.read_bytes()
    before_proposal = out_path.read_bytes()
    args = argparse.Namespace(proposal=str(out_path), ledger=str(ledger), dry_run=True)
    rc = handlers.do_authorize(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "[dry] would append RECONCILIATION Entry #3" in out
    assert "[dry] would mark proposal authorized" in out
    assert ledger.read_bytes() == before_ledger
    assert out_path.read_bytes() == before_proposal
    # library-level: dry append computes the preview without writing
    proposal = json.loads(out_path.read_text(encoding="utf-8"))
    result = reconcile.append_reconciliation_entry(
        ledger, proposal, ts="2026-07-04T12:00:00Z", dry_run=True
    )
    assert result["entry_num"] == 3
    assert ledger.read_bytes() == before_ledger


def test_changelog_stamp_dry_run_preserves_file_and_still_validates(tmp_path, capsys):
    from qor.scripts import changelog_backends
    from qor.scripts.changelog_stamp import apply_stamp

    cl = tmp_path / "CHANGELOG.md"
    cl.write_text("# Changelog\n\n## [Unreleased]\n\n- something\n\n## [0.1.0] - 2026-01-01\n",
                  encoding="utf-8")
    before = cl.read_bytes()
    fmt = changelog_backends.stamp(cl, "0.2.0", "2026-07-04", dry_run=True)
    assert fmt == "keepachangelog"
    assert cl.read_bytes() == before
    assert "[dry] would stamp" in capsys.readouterr().out
    empty = tmp_path / "EMPTY.md"
    empty.write_text("# Changelog\n\n## [Unreleased]\n\n## [0.1.0] - 2026-01-01\n",
                     encoding="utf-8")
    with pytest.raises(ValueError):
        apply_stamp(empty, "0.2.0", "2026-07-04", dry_run=True)
    assert cl.read_bytes() == before


def test_session_tool_rotate_dry_run_does_not_move_marker(tmp_path, capsys):
    from unittest import mock

    from qor.scripts import session, session_tool

    marker = tmp_path / "current"
    marker.write_text("2026-07-04T1200-abc123\n", encoding="utf-8")
    with mock.patch.object(session, "MARKER_PATH", marker):
        rc = session_tool.main(["current"])
        assert rc == 0
        assert "2026-07-04T1200-abc123" in capsys.readouterr().out
        rc = session_tool.main(["rotate", "--dry-run"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "[dry] would rotate session: 2026-07-04T1200-abc123 ->" in out
        assert marker.read_text(encoding="utf-8").strip() == "2026-07-04T1200-abc123"
        rc = session_tool.main(["rotate"])
        assert rc == 0
        assert marker.read_text(encoding="utf-8").strip() != "2026-07-04T1200-abc123"


def test_governance_index_advance_dry_run(tmp_path, capsys):
    from qor.scripts import governance_index

    docs = tmp_path / "docs"
    docs.mkdir()
    index = docs / "GOVERNANCE_INDEX.md"
    index.write_text("# Governance Index\n\n**Last Reviewed**: 2026-01-01\n", encoding="utf-8")
    before = index.read_bytes()
    changed = governance_index.advance_last_reviewed(tmp_path, "2026-07-04", dry_run=True)
    assert changed is True
    assert index.read_bytes() == before
    assert "[dry] would advance Last Reviewed" in capsys.readouterr().out
    changed = governance_index.advance_last_reviewed(tmp_path, "2026-07-04")
    assert changed is True
    assert "2026-07-04" in index.read_text(encoding="utf-8")


def test_uninstall_dry_run_lists_without_removing(tmp_path, capsys):
    from qor.install import _do_uninstall

    base = tmp_path / "host"
    (base / "skills").mkdir(parents=True)
    f1 = base / "skills" / "a.md"
    f1.write_text("x", encoding="utf-8")
    record = base / ".qorlogic-installed.json"
    record.write_text(json.dumps({"files": [{"path": str(f1)}]}), encoding="utf-8")
    rc = _do_uninstall(target_override=base, dry_run=True)
    out = capsys.readouterr().out
    assert rc == 0
    assert "[dry] Would remove 1 files" in out
    assert f1.exists() and record.exists()
    rc = _do_uninstall(target_override=base)
    assert rc == 0
    assert not f1.exists() and not record.exists()
