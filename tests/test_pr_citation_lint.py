"""Phase 31 Phase 3: PR citation lint.

Every PR description must cite plan file path + ledger entry + Merkle seal
hash per doctrine-governance-enforcement.md Section 6. Lint function
parses a body string and returns missing items.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import pr_citation_lint as lint  # noqa: E402


_COMPLETE_BODY = """
## Summary

Phase 42 closes some stuff.

- Plan: docs/plan-qor-phase42-something-neat.md
- Ledger entry: #150
- Merkle seal: abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789
"""


def test_all_citations_present():
    assert lint.check_pr_body(_COMPLETE_BODY) == []


def test_missing_plan_path():
    body = _COMPLETE_BODY.replace("docs/plan-qor-phase42-something-neat.md", "")
    missing = lint.check_pr_body(body)
    assert any("plan" in m.lower() for m in missing), f"Expected plan missing, got {missing}"


def test_missing_ledger_entry():
    body = _COMPLETE_BODY.replace("Ledger entry: #150", "")
    missing = lint.check_pr_body(body)
    assert any("ledger" in m.lower() for m in missing), f"Expected ledger missing, got {missing}"


def test_missing_merkle_seal():
    body = _COMPLETE_BODY.replace(
        "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789", ""
    )
    missing = lint.check_pr_body(body)
    assert any("merkle" in m.lower() or "seal" in m.lower() for m in missing), (
        f"Expected seal missing, got {missing}"
    )


def test_all_three_missing():
    missing = lint.check_pr_body("## Empty body\n\nNo citations here.\n")
    assert len(missing) == 3


def test_seal_matches_hex_but_too_short():
    body = _COMPLETE_BODY.replace(
        "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "abcdef0123456789",  # 16 chars, not 64
    )
    missing = lint.check_pr_body(body)
    assert any("merkle" in m.lower() or "seal" in m.lower() for m in missing), (
        "Short hex should NOT be accepted as seal"
    )


def test_case_insensitive_entry_reference():
    body = """
Plan: docs/plan-qor-phase50-test.md
Ledger Entry: #200
Merkle seal: 0000000000000000000000000000000000000000000000000000000000000000
"""
    assert lint.check_pr_body(body) == []


# --- Phase 139: bot-author exemption ---

import io  # noqa: E402


def test_is_exempt_actor_true_for_dependabot():
    assert lint.is_exempt_actor("dependabot[bot]") is True


def test_is_exempt_actor_true_for_other_bot():
    assert lint.is_exempt_actor("renovate[bot]") is True


def test_is_exempt_actor_false_for_human():
    assert lint.is_exempt_actor("Knapp-Kevin") is False


def test_main_skips_bot_actor_despite_missing_citations(monkeypatch):
    # Uncited body: a human would fail, but a bot author is exempt -> exit 0.
    monkeypatch.setattr("sys.stdin", io.StringIO("## bump deps\n\nno citations here\n"))
    assert lint.main(["--actor", "dependabot[bot]"]) == 0


def test_main_enforces_for_human_missing_citations(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("## empty\n\nno citations\n"))
    assert lint.main(["--actor", "alice"]) == 1


def test_main_passes_human_with_full_citations(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(_COMPLETE_BODY))
    assert lint.main(["--actor", "alice"]) == 0
