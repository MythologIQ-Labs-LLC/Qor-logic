"""Phase 275 (GH #424, GH #462): one definition of the audit verdict.

Three modules parsed "the audit verdict" with three regexes and no shared
definition. Two of them read the SAME file and disagreed about what a PASS
looks like on 84 of 189 real reports.

The tests here pin the dialect's decisions, not its implementation. The rows
that matter most are the ones where a line is *unreadable* rather than absent:
iteration 1 of this phase shipped a value pattern under which a qualified
verdict line vanished instead of conflicting, which left GH #424 open, and
iteration 2 shipped a label probe that could not see a lowercase label, which
left the same hole one layer down. Both are pinned below.
"""
from __future__ import annotations

import pytest

from qor.scripts import verdict_dialect as vd


def _v(body: str):
    return vd.read_verdict(body)


# ----- the reported defect (GH #424) -----

def test_quoted_pass_line_inside_a_veto_report_is_not_pass():
    """The issue as filed: a VETO report that states the canonical form."""
    v = _v("# Audit\n\n## VERDICT: PASS\n\n**Verdict**: VETO\n")
    assert v.conflict is True
    assert v.value is None
    assert vd.is_pass(v) is False


def test_qualified_veto_line_conflicts_rather_than_vanishing():
    """Iteration 1's hole.

    Under a bare `([A-Z]+)$` value pattern this line is INVISIBLE, not
    conflicting, so the PASS above it wins uncontested and the gate authorizes
    capture on a VETO report. The trailing-qualifier group is what makes it
    read as VETO and therefore conflict.
    """
    v = _v("## VERDICT: PASS\n\n**Verdict**: VETO (finding 3 unresolved)\n")
    assert "VETO" in [x.upper() for x in v.values]
    assert v.conflict is True
    assert vd.is_pass(v) is False


def test_pass_beside_an_unenumerated_verdict_is_a_conflict():
    """The value pattern must capture whatever word is there.

    An enumeration like `(PASS|VETO|FAIL)` silently ignores BLOCKED, and the
    PASS then reads as uncontested.
    """
    v = _v("## VERDICT: PASS\n\n**Verdict**: BLOCKED\n")
    assert v.conflict is True
    assert vd.is_pass(v) is False


def test_lowercase_verdict_label_is_unreadable_not_invisible():
    """Iteration 2's hole: the guard must be wider than the reader.

    A lowercase label matches neither the value pattern nor a case-anchored
    probe, so the line disappears from both and `is_pass` returns True on a
    report whose stated verdict is VETO.
    """
    v = _v("## VERDICT: PASS\n\nverdict: VETO\n")
    assert v.unreadable is True
    assert vd.is_pass(v) is False


def test_mixed_case_verdict_label_is_unreadable():
    v = _v("## VERDICT: PASS\n\nVeRdIcT: VETO\n")
    assert v.unreadable is True
    assert vd.is_pass(v) is False


def test_lowercase_verdict_value_is_unreadable_not_accepted():
    """The value stays case-sensitive; only the label probe is not."""
    v = _v("**Verdict**: pass\n")
    assert v.unreadable is True
    assert vd.is_pass(v) is False


# ----- forms that must keep working -----

@pytest.mark.parametrize("body", [
    "## VERDICT: PASS\n",
    "### Verdict: PASS\n",
    "Verdict: PASS\n",
    "VERDICT: PASS\n",
    "Verdict - PASS\n",
    "**Verdict**: PASS\n",
    "**Verdict**: **PASS**\n",
    "## VERDICT: PASS (L1)\n",
    "**Verdict**: **PASS** (L1)\n",
    "*Verdict: PASS (L1)*\n",
])
def test_real_pass_forms_are_read(body):
    """Every shape attested in the 204-report corpus."""
    assert vd.is_pass(_v(body)) is True


def test_repeated_identical_verdicts_are_not_a_conflict():
    """39 of 204 reports state the verdict twice: the template asks twice."""
    v = _v("## VERDICT: PASS\n\n**Verdict**: PASS\n")
    assert v.conflict is False
    assert vd.is_pass(v) is True


def test_qualified_pass_is_read_as_pass():
    """Three corpus reports; a strict pattern would wrongly refuse them."""
    assert vd.is_pass(_v("## VERDICT: PASS (L1)\n")) is True


def test_a_verdict_word_inside_a_qualifier_is_not_a_value():
    """The boundary that makes the qualifier group safe rather than permissive.

    The qualifier is commentary. A VETO mentioned inside it is not a second
    verdict, so this must read PASS and must not conflict.
    """
    v = _v("## VERDICT: PASS (VETO withdrawn on iteration 1)\n")
    assert v.conflict is False
    assert vd.is_pass(v) is True


# ----- refusals -----

@pytest.mark.parametrize("body,why", [
    ("## VERDICT: VETO\n", "a genuine veto"),
    ("", "empty file"),
    ("nothing here\n", "no verdict at all"),
    ("   Verdict: PASS\n", "indented -- Phase 53 anchor"),
    ("If the test does not PASS, the VERDICT: PASS shall not stand\n", "prose"),
    ("## VERDICT: PASS (iteration 2; iteration 1 was VETO) extra\n", "trailing text"),
])
def test_refused_shapes(body, why):
    assert vd.is_pass(_v(body)) is False, why


@pytest.mark.parametrize("body", [
    "## VERDICT: PASS (a) (b)\n",
    "## VERDICT: PASS (a (b))\n",
    "## VERDICT: PASS (a\n",
    "## VERDICT: PASS a)\n",
    "## VERDICT: (PASS)\n",
])
def test_malformed_qualifier_is_unreadable_not_ignored(body):
    """A later 'improvement' tolerating nesting or repetition reopens the hole.

    These must be UNREADABLE rather than skipped: skipped means a PASS
    elsewhere carries the report.
    """
    v = _v(body)
    assert v.unreadable is True
    assert vd.is_pass(v) is False


def test_absent_verdict_reads_as_none_not_as_pass():
    v = _v("# Report\n\nNo verdict field.\n")
    assert v.value is None
    assert v.unreadable is False
    assert vd.is_pass(v) is False


def test_a_report_quoting_the_template_placeholder_is_refused():
    """The template emits `## VERDICT: [PASS / VETO]`; a report quoting it
    unindented is refused. Fenced blocks do NOT protect -- only indentation."""
    v = _v("## VERDICT: PASS\n\n```\n## VERDICT: [PASS / VETO]\n```\n")
    assert v.unreadable is True
    assert vd.is_pass(v) is False


def test_an_indented_quotation_of_the_placeholder_reads_clean():
    """The documented workaround: indent by four spaces."""
    v = _v("## VERDICT: PASS\n\n    ## VERDICT: [PASS / VETO]\n")
    assert v.unreadable is False
    assert vd.is_pass(v) is True


# ----- the contract that makes the API safe for reconcile -----

def test_value_is_none_under_conflict():
    """`reconcile` branches on the raw string. If `value` could be 'PASS'
    while conflicting, that branch accepts a conflicted report."""
    assert _v("## VERDICT: PASS\n\n**Verdict**: VETO\n").value is None


def test_value_is_none_under_unreadable():
    assert _v("## VERDICT: PASS\n\nverdict: VETO\n").value is None


def test_the_probe_is_strictly_wider_than_the_reader():
    """The structural property the design rests on.

    Any line the value pattern reads must also trip the label probe;
    otherwise a readable verdict could escape the guard.
    """
    samples = [
        "## VERDICT: PASS", "**Verdict**: **PASS**", "Verdict - PASS",
        "### Verdict: VETO", "*Verdict: PASS (L1)*", "VERDICT: PASS (L1)",
        "**Verdict**: BLOCKED", "verdict: veto", "_Verdict_: PASS",
    ]
    for line in samples:
        if vd.VALUE_RE.match(line):
            assert vd.LABEL_RE.match(line), f"reader accepts but guard misses: {line!r}"


@pytest.mark.parametrize("line", [
    "### Verdict Hash",
    "## Verdict",
    "## Verdict Summary",
    "**Verdict ID**: [from audit report]",
    "_Verdict is binding on the operator._",
])
def test_headings_and_prose_do_not_trip_the_probe(line):
    """57 + 24 + 11 corpus occurrences. A false positive here would make
    ordinary reports unreadable."""
    assert vd.LABEL_RE.match(line) is None


# ----- the target field: agreement-required, not first-match -----

def test_target_reads_a_bare_path():
    assert vd.read_target("**Target**: docs/plan-x.md\n").value == "docs/plan-x.md"


def test_target_reads_a_backticked_path():
    """29 reports; capturing the backticks turns report-unreadable into
    target-mismatch -- a different code and the same refusal."""
    assert vd.read_target("**Target**: `docs/plan-x.md`\n").value == "docs/plan-x.md"


def test_target_reads_a_qualified_path():
    t = vd.read_target("**Target**: docs/plan-x.md (GH #410, #405)\n")
    assert t.value == "docs/plan-x.md"


def test_target_reads_a_backticked_and_qualified_path():
    t = vd.read_target("**Target**: `docs/plan-x.md` (GH #410)\n")
    assert t.value == "docs/plan-x.md"


def test_disagreeing_target_lines_do_not_take_the_first():
    """First-match lets a quoted or superseded path above the real one win.
    `.agent/staging/` is not session-scoped, so a stale report survives."""
    t = vd.read_target("**Target**: docs/plan-old.md\n**Target**: docs/plan-new.md\n")
    assert t.conflict is True
    assert t.value is None


def test_repeated_identical_target_lines_are_not_a_conflict():
    """0 of 204 reports disagree, so this refuses nothing ever written."""
    t = vd.read_target("**Target**: docs/plan-x.md\n**Target**: docs/plan-x.md\n")
    assert t.conflict is False
    assert t.value == "docs/plan-x.md"


def test_absent_target_reads_as_none():
    t = vd.read_target("# Report\n\n**Risk grade**: L3\n")
    assert t.value is None
    assert t.conflict is False
