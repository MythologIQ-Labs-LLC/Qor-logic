"""Phase 23 Track C: NIST SSDF evidence framework tests."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCTRINE_PATH = REPO_ROOT / "qor" / "references" / "doctrine-nist-ssdf-alignment.md"


def test_compliance_cli_imports():
    """compliance subcommand is importable from cli module."""
    from qor.cli import main
    # --help should not crash
    with pytest.raises(SystemExit) as exc:
        main(["compliance", "--help"])
    assert exc.value.code == 0


def test_compliance_report_format(tmp_path):
    """compliance report outputs practice coverage lines."""
    from qor.cli_handlers.compliance import do_report as _do_compliance_report
    # Create a minimal ledger with SSDF tags
    ledger = tmp_path / "META_LEDGER.md"
    ledger.write_text("""### Entry #1: Test
**SSDF Practices**: PW.1.1, PS.1.1
**Content Hash**: `aaaa`

### Entry #2: Test2
**SSDF Practices**: PW.1.1, RV.1.1
**Content Hash**: `bbbb`
""", encoding="utf-8")
    output = _do_compliance_report(ledger_path=ledger)
    assert "PW.1.1" in output
    assert "PS.1.1" in output
    assert "RV.1.1" in output


def test_practice_tag_parsing(tmp_path):
    """SSDF practice tags are extracted from ledger entries."""
    from qor.scripts.ledger_hash import extract_ssdf_practices
    ledger = tmp_path / "ledger.md"
    ledger.write_text("""### Entry #1: Test
**SSDF Practices**: PO.1.1, PW.5.1
Some other text
""", encoding="utf-8")
    practices = extract_ssdf_practices(ledger)
    assert practices == {1: ["PO.1.1", "PW.5.1"]}


def test_coverage_calculation(tmp_path):
    """Coverage counts practice groups and individual practices."""
    from qor.cli_handlers.compliance import _compute_coverage
    practice_map = {
        1: ["PO.1.1", "PW.1.1"],
        2: ["PS.1.1", "RV.1.1"],
        3: ["PW.1.1"],
    }
    groups, practices, total = _compute_coverage(practice_map)
    assert groups == 4  # PO, PW, PS, RV
    assert practices == 4  # PO.1.1, PW.1.1, PS.1.1, RV.1.1
    assert total == 5  # total tag occurrences


def test_empty_ledger_handling(tmp_path):
    """compliance report handles empty ledger gracefully."""
    from qor.cli_handlers.compliance import do_report as _do_compliance_report
    ledger = tmp_path / "ledger.md"
    ledger.write_text("# Empty Ledger\n", encoding="utf-8")
    output = _do_compliance_report(ledger_path=ledger)
    assert "Coverage: 0" in output or "No SSDF" in output


def test_nist_doctrine_evidence_section():
    """NIST doctrine has Evidence Collection section."""
    body = DOCTRINE_PATH.read_text(encoding="utf-8")
    assert "Evidence Collection" in body
