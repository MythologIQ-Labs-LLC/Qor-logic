"""Tests for qor/scripts/ledger_hash.py (Phase 12 / S-11 closure).

Critical infrastructure: every audit/substantiate writes via this module.
Previously had zero direct test coverage.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import ledger_hash as lh


def _digest(seed: bytes) -> str:
    """Phase 66 helper: produce a real-shape SHA-256 digest for fixtures.
    Synthetic "a"*64 / "b"*64 fixtures trigger the placeholder detector
    introduced by GH #54 (Phase 66). Replace with hashlib.sha256 outputs.
    """
    import hashlib
    return hashlib.sha256(seed).hexdigest()

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
    Phase 23: chain_hash now uses "|" separator between content and prev.
    """
    import hashlib
    content = _digest(b"a")
    prev = _digest(b"b")
    # Compute expected via the same algorithm we're testing — inverts to identity check
    # but still validates the hash function isn't silently broken (e.g., returns "")
    expected = hashlib.sha256((content + "|" + prev).encode("utf-8")).hexdigest()
    assert lh.chain_hash(content, prev) == expected
    assert len(lh.chain_hash(content, prev)) == 64


def test_chain_hash_differs_on_content_change():
    prev = "0" * 64
    h1 = lh.chain_hash(_digest(b"a"), prev)
    h2 = lh.chain_hash(_digest(b"b"), prev)
    assert h1 != h2


def test_chain_hash_differs_on_prev_change():
    content = _digest(b"a")
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
    content_a = _digest(b"a")
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)
    content_b = _digest(b"b")
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


def test_verify_clean_synthetic_ledger(tmp_path, capsys):
    """Build a known-good 2-entry ledger; verify passes and both entries exercise chain math.

    Phase 41: uses bold-anchored `**Chain Hash**:` form. Capsys assertion
    guards against vacuous-green regression -- if a future regex change
    silently skips these entries, `OK   Entry #N:` lines disappear even
    though `rc == 0` is still satisfied by the skipped-no-errors path.
    """
    content_a = _digest(b"a")
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)
    content_b = _digest(b"b")
    chain_b = lh.chain_hash(content_b, chain_a)

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: TEST
**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
**Chain Hash**: `{chain_a}`

### Entry #2: TEST
**Content Hash**: `{content_b}`
**Previous Hash**: `{chain_a}`
**Chain Hash**: `{chain_b}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #1:" in out
    assert "OK   Entry #2:" in out


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

def test_verify_handles_non_monotonic_entry_numbers(tmp_path, capsys):
    """Verify() doesn't crash if entry numbers are not strictly monotonic.

    Real ledgers may have skipped or out-of-order numbers due to history rewrites
    or manual entry corrections. Parser must process each entry independently.

    Phase 41: uses bold-anchored `**Chain Hash**:` form with capsys assertion to
    guard against vacuous-green regression.
    """
    content_a = _digest(b"a")
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #5: OUT OF ORDER

**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
**Chain Hash**: `{chain_a}`

### Entry #2: EARLIER NUMBER LATER

**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
**Chain Hash**: `{chain_a}`
""", encoding="utf-8")
    # Should not crash on out-of-order numbers
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #5:" in out
    assert "OK   Entry #2:" in out


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


def test_verify_accepts_inline_backtick_chain_hash(tmp_path):
    """Chain hashes written as `` `<hex>` `` verify identically to `= <hex>` form.

    Ensures the canonical inline-backtick markup (symmetric with Content/Previous)
    is accepted by the verifier. Regression test for downstream projects whose
    ledgers adopt the inline form to satisfy all three hash-field regexes with
    one consistent markup.
    """
    content_a = _digest(b"a")
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)
    content_b = _digest(b"b")
    chain_b = lh.chain_hash(content_b, chain_a)

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: INLINE-BACKTICK CHAIN
**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
**Chain Hash**: `{chain_a}`

### Entry #2: ALSO INLINE
**Content Hash**: `{content_b}`
**Previous Hash**: `{chain_a}`
**Chain Hash**: `{chain_b}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    assert rc == 0


def test_verify_accepts_mixed_chain_hash_forms(tmp_path, capsys):
    """A ledger with one fenced `= <hex>` entry and one inline `` `<hex>` `` entry verifies clean.

    Phase 41: equation-form entry is bold-anchored and fenced (the only form
    the stricter regex accepts for `= <hex>`). Capsys assertion guards against
    vacuous-green regression.
    """
    content_a = _digest(b"a")
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)
    content_b = _digest(b"b")
    chain_b = lh.chain_hash(content_b, chain_a)

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: EQUATION FORM
**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
**Chain Hash**:
```
SHA256(content_hash + previous_hash)
= {chain_a}
```

### Entry #2: INLINE FORM
**Content Hash**: `{content_b}`
**Previous Hash**: `{chain_a}`
**Chain Hash**: `{chain_b}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #1:" in out
    assert "OK   Entry #2:" in out


def test_verify_detects_tampered_inline_backtick_chain(tmp_path):
    """Inline-backtick chain with a wrong hash should still be detected as FAIL."""
    content_a = _digest(b"a")
    prev_a = "0" * 64
    wrong_chain = "deadbeef" * 8  # 64 hex but wrong

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: TAMPERED INLINE
**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
**Chain Hash**: `{wrong_chain}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    assert rc == 1


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


# ----- Phase 41 regression tests (issue #13) -----

def test_verify_chain_anchor_rejects_prose_mention(tmp_path, capsys):
    """Prose containing the phrase 'Chain Hash' must not capture unrelated backtick-hex.

    Under the pre-Phase-41 regex, CHAIN_HASH_RE lacked the **...** bold anchor,
    so prose like 'the chain hash is then computed' captured the first
    backtick-hex that followed -- often the content_hash value from an earlier
    field. The stricter anchor `\\*\\*Chain Hash\\*\\*` rejects prose mentions.
    """
    content_a = _digest(b"a")
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)
    unrelated_hex = _digest(b"c")  # appears in prose, must not be captured

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: PROSE MENTION

**Decision**: The Chain Hash field below is the load-bearing value; `{unrelated_hex}` in this sentence is prose only.

**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
**Chain Hash**: `{chain_a}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #1:" in out


def test_verify_fenced_content_with_trailing_inline_hash(tmp_path, capsys):
    """Fenced Content Hash must not bleed into a later inline-backtick hex field.

    Pre-Phase-41 behavior: CONTENT_HASH_RE only accepted inline-backtick form,
    so with a fenced Content Hash the regex would silently sweep forward under
    re.DOTALL and capture a later Plan Hash's backtick-hex value as content.
    """
    content_a = _digest(b"a")
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)
    plan_hex = _digest(b"d")  # unrelated; must not be captured as content

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: FENCED CONTENT + INLINE PLAN

**Content Hash**:
```
SHA256(stuff)
= {content_a}
```

**Previous Hash**: `{prev_a}`
**Chain Hash**: `{chain_a}`
**Plan Hash**: `{plan_hex}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #1:" in out


def test_verify_fenced_previous_with_trailing_inline_hash(tmp_path, capsys):
    """Fenced Previous Hash must not bleed into a later inline-backtick hex field."""
    content_a = _digest(b"a")
    prev_a = _digest(b"f")
    chain_a = lh.chain_hash(content_a, prev_a)
    plan_hex = _digest(b"d")

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: FENCED PREVIOUS + INLINE PLAN

**Content Hash**: `{content_a}`
**Previous Hash**:
```
SHA256(prior entry content)
= {prev_a}
```

**Chain Hash**: `{chain_a}`
**Plan Hash**: `{plan_hex}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #1:" in out


def test_verify_bounded_span_stops_at_next_field(tmp_path, capsys):
    """When a field's hex value is absent, the regex must not sweep into the next field.

    Entry has broken markup: Content Hash header with no hex value before the
    next **Previous Hash** marker. The bounded span stops at the next
    `\\*\\*FieldName\\*\\*` marker; CONTENT_HASH_RE returns None; the entry is
    routed to the skipped counter rather than falsely verified with Previous
    Hash's value captured as content.
    """
    prev_a = "0" * 64
    chain_mismatch = _digest(b"e")  # unrelated to any valid chain computation

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: BROKEN MARKUP

**Content Hash**:

**Previous Hash**: `{prev_a}`
**Chain Hash**: `{chain_mismatch}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out + capsys.readouterr().err
    # Entry must be skipped (no content hash), not FAIL on bogus chain math
    assert rc == 0
    assert "OK   Entry #1:" not in out
    assert "FAIL Entry #1" not in out


def test_verify_accepts_fenced_content_hash(tmp_path, capsys):
    """**Content Hash** in fenced `= <hex>` form verifies clean (symmetric with chain hash)."""
    content_a = _digest(b"a")
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: FENCED CONTENT
**Content Hash**:
```
SHA256(file bytes)
= {content_a}
```
**Previous Hash**: `{prev_a}`
**Chain Hash**: `{chain_a}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #1:" in out


def test_verify_accepts_fenced_previous_hash(tmp_path, capsys):
    """**Previous Hash** in fenced `= <hex>` form verifies clean."""
    content_a = _digest(b"a")
    prev_a = _digest(b"f")
    chain_a = lh.chain_hash(content_a, prev_a)

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: FENCED PREVIOUS
**Content Hash**: `{content_a}`
**Previous Hash**:
```
SHA256(prior content)
= {prev_a}
```
**Chain Hash**: `{chain_a}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #1:" in out


def test_verify_accepts_mixed_content_hash_forms(tmp_path, capsys):
    """A ledger mixing inline-backtick and fenced Content Hash forms verifies clean."""
    content_a = _digest(b"a")
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)
    content_b = _digest(b"b")
    chain_b = lh.chain_hash(content_b, chain_a)

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: FENCED CONTENT
**Content Hash**:
```
SHA256(file bytes)
= {content_a}
```
**Previous Hash**: `{prev_a}`
**Chain Hash**: `{chain_a}`

### Entry #2: INLINE CONTENT
**Content Hash**: `{content_b}`
**Previous Hash**: `{chain_a}`
**Chain Hash**: `{chain_b}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #1:" in out
    assert "OK   Entry #2:" in out


def test_verify_real_ledger_still_passes():
    """Regression: the repo's own docs/META_LEDGER.md still verifies after regex changes.

    Guards against regressions introduced by the new bounded-span rule and
    anchor tightening. If this fails after the Phase 41 patch, the regex
    changes have broken the load-bearing real ledger.
    """
    rc = lh.verify(LEDGER_MD)
    assert rc == 0


# ----- Phase 44 regression tests (parenthetical-suffix on hash labels) -----

def test_verify_accepts_chain_hash_with_merkle_seal_suffix(tmp_path, capsys):
    """`**Chain Hash (Merkle seal)**:` is the standard SESSION SEAL convention.

    Phase 41's strict `\\*\\*Chain Hash\\*\\*` anchor missed this form and
    silently skipped 7+ ledger entries. Phase 44 relaxes the anchor to accept
    an optional parenthetical suffix inside the bold markers.
    """
    content_a = _digest(b"a")
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: SESSION SEAL
**Content Hash**: `{content_a}`
**Previous Hash**: `{prev_a}`
**Chain Hash (Merkle seal)**: `{chain_a}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #1:" in out


def test_verify_accepts_content_hash_with_session_seal_suffix(tmp_path, capsys):
    """`**Content Hash (session seal)**:` is the SESSION SEAL convention paired with Chain Hash."""
    content_a = _digest(b"a")
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: SESSION SEAL
**Content Hash (session seal)**: `{content_a}`
**Previous Hash**: `{prev_a}`
**Chain Hash (Merkle seal)**: `{chain_a}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #1:" in out


def test_verify_accepts_previous_hash_with_arbitrary_suffix(tmp_path, capsys):
    """Symmetric handling: Previous Hash with parenthetical suffix also matches.

    Real ledgers don't use this convention for Previous Hash today, but the
    regex change applies symmetrically; this test guards against future drift.
    """
    content_a = _digest(b"a")
    prev_a = "0" * 64
    chain_a = lh.chain_hash(content_a, prev_a)

    fake_ledger = tmp_path / "ledger.md"
    fake_ledger.write_text(f"""### Entry #1: SESSION SEAL
**Content Hash**: `{content_a}`
**Previous Hash (sealed reference)**: `{prev_a}`
**Chain Hash**: `{chain_a}`
""", encoding="utf-8")
    rc = lh.verify(fake_ledger)
    out = capsys.readouterr().out
    assert rc == 0
    assert "OK   Entry #1:" in out


def test_verify_real_ledger_seal_entries_verify_clean(capsys):
    """Anti-vacuous-green guard: every modern SESSION SEAL entry must verify (not skip).

    Phase 41's regex tightening silently skipped seal entries with parenthetical
    field labels (`**Chain Hash (Merkle seal)**:`); the original Phase 41 test
    only asserted `rc == 0`, which was satisfied by silent skip rather than
    verified chain. This test counts verified entries against a known list of
    SESSION SEAL entry numbers and would have caught the regression.
    """
    rc = lh.verify(LEDGER_MD)
    out = capsys.readouterr().out
    assert rc == 0

    # SESSION SEAL entries with the parenthetical-suffix convention (post-Phase-23 modern format).
    # Hard-coded list reflects current state of docs/META_LEDGER.md; if a future seal entry uses a
    # different convention, this list must be updated explicitly (anti-vacuous-green by design).
    expected_seal_entries = [126, 129, 132, 133, 137, 140, 143]
    for entry_num in expected_seal_entries:
        assert f"OK   Entry #{entry_num}:" in out, (
            f"SESSION SEAL entry #{entry_num} did not verify; suggests regex regression "
            f"on parenthetical field labels."
        )


def test_verify_real_ledger_no_silent_skips_for_modern_entries(capsys):
    """Generalization: every modern entry (>= #116) with hash markup must verify, not skip.

    Whitelist below documents legitimate exceptions — entries that genuinely lack the
    three hash fields by design (e.g., narrative-only entries between sealed phases).
    Any modern numbered entry not in the whitelist and not in the OK output indicates
    a regex regression.
    """
    import re as _re
    text = LEDGER_MD.read_text(encoding="utf-8")
    parts = lh.ENTRY_RE.split(text)

    # Whitelist of modern entries that legitimately lack one of the three hash fields.
    # Each entry is a narrative or bookkeeping record without full chain markup.
    legitimate_skip_whitelist = {
        # Currently empty: all modern hash-bearing entries should verify.
        # If a new narrative entry is added without hash markup, document it here
        # with a one-line rationale.
    }

    rc = lh.verify(LEDGER_MD)
    out = capsys.readouterr().out
    assert rc == 0

    modern_entries_with_hash_markup = []
    for i in range(1, len(parts), 2):
        num = int(parts[i])
        if num < 116:
            continue
        body = parts[i + 1] if i + 1 < len(parts) else ""
        # An entry "has hash markup" if it contains at least one bold "Hash" field marker.
        if _re.search(r"\*\*(Content Hash|Previous Hash|Chain Hash)", body):
            modern_entries_with_hash_markup.append(num)

    silent_skips = []
    for num in modern_entries_with_hash_markup:
        if num in legitimate_skip_whitelist:
            continue
        if f"OK   Entry #{num}:" not in out:
            silent_skips.append(num)

    assert not silent_skips, (
        f"Modern entries with hash markup that did NOT verify (silent skip):\n  "
        + "\n  ".join(f"#{n}" for n in silent_skips)
        + "\nAdd to legitimate_skip_whitelist with rationale, or fix the regex."
    )
