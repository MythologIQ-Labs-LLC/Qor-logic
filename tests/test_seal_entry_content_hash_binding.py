"""Phase 150 (GAP-GOV-01): the seal binds content_hash to the plan bytes.

seal_entry_check recomputes sha256 of the plan named in the latest entry's
`**Plan**:` field and fails the seal if it does not match the recorded
content_hash -- so the recorded hash can no longer be an unverified free field.
Forward-only: only the latest (just-sealed) entry is recomputed.
"""
from __future__ import annotations

import hashlib

from qor.reliability import seal_entry_check as sec
from qor.scripts import ledger_hash


def _h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _ledger_with_plan(plan_rel: str, content: str, *, prev: str | None = None, phase: int = 99) -> str:
    prev = prev or _h("p")
    chain = ledger_hash.chain_hash(content, prev)
    return (
        "# Meta Ledger\n\n"
        f"### Entry #1: SESSION SEAL -- Phase {phase} demo\n\n"
        f"**Plan**: {plan_rel}\n"
        f"**Content Hash**: `{content}`\n"
        f"**Previous Hash**: `{prev}`\n"
        f"**Chain Hash (Merkle seal)**: `{chain}`\n\n"
        "clean ascii body -- ok\n"
    )


def _setup(tmp_path, plan_text: str, content: str):
    docs = tmp_path / "docs"
    docs.mkdir()
    plan = docs / "plan-x.md"
    plan.write_text(plan_text, encoding="utf-8")
    led = docs / "META_LEDGER.md"
    led.write_text(_ledger_with_plan("docs/plan-x.md", content), encoding="utf-8")
    return led, plan


def test_matching_content_hash_passes(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    plan = docs / "plan-x.md"
    plan.write_text("# Plan x\nbody\n", encoding="utf-8")
    content = ledger_hash.content_hash(plan)  # the honest hash of the plan bytes
    led = docs / "META_LEDGER.md"
    led.write_text(_ledger_with_plan("docs/plan-x.md", content), encoding="utf-8")
    result = sec.check(ledger_path=led, phase_num=99, repo_root=tmp_path)
    assert result.ok is True, result.errors


def test_tampered_content_hash_fails(tmp_path):
    # content_hash recorded as something that does NOT match the plan bytes
    # (chain is kept self-consistent so the recompute mismatch is the sole failure).
    led, _plan = _setup(tmp_path, "# Plan x\nbody\n", content=_h("not the plan"))
    result = sec.check(ledger_path=led, phase_num=99, repo_root=tmp_path)
    assert result.ok is False
    assert any("content_hash" in e and "plan" in e.lower() for e in result.errors), result.errors


def test_missing_plan_file_fails(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    led = docs / "META_LEDGER.md"
    led.write_text(_ledger_with_plan("docs/plan-missing.md", _h("c")), encoding="utf-8")
    result = sec.check(ledger_path=led, phase_num=99, repo_root=tmp_path)
    assert result.ok is False
    assert any("plan" in e.lower() for e in result.errors), result.errors
