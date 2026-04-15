"""Tests for qor/scripts/ledger_hash.py (Phase 12 / S-11 closure).

Critical infrastructure: every audit/substantiate writes via this module.
Previously had zero direct test coverage.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import ledger_hash as lh

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_MD = REPO_ROOT / "docs" / "META_LEDGER.md"


# ----- content_hash -----

def test_content_hash_deterministic(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"identical content")
    h1 = lh.content_hash(p)
    h2 = lh.content_hash(p)
    assert h1 == h2
    assert len(h1) == 64


def test_content_hash_changes_on_byte_diff(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"hello")
    b.write_bytes(b"hellp")  # one byte different
    assert lh.content_hash(a) != lh.content_hash(b)


def test_content_hash_known_value(tmp_path):
    """SHA256 of 'abc' is a well-known value — sanity check the algorithm."""
    p = tmp_path / "f.txt"
    p.write_bytes(b"abc")
    expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert lh.content_hash(p) == expected


# ----- chain_hash -----

def test_chain_hash_recomputable_synthetic():
    """Chain hash recomputes correctly against synthetic inputs (no live-state coupling).

    Per doctrine-test-discipline.md Rule 3: tests must not assert against live ledger
    entries that change outside the test. Use synthetic inputs with computed expected.
    """
    import hashlib
    content = "a" * 64
    prev = "b" * 64
    # Compute expected via the same algorithm we're testing — inverts to identity check
    # but still validates the hash function isn't silently broken (e.g., returns "")
    expected = hashlib.sha256((content + prev).encode("utf-8")).hexdigest()
    assert lh.chain_hash(content, prev) == expected
    assert len(lh.chain_hash(content, prev)) == 64


def test_chain_hash_differs_on_content_change():
    prev = "0" * 64
    h1 = lh.chain_hash("a" * 64, prev)
    h2 = lh.chain_hash("b" * 64, prev)
    assert h1 != h2


def test_chain_hash_differs_on_prev_change():
    content = "a" * 64
    h1 = lh.chain_hash(content, "0" * 64)
    h2 = lh.chain_hash(content, "1" * 64)
    assert h1 != h2


# ----- write_manifest -----

def test_write_manifest_sorted_by_path(tmp_path):
    (tmp_path / "z.txt").write_bytes(b"z")
    (tmp_path / "a.txt").write_bytes(b"a")
    (tmp_path / "m.txt").write_bytes(b"m")
    out = tmp_path / "manifest.json"
    manifest = lh.write_manifest(tmp_path, ["*.txt"], out)
    paths = [p["path"] for p in manifest["paths"]]
    assert paths == sorted(paths)
    assert paths == ["a.txt", "m.txt", "z.txt"]


def test_write_manifest_includes_glob_matches(tmp_path):
    (tmp_path / "include.txt").write_bytes(b"x")
    (tmp_path / "exclude.md").write_bytes(b"x")
    out = tmp_path / "manifest.json"
    manifest = lh.write_manifest(tmp_path, ["*.txt"], out)
    paths = [p["path"] for p in manifest["paths"]]
    assert "include.txt" in paths
    assert "exclude.md" not in paths


def test_write_manifest_recurses_directories(tmp_path):
    sub = tmp_path / "sub" / "deeper"
    sub.mkdir(parents=True)
    (sub / "nested.txt").write_bytes(b"nested")
    out = tmp_path / "manifest.json"
    manifest = lh.write_manifest(tmp_path, ["sub/**"], out)
    paths = [p["path"] for p in manifest["paths"]]
    assert "sub/deeper/nested.txt" in paths


def test_write_manifest_reproducible(tmp_path):
    """Same input tree → same manifest content (excluding generated_ts)."""
    for name in ("a", "b", "c"):
        (tmp_path / f"{name}.txt").write_bytes(name.encode())
    out1 = tmp_path / "m1.json"
    out2 = tmp_path / "m2.json"
    m1 = lh.write_manifest(tmp_path, ["*.txt"], out1)
    m2 = lh.write_manifest(tmp_path, ["*.txt"], out2)
    # Strip ts which differs by run; everything else identical
    m1.pop("generated_ts")
    m2.pop("generated_ts")
    assert m1 == m2


def test_write_manifest_uses_os_replace(tmp_path, monkeypatch):
    """Write goes through os.replace (atomicity is an os-level guarantee delegated to stdlib).

    Renamed from test_write_manifest_atomic_write per Phase 12 v2 audit V-3:
    the test verifies os.replace is called, not actual atomicity (which would
    require simulating mid-write failure — out of scope for this unit).
    """
    import os
    (tmp_path / "x.txt").write_bytes(b"x")
    out = tmp_path / "manifest.json"

    real_replace = os.replace
    calls = []
    def spy_replace(src, dst):
        calls.append((src, dst))
        real_replace(src, dst)
    monkeypatch.setattr(os, "replace", spy_replace)

    lh.write_manifest(tmp_path, ["*.txt"], out)
    assert len(calls) == 1
    assert calls[0][1] == out


# ----- verify against real ledger -----

def test_verify_passes_on_current_ledger():
    """Verify the actual repo ledger; should exit 0."""
    rc = lh.verify(LEDGER_MD)
    assert rc == 0, "Current docs/META_LEDGER.md chain must verify clean"


def test_verify_detects_tampered_chain_hash(tmp_path):
    """Flip one chain hash byte; verify should fail."""
    fake_ledger = tmp_path / "ledger.md"
    # Build a minimal valid 2-entry ledger
    content_a = "a" * 64
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)
    content_b = "b" * 64
    chain_b = lh.chain_hash(content_b, chain_a)

    fake_ledger.write_text(f"""# Test ledger

### Entry #1: TEST

**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
**Chain Hash**:
```
SHA256(content_hash + previous_hash)
= {chain_a}
```

### Entry #2: TEST

**Content Hash**: `{content_b}`
**Previous Hash**: `{chain_a}`
**Chain Hash**:
```
SHA256(content_hash + previous_hash)
= deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef
```
""", encoding="utf-8")

    rc = lh.verify(fake_ledger)
    assert rc == 1


def test_verify_clean_synthetic_ledger(tmp_path):
    """Build a known-good 2-entry ledger; verify passes."""
    content_a = "a" * 64
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)
    content_b = "b" * 64
    chain_b = lh.chain_hash(content_b, chain_a)

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: TEST
**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
Chain Hash = {chain_a}

### Entry #2: TEST
**Content Hash**: `{content_b}`
**Previous Hash**: `{chain_a}`
Chain Hash = {chain_b}
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    assert rc == 0


def test_verify_skips_entries_without_required_markers(tmp_path):
    """Entries lacking Content/Previous/Chain hash markup are skipped, not failed."""
    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text("""### Entry #1: ANCIENT

**Decision**: this entry is from before the chain hash convention.

### Entry #2: MODERN

**Content Hash**: `aaaa...` is malformed; should also be skipped quietly.
""", encoding="utf-8")
    # Should not crash; should return 0 (no errors)
    rc = lh.verify(fake_ledger)
    assert rc == 0


# ----- V-10 (Phase 12 v2 audit) parser-robustness tests, split per V-B -----

def test_verify_handles_non_monotonic_entry_numbers(tmp_path):
    """Verify() doesn't crash if entry numbers are not strictly monotonic.

    Real ledgers may have skipped or out-of-order numbers due to history rewrites
    or manual entry corrections. Parser must process each entry independently.
    """
    content_a = "a" * 64
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #5: OUT OF ORDER

**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
Chain Hash = {chain_a}

### Entry #2: EARLIER NUMBER LATER

**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
Chain Hash = {chain_a}
""", encoding="utf-8")
    # Should not crash on out-of-order numbers
    rc = lh.verify(fake_ledger)
    assert rc == 0


def test_verify_handles_missing_hash_markers_gracefully(tmp_path):
    """Verify() skips entries with no Content/Previous/Chain markers (e.g., legacy)."""
    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text("""### Entry #1: LEGACY

**Decision**: This is a pre-chain entry; no hashes recorded.

### Entry #2: ALSO LEGACY

**Author**: Governor
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    assert rc == 0  # No errors; entries are skipped, not failed


def test_verify_handles_malformed_numeric_id(tmp_path):
    """Verify() processes entry headers even if surrounding markup is unusual.

    The ENTRY_RE only matches digits. Non-numeric or hex IDs in entry headers
    won't match the pattern and are simply skipped.
    """
    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text("""### Entry #ABC: NON-NUMERIC

**Decision**: Should not be matched by parser.

### Entry #99: VALID

**Decision**: Valid entry but no hash markers; skipped quietly.
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    assert rc == 0  # No crash, no errors
