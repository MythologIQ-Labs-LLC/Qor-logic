"""Phase 145 (GH #201 follow-on): seal_entry_check fails closed when the latest
SESSION SEAL entry carries non-ASCII or invalid-UTF-8 bytes.
"""
from __future__ import annotations

import hashlib

from qor.reliability import seal_entry_check as sec
from qor.scripts import ledger_hash


def _h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _ledger(body: str, *, content=None, prev=None, chain=None, phase=99) -> str:
    content = content or _h("c")
    prev = prev or _h("p")
    chain = chain if chain is not None else ledger_hash.chain_hash(content, prev)
    return (
        "# Meta Ledger\n\n"
        f"### Entry #1: SESSION SEAL -- Phase {phase} demo\n\n"
        f"**Content Hash**: `{content}`\n"
        f"**Previous Hash**: `{prev}`\n"
        f"**Chain Hash (Merkle seal)**: `{chain}`\n\n"
        f"{body}\n"
    )


def test_non_ascii_latest_entry_fails(tmp_path):
    led = tmp_path / "META_LEDGER.md"
    led.write_text(_ledger("decision body with an em-dash \u2014 here"), encoding="utf-8")
    result = sec.check(ledger_path=led, phase_num=99)
    assert result.ok is False
    assert any("U+2014" in e for e in result.errors), result.errors


def test_clean_ascii_latest_entry_passes(tmp_path):
    led = tmp_path / "META_LEDGER.md"
    led.write_text(_ledger("clean ascii decision body -- ok"), encoding="utf-8")
    result = sec.check(ledger_path=led, phase_num=99)
    assert result.ok is True, result.errors


def test_invalid_utf8_ledger_fails_closed(tmp_path):
    led = tmp_path / "META_LEDGER.md"
    # Write raw invalid-UTF-8 bytes (0x92 is the cp1252 smart-quote origin byte).
    led.write_bytes(_ledger("deliver  seal").encode("utf-8").replace(b"deliver  seal", b"deliver \x92 seal"))
    result = sec.check(ledger_path=led, phase_num=99)
    assert result.ok is False  # must not raise UnicodeDecodeError
