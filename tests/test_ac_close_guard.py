"""Behavioral tests for the acceptance-criteria close guard (Phase 114, #158).

WARN-first: the guard never blocks a seal in V1 (CLI exits 0); these tests
exercise the pure parse/evaluate logic that the future --enforce mode will gate
on, plus the WARN-first CLI envelope.
"""
from __future__ import annotations

from qor.scripts import ac_close_guard as guard

_BODY = """\
## Context
Some preamble.

## Acceptance criteria
- [x] First thing done
- [ ] Second thing not done
- [x] Third thing done

## Notes
- [ ] this bullet is outside the AC section and must be ignored
"""


def test_parse_met_and_unmet():
    crits = guard.parse_acceptance_criteria(_BODY)
    assert len(crits) == 3
    assert [c.met for c in crits] == [True, False, True]
    assert crits[1].text.startswith("Second thing")


def test_parse_no_checklist_returns_empty():
    assert guard.parse_acceptance_criteria("# Title\n\nJust prose, no checklist.\n") == []


def test_parse_ignores_fenced_checkboxes():
    body = "## Acceptance criteria\n```\n- [ ] fenced example, not real\n```\n- [x] real one\n"
    crits = guard.parse_acceptance_criteria(body)
    assert len(crits) == 1 and crits[0].met is True


def test_evaluate_all_met_allows():
    crits = [guard.Criterion("a", True), guard.Criterion("b", True)]
    d = guard.evaluate_closure(crits, has_followon=False, qa_verdict="PASS")
    assert d.allow is True
    assert d.blocking_reasons == []


def test_evaluate_unmet_without_followon_flags():
    crits = [guard.Criterion("a", True), guard.Criterion("b", False)]
    d = guard.evaluate_closure(crits, has_followon=False, qa_verdict="PASS")
    assert d.allow is False
    assert any("b" in r for r in d.blocking_reasons)


def test_evaluate_unmet_with_followon_ok():
    crits = [guard.Criterion("b", False)]
    d = guard.evaluate_closure(crits, has_followon=True, qa_verdict="PASS")
    assert d.allow is True


def test_evaluate_qa_verdict_fail_warns():
    crits = [guard.Criterion("a", True)]
    d = guard.evaluate_closure(crits, has_followon=False, qa_verdict="FAIL")
    assert d.warnings
    assert any("qa" in w.lower() for w in d.warnings)


def test_no_checklist_fallback_allows_with_warn():
    d = guard.evaluate_closure([], has_followon=False, qa_verdict="PASS")
    assert d.allow is True
    assert d.warnings


def test_extract_closes_refs():
    body = "Fixes #12 and closes #34. resolves #5; see #999 (not a verb)."
    refs = guard.extract_closes_refs(body)
    assert set(refs) == {12, 34, 5}


def test_cli_warn_first_exits_zero_with_no_targets(tmp_path):
    pr = tmp_path / "pr.md"
    pr.write_text("PR body with no closing keywords. See #7 for context.\n", encoding="utf-8")
    rc = guard.main(["--pr-body-file", str(pr)])
    assert rc == 0
