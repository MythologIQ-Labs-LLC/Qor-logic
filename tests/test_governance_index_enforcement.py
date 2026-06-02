"""Phase 120 (GH #149): governance-index enforcement.

Behavioral tests for the enforcement layer wired into /qor-substantiate
(advance Last Reviewed + fail-closed drift) and /qor-validate (read-only
ledger cross-check). Synthetic tmp-path workspaces; assertions check returned
findings / file state, not section presence (doctrine-test-functionality.md).
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts import governance_index as gi

REPO_ROOT = Path(__file__).resolve().parent.parent


def _ledger(seal_date: str, phase: int = 50) -> str:
    return (
        f"# META_LEDGER\n\n### Entry #1: SESSION SEAL -- Phase {phase} test\n\n"
        f"**Timestamp**: {seal_date}\n\n**Chain Hash**: `{'a'*64}`\n"
    )


def _index(reviewed: str, *, tier3_rows: str = "_none open_ | `.qor/session/` | n/a",
           extra_registered: str = "") -> str:
    return f"""# Governance Index

**Last Reviewed**: {reviewed}

## Tier 1 — Canonical Source

| Artifact | Path | Freshness |
|---|---|---|
| Meta Ledger | `docs/META_LEDGER.md` | latest seal |
| Plans | `docs/plan-*.md` | per-phase |
{extra_registered}

## Tier 3 — Active Initiative

| Artifact | Path | Opened |
|---|---|---|
| {tier3_rows} |

## Tier 4 — Per-Plan Artifact

| Artifact | Path | Plan |
|---|---|---|
| Plans (all) | `docs/plan-*.md` | per-phase |
"""


def _workspace(tmp_path: Path, reviewed: str, *, seal_date: str = "2026-05-29",
               tier3_rows: str | None = None, extra_docs=(), extra_registered: str = "") -> Path:
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "META_LEDGER.md").write_text(_ledger(seal_date), encoding="utf-8")
    kwargs = {"extra_registered": extra_registered}
    if tier3_rows is not None:
        kwargs["tier3_rows"] = tier3_rows
    (tmp_path / "docs" / "GOVERNANCE_INDEX.md").write_text(_index(reviewed, **kwargs), encoding="utf-8")
    for name in extra_docs:
        (tmp_path / "docs" / name).write_text("# doc\n", encoding="utf-8")
    return tmp_path


def test_advance_last_reviewed_rewrites_date(tmp_path):
    base = _workspace(tmp_path, "2026-01-01")
    changed = gi.advance_last_reviewed(base, "2026-05-30")
    assert changed is True
    text = (base / "docs" / "GOVERNANCE_INDEX.md").read_text(encoding="utf-8")
    assert "2026-05-30" in text and "2026-01-01" not in text
    # Idempotent: advancing to the same date reports no change.
    assert gi.advance_last_reviewed(base, "2026-05-30") is False


def test_enforce_at_seal_passes_when_clean(tmp_path):
    base = _workspace(tmp_path, "2026-01-01", seal_date="2026-05-30")
    findings = gi.enforce_at_seal(base, "2026-05-30")
    assert findings == [], findings
    # Last Reviewed advanced to the seal date (stale-tier1 cleared by construction).
    assert "2026-05-30" in (base / "docs" / "GOVERNANCE_INDEX.md").read_text(encoding="utf-8")


def test_enforce_at_seal_fails_on_unregistered(tmp_path):
    base = _workspace(tmp_path, "2026-01-01", seal_date="2026-05-30",
                      extra_docs=("rogue-unregistered-doc.md",))
    findings = gi.enforce_at_seal(base, "2026-05-30")
    kinds = {(f.kind, f.path) for f in findings}
    assert ("unregistered", "docs/rogue-unregistered-doc.md") in kinds, findings


def test_enforce_at_seal_flags_tier3_unarchived(tmp_path):
    base = _workspace(
        tmp_path, "2026-01-01", seal_date="2026-05-30",
        tier3_rows="Reconcile tool | `phase 119` | 2026-05-29",
    )
    # Ledger contains a SESSION SEAL for Phase 119 -> Tier3 row is stale.
    (base / "docs" / "META_LEDGER.md").write_text(
        _ledger("2026-05-30", phase=119), encoding="utf-8")
    findings = gi.enforce_at_seal(base, "2026-05-30")
    assert any(f.kind == "tier3-unarchived" for f in findings), findings


def test_cross_check_flags_stale_last_reviewed(tmp_path):
    base = _workspace(tmp_path, "2026-05-20", seal_date="2026-05-30")
    findings = gi.cross_check_index_against_ledger(base)
    assert any(f.kind == "stale-tier1" for f in findings), findings


def test_cross_check_clean_when_current_and_archived(tmp_path):
    base = _workspace(tmp_path, "2026-05-30", seal_date="2026-05-30")
    findings = gi.cross_check_index_against_ledger(base)
    assert findings == [], findings


def test_disclosed_skip_when_index_absent(tmp_path):
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "META_LEDGER.md").write_text(_ledger("2026-05-30"), encoding="utf-8")
    # No GOVERNANCE_INDEX.md: both entry points return missing-index, never raise.
    assert any(f.kind == "missing-index" for f in gi.enforce_at_seal(tmp_path, "2026-05-30"))
    assert any(f.kind == "missing-index" for f in gi.cross_check_index_against_ledger(tmp_path))


def test_doctrine_marks_enforcement_shipped():
    doctrine = (REPO_ROOT / "qor" / "references"
                / "doctrine-governance-index.md").read_text(encoding="utf-8")
    assert "Phase 120" in doctrine
    assert "cross-check" in doctrine.lower()
    assert "/qor-substantiate" in doctrine
