"""Phase 66 (#54): taint propagation in ledger_hash.verify.

When Entry N fails chain math, downstream entries N+1, N+2, ... are
classified as TAINTED (their chain math is internally consistent only
because they chain from a known-bad parent). Taint clears at the next
chain-link that genuinely verifies against the prior recorded chain
value.
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


def test_downstream_entries_after_fail_marked_tainted(tmp_path, capsys):
    """A->B(FAIL)->C: C is reported TAINTED because B failed."""
    a_content = _digest(b"a-content")
    a_prev = "0" * 64
    a_chain = lh.chain_hash(a_content, a_prev)

    b_content = _digest(b"b-content")
    b_fabricated_chain = _digest(b"not-the-real-chain")

    c_content = _digest(b"c-content")
    # C correctly chains from B's recorded (fabricated) value; chain math is
    # internally consistent but rooted in a failed predecessor.
    c_chain = lh.chain_hash(c_content, b_fabricated_chain)

    body = (
        _entry(1, a_content, a_prev, a_chain)
        + _entry(2, b_content, a_chain, b_fabricated_chain)
        + _entry(3, c_content, b_fabricated_chain, c_chain)
    )
    p = _write(tmp_path, body)
    rc = lh.verify(p)
    out = capsys.readouterr()
    assert rc == 1
    assert "Entry #1: chain hash verified" in out.out
    assert "FAIL Entry #2" in out.err
    assert "TAINTED Entry #3" in out.err


def test_self_consistent_entry_after_fail_still_tainted(tmp_path, capsys):
    """Per Phase 66 contract (GH #54): a downstream entry whose own chain
    math is self-consistent is STILL tainted when it chains from a failed
    predecessor's recorded value. Math consistency alone is not trust;
    the chain root is poisoned. Operators must fix the upstream FAIL to
    clear taint -- there is no auto-relink in V1.
    """
    a_content = _digest(b"a-content")
    a_prev = "0" * 64
    a_chain = lh.chain_hash(a_content, a_prev)

    b_content = _digest(b"b-content")
    b_fab = _digest(b"fabricated-b-chain")

    c_content = _digest(b"c-content")
    c_self_consistent_chain = lh.chain_hash(c_content, b_fab)

    body = (
        _entry(1, a_content, a_prev, a_chain)
        + _entry(2, b_content, a_chain, b_fab)
        + _entry(3, c_content, b_fab, c_self_consistent_chain)
    )
    p = _write(tmp_path, body)
    rc = lh.verify(p)
    out = capsys.readouterr()
    assert rc == 1
    assert "FAIL Entry #2" in out.err
    assert "TAINTED Entry #3: depends on failed predecessor #2" in out.err
    # Importantly, Entry #3 is NOT reported as plain OK -- math consistency
    # cannot launder a poisoned chain root.
    assert "Entry #3: chain hash verified" not in out.out


def test_taint_reports_root_cause_entry_number(tmp_path, capsys):
    """TAINTED output names the originating FAIL entry number."""
    a_content = _digest(b"a")
    a_prev = "0" * 64
    a_chain = lh.chain_hash(a_content, a_prev)

    b_content = _digest(b"b")
    b_wrong = _digest(b"wrong-chain")

    c_content = _digest(b"c")
    # C's chain math also fails (downstream of B's failure)
    c_wrong = _digest(b"unrelated-c-chain")

    body = (
        _entry(1, a_content, a_prev, a_chain)
        + _entry(2, b_content, a_chain, b_wrong)
        + _entry(3, c_content, b_wrong, c_wrong)
    )
    p = _write(tmp_path, body)
    rc = lh.verify(p)
    err = capsys.readouterr().err
    assert rc == 1
    assert "FAIL Entry #2" in err
    assert "TAINTED Entry #3: depends on failed predecessor #2" in err


def test_first_entry_failure_does_not_taint_prior_entries(tmp_path, capsys):
    """Entry #1 failing does not retroactively taint anything (there are no prior entries)."""
    bad_content = _digest(b"x")
    bad_prev = "0" * 64
    wrong_chain = _digest(b"wrong")
    p = _write(tmp_path, _entry(1, bad_content, bad_prev, wrong_chain))
    rc = lh.verify(p)
    err = capsys.readouterr().err
    assert rc == 1
    assert "FAIL Entry #1" in err
    assert "TAINTED" not in err
