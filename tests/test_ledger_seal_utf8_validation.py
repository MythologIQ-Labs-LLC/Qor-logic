"""Behavioral tests for the ledger-seal UTF-8/ASCII validity gate (GH #201).

Each test invokes the unit (``assert_sealable_text`` / ``normalize_punctuation``
/ ``write_fragment`` / ``canonicalize_fragments``) and asserts on the raised
error, the returned value, or the observable filesystem side-effect -- not on
artifact presence alone. Non-ASCII inputs are built from ``\\u`` escapes so this
test source stays pure ASCII.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from qor.scripts import ledger_fragment, ledger_hash
from qor.scripts.ledger_fragment import LedgerFragment


def test_assert_sealable_rejects_em_dash_with_codepoint_and_index():
    bad = "a \u2014 b"  # em-dash at index 2
    with pytest.raises(ValueError) as exc:
        ledger_hash.assert_sealable_text(bad)
    msg = str(exc.value)
    assert "U+2014" in msg
    assert "index 2" in msg


def test_assert_sealable_accepts_clean_ascii():
    assert ledger_hash.assert_sealable_text("plain ascii body -- ok") is None


def test_normalize_punctuation_maps_to_ascii_and_is_idempotent():
    raw = "\u2014\u2013\u2019\u201c\u201d\u2192\u2026"
    out = ledger_hash.normalize_punctuation(raw)
    assert out.isascii()
    assert ledger_hash.normalize_punctuation(out) == out
    assert ledger_hash.normalize_punctuation("a\u2014b") == "a--b"
    assert ledger_hash.normalize_punctuation("a\u2192b") == "a->b"


def _frag(body: str) -> LedgerFragment:
    return LedgerFragment(
        uid="le_0123456789abcdef",
        ts="2026-06-09T00:00:00Z",
        session_id="2026-06-09T0000-test",
        title="TEST",
        body=body,
        content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
    )


def test_write_fragment_rejects_non_ascii_body(tmp_path):
    frag = _frag("body with \u2019 smart quote")
    with pytest.raises(ValueError) as exc:
        ledger_fragment.write_fragment(tmp_path, frag)
    assert "U+2019" in str(exc.value)
    written = tmp_path / ".qor" / "ledger" / "fragments" / "le_0123456789abcdef.json"
    assert not written.exists()


def test_canonicalize_rejects_non_ascii_and_leaves_ledger_unchanged(tmp_path):
    ledger = tmp_path / "META_LEDGER.md"
    original = "# Meta Ledger\n\n### Entry #1: SEED\n\nbody\n"
    ledger.write_text(original, encoding="utf-8")
    frag_dir = tmp_path / ".qor" / "ledger" / "fragments"
    frag_dir.mkdir(parents=True)
    # Simulate a rogue cp1252 writer that bypassed write_fragment's gate.
    bad_body = "deliver \u0092 seal"  # U+0092: cp1252 smart-quote origin byte
    raw = {
        "uid": "le_0123456789abcdef",
        "ts": "2026-06-09T00:00:00Z",
        "session_id": "s",
        "title": "BAD",
        "body": bad_body,
        "content_hash": hashlib.sha256(bad_body.encode("utf-8")).hexdigest(),
    }
    (frag_dir / "le_0123456789abcdef.json").write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError):
        ledger_fragment.canonicalize_fragments(ledger, tmp_path)
    # The ledger write must not have happened.
    assert ledger.read_text(encoding="utf-8") == original
    # The fragment must remain pending (not consumed/archived).
    pending = ledger_fragment.read_fragments(tmp_path)
    assert len(pending) == 1
    assert pending[0].uid == "le_0123456789abcdef"
