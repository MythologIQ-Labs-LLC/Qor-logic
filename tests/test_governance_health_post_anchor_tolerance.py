"""Behavioral tests for skill-entry disclosed-pre-anchor tolerance (GH #199).

Builds synthetic ledgers with ``ledger_hash.chain_hash`` so the post-anchor band
is genuinely valid, then invokes ``governance_health._classify_one`` and asserts
on the returned status (OK vs DAMAGED) -- the classifier's actual behavior, not
artifact presence.
"""
from __future__ import annotations

import hashlib

from qor.scripts import governance_health, ledger_hash
from qor.scripts.governance_health import ArtifactStatus


def _h(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _entry(n: int, title: str, content: str, prev: str, recorded: str) -> str:
    return (
        f"### Entry #{n}: {title}\n\n"
        f"**Content Hash**: `{content}`\n"
        f"**Previous Hash**: `{prev}`\n"
        f"**Chain Hash (Merkle seal)**: `{recorded}`\n\n---\n\n"
    )


def _write_ledger(base, entries, declare_boundary=None) -> None:
    docs = base / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "META_LEDGER.md").write_text(
        "# QoreLogic Meta Ledger\n\n" + "".join(entries), encoding="utf-8"
    )
    if declare_boundary is not None:
        # Phase 270: pre-anchor tolerance is an operator ASSERTION, not an
        # inference drawn from the entries being judged. These fixtures always
        # meant "the operator has disclosed this history"; before a declaration
        # existed there was no way to say so, and the auto-detected boundary
        # said it on their behalf -- which is the defect this phase removes.
        import json as _json

        conf = base / ".qorlogic"
        conf.mkdir(parents=True, exist_ok=True)
        (conf / "config.json").write_text(
            _json.dumps({"ledger": {"post_anchor_boundary": declare_boundary}}),
            encoding="utf-8",
        )


def _classify(base):
    return governance_health._classify_one(base, "docs/META_LEDGER.md", True)


def test_disclosed_pre_anchor_residual_is_not_damaged(tmp_path):
    # Phase 270: chained properly, so the ONLY defect is entry 2's arithmetic.
    # These fixtures previously gave every entry an arbitrary previous_hash,
    # which also produced linkage breaks that were never what the test was
    # about -- the same defect test_fully_valid_ledger_is_ok carried.
    c1, p1 = _h("c1"), _h("p1")
    ch1 = ledger_hash.chain_hash(c1, p1)
    c2 = _h("c2")
    ch2_wrong = ledger_hash.chain_hash(_h("x"), _h("y"))
    c3 = _h("c3")
    ch3 = ledger_hash.chain_hash(c3, ch2_wrong)
    entries = [
        _entry(1, "A", c1, p1, ch1),               # ok
        _entry(2, "B", c2, ch1, ch2_wrong),        # math fails, links correctly
        _entry(3, "C", c3, ch2_wrong, ch3),        # ok, follows 2's recorded hash
    ]
    _write_ledger(tmp_path, entries, declare_boundary=2)
    # Strict verify fails (entry 2 fail + entry 3 taint); post-anchor is clean
    # (boundary = entry 3, entry 2 tolerated as DISCLOSED_PRE_ANCHOR).
    finding = _classify(tmp_path)
    assert finding.status is not ArtifactStatus.DAMAGED
    assert finding.status is ArtifactStatus.OK


def test_post_anchor_failure_is_still_damaged(tmp_path):
    c1, p1 = _h("c1"), _h("p1")
    c2, p2 = _h("c2"), _h("p2")
    c3, p3 = _h("c3"), _h("p3")
    entries = [
        _entry(1, "A", c1, p1, ledger_hash.chain_hash(c1, p1)),            # ok
        _entry(2, "B", c2, p2, ledger_hash.chain_hash(c2, p2)),            # ok
        _entry(3, "C", c3, p3, ledger_hash.chain_hash(_h("x"), _h("y"))),  # newest fails
    ]
    _write_ledger(tmp_path, entries)
    finding = _classify(tmp_path)
    assert finding.status is ArtifactStatus.DAMAGED
    assert "/qor-remediate" in finding.legal_next


def test_fully_valid_ledger_is_ok(tmp_path):
    """A genuinely valid ledger is OK with no declaration at all.

    Phase 270: this fixture used to give every entry an arbitrary previous_hash,
    so `verify()` rejected it with a BREAK while the test asserted OK -- the
    verdict came entirely from the post-anchor mode being weaker than verify().
    A test named for validity ran on a ledger verify() rejects. It is now
    chained properly, so it tests what its name claims and needs no declaration:
    auto-detection is permitted precisely because a strict pass raises nothing.
    """
    c1, p1 = _h("c1"), _h("p1")
    ch1 = ledger_hash.chain_hash(c1, p1)
    c2 = _h("c2")
    ch2 = ledger_hash.chain_hash(c2, ch1)
    c3 = _h("c3")
    ch3 = ledger_hash.chain_hash(c3, ch2)
    entries = [
        _entry(1, "A", c1, p1, ch1),
        _entry(2, "B", c2, ch1, ch2),
        _entry(3, "C", c3, ch2, ch3),
    ]
    _write_ledger(tmp_path, entries)
    finding = _classify(tmp_path)
    assert finding.status is ArtifactStatus.OK


def test_tolerated_residuals_emit_no_fail_or_tainted_lines(tmp_path, capsys):
    """Phase 182 (GH #268): diagnostics must match the verdict -- a tolerated
    re-anchored ledger classifies OK with ZERO raw FAIL/TAINTED lines on
    either stream (the stderr bleed contradicted the OK verdict)."""
    # Phase 270: chained properly, so the ONLY defect is entry 2's arithmetic.
    # These fixtures previously gave every entry an arbitrary previous_hash,
    # which also produced linkage breaks that were never what the test was
    # about -- the same defect test_fully_valid_ledger_is_ok carried.
    c1, p1 = _h("c1"), _h("p1")
    ch1 = ledger_hash.chain_hash(c1, p1)
    c2 = _h("c2")
    ch2_wrong = ledger_hash.chain_hash(_h("x"), _h("y"))
    c3 = _h("c3")
    ch3 = ledger_hash.chain_hash(c3, ch2_wrong)
    entries = [
        _entry(1, "A", c1, p1, ch1),               # ok
        _entry(2, "B", c2, ch1, ch2_wrong),        # math fails, links correctly
        _entry(3, "C", c3, ch2_wrong, ch3),        # ok, follows 2's recorded hash
    ]
    _write_ledger(tmp_path, entries, declare_boundary=2)
    finding = _classify(tmp_path)
    captured = capsys.readouterr()
    assert finding.status is ArtifactStatus.OK
    for stream in (captured.out, captured.err):
        assert "FAIL Entry" not in stream
        assert "TAINTED" not in stream


def test_ok_reason_names_the_disclosed_tolerance(tmp_path):
    """Phase 182 (GH #268): the tolerance is surfaced positively -- the OK
    reason identifies the disclosed pre-anchor state."""
    # Phase 270: chained properly, so the ONLY defect is entry 2's arithmetic.
    # These fixtures previously gave every entry an arbitrary previous_hash,
    # which also produced linkage breaks that were never what the test was
    # about -- the same defect test_fully_valid_ledger_is_ok carried.
    c1, p1 = _h("c1"), _h("p1")
    ch1 = ledger_hash.chain_hash(c1, p1)
    c2 = _h("c2")
    ch2_wrong = ledger_hash.chain_hash(_h("x"), _h("y"))
    c3 = _h("c3")
    ch3 = ledger_hash.chain_hash(c3, ch2_wrong)
    entries = [
        _entry(1, "A", c1, p1, ch1),               # ok
        _entry(2, "B", c2, ch1, ch2_wrong),        # math fails, links correctly
        _entry(3, "C", c3, ch2_wrong, ch3),        # ok, follows 2's recorded hash
    ]
    _write_ledger(tmp_path, entries, declare_boundary=2)
    finding = _classify(tmp_path)
    assert "disclosed pre-anchor residuals tolerated" in finding.reason
