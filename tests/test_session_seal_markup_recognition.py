"""Phase 66 (#54): Session Seal markup recognition in ledger_hash.verify.

Some historical SESSION SEAL entries record the chain hash as
`**Session Seal**:\n SHA256(content + prev) = \`<hex>\`` instead of
`**Chain Hash (...)**: \`<hex>\``. Pre-Phase-66 verify() skipped those
entries, allowing downstream entries chained from their parsed value
to be classified as OK while the seal entry itself was invisible.

Acceptance question: "If the unit's behavior were silently broken but
the artifact still existed, would this test fail?" - yes. Removing
SESSION_SEAL_RE recognition from verify() makes the fixtures here
report Skipped rather than OK/FAIL.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from qor.scripts import ledger_hash as lh


def _digest(seed: bytes) -> str:
    return hashlib.sha256(seed).hexdigest()


def _entry_with_session_seal(num: int, content: str, prev: str, seal: str) -> str:
    return (
        f"### Entry #{num}: SESSION SEAL TEST\n\n"
        f"**Content Hash**: `{content}`\n\n"
        f"**Previous Hash**: `{prev}`\n\n"
        f"**Session Seal**:\nSHA256(content_hash + previous_hash)\n"
        f"= `{seal}`\n\n"
    )


def _entry_canonical(num: int, content: str, prev: str, chain: str) -> str:
    return (
        f"### Entry #{num}: CANONICAL\n\n"
        f"**Content Hash**: `{content}`\n\n"
        f"**Previous Hash**: `{prev}`\n\n"
        f"**Chain Hash**: `{chain}`\n\n"
    )


def _write(tmp: Path, body: str) -> Path:
    p = tmp / "META_LEDGER.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_session_seal_regex_matches_canonical_form():
    """The SESSION_SEAL_RE captures the recorded chain hex from canonical markup."""
    body = (
        "**Session Seal**:\n"
        "SHA256(content_hash + previous_hash)\n"
        "= `abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789`"
    )
    m = lh.SESSION_SEAL_RE.search(body)
    assert m is not None
    assert m.group(1) == "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"


def test_verify_recognizes_session_seal_only_entry(tmp_path, capsys):
    content = _digest(b"phase66-content")
    prev = "0" * 64
    seal = lh.chain_hash(content, prev)
    p = _write(tmp_path, _entry_with_session_seal(1, content, prev, seal))
    rc = lh.verify(p)
    out = capsys.readouterr()
    assert rc == 0
    assert "Entry #1: chain hash verified" in out.out
    assert "Skipped" not in out.out


def test_verify_rejects_session_seal_with_invalid_chain(tmp_path, capsys):
    content = _digest(b"a")
    prev = _digest(b"b")
    wrong_seal = _digest(b"definitely-not-the-real-chain")
    p = _write(tmp_path, _entry_with_session_seal(1, content, prev, wrong_seal))
    rc = lh.verify(p)
    err = capsys.readouterr().err
    assert rc == 1
    assert "FAIL Entry #1" in err


def test_verify_session_seal_continuity_into_chain_hash(tmp_path, capsys):
    """Entry #2 (canonical) must chain-verify against Entry #1's Session Seal value."""
    content1 = _digest(b"phase66-e1-content")
    prev1 = "0" * 64
    seal1 = lh.chain_hash(content1, prev1)

    content2 = _digest(b"phase66-e2-content")
    chain2 = lh.chain_hash(content2, seal1)

    body = (
        _entry_with_session_seal(1, content1, prev1, seal1)
        + _entry_canonical(2, content2, seal1, chain2)
    )
    p = _write(tmp_path, body)
    rc = lh.verify(p)
    out = capsys.readouterr()
    assert rc == 0
    assert "Entry #1: chain hash verified" in out.out
    assert "Entry #2: chain hash verified" in out.out


def test_skipped_summary_distinguishes_session_seal_only_from_no_markup(tmp_path, capsys):
    """Entries with neither Chain Hash nor Session Seal markup are skipped;
    entries with Session Seal markup are verified (not skipped)."""
    # Entry #1: Session Seal only -- verifies
    content1 = _digest(b"phase66-e1")
    prev1 = "0" * 64
    seal1 = lh.chain_hash(content1, prev1)
    e1 = _entry_with_session_seal(1, content1, prev1, seal1)
    # Entry #2: bare prose, no hash markup -- skipped
    e2 = "### Entry #2: NARRATIVE\n\nNothing parseable here.\n\n"
    p = _write(tmp_path, e1 + e2)
    rc = lh.verify(p)
    out = capsys.readouterr().out
    assert rc == 0
    assert "Entry #1: chain hash verified" in out
    assert "Skipped 1 entries" in out
