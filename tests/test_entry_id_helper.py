"""Phase 76 P1: entry_id helper tests (GH #51)."""
from __future__ import annotations

import os

import pytest

from qor.scripts import entry_id


def test_derive_entry_id_deterministic():
    a = entry_id.derive_entry_id("2026-05-14T22:00:00Z", "substantiate", "a" * 64)
    b = entry_id.derive_entry_id("2026-05-14T22:00:00Z", "substantiate", "a" * 64)
    assert a == b
    assert len(a) == 12
    assert all(c in "0123456789abcdef" for c in a)


def test_derive_entry_id_distinguishes_inputs():
    seen = set()
    for i in range(1000):
        h = format(i, "064x")
        seen.add(entry_id.derive_entry_id("2026-05-14T22:00:00Z", "substantiate", h))
    assert len(seen) == 1000, f"Expected 1000 unique IDs from 1000 distinct content_hashes; got {len(seen)}"


def test_derive_entry_id_full_hash_mode_via_env_var(monkeypatch):
    monkeypatch.setenv("QOR_ENTRY_ID_FULL_HASH", "1")
    eid = entry_id.derive_entry_id("2026-05-14T22:00:00Z", "substantiate", "a" * 64)
    assert len(eid) == 64
    assert all(c in "0123456789abcdef" for c in eid)
