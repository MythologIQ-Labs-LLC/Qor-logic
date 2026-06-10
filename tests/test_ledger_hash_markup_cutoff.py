"""Phase 155 (GAP-GOV-09): verify() FAILs a modern (>= cutoff) ledger entry that
lacks canonical hash markup, instead of silently skipping it. Historical
entries (< cutoff, the 32 pre-canonical-markup originals) stay grandfathered.
"""
from __future__ import annotations

from pathlib import Path

from qor.scripts import ledger_hash


def _ledger(num: int) -> str:
    # an entry with NO canonical Content/Previous/Chain markup and no Session-Seal line
    return (
        "# Meta Ledger\n\n"
        f"### Entry #{num}: SOME KIND -- no hashes in this body\n\n"
        "just prose, nothing verifiable here.\n"
    )


def test_modern_missing_markup_fails(tmp_path, capsys):
    led = tmp_path / "META_LEDGER.md"
    led.write_text(_ledger(123), encoding="utf-8")
    rc = ledger_hash.verify(led)
    err = capsys.readouterr().err
    assert rc == 1
    assert "Entry #123" in err and "missing canonical hash markup" in err


def test_historical_missing_markup_skipped(tmp_path, capsys):
    led = tmp_path / "META_LEDGER.md"
    led.write_text(_ledger(100), encoding="utf-8")
    rc = ledger_hash.verify(led)
    out = capsys.readouterr().out
    assert rc == 0
    assert "Skipped 1 entries with non-verifiable markup" in out


def test_cutoff_boundary(tmp_path):
    # exactly at the cutoff -> FAIL; one below -> skip (off-by-one guard)
    at = tmp_path / "at.md"
    at.write_text(_ledger(123), encoding="utf-8")
    assert ledger_hash.verify(at, markup_required_cutoff=123) == 1
    below = tmp_path / "below.md"
    below.write_text(_ledger(122), encoding="utf-8")
    assert ledger_hash.verify(below, markup_required_cutoff=123) == 0


def test_real_ledger_clean():
    # regression: the 32 historical skips (all <= 122) stay grandfathered, and no
    # modern entry is missing markup, so the real chain still verifies clean.
    repo = Path(__file__).resolve().parents[1]
    assert ledger_hash.verify(repo / "docs" / "META_LEDGER.md") == 0
