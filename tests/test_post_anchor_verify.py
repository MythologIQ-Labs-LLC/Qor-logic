"""Phase 66 (#55): verify_post_anchor mode for re-anchored consumer ledgers.

A re-anchored ledger has documented pre-anchor entries that the operator
has accepted as historical disclosures; the post-anchor surface is what
release gates check. verify_post_anchor() tolerates FAILs at entry ids
<= boundary and exits 0 when the post-boundary surface is clean.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from qor.scripts import ledger_hash as lh


def _digest(seed: bytes) -> str:
    return hashlib.sha256(seed).hexdigest()


def _entry(num: int, content: str, prev: str, chain: str) -> str:
    return (
        f"### Entry #{num}: TEST\n\n"
        f"**Content Hash**: `{content}`\n\n"
        f"**Previous Hash**: `{prev}`\n\n"
        f"**Chain Hash**: `{chain}`\n\n"
    )


def _write(tmp: Path, body: str) -> Path:
    p = tmp / "META_LEDGER.md"
    p.write_text(body, encoding="utf-8")
    return p


def _chain_genesis(content_seed: bytes) -> tuple[str, str, str]:
    """Build a single-entry chain anchored from all-zeros previous_hash."""
    content = _digest(content_seed)
    prev = "0" * 64
    chain = lh.chain_hash(content, prev)
    return content, prev, chain


def test_post_anchor_clean_when_pre_anchor_fails_tolerated(tmp_path, capsys):
    """Pre-boundary FAIL is reported DISCLOSED_PRE_ANCHOR; post-boundary is clean."""
    # Entry #1: clean genesis
    c1, p1, ch1 = _chain_genesis(b"e1")
    # Entry #2: deliberate FAIL (fabricated chain)
    c2 = _digest(b"e2")
    fab = _digest(b"fabricated")
    # Entry #3: clean re-anchor from a fresh genesis (operator intervened)
    c3 = _digest(b"e3")
    ch3 = lh.chain_hash(c3, fab)  # internally consistent with what's recorded

    body = _entry(1, c1, p1, ch1) + _entry(2, c2, ch1, fab) + _entry(3, c3, fab, ch3)
    p = _write(tmp_path, body)
    # Operator pins boundary at #3 (the last OK entry under raw verify is #3).
    rc = lh.verify_post_anchor(p, boundary_entry=3)
    out = capsys.readouterr().out
    err = capsys.readouterr().err
    # Joining out+err for assertion since DISCLOSED prints to stdout
    full = out + err
    assert rc == 0
    assert "DISCLOSED_PRE_ANCHOR Entry #2" in full
    assert "OK Entry #1" in full or "OK Entry #3" in full


def test_post_anchor_dirty_when_post_boundary_fails(tmp_path, capsys):
    """A FAIL at entry id > boundary is a hard error."""
    c1, p1, ch1 = _chain_genesis(b"e1")
    c2 = _digest(b"e2")
    ch2 = lh.chain_hash(c2, ch1)  # Entry #2 clean
    c3 = _digest(b"e3")
    fab3 = _digest(b"fabricated-3")  # Entry #3 FAIL

    body = _entry(1, c1, p1, ch1) + _entry(2, c2, ch1, ch2) + _entry(3, c3, ch2, fab3)
    p = _write(tmp_path, body)
    rc = lh.verify_post_anchor(p, boundary_entry=2)
    assert rc != 0


def test_boundary_defaults_to_last_clean_entry(tmp_path, capsys):
    """When boundary_entry is None, auto-detect highest-numbered clean entry."""
    c1, p1, ch1 = _chain_genesis(b"e1")
    c2 = _digest(b"e2")
    ch2 = lh.chain_hash(c2, ch1)
    body = _entry(1, c1, p1, ch1) + _entry(2, c2, ch1, ch2)
    p = _write(tmp_path, body)
    rc = lh.verify_post_anchor(p)  # no explicit boundary
    out = capsys.readouterr().out
    assert rc == 0
    assert "boundary=#2" in out


def test_explicit_boundary_overrides_auto_detection(tmp_path, capsys):
    """Operator-pinned boundary overrides auto-detection."""
    c1, p1, ch1 = _chain_genesis(b"e1")
    c2 = _digest(b"e2")
    ch2 = lh.chain_hash(c2, ch1)
    body = _entry(1, c1, p1, ch1) + _entry(2, c2, ch1, ch2)
    p = _write(tmp_path, body)
    rc = lh.verify_post_anchor(p, boundary_entry=1)
    out = capsys.readouterr().out
    assert "boundary=#1" in out


def test_empty_ledger_returns_clean(tmp_path, capsys):
    """An empty ledger has no entries and is trivially clean."""
    p = _write(tmp_path, "# Empty Ledger\n\nNo entries.\n")
    rc = lh.verify_post_anchor(p)
    assert rc == 0


def test_corefoge_pre_anchor_cluster_tolerated(tmp_path, capsys):
    """Issue #55 pattern: pre-anchor FAIL cluster, post-anchor clean.

    Mimics a sibling workspace's disclosed-edit cluster at entries #156-#169 followed
    by clean post-anchor entries. With operator-pinned boundary at #169,
    the pre-anchor FAILs are tolerated and post-anchor verifies clean.
    """
    bodies = []
    # Build a clean chain entries #1..#5 to anchor pre-cluster
    prev = "0" * 64
    for i in range(1, 6):
        content = _digest(f"clean-{i}".encode())
        chain = lh.chain_hash(content, prev)
        bodies.append(_entry(i, content, prev, chain))
        prev = chain
    # Entry #6: FAIL (disclosed pre-anchor edit)
    bad_content = _digest(b"e6")
    bad_chain = _digest(b"fabricated-6")
    bodies.append(_entry(6, bad_content, prev, bad_chain))
    # Entry #7+: post-anchor clean -- operator re-anchored from a known-good
    # genesis (recorded previous_hash references the parsed bad chain only
    # because of chain mechanics; under post-anchor mode, entry id > boundary
    # is what matters, and these entries' own math is self-consistent).
    prev = bad_chain
    for i in range(7, 10):
        content = _digest(f"post-{i}".encode())
        chain = lh.chain_hash(content, prev)
        bodies.append(_entry(i, content, prev, chain))
        prev = chain
    body = "".join(bodies)
    p = _write(tmp_path, body)
    # Pin boundary at #6 -- pre-anchor failure cluster is just that one entry.
    rc = lh.verify_post_anchor(p, boundary_entry=6)
    out = capsys.readouterr().out
    err = capsys.readouterr().err
    full = out + err
    assert rc == 0
    assert "DISCLOSED_PRE_ANCHOR Entry #6" in full


def test_session_seal_entry_counts_as_clean_boundary_candidate(tmp_path, capsys):
    """A Session Seal entry that verifies internally is eligible to be the boundary."""
    c1 = _digest(b"e1")
    p1 = "0" * 64
    seal1 = lh.chain_hash(c1, p1)
    body = (
        f"### Entry #1: SESSION SEAL TEST\n\n"
        f"**Content Hash**: `{c1}`\n\n"
        f"**Previous Hash**: `{p1}`\n\n"
        f"**Session Seal**:\nSHA256(content + prev)\n= `{seal1}`\n\n"
    )
    p = _write(tmp_path, body)
    rc = lh.verify_post_anchor(p)
    out = capsys.readouterr().out
    assert rc == 0
    assert "boundary=#1" in out


def test_post_boundary_failure_reported_with_entry_number(tmp_path, capsys):
    """The FAIL output names the post-boundary entry causing the dirty verdict."""
    c1, p1, ch1 = _chain_genesis(b"e1")
    c2 = _digest(b"e2")
    fab2 = _digest(b"fab-2")
    body = _entry(1, c1, p1, ch1) + _entry(2, c2, ch1, fab2)
    p = _write(tmp_path, body)
    rc = lh.verify_post_anchor(p, boundary_entry=1)
    err = capsys.readouterr().err
    assert rc != 0
    assert "FAIL Entry #2" in err
