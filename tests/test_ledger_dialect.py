"""Behavioral tests for the shared ledger-dialect parser (GH #282).

Proves the three hash-value forms parse identically, the separate `**Phase**:`
line is recognized, all three ledger consumers agree on a fenced+separate-Phase
fixture, and every rejection is preserved.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from qor.scripts import ledger_dialect as ld
from qor.scripts import ledger_hash as lh
from qor.scripts import governance_health as gh
from qor.reliability import seal_entry_check as sec


def _digest(seed: bytes) -> str:
    return hashlib.sha256(seed).hexdigest()


# ---------- hash-value forms ----------

def test_three_hash_forms_extract_same_value():
    hexval = _digest(b"content")
    inline = f"**Content Hash**: `{hexval}`"
    eq_form = f"**Content Hash**:\n```\nSHA256(x)\n= {hexval}\n```"
    fenced_bare = f"**Content Hash**:\n```\n{hexval}\n```"
    for body in (inline, eq_form, fenced_bare):
        m = ld.CONTENT_HASH_RE.search(body)
        assert ld.hash_value(m) == hexval, body


def test_entry_phase_reads_header_and_separate_line():
    assert ld.entry_phase("### Entry #9: SESSION SEAL -- Phase 42 foo", "") == 42
    body = "**Phase**: SUBSTANTIATE (Phase 7; feature)\n\n**Content Hash**: `x`"
    assert ld.entry_phase("### Entry #9: SESSION SEAL", body) == 7
    assert ld.entry_phase("### Entry #9: SESSION SEAL", "no phase here") is None


def test_compat_boundary_is_single_valued():
    assert ld.MARKUP_COMPAT_BOUNDARY == 123


# ---------- three-consumer consistency ----------

def _fenced_entry(num: int, kind: str, content: str, prev: str, phase: int, plan_line: str = "") -> str:
    chain = lh.chain_hash(content, prev)
    plan = f"**Plan**: {plan_line}\n" if plan_line else ""
    return (
        f"### Entry #{num}: {kind}\n\n"
        f"**Phase**: {kind} (Phase {phase})\n"
        f"{plan}"
        f"\n**Content Hash**:\n```\n{content}\n```\n"
        f"\n**Previous Hash**:\n```\n{prev}\n```\n"
        f"\n**Chain Hash**:\n```\n{chain}\n```\n"
    )


def _fenced_ledger(tmp_path: Path) -> Path:
    c123, p123 = _digest(b"e123"), "0" * 64
    e123 = _fenced_entry(123, "IMPLEMENTATION", c123, p123, 50)
    c124, p124 = _digest(b"e124"), lh.chain_hash(c123, p123)
    e124 = _fenced_entry(124, "SESSION SEAL", c124, p124, 50)
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + e123 + "\n" + e124 + "\n", encoding="utf-8")
    return ledger


def test_all_three_consumers_agree_on_fenced_separate_phase_fixture(tmp_path):
    ledger = _fenced_ledger(tmp_path)
    # 1. verify-ledger
    assert lh.verify(ledger) == 0
    # 2. governance-health's ledger verdict uses the same parser
    assert gh._verify_ledger_chain(ledger) == 0
    # 3. seal_entry_check parses + chain-verifies the latest fenced entry
    result = sec.check(ledger, phase_num=50)
    assert result.ok, result.errors


def test_seal_entry_parses_separate_phase_and_fenced_hashes(tmp_path):
    ledger = _fenced_ledger(tmp_path)
    latest = sec._parse_latest_entry(ledger.read_text(encoding="utf-8"))
    assert latest is not None
    assert latest["kind"] == "SESSION SEAL"
    assert latest["phase_num"] == 50
    assert latest["content_hash"] == _digest(b"e124")


# ---------- preserved rejections ----------

def test_malformed_hash_at_boundary_fails(tmp_path):
    bad = (
        "### Entry #123: SESSION SEAL\n\n**Phase**: SESSION SEAL (Phase 1)\n"
        "\n**Content Hash**:\n```\nnot-a-valid-hash\n```\n"
        "\n**Previous Hash**:\n```\n" + "0" * 64 + "\n```\n"
        "\n**Chain Hash**:\n```\n" + _digest(b"z") + "\n```\n"
    )
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + bad + "\n", encoding="utf-8")
    assert lh.verify(ledger) != 0


def test_chain_mismatch_fails(tmp_path):
    content, prev = _digest(b"a"), "0" * 64
    wrong_chain = _digest(b"wrong")
    entry = (
        "### Entry #124: SESSION SEAL\n\n**Phase**: SESSION SEAL (Phase 1)\n"
        f"\n**Content Hash**:\n```\n{content}\n```\n"
        f"\n**Previous Hash**:\n```\n{prev}\n```\n"
        f"\n**Chain Hash**:\n```\n{wrong_chain}\n```\n"
    )
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + entry + "\n", encoding="utf-8")
    assert lh.verify(ledger) != 0


def test_duplicate_previous_hash_post_boundary_fails(tmp_path):
    shared_prev = _digest(b"shared")
    e_a = _fenced_entry(300, "IMPLEMENTATION", _digest(b"a"), shared_prev, 60)
    e_b = _fenced_entry(301, "SESSION SEAL", _digest(b"b"), shared_prev, 60)
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + e_a + "\n" + e_b + "\n", encoding="utf-8")
    res = sec.check_previous_hash_uniqueness(ledger, min_entry_num=207)
    assert not res.ok


def test_tampered_content_breaks_plan_binding(tmp_path):
    plan = tmp_path / "docs" / "plan-x.md"
    plan.parent.mkdir(parents=True)
    plan.write_text("real plan bytes\n", encoding="utf-8")
    wrong_content = _digest(b"not the plan")
    prev = "0" * 64
    chain = lh.chain_hash(wrong_content, prev)
    entry = (
        "### Entry #124: SESSION SEAL\n\n**Phase**: SESSION SEAL (Phase 1)\n"
        "**Plan**: docs/plan-x.md\n"
        f"\n**Content Hash**:\n```\n{wrong_content}\n```\n"
        f"\n**Previous Hash**:\n```\n{prev}\n```\n"
        f"\n**Chain Hash**:\n```\n{chain}\n```\n"
    )
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("# Meta Ledger\n\n" + entry + "\n", encoding="utf-8")
    res = sec.check(ledger, phase_num=1, repo_root=tmp_path)
    assert not res.ok
