"""Phase 53: intent_lock LOW-4 anchored-PASS regex tightening.

The pre-Phase-53 implementation used ``re.search(r"VERDICT.*PASS", body, re.IGNORECASE)``
which admitted substring "PASS" mentions in narrative prose. The Phase 53
form anchors to a multiline-anchored canonical verdict line and rejects
prose mentions.
"""
from __future__ import annotations

import textwrap

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
