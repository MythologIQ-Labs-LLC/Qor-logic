"""Phase 48 meta_ledger_walker behavior tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts.meta_ledger_walker import walk, last_n_audit_entries, LedgerRecord


def _ledger(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "META_LEDGER.md"
    p.write_text(body, encoding="utf-8")
    return p


_THREE_AUDITS = """# Ledger

### Entry #1: GENESIS

**Timestamp**: 2026-01-01T00:00:00Z
**Phase**: BOOTSTRAP

### Entry #2: AUDIT

**Timestamp**: 2026-02-01T00:00:00Z
**Verdict**: VETO
**Target**: `docs/plan-a.md`
**Findings categories**: specification-drift

### Entry #3: AUDIT

**Timestamp**: 2026-02-02T00:00:00Z
**Verdict**: PASS
**Target**: `docs/plan-a.md`

### Entry #4: SESSION SEAL -- phase X sealed

**Timestamp**: 2026-02-03T00:00:00Z
**Verdict**: PASS (smoke)
**Target**: `docs/plan-a.md`
"""


def test_walk_parses_three_entries(tmp_path):
    p = _ledger(tmp_path, _THREE_AUDITS)
    records = walk(p)
    assert len(records) == 4
    assert records[0].entry_id == 1
    assert records[3].entry_id == 4


def test_walk_extracts_verdict_target_ts():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as d:
        p = _ledger(pathlib.Path(d), _THREE_AUDITS)
        records = walk(p)
        veto = records[1]
        assert veto.verdict == "VETO"
        assert veto.target == "docs/plan-a.md"
        assert veto.ts == "2026-02-01T00:00:00Z"


def test_walk_extracts_signature_from_findings_categories(tmp_path):
    p = _ledger(tmp_path, _THREE_AUDITS)
    records = walk(p)
    veto = records[1]
    assert veto.signature == "specification-drift"


def test_walk_handles_legacy_entries_without_signature(tmp_path):
    body = (
        "### Entry #5: AUDIT\n\n"
        "**Timestamp**: 2026-03-01T00:00:00Z\n"
        "**Verdict**: VETO\n"
        "**Target**: `docs/x.md`\n"
    )
    p = _ledger(tmp_path, body)
    records = walk(p)
    assert records[0].signature is None
    assert records[0].verdict == "VETO"


def test_last_n_audit_entries_returns_only_audit_class(tmp_path):
    p = _ledger(tmp_path, _THREE_AUDITS)
    audits = last_n_audit_entries(p, 10)
    assert len(audits) == 3
    assert audits[0].entry_id == 2
    assert audits[-1].entry_id == 4


def test_last_n_audit_entries_caps_at_n(tmp_path):
    p = _ledger(tmp_path, _THREE_AUDITS)
    audits = last_n_audit_entries(p, 2)
    assert len(audits) == 2
    assert audits[0].entry_id == 3
    assert audits[-1].entry_id == 4


def test_last_n_audit_entries_returns_empty_when_no_audits(tmp_path):
    body = "### Entry #1: GENESIS\n\n**Timestamp**: 2026-01-01T00:00:00Z\n"
    p = _ledger(tmp_path, body)
    assert last_n_audit_entries(p, 5) == []
