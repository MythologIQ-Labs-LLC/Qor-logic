"""Phase 156 (GAP-GOV-03): seal_entry_check --auto re-verifies the committed
seal's content_hash<->plan binding without an external --plan argument (it
derives the phase + plan from the latest entry). Wired into CI so the binding
is re-checked on the committed bytes, not only locally pre-commit.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from qor.reliability import seal_entry_check as sec
from qor.scripts import ledger_hash


def _h(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _ledger(plan_rel: str, content: str, *, prev: str | None = None, phase: int = 99) -> str:
    prev = prev or _h("p")
    chain = ledger_hash.chain_hash(content, prev)
    return (
        "# Meta Ledger\n\n"
        f"### Entry #500: SESSION SEAL -- Phase {phase} demo\n\n"
        f"**Plan**: {plan_rel}\n"
        f"**Content Hash**: `{content}`\n"
        f"**Previous Hash**: `{prev}`\n"
        f"**Chain Hash (Merkle seal)**: `{chain}`\n\n"
        "clean ascii body -- ok\n"
    )


def _setup(tmp_path, content):
    docs = tmp_path / "docs"
    docs.mkdir()
    plan = docs / "plan-x.md"
    plan.write_text("# Plan x\nbody\n", encoding="utf-8")
    led = docs / "META_LEDGER.md"
    led.write_text(_ledger("docs/plan-x.md", content), encoding="utf-8")
    return led, plan


def test_check_latest_passes_on_bound_seal(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    plan = docs / "plan-x.md"
    plan.write_text("# Plan x\nbody\n", encoding="utf-8")
    content = ledger_hash.content_hash(plan)
    led = docs / "META_LEDGER.md"
    led.write_text(_ledger("docs/plan-x.md", content), encoding="utf-8")
    result = sec.check_latest(led, repo_root=tmp_path)
    assert result.ok is True, result.errors


def test_check_latest_fails_on_unbound_seal(tmp_path):
    led, _ = _setup(tmp_path, content=_h("not the plan"))
    result = sec.check_latest(led, repo_root=tmp_path)
    assert result.ok is False
    assert any("content_hash" in e and "plan" in e.lower() for e in result.errors), result.errors


def test_auto_cli_exit_codes(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    plan = docs / "plan-x.md"
    plan.write_text("# Plan x\nbody\n", encoding="utf-8")
    good = docs / "META_LEDGER.md"
    good.write_text(_ledger("docs/plan-x.md", ledger_hash.content_hash(plan)), encoding="utf-8")
    assert sec._main(["--ledger", str(good), "--auto"]) == 0
    bad = tmp_path / "bad.md"
    bad.write_text(_ledger("docs/plan-x.md", _h("wrong")), encoding="utf-8")
    # repo_root for bad resolves to tmp_path (bad.parent.parent), where docs/plan-x.md exists
    assert sec._main(["--ledger", str(bad), "--auto"]) == 1


def test_ci_step_present():
    ci = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "seal_entry_check" in ci and "--auto" in ci, "CI must re-verify the committed seal binding"


def test_content_hash_crlf_invariant(tmp_path):
    # GAP-GOV-03 follow-on: content_hash must be invariant to CRLF<->LF so the
    # GOV-01 binding survives git's autocrlf conversion of the committed plan.
    lf = tmp_path / "lf.md"
    lf.write_bytes(b"# Plan\nline one\nline two\n")
    crlf = tmp_path / "crlf.md"
    crlf.write_bytes(b"# Plan\r\nline one\r\nline two\r\n")
    assert ledger_hash.content_hash(lf) == ledger_hash.content_hash(crlf)
