"""Phase 112 (#140): governance_index drift checker behavioral tests."""
from __future__ import annotations

from qor.scripts.governance_index import check_index_drift


_LEDGER = (
    "# QoreLogic Meta Ledger\n\n"
    "### Entry #1: SESSION SEAL\n\n**Timestamp**: 2026-05-20\nsealed.\n\n"
    "### Entry #2: SESSION SEAL\n\n**Timestamp**: 2026-05-28\nsealed.\n"
)

_INDEX_HEADER = "# Governance Index\n\n**Last Reviewed**: {date}\n\n"
_TIER1 = "## Tier 1 — Canonical Source\n\n| Artifact | Path |\n|---|---|\n| Ledger | `docs/META_LEDGER.md` |\n"


def _workspace(tmp_path, reviewed, extra_rows="", extra_docs=()):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "META_LEDGER.md").write_text(_LEDGER, encoding="utf-8")
    (docs / "GOVERNANCE_INDEX.md").write_text(_INDEX_HEADER.format(date=reviewed) + _TIER1 + extra_rows, encoding="utf-8")
    for name in extra_docs:
        (docs / name).write_text("# doc\n", encoding="utf-8")
    return tmp_path


def _kinds(findings):
    return {f.kind for f in findings}


def test_stale_last_reviewed_flags_tier1_drift(tmp_path):
    ws = _workspace(tmp_path, reviewed="2026-05-21")  # before latest seal 2026-05-28
    assert "stale-tier1" in _kinds(check_index_drift(ws))


def test_current_last_reviewed_passes(tmp_path):
    ws = _workspace(tmp_path, reviewed="2026-05-28")  # == latest seal
    assert "stale-tier1" not in _kinds(check_index_drift(ws))


def test_unregistered_governance_doc_flags(tmp_path):
    ws = _workspace(tmp_path, reviewed="2026-05-28", extra_docs=("NEWDOC.md",))
    findings = check_index_drift(ws)
    unreg = [f for f in findings if f.kind == "unregistered"]
    assert any(f.path == "docs/NEWDOC.md" for f in unreg)


def test_registered_doc_does_not_flag(tmp_path):
    ws = _workspace(
        tmp_path, reviewed="2026-05-28",
        extra_rows="| New | `docs/NEWDOC.md` |\n", extra_docs=("NEWDOC.md",),
    )
    findings = check_index_drift(ws)
    assert not any(f.path == "docs/NEWDOC.md" for f in findings)


def test_missing_index_returns_missing_finding(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text(_LEDGER, encoding="utf-8")
    findings = check_index_drift(tmp_path)
    assert _kinds(findings) == {"missing-index"}
