"""Phase 53: intent_lock LOW-4 anchored-PASS regex tightening.

The pre-Phase-53 implementation used ``re.search(r"VERDICT.*PASS", body, re.IGNORECASE)``
which admitted substring "PASS" mentions in narrative prose. The Phase 53
form anchors to a multiline-anchored canonical verdict line and rejects
prose mentions.
"""
from __future__ import annotations

import textwrap

from qor.reliability import intent_lock
from qor.reliability.intent_lock import _audit_has_pass


def _write(tmp_path, content: str):
    p = tmp_path / "audit.md"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def test_audit_body_with_canonical_verdict_line_passes(tmp_path):
    audit = _write(tmp_path, """
        # AUDIT REPORT

        **Target**: docs/plan.md
        Verdict: PASS

        body...
    """)
    assert _audit_has_pass(audit)


def test_audit_body_with_uppercase_verdict_passes(tmp_path):
    audit = _write(tmp_path, """
        # AUDIT REPORT

        VERDICT: PASS
    """)
    assert _audit_has_pass(audit)


def test_audit_body_with_bold_markdown_verdict_passes(tmp_path):
    audit = _write(tmp_path, """
        # AUDIT REPORT

        **Verdict**: **PASS**
    """)
    assert _audit_has_pass(audit)


def test_audit_body_with_substring_pass_in_prose_rejects(tmp_path):
    """LOW-4 regression test.

    Prior loose regex ``re.search("VERDICT.*PASS")`` admitted any audit body
    containing both substrings on the same line, including narrative prose.
    The anchored form rejects this.
    """
    audit = _write(tmp_path, """
        # AUDIT REPORT

        Notes: VERDICT discussion below. Note that to PASS this audit, the
        operator must have completed all phases.
    """)
    assert not _audit_has_pass(audit)


def test_audit_body_with_indented_verdict_rejects(tmp_path):
    audit = _write(tmp_path, """
        # AUDIT REPORT

           Verdict: PASS
    """)
    assert not _audit_has_pass(audit)


def test_audit_body_with_dash_separator_passes(tmp_path):
    audit = _write(tmp_path, """
        # AUDIT REPORT

        Verdict - PASS
    """)
    assert _audit_has_pass(audit)


def test_audit_body_without_verdict_rejects(tmp_path):
    audit = _write(tmp_path, """
        # AUDIT REPORT

        Test passed. Build passed. Linter passed.
    """)
    assert not _audit_has_pass(audit)


def test_audit_body_with_veto_rejects(tmp_path):
    audit = _write(tmp_path, """
        # AUDIT REPORT

        Verdict: VETO
    """)
    assert not _audit_has_pass(audit)


# ----- Phase 183 (GH #263): markdown-heading verdict forms -----

def test_audit_body_with_h2_heading_verdict_passes(tmp_path):
    """GH #263 acceptance: '## VERDICT: PASS' is a structural declaration in
    real production use (the Phase 173 tribunal hit its rejection live)."""
    audit = tmp_path / "AUDIT_REPORT.md"
    audit.write_text("# Report\n\n## VERDICT: PASS\n\nbody\n", encoding="utf-8")
    assert intent_lock._audit_has_pass(audit) is True


def test_audit_body_with_h3_mixed_case_heading_passes(tmp_path):
    audit = tmp_path / "AUDIT_REPORT.md"
    audit.write_text("# Report\n\n### Verdict: PASS\n", encoding="utf-8")
    assert intent_lock._audit_has_pass(audit) is True


def test_prose_and_indented_rejections_unchanged(tmp_path):
    """LOW-4 regression locks re-asserted post-widening."""
    audit = tmp_path / "AUDIT_REPORT.md"
    audit.write_text(
        "If the test does not PASS, the VERDICT: PASS shall not stand today\n"
        "  Verdict: PASS\n",  # indented -> still rejected
        encoding="utf-8",
    )
    assert intent_lock._audit_has_pass(audit) is False


def test_capture_error_hints_at_format_when_verdict_present(tmp_path, capsys, monkeypatch):
    """A non-canonical verdict line yields the format hint; a verdict-free
    audit keeps the plain not-PASS error."""
    plan = tmp_path / "plan.md"
    plan.write_text("# plan\n", encoding="utf-8")
    audit = tmp_path / "AUDIT_REPORT.md"

    audit.write_text("Verdict -> PASS\n", encoding="utf-8")  # unsupported separator
    rc = intent_lock.main(["capture", "--session", "2026-07-13T0000-t3st01",
                           "--plan", str(plan), "--audit", str(audit)])
    err = capsys.readouterr().err
    assert rc == 1 and "canonical form" in err

    audit.write_text("no verdict content here\n", encoding="utf-8")
    rc = intent_lock.main(["capture", "--session", "2026-07-13T0000-t3st01",
                           "--plan", str(plan), "--audit", str(audit)])
    err = capsys.readouterr().err
    assert rc == 1 and "audit not PASS" in err and "canonical form" not in err
