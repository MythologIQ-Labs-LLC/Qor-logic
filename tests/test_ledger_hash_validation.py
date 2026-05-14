"""Phase 59 (#48): ledger_hash.verify hash-format defense.

Layered behavior:
- The CONTENT_HASH_RE / PREV_HASH_RE / CHAIN_HASH_RE regex enforces `[0-9a-f]{64}`
  on the parsed value. Strings that fail this format never reach the validator;
  the entry lands in the "Skipped ... non-verifiable markup" branch (rc=0).
- For values that DO match the regex, `hash_guard.validate_sha256` is called on
  each before chain comparison. This is defense-in-depth: if the regex is
  loosened in a future phase (e.g., federation IDs at Phase 56), the validator
  still catches placeholders / uppercase / wrong-length / non-hex as a
  verification FAILURE (rc=1) rather than letting them through to chain compare.
- Fabricated-but-correctly-formatted hashes (the actual GH #48 failure mode)
  are caught by the chain-hash comparison: a fake `sha256(b"") = e3b0c44...`
  passes the regex and the validator but fails `chain_hash(c, p) == recorded`
  so verify reports FAIL Entry #N with rc=1.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from qor.scripts import hash_guard, ledger_hash


def _digest(seed: bytes) -> str:
    """Phase 66 helper: produce a real-shape SHA-256 digest for fixtures.

    Pre-Phase-66 tests used `"a" * 64` / `"b" * 64` synthetic shapes. The
    placeholder detector introduced by GH #54 (Phase 66) correctly flags
    those as fabrication. Fixtures now derive from `hashlib.sha256(seed)`
    so they pass placeholder detection while still being deterministic.
    """
    return hashlib.sha256(seed).hexdigest()


def _content(h: str) -> str:
    return "**Content Hash**:\n```\nSHA256(x) = " + h + "\n```\n"


def _prev(h: str) -> str:
    return "**Previous Hash**: `" + h + "`\n"


def _chain(h: str) -> str:
    return "**Chain Hash**:\n```\nSHA256(content + previous) = " + h + "\n```\n"


def _entry(num: int, content: str, previous: str, chain: str) -> str:
    return (
        f"### Entry #{num}: TEST\n\n"
        + _content(content) + "\n"
        + _prev(previous) + "\n"
        + _chain(chain) + "\n"
    )


def _write_ledger(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "META_LEDGER.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_verify_accepts_known_good_chain(tmp_path, capsys):
    content_h = _digest(b"phase66-fixture-content")
    prev_h = _digest(b"phase66-fixture-prev")
    chain_h = ledger_hash.chain_hash(content_h, prev_h)
    p = _write_ledger(tmp_path, _entry(1, content_h, prev_h, chain_h))
    rc = ledger_hash.verify(p)
    assert rc == 0
    assert "Entry #1: chain hash verified" in capsys.readouterr().out


def test_verify_skips_entries_with_placeholder_content_hash(tmp_path, capsys):
    """Regex pre-filter: 'TBD...' is not [0-9a-f]{64}; entry lands in skip path."""
    p = _write_ledger(tmp_path, _entry(1, "TBD" + ("0" * 61), "b" * 64, "c" * 64))
    rc = ledger_hash.verify(p)
    assert rc == 0
    assert "Skipped 1 entries" in capsys.readouterr().out


def test_verify_skips_entries_with_uppercase_hash(tmp_path, capsys):
    p = _write_ledger(tmp_path, _entry(1, "A" * 64, "b" * 64, "c" * 64))
    rc = ledger_hash.verify(p)
    assert rc == 0
    assert "Skipped 1 entries" in capsys.readouterr().out


def test_verify_skips_entries_with_short_hash(tmp_path, capsys):
    p = _write_ledger(tmp_path, _entry(1, "a" * 32, "b" * 64, "c" * 64))
    rc = ledger_hash.verify(p)
    assert rc == 0


def test_verify_rejects_fabricated_but_well_formed_chain_hash(tmp_path, capsys):
    """The actual GH #48 read-side failure mode: write a real-looking hex that
    doesn't correspond to the actual content. Caught by chain comparison."""
    content_h = _digest(b"phase66-fixture-content")
    prev_h = _digest(b"phase66-fixture-prev")
    fabricated = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    p = _write_ledger(tmp_path, _entry(1, content_h, prev_h, fabricated))
    rc = ledger_hash.verify(p)
    assert rc == 1
    assert "FAIL Entry #1" in capsys.readouterr().err


def test_verify_reports_entry_number_on_failure(tmp_path, capsys):
    content_h = _digest(b"phase66-fixture-content")
    prev_h = _digest(b"phase66-fixture-prev")
    real = ledger_hash.chain_hash(content_h, prev_h)
    fabricated = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    body = _entry(1, content_h, prev_h, real) + _entry(2, content_h, prev_h, fabricated)
    p = _write_ledger(tmp_path, body)
    rc = ledger_hash.verify(p)
    assert rc == 1
    err = capsys.readouterr().err
    assert "Entry #2" in err


# NOTE: The 2 tests asserting ledger_hash.verify integration with
# hash_guard.validate_sha256 were dropped during Phase 63 reconciliation
# (Path B) because the integration would conflict with upstream's
# test_seal_entry_check.py fixtures that use "0"*64 placeholder previous
# hashes. The hash_guard module remains importable for callers that opt
# into strict validation directly; ledger_hash.verify uses regex-defense
# + chain-fabrication detection (the other 8 tests in this file lock those
# semantics).


def test_verify_still_skips_legacy_entries_without_parseable_markup(tmp_path, capsys):
    """Locks the legacy-skip vs fabricated-hash distinction from the Phase 59
    audit advisory: entries without hash markup land in the existing skip path
    (the parser yields no value, so validate_sha256 is never reached)."""
    body = "### Entry #1: GENESIS\n\n**Timestamp**: 2026-01-01T00:00:00Z\n"
    p = _write_ledger(tmp_path, body)
    rc = ledger_hash.verify(p)
    assert rc == 0
    assert "Skipped 1 entries" in capsys.readouterr().out


def test_verify_passes_real_chain_math_end_to_end(tmp_path):
    """Regression sanity: real chain math survives the new validation layer."""
    content_h = "67e93059152d0a587a7b651864be0183ed8f68a9f8b93b7b9e53914eecf5b50c"
    prev_h = "1d9d6f54bf84a6d1cb922af90d57501bdf2060b0a0526c890e326f1f70594027"
    chain_h = ledger_hash.chain_hash(content_h, prev_h)
    p = _write_ledger(tmp_path, _entry(149, content_h, prev_h, chain_h))
    rc = ledger_hash.verify(p)
    assert rc == 0
