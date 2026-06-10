"""Phase 153 (GAP-CQ-02): direct unit tests for the helpers extracted from
ledger_hash.verify(). The 5 existing ledger-hash test files cover verify()
end-to-end (behavior preservation); these pin the extracted units directly.
"""
from __future__ import annotations

import hashlib

from qor.scripts.ledger_hash import (
    _classify_entry,
    _resolve_recorded,
    chain_hash,
)


def _h(seed: str) -> str:
    # random-looking sha256 hex: >6 distinct chars so it is NOT a placeholder pattern
    return hashlib.sha256(seed.encode()).hexdigest()


def test_resolve_recorded_canonical():
    c, p = _h("content"), _h("prev")
    x = _h("chain")
    body = (
        f"**Content Hash**: `{c}`\n"
        f"**Previous Hash**: `{p}`\n"
        f"**Chain Hash (Merkle seal)**: `{x}`\n"
    )
    assert _resolve_recorded(body) == (c, p, x)
    # neither canonical markup nor a Session-Seal line -> non-verifiable (skip)
    assert _resolve_recorded("just prose, no hashes here\n") is None


def test_classify_ok_and_fail():
    c, p = _h("c"), _h("p")
    ok = chain_hash(c, p)
    msg, stderr, err, setlf = _classify_entry(
        7, c, p, ok, grandfathered=frozenset(), reconciled=frozenset(), last_failed=0)
    assert msg.startswith("OK") and stderr is False and err is False and setlf is False
    msg, stderr, err, setlf = _classify_entry(
        8, c, p, _h("wrong"), grandfathered=frozenset(), reconciled=frozenset(), last_failed=0)
    assert msg.startswith("FAIL") and stderr is True and err is True and setlf is True


def test_classify_taint_after_failure():
    c, p = _h("c"), _h("p")
    ok = chain_hash(c, p)  # would be OK in isolation
    msg, stderr, err, setlf = _classify_entry(
        9, c, p, ok, grandfathered=frozenset(), reconciled=frozenset(), last_failed=5)
    # tainted: error, names the original predecessor, but does NOT advance last_failed
    assert msg.startswith("TAINTED") and "#5" in msg and err is True and setlf is False


def test_classify_grandfathered_and_reconciled():
    c, p = _h("c"), _h("p")
    bad = _h("mismatch")  # math fails
    gf = _classify_entry(50, c, p, bad, grandfathered=frozenset({50}), reconciled=frozenset(), last_failed=0)
    assert gf[0].startswith("DISCLOSED_GRANDFATHERED") and gf[2] is False
    rc = _classify_entry(60, c, p, bad, grandfathered=frozenset(), reconciled=frozenset({60}), last_failed=0)
    assert rc[0].startswith("DISCLOSED_RECONCILED") and rc[2] is False
