"""Phase 119 (GH #148): reconcile core — detect residual, build proposal,
append a forward-only RECONCILIATION entry.

Synthetic ledgers reconstruct the #85 external-exemplar #16a/b,#17a/b,#18a/b
corpus: pairs of entries sharing a previous_hash with forced chain-math
failures (the consumer blocker). Per doctrine-test-functionality.md every test
invokes the unit and asserts on its output / observable file state.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

from qor.scripts import reconcile
from qor.scripts.ledger_hash import chain_hash

TS = "2026-05-30T00:00:00Z"  # fixed; tests must not couple to wall-clock


def _hex(seed: str) -> str:
    import hashlib
    return hashlib.sha256(seed.encode()).hexdigest()


def _entry(num: int, content: str, previous: str, *, chain_override: str | None = None) -> str:
    chain = chain_override if chain_override is not None else chain_hash(content, previous)
    return textwrap.dedent(
        f"""

        ### Entry #{num}: TEST

        **Content Hash**: `{content}`

        **Previous Hash**: `{previous}`

        **Chain Hash**: `{chain}`
        """
    )


def _corpus_ledger() -> str:
    """3 duplicate-previous_hash pairs (16&17, 18&19, 20&21) with forced
    chain-math failures, mirroring #16a/b,#17a/b,#18a/b; a clean trailer #22."""
    h1, h2, h3 = _hex("H1"), _hex("H2"), _hex("H3")
    entries = [
        _entry(16, _hex("c16"), h1, chain_override=_hex("bad16")),
        _entry(17, _hex("c17"), h1, chain_override=_hex("bad17")),
        _entry(18, _hex("c18"), h2, chain_override=_hex("bad18")),
        _entry(19, _hex("c19"), h2, chain_override=_hex("bad19")),
        _entry(20, _hex("c20"), h3, chain_override=_hex("bad20")),
        _entry(21, _hex("c21"), h3, chain_override=_hex("bad21")),
        _entry(22, _hex("c22"), _hex("uniqueprev")),  # clean, unique prev
    ]
    return "# META_LEDGER\n" + "".join(entries)


def _write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "META_LEDGER.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_detect_residual_finds_duplicate_previous_hash_groups(tmp_path):
    led = _write(tmp_path, _corpus_ledger())
    groups = reconcile.detect_residual(led.read_text(encoding="utf-8"))
    all_nums = sorted(n for nums in groups.values() for n in nums)
    assert all_nums == [16, 17, 18, 19, 20, 21], all_nums
    # Each group has exactly its pair; the unique-prev entry #22 is excluded.
    assert all(len(nums) == 2 for nums in groups.values())
    assert 22 not in all_nums


def test_build_proposal_is_pending_and_nonmutating(tmp_path):
    led = _write(tmp_path, _corpus_ledger())
    before = led.read_bytes()
    proposal = reconcile.build_proposal(led, ts=TS)
    assert proposal["status"] == "pending"
    assert sorted(proposal["residual_entry_nums"]) == [16, 17, 18, 19, 20, 21]
    assert len(proposal["previous_hashes"]) == 3
    assert led.read_bytes() == before, "build_proposal must not mutate the ledger"


def test_append_reconciliation_entry_is_forward_only(tmp_path):
    import re
    led = _write(tmp_path, _corpus_ledger())
    before = led.read_text(encoding="utf-8")
    proposal = reconcile.build_proposal(led, ts=TS)
    result = reconcile.append_reconciliation_entry(led, proposal, ts=TS)
    after = led.read_text(encoding="utf-8")
    # Strongest forward-only guarantee: the new ledger is a byte-exact append.
    # No prior entry's content/hashes/numbering can have changed.
    assert after.startswith(before), "reconcile must append, never rewrite prior bytes"
    appended = after[len(before):]
    # Exactly one new entry was added, and it is the RECONCILIATION entry.
    assert len(re.findall(r"### Entry #\d+:", appended)) == 1
    assert f"### Entry #{result['entry_num']}: RECONCILIATION" in appended
    # Reconciled set recorded for verify() to parse.
    for n in (16, 17, 18, 19, 20, 21):
        assert f"#{n}" in appended


def test_reconciliation_entry_chain_hash_is_consistent(tmp_path):
    led = _write(tmp_path, _corpus_ledger())
    proposal = reconcile.build_proposal(led, ts=TS)
    result = reconcile.append_reconciliation_entry(led, proposal, ts=TS)
    # The new entry is a normal forward link: chain_hash(content, prev) == recorded.
    assert chain_hash(result["content_hash"], result["previous_hash"]) == result["chain_hash"]


def test_build_proposal_empty_when_no_residual(tmp_path):
    clean = "# META_LEDGER\n" + _entry(1, _hex("a"), _hex("p1")) + _entry(2, _hex("b"), _hex("p2"))
    led = _write(tmp_path, clean)
    proposal = reconcile.build_proposal(led, ts=TS)
    assert proposal["residual_entry_nums"] == []
