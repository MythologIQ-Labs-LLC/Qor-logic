"""Phase 56 canonicalization tests."""
from __future__ import annotations

import hashlib
from pathlib import Path

from qor.scripts import ledger_hash
from qor.scripts.ledger_fragment import (
    LedgerFragment,
    canonicalize_fragments,
    next_entry_number,
    write_fragment,
)


def _ledger(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "META_LEDGER.md"
    p.write_text(body, encoding="utf-8")
    return p


def _entry(num: int, content: str, prev: str, chain: str) -> str:
    return (
        f"\n---\n\n### Entry #{num}: TEST\n\n"
        f"**Content Hash**:\n```\nSHA256(x) = {content}\n```\n\n"
        f"**Previous Hash**: `{prev}`\n\n"
        f"**Chain Hash**:\n```\nSHA256(content + previous) = {chain}\n```\n"
    )


def _frag(uid: str, ts: str, title: str, body: str) -> LedgerFragment:
    return LedgerFragment(
        uid=uid, ts=ts, session_id="sess-x", title=title,
        body=body, content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
    )


def test_next_entry_number_returns_one_for_empty_ledger():
    assert next_entry_number("# Ledger\n") == 1


def test_next_entry_number_returns_next_after_max(tmp_path):
    text = "### Entry #5: A\n\n### Entry #10: B\n"
    assert next_entry_number(text) == 11


def test_canonicalize_returns_zero_when_no_fragments(tmp_path):
    p = _ledger(tmp_path, "# Ledger\n\n### Entry #1: GENESIS\n")
    assert canonicalize_fragments(p, tmp_path) == 0


def test_canonicalize_assigns_contiguous_display_numbers(tmp_path):
    p = _ledger(tmp_path, "# Ledger\n\n### Entry #5: GENESIS\n")
    write_fragment(tmp_path, _frag("le_0000000000000001",
                                   "2026-05-11T16:00:00Z", "A", "body A\n"))
    write_fragment(tmp_path, _frag("le_0000000000000002",
                                   "2026-05-11T17:00:00Z", "B", "body B\n"))
    appended = canonicalize_fragments(p, tmp_path)
    assert appended == 2
    body = p.read_text(encoding="utf-8")
    assert "### Entry #6: A" in body
    assert "### Entry #7: B" in body


def test_canonicalize_sorts_by_ts_then_uid(tmp_path):
    p = _ledger(tmp_path, "# Ledger\n")
    write_fragment(tmp_path, _frag("le_0000000000000002",
                                   "2026-05-11T17:00:00Z", "B", "body B\n"))
    write_fragment(tmp_path, _frag("le_0000000000000001",
                                   "2026-05-11T16:00:00Z", "A", "body A\n"))
    canonicalize_fragments(p, tmp_path)
    body = p.read_text(encoding="utf-8")
    pos_a = body.find("### Entry #1: A")
    pos_b = body.find("### Entry #2: B")
    assert 0 <= pos_a < pos_b


def test_canonicalize_archives_consumed_fragments(tmp_path):
    p = _ledger(tmp_path, "# Ledger\n")
    write_fragment(tmp_path, _frag("le_0000000000000001",
                                   "2026-05-11T16:00:00Z", "A", "body A\n"))
    canonicalize_fragments(p, tmp_path)
    base = tmp_path / ".qor" / "ledger" / "fragments"
    assert not (base / "le_0000000000000001.json").exists()
    assert (base / "consumed" / "le_0000000000000001.json").exists()


def test_canonicalize_emission_uses_existing_hash_regex_shapes(tmp_path):
    """Phase 59 cross-check: canonicalized entries must be parseable by
    CONTENT_HASH_RE / PREV_HASH_RE / CHAIN_HASH_RE for the hash-integrity
    gate to fire. Compose a real chain end-to-end."""
    p = _ledger(tmp_path, "# Ledger\n")
    content_h = "a" * 64
    prev_h = "b" * 64
    chain_h = ledger_hash.chain_hash(content_h, prev_h)
    body = (
        f"**Content Hash**:\n```\nSHA256(x) = {content_h}\n```\n\n"
        f"**Previous Hash**: `{prev_h}`\n\n"
        f"**Chain Hash**:\n```\nSHA256(content + previous) = {chain_h}\n```\n"
    )
    write_fragment(tmp_path, _frag("le_0000000000000003",
                                   "2026-05-11T16:00:00Z", "REAL", body))
    canonicalize_fragments(p, tmp_path)
    rc = ledger_hash.verify(p)
    assert rc == 0  # parses + validates + chain compares clean
