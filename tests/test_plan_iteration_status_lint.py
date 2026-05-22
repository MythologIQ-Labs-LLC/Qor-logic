"""Phase 84: tests for the pre-audit readiness short-circuit detector (GH #81)."""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from qor.scripts.plan_iteration_status_lint import check_plan

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write_plan(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "plan.md"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


def _run_cli(plan: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "qor.scripts.plan_iteration_status_lint",
         "--plan", str(plan)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


def test_detects_draft_iteration_field(tmp_path):
    plan = _write_plan(tmp_path, """
        # Plan
        **iteration**: draft (pre-audit)
        ## Phase 1
    """)
    findings = check_plan(plan)
    assert len(findings) == 1
    assert findings[0].signal == "draft-iteration"
    assert "iteration" in findings[0].excerpt.lower()


def test_detects_preaudit_iteration_field(tmp_path):
    plan = _write_plan(tmp_path, """
        # Plan
        **iteration**: iter-1 (pre-audit)
    """)
    findings = check_plan(plan)
    assert len(findings) == 1
    assert findings[0].signal == "draft-iteration"


def test_detects_operator_decisions_section(tmp_path):
    plan = _write_plan(tmp_path, """
        # Plan
        ## Operator Decisions Required Before Audit
        1. Pick a database.
    """)
    findings = check_plan(plan)
    assert len(findings) == 1
    assert findings[0].signal == "operator-decisions-section"


def test_detects_operator_confirms_open_question(tmp_path):
    plan = _write_plan(tmp_path, """
        # Plan
        ## Open Questions
        - Should we cache results? Operator confirms before audit.
    """)
    findings = check_plan(plan)
    assert len(findings) == 1
    assert findings[0].signal == "operator-confirms-oq"


def test_clean_plan_returns_no_findings(tmp_path):
    plan = _write_plan(tmp_path, """
        # Plan
        **iteration**: iter-2
        ## Open Questions
        None
        ## Phase 1
    """)
    assert check_plan(plan) == []


def test_main_exits_nonzero_and_prints_guidance_on_detection(tmp_path):
    plan = _write_plan(tmp_path, """
        # Plan
        **iteration**: draft (pre-audit)
    """)
    proc = _run_cli(plan)
    assert proc.returncode == 1
    assert "re-run /qor-audit" in proc.stderr
    assert "draft-iteration" in proc.stderr


def test_main_exits_zero_on_clean_plan(tmp_path):
    plan = _write_plan(tmp_path, """
        # Plan
        **iteration**: iter-2
        ## Open Questions
        None
    """)
    proc = _run_cli(plan)
    assert proc.returncode == 0
    assert proc.stderr == ""


def test_missing_plan_returns_empty_and_exits_zero(tmp_path):
    plan = tmp_path / "missing.md"
    assert check_plan(plan) == []
    proc = _run_cli(plan)
    assert proc.returncode == 0
