"""GH #361: a duplicated entry number, or two entries that each honestly
chain off the same predecessor (a merged ledger fork), must not verify
clean. Both classes were previously invisible:

- ``verify()``'s sequence-break check unconditionally tolerated ANY
  duplicate-previous_hash member, with no attestation or cutoff gate --
  disarming the one check that could catch a fork, since each branch is
  individually valid by per-entry chain math.
- ``verify_post_anchor()`` (the release-gate surface the issue's own repro
  targets) never checked sequence continuity or duplicate numbers at all;
  two occurrences of the same #N each classify "ok" independently.

Per doctrine-test-functionality.md, assertions check exit code and
stdout/stderr, not section presence.
"""
from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from qor.scripts.ledger_hash import chain_hash, verify, verify_post_anchor

GENESIS = "0" * 64


def _entry(num: int, content: str, previous: str, chain: str) -> str:
    return (
        f"### Entry #{num}: TEST\n\n"
        f"**Content Hash**: `{content}`\n\n"
        f"**Previous Hash**: `{previous}`\n\n"
        f"**Chain Hash**: `{chain}`\n\n"
    )


def _hex(seed: str) -> str:
    import hashlib
    return hashlib.sha256(seed.encode()).hexdigest()


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "META_LEDGER.md"
    p.write_text(text, encoding="utf-8")
    return p


def _capture_verify(ledger_path: Path):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = verify(ledger_path)
    return rc, out.getvalue(), err.getvalue()


def _capture_post_anchor(ledger_path: Path, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = verify_post_anchor(ledger_path, **kwargs)
    return rc, out.getvalue(), err.getvalue()


def test_verify_flags_unattested_fork_previously_tolerated_by_bare_duplicate_previous_hash(tmp_path):
    """Two entries (#2, #3) each honestly chain off #1's recorded hash -- a
    fork, not a legitimate two-child ledger. Neither is reconciled nor
    grandfathered (strict default, no --tolerate flag). Before the fix, bare
    duplicate-previous_hash membership silently exempted BOTH from the
    sequence-break check; after the fix, the second entry in file order
    (#3) must BREAK because its claimed previous_hash no longer matches the
    chain actually produced by its immediate file-order predecessor (#2)."""
    c1 = _hex("c1")
    ch1 = chain_hash(c1, GENESIS)
    c2 = _hex("c2-branch-a")
    ch2 = chain_hash(c2, ch1)
    c3 = _hex("c3-branch-b")
    ch3 = chain_hash(c3, ch1)  # forks off #1, same as #2 -- NOT off #2

    body = "# META_LEDGER\n" + _entry(1, c1, GENESIS, ch1) + _entry(2, c2, ch1, ch2) + _entry(3, c3, ch1, ch3)
    led = _write(tmp_path, body)
    rc, _out, err = _capture_verify(led)
    assert rc != 0, "an unattested ledger fork must not verify clean"
    assert "BREAK Entry #3" in err


def test_verify_still_passes_on_a_single_honest_chain(tmp_path):
    """Regression guard: a normal, non-forked chain has no duplicate
    previous_hash members at all, so the fix must not introduce a false
    BREAK on ordinary sequential entries."""
    c1 = _hex("s1")
    ch1 = chain_hash(c1, GENESIS)
    c2 = _hex("s2")
    ch2 = chain_hash(c2, ch1)
    c3 = _hex("s3")
    ch3 = chain_hash(c3, ch2)

    body = "# META_LEDGER\n" + _entry(1, c1, GENESIS, ch1) + _entry(2, c2, ch1, ch2) + _entry(3, c3, ch2, ch3)
    led = _write(tmp_path, body)
    rc, _out, err = _capture_verify(led)
    assert rc == 0, err


def test_verify_fails_on_duplicate_entry_number_with_fully_valid_chaining(tmp_path):
    """A duplicated #N reused later for an unrelated, honestly-chained entry
    (no fork -- pure renumbering mistake). Sequence continuity is perfect
    throughout, so only a dedicated duplicate-number check can catch it."""
    c1 = _hex("d1")
    ch1 = chain_hash(c1, GENESIS)
    c2 = _hex("d2")
    ch2 = chain_hash(c2, ch1)
    c3 = _hex("d3")
    ch3 = chain_hash(c3, ch2)
    c2_again = _hex("d2-reused-number")
    ch4 = chain_hash(c2_again, ch3)

    body = (
        "# META_LEDGER\n"
        + _entry(1, c1, GENESIS, ch1)
        + _entry(2, c2, ch1, ch2)
        + _entry(3, c3, ch2, ch3)
        + _entry(2, c2_again, ch3, ch4)  # duplicate number, valid chain math and sequence
    )
    led = _write(tmp_path, body)
    rc, _out, err = _capture_verify(led)
    assert rc != 0, "a duplicated entry number must FAIL even with valid chain math"
    assert "duplicate entry number" in err
    assert "[2]" in err


def test_post_anchor_detects_ledger_fork_at_boundary(tmp_path):
    """Issue #361's own repro, against the release-gate surface: two #3
    entries independently, honestly chain off #2. verify_post_anchor()
    must not report post-anchor clean."""
    c1 = _hex("p1")
    ch1 = chain_hash(c1, GENESIS)
    c2 = _hex("p2")
    ch2 = chain_hash(c2, ch1)
    c3a = _hex("p3-branch-a")
    ch3a = chain_hash(c3a, ch2)
    c3b = _hex("p3-branch-b")
    ch3b = chain_hash(c3b, ch2)

    body = (
        "# META_LEDGER\n"
        + _entry(1, c1, GENESIS, ch1)
        + _entry(2, c2, ch1, ch2)
        + _entry(3, c3a, ch2, ch3a)
        + _entry(3, c3b, ch2, ch3b)
    )
    led = _write(tmp_path, body)
    rc, out, err = _capture_post_anchor(led)
    full = out + err
    assert rc != 0, "a merged fork must not report post-anchor clean"
    assert "duplicate entry number" in full
    assert "FAIL Entry #3" in err


def test_post_anchor_tolerates_duplicate_number_strictly_before_boundary(tmp_path):
    """A duplicate entry number entirely pre-boundary (historical residual,
    operator has already pinned the boundary past it) is disclosed, not a
    hard failure -- consistent with every other pre-anchor tolerance in this
    module."""
    c1 = _hex("q1")
    ch1 = chain_hash(c1, GENESIS)
    c1_dup = _hex("q1-dup")
    ch1_dup = chain_hash(c1_dup, GENESIS)
    c2 = _hex("q2")
    ch2 = chain_hash(c2, ch1_dup)

    body = (
        "# META_LEDGER\n"
        + _entry(1, c1, GENESIS, ch1)
        + _entry(1, c1_dup, GENESIS, ch1_dup)
        + _entry(2, c2, ch1_dup, ch2)
    )
    led = _write(tmp_path, body)
    rc, out, _err = _capture_post_anchor(led, boundary_entry=2)
    assert rc == 0, "pre-boundary duplicate must be tolerated, not fail the gate"
    assert "DISCLOSED_PRE_ANCHOR Entry #1: duplicate entry number" in out
