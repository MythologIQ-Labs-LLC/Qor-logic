"""Phase 52: compliance report functional test against synthetic ledger fixtures.

Closes the SG-VacuousLint anti-pattern that Phase 51 WIP exhibited
(`pytest.skip` when ledger empty). Both tests use synthetic fixtures
with controlled inputs and assert on returned/printed output.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-nist-ssdf-alignment.md"


def test_compliance_report_finds_tags_in_synthetic_ledger_with_tags(tmp_path):
    """Build a synthetic ledger with one entry containing SSDF tags;
    invoke the compliance-report function with controlled input;
    assert returned report mentions the practice IDs."""
    from qor.cli import _do_compliance_report

    fixture = tmp_path / "META_LEDGER.md"
    fixture.write_text(
        "### Entry #1: SESSION SEAL -- Phase 52 feature substantiated\n"
        "\n"
        "**Session**: `s52`\n"
        "\n"
        "**Content Hash**: `aaa`\n"
        "**Previous Hash**: `bbb`\n"
        "**Chain Hash**: `ccc`\n"
        "\n"
        "**SSDF Practices**: PS.2.1, PW.1.1, PW.5.1\n"
        "\n"
        "---\n",
        encoding="utf-8",
    )
    report = _do_compliance_report(ledger_path=fixture)
    assert "PS.2.1" in report
    assert "PW.1.1" in report
    assert "PW.5.1" in report
    assert "Coverage:" in report


def test_compliance_report_reports_zero_for_synthetic_ledger_without_tags(tmp_path):
    """Functional test: empty ledger returns the canonical 'no tags' message."""
    from qor.cli import _do_compliance_report

    fixture = tmp_path / "META_LEDGER.md"
    fixture.write_text(
        "### Entry #1: SESSION SEAL -- Phase 51 feature\n"
        "\n"
        "**Session**: `s51`\n"
        "\n"
        "(no tags here)\n"
        "\n---\n",
        encoding="utf-8",
    )
    report = _do_compliance_report(ledger_path=fixture)
    assert report == "No SSDF practice tags found in ledger. Coverage: 0"


def test_doctrine_documents_phase_52_forward_only_emission():
    """Doctrine §Evidence Collection must document the forward-only contract."""
    body = DOCTRINE.read_text(encoding="utf-8")
    m = re.search(r"^## Evidence Collection", body, re.MULTILINE)
    assert m, "doctrine must contain '## Evidence Collection' section"
    window = body[m.end(): m.end() + 4000]
    assert "Phase 52" in window
    assert re.search(r"forward.only|grandfather", window, re.IGNORECASE)
    assert "ssdf_tagger" in window
