"""Behavior tests for the delivery_branch_lint pre-audit lint (Phase 83, GH #87).

Each test builds a synthetic plan fixture, invokes check_delivery_branch (or
the module CLI), and asserts on the returned findings / exit code — never on
artifact presence alone. Per qor/references/doctrine-test-functionality.md.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

from qor.scripts.delivery_branch_lint import check_delivery_branch

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write_plan(tmp_path: Path, pr_target_line: str | None) -> Path:
    body = "# Plan: fixture\n\n**change_class**: feature\n"
    if pr_target_line is not None:
        body += f"\n{pr_target_line}\n"
    p = tmp_path / "plan-qor-phase99-fixture.md"
    p.write_text(body, encoding="utf-8")
    return p


def _raising_resolver(_branch: str) -> bool:
    raise AssertionError("branch_resolver must not be called")


def test_no_pr_target_yields_no_findings(tmp_path):
    # A plan with no pr_target front-matter is the common case; the resolver
    # must never be reached and the result must be empty.
    plan = _write_plan(tmp_path, None)
    result = check_delivery_branch(plan, branch_resolver=_raising_resolver)
    assert result == []


def test_existing_pr_target_yields_no_findings(tmp_path):
    plan = _write_plan(tmp_path, "**pr_target**: RC1.4")
    result = check_delivery_branch(plan, branch_resolver=lambda _b: True)
    assert result == []


def test_dash_prefixed_pr_target_rejected_without_resolver(tmp_path):
    # OWASP A03 guard: a '-'-prefixed pr_target would be parsed by git as an
    # option. It must be reported as a finding and the resolver must NOT run.
    plan = _write_plan(tmp_path, "**pr_target**: --upload-pack=evil")
    result = check_delivery_branch(plan, branch_resolver=_raising_resolver)
    assert len(result) == 1
    assert result[0].pr_target == "--upload-pack=evil"
    assert "not a well-formed branch name" in result[0].reason


def test_absent_pr_target_yields_finding(tmp_path):
    plan = _write_plan(tmp_path, "**pr_target**: RC9.9")
    result = check_delivery_branch(plan, branch_resolver=lambda _b: False)
    assert len(result) == 1
    assert result[0].pr_target == "RC9.9"
    assert "not found on origin" in result[0].reason


def test_cli_exits_nonzero_on_absent_branch(tmp_path):
    # CLI end-to-end: the QOR_DELIVERY_BRANCH_LINT_FAKE test seam forces the
    # resolver to report the branch absent; the CLI must exit non-zero and
    # name the branch on stderr.
    plan = _write_plan(tmp_path, "**pr_target**: RC9.9")
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.delivery_branch_lint",
         "--plan", str(plan)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
        env={**os.environ, "QOR_DELIVERY_BRANCH_LINT_FAKE": "absent"},
    )
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert "RC9.9" in result.stderr


def test_plan_schema_accepts_pr_target():
    # plan.schema.json must declare pr_target as an optional string: a string
    # value validates; a non-string value is rejected (additionalProperties
    # alone would let 123 through).
    schema = json.loads(
        (REPO_ROOT / "qor/gates/schema/plan.schema.json").read_text(encoding="utf-8")
    )
    base = {
        "phase": "plan", "ts": "2026-05-22T00:00:00Z", "session_id": "test-sid",
        "plan_path": "docs/plan-x.md", "phases": ["P1"], "ci_commands": ["pytest"],
    }
    jsonschema.validate({**base, "pr_target": "RC1.4"}, schema)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({**base, "pr_target": 123}, schema)
