"""Phase 92: behavior tests for qor.scripts.dod_record (GH #86).

Fixture-driven; each test exercises one branch of the parser
(empty-section / single-deliverable / multi-deliverable / D4.d waiver).
Per qor/references/doctrine-test-functionality.md, assertions verify
the parser's return shape against operative input, not header presence.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

from qor.scripts.dod_record import DodRecord, parse_plan


def _write_plan(tmp_path: Path, body: str) -> Path:
    plan = tmp_path / "plan.md"
    plan.write_text(body, encoding="utf-8")
    return plan


def test_parse_plan_returns_empty_when_section_absent(tmp_path):
    plan = _write_plan(tmp_path, "# Plan\n\nNo DoD section here.\n")
    assert parse_plan(plan) == []


def test_parse_plan_extracts_single_deliverable_d1_d2_d3_d4(tmp_path):
    plan = _write_plan(tmp_path, textwrap.dedent("""
        # Plan

        ## Definition of Done

        ### Deliverable: foo

        - **D1**: vision text
        - **D2**: code at module.py
        - **D3**: ledger entry + system_state entry
        - **D4**: test_foo asserts behavior X
        """))
    records = parse_plan(plan)
    assert len(records) == 1, f"expected 1 record, got {len(records)}: {records}"
    rec = records[0]
    assert rec.deliverable == "foo"
    assert rec.d1 and "vision text" in rec.d1
    assert rec.d2 and "module.py" in rec.d2
    assert rec.d3 and "ledger entry" in rec.d3
    assert rec.d4 and "test_foo" in rec.d4
    assert rec.d4_waiver_rationale is None
    assert rec.d4_waiver_followup is None


def test_parse_plan_extracts_multiple_deliverables(tmp_path):
    plan = _write_plan(tmp_path, textwrap.dedent("""
        # Plan

        ## Definition of Done

        ### Deliverable: alpha

        - **D1**: alpha spec
        - **D2**: alpha code
        - **D3**: alpha governance
        - **D4**: alpha test

        ### Deliverable: beta

        - **D1**: beta spec
        - **D2**: beta code
        - **D3**: beta governance
        - **D4**: beta test
        """))
    records = parse_plan(plan)
    assert len(records) == 2
    assert records[0].deliverable == "alpha"
    assert records[1].deliverable == "beta"
    # Order preserved by document order
    assert records[0].d1 and "alpha spec" in records[0].d1


def test_parse_plan_recognizes_d4_d_waiver_with_rationale_and_followup(tmp_path):
    plan = _write_plan(tmp_path, textwrap.dedent("""
        # Plan

        ## Definition of Done

        ### Deliverable: docs-only-change

        - **D1**: doc surface updated
        - **D2**: file edited
        - **D3**: ledger entry seals
        - **D4.d**: prose-only change; no runtime to exercise. **Follow-up phase**: reserved for future doctrine sweep.
        """))
    records = parse_plan(plan)
    assert len(records) == 1
    rec = records[0]
    assert rec.d4 is None, f"d4 should be None when D4.d waiver present; got {rec.d4!r}"
    assert rec.d4_waiver_rationale is not None
    assert "prose-only change" in rec.d4_waiver_rationale
    assert rec.d4_waiver_followup is not None
    assert "future doctrine sweep" in rec.d4_waiver_followup
