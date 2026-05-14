"""Phase 76 P2: seal_entry_check previous_hash uniqueness detection (GH #51)."""
from __future__ import annotations

from pathlib import Path

from qor.reliability import seal_entry_check


def _synthetic_ledger(entries: list[dict]) -> str:
    """Build a synthetic META_LEDGER body from entry dicts. Each dict has
    `num`, `phase`, `content_hash`, `previous_hash`, `chain_hash` fields."""
    lines = ["# META_LEDGER\n"]
    for e in entries:
        lines.append(
            f"### Entry #{e['num']}: SESSION SEAL — Phase {e['phase']} feature\n\n"
            f"**Timestamp**: 2026-05-14T22:00:00Z\n\n"
            f"**Phase**: SUBSTANTIATE (Phase {e['phase']} feature)\n\n"
            f"**Content Hash (session seal)**: `{e['content_hash']}`\n\n"
            f"**Previous Hash**: `{e['previous_hash']}`\n\n"
            f"**Chain Hash (Merkle seal)**: `{e['chain_hash']}`\n\n"
        )
    return "\n".join(lines)


def test_unique_previous_hash_passes(tmp_path):
    ledger = tmp_path / "META_LEDGER.md"
    entries = [
        {"num": i, "phase": i, "content_hash": format(i, "064x"),
         "previous_hash": format(i - 1, "064x"), "chain_hash": format(i + 100, "064x")}
        for i in range(1, 6)
    ]
    ledger.write_text(_synthetic_ledger(entries), encoding="utf-8")
    result = seal_entry_check.check_previous_hash_uniqueness(ledger, min_entry_num=1)
    assert result.ok is True, f"Expected unique previous_hashes to pass; errors={result.errors}"


def test_duplicate_previous_hash_fails_with_entry_names(tmp_path):
    ledger = tmp_path / "META_LEDGER.md"
    dup_prev = format(3, "064x")
    entries = [
        {"num": 1, "phase": 1, "content_hash": format(1, "064x"),
         "previous_hash": format(0, "064x"), "chain_hash": format(101, "064x")},
        {"num": 2, "phase": 2, "content_hash": format(2, "064x"),
         "previous_hash": format(1, "064x"), "chain_hash": format(102, "064x")},
        {"num": 3, "phase": 3, "content_hash": format(3, "064x"),
         "previous_hash": dup_prev, "chain_hash": format(103, "064x")},
        {"num": 4, "phase": 4, "content_hash": format(4, "064x"),
         "previous_hash": dup_prev, "chain_hash": format(104, "064x")},
    ]
    ledger.write_text(_synthetic_ledger(entries), encoding="utf-8")
    result = seal_entry_check.check_previous_hash_uniqueness(ledger, min_entry_num=1)
    assert result.ok is False
    joined = " ".join(result.errors)
    assert "3" in joined and "4" in joined, f"Expected duplicate entry nums in errors; got {result.errors}"
    assert dup_prev[:8] in joined or dup_prev in joined, "Expected duplicate hash prefix in error message"


def test_canonical_meta_ledger_has_no_race_signature():
    # Forward-only per Phase 76 design: only check entries from #207 onward.
    # Past duplicate instances (e.g., #109/#111/#113) are documented residual
    # in SG-ConcurrentLedgerRace-A; V2 reconciliation is the only path that
    # may resolve them. Pre-Phase-76 entries are grandfathered.
    result = seal_entry_check.check_previous_hash_uniqueness(Path("docs/META_LEDGER.md"))
    assert result.ok is True, (
        f"Canonical META_LEDGER.md must have no Phase 76+ duplicate-previous_hash signature; "
        f"got errors={result.errors}"
    )


def test_check_grandfathers_pre_phase_76_entries(tmp_path):
    """Past entries (num < min_entry_num) are NOT checked even if they have duplicate previous_hash."""
    ledger = tmp_path / "META_LEDGER.md"
    dup_prev = format(99, "064x")
    entries = [
        # Two pre-Phase-76 entries with duplicate previous_hash (would have failed without grandfather)
        {"num": 109, "phase": 0, "content_hash": format(109, "064x"),
         "previous_hash": dup_prev, "chain_hash": format(1109, "064x")},
        {"num": 111, "phase": 0, "content_hash": format(111, "064x"),
         "previous_hash": dup_prev, "chain_hash": format(1111, "064x")},
    ]
    ledger.write_text(_synthetic_ledger(entries), encoding="utf-8")
    result = seal_entry_check.check_previous_hash_uniqueness(ledger, min_entry_num=207)
    assert result.ok is True, f"Pre-Phase-76 entries must be grandfathered; got errors={result.errors}"
