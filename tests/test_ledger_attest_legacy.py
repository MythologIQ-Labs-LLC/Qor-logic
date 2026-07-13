"""Phase 193 (GH #278): retroactive attestation of the pre-convention band."""
from __future__ import annotations

from pathlib import Path

from qor.scripts.ledger_attest_legacy import (
    build_attestation_entry,
    collect_unverifiable,
    write_attestation,
)
from qor.scripts.ledger_hash import chain_hash, verify

REPO_ROOT = Path(__file__).resolve().parent.parent

TAIL = "\n---\n\n*Chain integrity: VALID*\n"

import hashlib

_M_CONTENT = hashlib.sha256(b"modern-content").hexdigest()
_M_PREV = hashlib.sha256(b"modern-prev").hexdigest()
_M_CHAIN = chain_hash(_M_CONTENT, _M_PREV)

LEGACY_LEDGER = (
    "# Meta Ledger\n\n"
    "### Entry #1: OLD DECISION\n\n"
    "prose only, no hash markup at all\n\n---\n\n"
    "### Entry #2: OLD RESEARCH\n\n"
    "also markup-free legacy prose\n\n---\n\n"
    "### Entry #3: OLD SEAL\n\n"
    "third legacy body\n\n---\n\n"
    "### Entry #4: MODERN\n\n"
    "**Content Hash**: `" + _M_CONTENT + "`\n"
    "**Previous Hash**: `" + _M_PREV + "`\n"
    "**Chain Hash (Merkle seal)**: `" + _M_CHAIN + "`\n"
    + TAIL
)


def _fixture(tmp_path: Path) -> Path:
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text(LEGACY_LEDGER, encoding="utf-8")
    return ledger


def test_collect_matches_verify_skip_set(tmp_path, capsys):
    ledger = _fixture(tmp_path)
    verify(ledger)
    out = capsys.readouterr().out
    assert "Skipped 3 entries" in out
    collected = collect_unverifiable(ledger)
    assert [num for num, _ in collected] == [1, 2, 3]
    assert all(len(d) == 12 for _, d in collected)


def test_attestation_clears_skips(tmp_path, capsys):
    ledger = _fixture(tmp_path)
    write_attestation(ledger)
    rc = verify(ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "Skipped" not in out
    assert "attested by migration entry" in out


def test_tampered_legacy_body_fails_after_attestation(tmp_path, capsys):
    ledger = _fixture(tmp_path)
    write_attestation(ledger)
    text = ledger.read_text(encoding="utf-8")
    ledger.write_text(text.replace("third legacy body", "REWRITTEN history"),
                      encoding="utf-8")
    rc = verify(ledger)
    err = capsys.readouterr().err
    assert rc == 1
    assert "attestation digest mismatch" in err


def test_attestation_entry_itself_chain_verifies(tmp_path, capsys):
    ledger = _fixture(tmp_path)
    write_attestation(ledger)
    text = ledger.read_text(encoding="utf-8")
    assert "MIGRATION ATTESTATION" in text
    rc = verify(ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "Entry #5" in out  # the migration entry verifies like any modern entry


def test_live_ledger_zero_skips(capsys):
    """RED until the LD-4 live migration lands in this session's seal."""
    rc = verify(REPO_ROOT / "docs" / "META_LEDGER.md")
    out = capsys.readouterr().out
    assert rc == 0
    assert "Skipped" not in out, "live ledger still carries unattested legacy entries"
