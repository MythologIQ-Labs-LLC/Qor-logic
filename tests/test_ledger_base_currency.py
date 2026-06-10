"""Phase 162 (GH #231 Option 1): ledger base-currency gate + re-anchor helper.

A linear hash chain over a git branch DAG forks when a branch seals against a
stale `main` tip. `check` flags that (the first new-on-branch entry must chain
from the base tip); `reanchor` deterministically rebuilds a sub-chain onto the
live base tip. WARN-first in V1.

Behavioral: each test invokes the unit and asserts on its return/exit value.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from qor.reliability import ledger_base_currency as lbc
from qor.scripts.ledger_hash import chain_hash


def _content(seed: int) -> str:
    return hashlib.sha256(f"content-{seed}".encode()).hexdigest()


def _entry(num: int, prev: str, content: str) -> tuple[str, str]:
    chain = chain_hash(content, prev)
    block = (
        f"### Entry #{num}: SESSION SEAL -- Phase {num} x\n\n"
        f"**Content Hash**: `{content}`\n"
        f"**Previous Hash**: `{prev}`\n"
        f"**Chain Hash (Merkle seal)**: `{chain}`\n"
    )
    return block, chain


def _ledger(blocks: list[str]) -> str:
    return "# Ledger\n\n" + "\n---\n\n".join(blocks) + "\n"


def _base_and_tip() -> tuple[str, str]:
    """A 2-entry base ledger; returns (text, tip_chain_hash)."""
    g = "0" * 64
    a, ca = _entry(100, g, _content(1))
    b, cb = _entry(101, ca, _content(2))
    return _ledger([a, b]), cb


# ----------------------------------------------------------------- check()

def test_check_ok_when_branch_chains_from_base_tip():
    base_text, tip = _base_and_tip()
    a, ca = _entry(100, "0" * 64, _content(1))
    b, cb = _entry(101, ca, _content(2))
    c, _ = _entry(102, cb, _content(3))  # new entry chains from base tip
    res = lbc.check_base_currency(_ledger([a, b, c]), base_text)
    assert res.ok is True


def test_check_flags_stale_base():
    base_text, tip = _base_and_tip()
    a, ca = _entry(100, "0" * 64, _content(1))
    # branch's new entry cites the OLD tip (ca), not the current base tip (cb)
    c, _ = _entry(102, ca, _content(3))
    res = lbc.check_base_currency(_ledger([a, c]), base_text)
    assert res.ok is False
    assert "stale base" in res.message and "#102" in res.message


def test_check_ok_when_no_new_entries():
    base_text, _ = _base_and_tip()
    res = lbc.check_base_currency(base_text, base_text)
    assert res.ok is True


def test_check_ok_with_multi_new_entries():
    base_text, _ = _base_and_tip()
    a, ca = _entry(100, "0" * 64, _content(1))
    b, cb = _entry(101, ca, _content(2))
    trib, ct = _entry(102, cb, _content(3))   # first new chains from base tip
    seal, _ = _entry(103, ct, _content(4))    # seal chains from the tribunal
    res = lbc.check_base_currency(_ledger([a, b, trib, seal]), base_text)
    assert res.ok is True


# ----------------------------------------------------------------- reanchor()

def test_reanchor_recomputes_a_valid_subchain():
    tip = "a" * 64
    new = [
        {"content_hash": _content(10), "ts": "2026-06-10T00:00:00Z", "phase": "audit"},
        {"content_hash": _content(11), "ts": "2026-06-10T00:01:00Z", "phase": "substantiate"},
    ]
    out = lbc.reanchor(tip, new)
    assert out[0].previous_hash == tip
    assert out[0].chain_hash == chain_hash(_content(10), tip)
    assert out[1].previous_hash == out[0].chain_hash
    assert out[1].chain_hash == chain_hash(_content(11), out[0].chain_hash)
    assert len(out[0].entry_id) == 12


def test_reanchor_changes_a_stale_subchain_to_base_tip():
    live_tip = "b" * 64
    # the same content hashes that were stale-anchored elsewhere, re-anchored:
    new = [{"content_hash": _content(20), "ts": "2026-06-10T00:00:00Z", "phase": "substantiate"}]
    out = lbc.reanchor(live_tip, new)
    assert out[0].previous_hash == live_tip  # now links to the live base tip


# ----------------------------------------------------------------- CLI (WARN-first)

def test_main_cli_warn_only_exits_zero_on_stale(tmp_path, monkeypatch, capsys):
    base_text, _ = _base_and_tip()
    a, ca = _entry(100, "0" * 64, _content(1))
    c, _ = _entry(102, ca, _content(3))  # stale
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text(_ledger([a, c]), encoding="utf-8")
    monkeypatch.setattr(lbc, "_base_ledger_text", lambda repo_root, base_ref: base_text)

    rc = lbc.main(["--repo-root", str(tmp_path), "--base-ref", "origin/main"])
    assert rc == 0
    assert "WARN" in capsys.readouterr().out

    rc_enforce = lbc.main(["--repo-root", str(tmp_path), "--enforce"])
    assert rc_enforce == 1


def test_main_cli_skips_when_base_unresolvable(tmp_path, monkeypatch, capsys):
    base_text, _ = _base_and_tip()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "META_LEDGER.md").write_text(base_text, encoding="utf-8")
    monkeypatch.setattr(lbc, "_base_ledger_text", lambda repo_root, base_ref: None)
    rc = lbc.main(["--repo-root", str(tmp_path)])
    assert rc == 0
    assert "SKIP" in capsys.readouterr().out
