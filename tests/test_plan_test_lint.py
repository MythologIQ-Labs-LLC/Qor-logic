"""Phase 55: tests for the presence-only test detector."""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from qor.scripts.plan_test_lint import check_plan

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write_plan(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "plan.md"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


def test_lint_detects_substring_presence_pattern(tmp_path):
    plan = _write_plan(tmp_path, """
        # Plan
        ## Phase 1
        ### Unit Tests
        - `test_x` — asserts the body contains the literal "foo".
    """)
    warnings = check_plan(plan)
    assert len(warnings) == 1
    assert warnings[0].pattern == "substring-presence"


def test_lint_detects_section_exists_pattern(tmp_path):
    plan = _write_plan(tmp_path, """
        ### Unit Tests
        - `test_x` — asserts the section exists.
    """)
    warnings = check_plan(plan)
    assert len(warnings) == 1
    assert warnings[0].pattern == "section-exists"


def test_lint_detects_substring_in_file_pattern(tmp_path):
    plan = _write_plan(tmp_path, """
        ### Unit Tests
        - `test_x` — assert "foo" in <file_text>.
    """)
    warnings = check_plan(plan)
    assert len(warnings) == 1


def test_lint_detects_path_exists_pattern(tmp_path):
    plan = _write_plan(tmp_path, """
        ### Unit Tests
        - `test_x` — assert path.exists().
    """)
    warnings = check_plan(plan)
    assert len(warnings) == 1
    assert warnings[0].pattern == "path-exists"


def test_lint_passes_for_behavior_invariant_test(tmp_path):
    plan = _write_plan(tmp_path, """
        ### Unit Tests
        - `test_x` — invokes scan() with input X and asserts the returned hit class is "y".
    """)
    warnings = check_plan(plan)
    assert warnings == []


def test_lint_handles_plan_without_test_descriptions(tmp_path):
    plan = _write_plan(tmp_path, "# Plan\n\nNo test bullets here.\n")
    warnings = check_plan(plan)
    assert warnings == []


def test_lint_cli_emits_warnings_to_stderr_with_line_numbers(tmp_path):
    plan = _write_plan(tmp_path, """
        ### Unit Tests
        - `test_x` — asserts the body contains the literal "foo".
    """)
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.plan_test_lint", "--plan", str(plan)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0  # WARN-only
    assert "WARN [plan-test-lint]" in proc.stderr
    assert "substring-presence" in proc.stderr


def test_lint_handles_missing_plan(tmp_path):
    plan = tmp_path / "missing.md"
    warnings = check_plan(plan)
    assert warnings == []
