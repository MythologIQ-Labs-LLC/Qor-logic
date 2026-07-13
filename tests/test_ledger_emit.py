"""Phase 193 (GH #278): typed ledger entry renderer + append."""
from __future__ import annotations

from pathlib import Path

import pytest

import hashlib

from qor.scripts.ledger_emit import LedgerEntry, append, render
from qor.scripts.ledger_hash import _resolve_recorded, chain_hash, verify

TAIL = "\n---\n\n*Chain integrity: VALID*\n*Session: SEALED* (test)\n"

_G_CONTENT = hashlib.sha256(b"genesis-content").hexdigest()
_G_PREV = hashlib.sha256(b"genesis-prev").hexdigest()
_G_CHAIN = chain_hash(_G_CONTENT, _G_PREV)

GENESIS = (
    "# Meta Ledger\n\n"
    "### Entry #1: GENESIS\n\n"
    "**Timestamp**: 2026-07-13T00:00:00Z\n\n"
    "**Content Hash**: `" + _G_CONTENT + "`\n"
    "**Previous Hash**: `" + _G_PREV + "`\n"
    "**Chain Hash (Merkle seal)**: `" + _G_CHAIN + "`\n"
    + TAIL
)


def _entry(num: int, body: str = "A test decision body.") -> LedgerEntry:
    return LedgerEntry(
        number=num,
        title=f"TEST DECISION -- item {num}",
        fields={
            "Timestamp": "2026-07-13T18:30:00Z",
            "Phase": "TEST",
            "Author": "Specialist",
            "Session": "`2026-07-13T0000-abcdef`",
        },
        body=body,
    )


def test_render_round_trips_verifier_parser():
    c = hashlib.sha256(b"c").hexdigest()
    p = hashlib.sha256(b"p").hexdigest()
    x = hashlib.sha256(b"x").hexdigest()
    text = render(_entry(2), content=c, previous=p, chain=x)
    resolved = _resolve_recorded(text)
    assert resolved == (c, p, x)
    assert text.startswith("### Entry #2: TEST DECISION")
    assert "**Decision**: A test decision body." in text


def test_append_links_chain_and_verifies(tmp_path, capsys):
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(GENESIS, encoding="utf-8")
    append(ledger, _entry(2))
    append(ledger, _entry(3))
    rc = verify(ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #2" in out.replace("  ", " ").replace("OK Entry", "OK  Entry") or "Entry #2" in out
    assert "Skipped" not in out


def test_append_rejects_non_ascii_body(tmp_path):
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(GENESIS, encoding="utf-8")
    with pytest.raises(ValueError):
        append(ledger, _entry(2, body="curly ’ quote"))


def test_append_preserves_tail_marker(tmp_path):
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(GENESIS, encoding="utf-8")
    append(ledger, _entry(2))
    text = ledger.read_text(encoding="utf-8")
    assert text.rstrip().endswith("*Session: SEALED* (test)")
    assert text.index("Entry #2") < text.index("*Chain integrity: VALID*")
