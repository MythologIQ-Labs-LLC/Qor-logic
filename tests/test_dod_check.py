"""Phase 92: behavior tests for qor.scripts.dod_check (GH #86).

Fixture-driven across each finding category, plus a CLI exit-0 contract
test and the deterministic self-application anchor (Phase 92's own plan
must report zero findings against the lint it introduces).

Per qor/references/doctrine-test-functionality.md, each assertion
verifies an operative property of the check function (finding category +
count + deliverable name) and not header presence.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from qor.scripts.dod_check import CheckFinding, check_plan

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write_plan(tmp_path: Path, body: str) -> Path:
    plan = tmp_path / "plan.md"
    plan.write_text(body, encoding="utf-8")
    return plan


def test_check_plan_emits_missing_dod_section_finding_when_absent(tmp_path):
    plan = _write_plan(tmp_path, "# Plan\n\nNo DoD here.\n")
    findings = check_plan(plan)
    assert len(findings) == 1, f"expected 1 finding, got: {findings}"
    assert findings[0].category == "missing-dod-section"
    assert findings[0].severity == "warn"


def test_check_plan_emits_deliverable_missing_tier_finding_for_partial_row(tmp_path):
    plan = _write_plan(tmp_path, textwrap.dedent("""
        # Plan

        ## Definition of Done

        ### Deliverable: partial

        - **D1**: spec exists
        - **D2**: code exists
        - **D3**: governance exists
        """))
    # No D4 or D4.d
    findings = check_plan(plan)
    assert any(
        f.category == "deliverable-missing-tier" and f.deliverable == "partial"
        for f in findings
    ), f"expected deliverable-missing-tier finding for 'partial'; got: {findings}"


def test_check_plan_emits_waiver_without_rationale_finding_for_empty_d4_d(tmp_path):
    plan = _write_plan(tmp_path, textwrap.dedent("""
        # Plan

        ## Definition of Done

        ### Deliverable: empty-waiver

        - **D1**: vision
        - **D2**: code
        - **D3**: governance
        - **D4.d**:
        """))
    findings = check_plan(plan)
    assert any(
        f.category == "waiver-without-rationale" and f.deliverable == "empty-waiver"
        for f in findings
    ), f"expected waiver-without-rationale finding; got: {findings}"


def test_check_plan_emits_waiver_without_followup_finding_when_phase_absent(tmp_path):
    plan = _write_plan(tmp_path, textwrap.dedent("""
        # Plan

        ## Definition of Done

        ### Deliverable: no-followup

        - **D1**: vision
        - **D2**: code
        - **D3**: governance
        - **D4.d**: prose-only change but no follow-up reference here.
        """))
    findings = check_plan(plan)
    assert any(
        f.category == "waiver-without-followup" and f.deliverable == "no-followup"
        for f in findings
    ), f"expected waiver-without-followup finding; got: {findings}"


def test_check_plan_emits_no_findings_for_complete_dod_block(tmp_path):
    plan = _write_plan(tmp_path, textwrap.dedent("""
        # Plan

        ## Definition of Done

        ### Deliverable: alpha

        - **D1**: alpha spec
        - **D2**: alpha code
        - **D3**: alpha governance
        - **D4**: alpha test passes

        ### Deliverable: beta

        - **D1**: beta spec
        - **D2**: beta code
        - **D3**: beta governance
        - **D4.d**: prose-only doc change. **Follow-up phase**: reserved.
        """))
    findings = check_plan(plan)
    assert findings == [], f"expected no findings on complete block; got: {findings}"


def test_main_cli_returns_zero_even_with_findings(tmp_path):
    plan = _write_plan(tmp_path, "# Plan\n\nNo DoD.\n")
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.dod_check", "--plan", str(plan)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"CLI must exit 0 (WARN-only contract); got exit={result.returncode} "
        f"stderr={result.stderr!r}"
    )
    assert "missing-dod-section" in (result.stdout + result.stderr), (
        f"CLI must surface finding category in output; got "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_check_plan_self_applies_to_phase_92_plan():
    """Self-application anchor: Phase 92's own plan must report zero findings
    against the lint it introduces. This is the deterministic shipping-
    correctness test mirroring Phase 89/91 pattern."""
    plan = REPO_ROOT / "docs" / "plan-qor-phase92-definition-of-done.md"
    findings = check_plan(plan)
    assert findings == [], (
        f"Phase 92's own plan must declare a complete ## Definition of Done block "
        f"with no findings. Unmatched: {findings}"
    )
