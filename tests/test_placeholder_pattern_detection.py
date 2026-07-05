"""Phase 66 (#54): placeholder-pattern detection for SHA-256-shaped strings.

Distinguishes obvious-fabrication hex strings from real digests. Used by
`qor/scripts/ledger_hash.verify()` to flag entries whose recorded hashes
match well-known placeholder shapes (ascending hex, repeating bigrams,
low-entropy runs), preventing the GH #54 failure mode where downstream
entries chain-verify against an untrusted placeholder seed.

Acceptance question: "If the unit's behavior were silently broken but the
artifact still existed, would this test fail?" - yes. Each test
constructs a 64-hex input and calls `is_placeholder_pattern()`; reverting
the detector to return False unconditionally fails the positive cases,
and reverting to return True unconditionally fails the negative case.
"""
from __future__ import annotations

import hashlib

import pytest

from qor.scripts.ledger_hash import is_placeholder_pattern


def test_ascending_hex_pattern_detected():
    """Operator-fabricated '0123456789abcdef' shapes are obvious placeholders."""
    value = ("0123456789abcdef" * 4)
    assert len(value) == 64
    assert is_placeholder_pattern(value) is True


def test_repeating_bigram_detected():
    """A single repeating 2-char unit across 64 chars has near-zero entropy."""
    value = "a1" * 32
    assert len(value) == 64
    assert is_placeholder_pattern(value) is True


def test_gh54_failure_mode_pattern_detected():
    """The literal Issue #54 placeholder hash form must be flagged.

    Per the issue body, a sibling product's ledger Entry #331 carried
    `Content Hash: a1b2c3d4e5f6...` — ascending odd-position hex digits
    repeated across the 64-char span. This is the canonical example the
    detector must catch.
    """
    value = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
    assert len(value) == 64
    assert is_placeholder_pattern(value) is True


def test_real_sha256_digest_passes():
    """A real digest of arbitrary content must not be flagged."""
    real = hashlib.sha256(b"Phase 66 fixture content").hexdigest()
    assert len(real) == 64
    assert is_placeholder_pattern(real) is False


def test_low_entropy_threshold():
    """A 64-hex string using only 3 distinct chars is unrealistically low entropy."""
    value = ("aaa1aaa2" * 8)  # 8 chars per unit, 64 total; ~3-char vocab per window
    assert len(value) == 64
    assert is_placeholder_pattern(value) is True


def test_genuine_chain_hash_from_meta_ledger_passes():
    """Regression guard: known-good chain hashes from this repo's ledger must pass.

    Anchor: the Phase 64 seal entry's chain hash (Entry #198) is a real
    digest produced by qor.scripts.ledger_hash.chain_hash() at seal time.
    """
    real_chain = "72f4919d3b282b46bbf266013c1d8d2f88d2cad0311359fad4c4b5c9b81a6065"
    assert is_placeholder_pattern(real_chain) is False
