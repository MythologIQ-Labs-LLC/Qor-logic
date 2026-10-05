"""Phase 89: behavior tests for qor.scripts.ci_coverage_lint (GH #91).

Each test uses tmp-path workflow + plan fixtures except the dedicated
self-application test, which runs the lint against Phase 89's own plan file
and a temporary copy of this repo's .github/workflows in which the Phase 303
allowance rewrites exactly one CI line (the publication-boundary step) back to
the form that sealed plan covers; every other line is copied unchanged.

Per qor/references/doctrine-test-functionality.md: each assertion verifies
the lint's behavior on a specific classification branch, not the existence
of an artifact. Fixtures construct the minimal workflow + plan shape that
would trip (or not trip) the branch under test.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from qor.scripts import ci_coverage_lint

REPO_ROOT = Path(__file__).resolve().parent.parent
LIVE_WORKFLOWS = REPO_ROOT / ".github" / "workflows"
PHASE_89_PLAN = REPO_ROOT / "docs" / "plan-qor-phase89-ci-commands-reconciliation.md"

# Phase 303 (GH #457): CI's publication-boundary step now passes
# `--expect-scope structural`. The Phase 89 plan is sealed and ledger-bound, so
# its CI Commands bullet is not edited; the self-application test maps exactly
# this one CI line back to the command that sealed plan covers.
_PHASE_303_CI_COMMAND = (
    "python -m qor.scripts.publication_boundary_lint --repo-root . --expect-scope structural")
_PHASE_89_COVERED_COMMAND = "python -m qor.scripts.publication_boundary_lint --repo-root ."


def _apply_phase_303_allowance(src: Path, dest: Path) -> int:
    """Copy every src/*.yml into dest, rewriting only the exact Phase 303 line.

    A line whose stripped text is exactly `run: <Phase 303 command>` becomes the
    same indentation plus `run: <Phase 89 covered command>`. Any other line,
    including one that differs in a single character, is copied unchanged.
    Returns how many lines were rewritten.
    """
    dest.mkdir(parents=True, exist_ok=True)
    rewritten = 0
    for wf in sorted(src.glob("*.yml")):
        out = []
        for line in wf.read_text(encoding="utf-8").splitlines(keepends=True):
            if line.strip() == f"run: {_PHASE_303_CI_COMMAND}":
                indent = line[: len(line) - len(line.lstrip())]
                eol = line[len(line.rstrip("\r\n")):]
                line = f"{indent}run: {_PHASE_89_COVERED_COMMAND}{eol}"
                rewritten += 1
            out.append(line)
        (dest / wf.name).write_text("".join(out), encoding="utf-8")
    return rewritten


def _write_workflow(tmp_path: Path, name: str, content: str) -> Path:
    wf_dir = tmp_path / "workflows"
    wf_dir.mkdir(exist_ok=True)
    p = wf_dir / name
    p.write_text(content, encoding="utf-8")
    return p


def _write_plan(tmp_path: Path, ci_commands_body: str | None,
                exemptions_body: str | None = None) -> Path:
    parts = ["# Plan: fixture", ""]
    if exemptions_body is not None:
        parts.append("## CI Coverage Exemptions")
        parts.append("")
        parts.append(exemptions_body)
        parts.append("")
    if ci_commands_body is not None:
        parts.append("## CI Commands")
        parts.append("")
        parts.append(ci_commands_body)
        parts.append("")
    plan = tmp_path / "plan.md"
    plan.write_text("\n".join(parts), encoding="utf-8")
    return plan


def test_python_pytest_command_in_workflow_matched_by_plan_yields_no_warning(tmp_path):
    _write_workflow(tmp_path, "ci.yml", """\
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: python -m pytest tests/ -v
""")
    plan = _write_plan(tmp_path, "- `python -m pytest tests/ -q` -- test runner.")
    warnings = ci_coverage_lint.check_plan(plan, tmp_path / "workflows")
    assert warnings == [], f"expected no warnings, got: {warnings}"


def test_python_script_command_missing_from_plan_yields_warning(tmp_path):
    _write_workflow(tmp_path, "ci.yml", """\
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: python qor/scripts/check_variant_drift.py
""")
    plan = _write_plan(tmp_path, ci_commands_body=None)
    warnings = ci_coverage_lint.check_plan(plan, tmp_path / "workflows")
    assert len(warnings) == 1, f"expected 1 warning, got: {warnings}"
    assert "check_variant_drift" in warnings[0].command


def test_pip_install_is_not_a_candidate(tmp_path):
    _write_workflow(tmp_path, "ci.yml", """\
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pip install -e ".[dev]"
""")
    plan = _write_plan(tmp_path, ci_commands_body=None)
    warnings = ci_coverage_lint.check_plan(plan, tmp_path / "workflows")
    assert warnings == [], f"pip install should be filtered, got: {warnings}"


def test_git_fetch_and_merge_base_are_not_candidates(tmp_path):
    _write_workflow(tmp_path, "release.yml", """\
name: Release
on: [pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: |
          git fetch origin main --depth=100
          git merge-base --is-ancestor "$GITHUB_SHA" origin/main
""")
    plan = _write_plan(tmp_path, ci_commands_body=None)
    warnings = ci_coverage_lint.check_plan(plan, tmp_path / "workflows")
    assert warnings == [], f"git plumbing should be filtered, got: {warnings}"


def test_doc_only_conditional_bash_is_not_a_candidate(tmp_path):
    _write_workflow(tmp_path, "pr-lint.yml", """\
name: PR Lint
on: [pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: |
          BASE_BRANCH="$GITHUB_BASE_REF"
          CHANGED=$(git diff --name-only)
          if [[ -z "$CHANGED" ]]; then
            echo "result=false" >> "$GITHUB_OUTPUT"
            exit 0
          fi
""")
    plan = _write_plan(tmp_path, ci_commands_body=None)
    warnings = ci_coverage_lint.check_plan(plan, tmp_path / "workflows")
    assert warnings == [], f"doc-only conditional bash should be filtered, got: {warnings}"


def test_tag_only_workflow_is_skipped(tmp_path):
    _write_workflow(tmp_path, "release.yml", """\
name: Release
on:
  push:
    tags: ['v*.*.*']
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: python -m build
""")
    plan = _write_plan(tmp_path, ci_commands_body=None)
    warnings = ci_coverage_lint.check_plan(plan, tmp_path / "workflows")
    assert warnings == [], f"tag-only workflows should be skipped, got: {warnings}"


def test_multiline_run_block_extracts_each_python_command(tmp_path):
    _write_workflow(tmp_path, "ci.yml", """\
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: |
          python -m qor.reliability.foo
          python -m qor.reliability.bar
""")
    plan = _write_plan(tmp_path, "- `python -m qor.reliability.foo` -- only one covered.")
    warnings = ci_coverage_lint.check_plan(plan, tmp_path / "workflows")
    assert len(warnings) == 1, f"expected 1 warning, got: {warnings}"
    assert "qor.reliability.bar" in warnings[0].command


def test_exemption_block_suppresses_matching_warning(tmp_path):
    _write_workflow(tmp_path, "ci.yml", """\
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: python qor/scripts/check_variant_drift.py
""")
    plan = _write_plan(
        tmp_path,
        ci_commands_body=None,
        exemptions_body="- `check_variant_drift` -- pre-existing infra CI; not phase-relevant.",
    )
    warnings = ci_coverage_lint.check_plan(plan, tmp_path / "workflows")
    assert warnings == [], f"exemption should suppress, got: {warnings}"


def test_exemption_pattern_must_appear_as_substring_of_command(tmp_path):
    _write_workflow(tmp_path, "ci.yml", """\
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: python qor/scripts/check_variant_drift.py
""")
    plan = _write_plan(
        tmp_path,
        ci_commands_body=None,
        exemptions_body="- `nonexistent_module_name` -- unrelated pattern.",
    )
    warnings = ci_coverage_lint.check_plan(plan, tmp_path / "workflows")
    assert len(warnings) == 1, f"unrelated exemption should not suppress, got: {warnings}"


def test_plan_missing_ci_commands_section_warns_for_every_candidate(tmp_path):
    _write_workflow(tmp_path, "ci.yml", """\
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: |
          python -m pytest tests/ -v
          python qor/scripts/check_variant_drift.py
""")
    plan = _write_plan(tmp_path, ci_commands_body=None)
    warnings = ci_coverage_lint.check_plan(plan, tmp_path / "workflows")
    assert len(warnings) == 2, f"expected 2 warnings (one per candidate), got: {warnings}"


def test_pytest_marker_form_is_candidate(tmp_path):
    _write_workflow(tmp_path, "ci.yml", """\
name: CI
on: [pull_request]
jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - run: python -m pytest tests/test_packaging_install.py -v -m integration
""")
    plan = _write_plan(tmp_path, ci_commands_body=None)
    warnings = ci_coverage_lint.check_plan(plan, tmp_path / "workflows")
    assert len(warnings) == 1, f"pytest marker form should be candidate, got: {warnings}"
    assert "test_packaging_install" in warnings[0].command


def test_main_cli_returns_zero_even_with_warnings(tmp_path):
    _write_workflow(tmp_path, "ci.yml", """\
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: python qor/scripts/check_variant_drift.py
""")
    plan = _write_plan(tmp_path, ci_commands_body=None)
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.ci_coverage_lint",
         "--plan", str(plan), "--workflows-dir", str(tmp_path / "workflows")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"CLI must exit 0 even when warnings emitted (WARN-only contract); "
        f"got exit={result.returncode} stderr={result.stderr!r}"
    )
    assert "check_variant_drift" in (result.stdout + result.stderr), (
        f"CLI must surface the warning command in output; got "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_lint_self_applies_to_phase_89_plan(tmp_path):
    """Self-application: the lint against Phase 89's own plan and a copy of
    this repo's workflows, with only the Phase 303 line mapped, reports zero
    WARNs. This is the deterministic shipping-correctness test for the lint.
    """
    workflows_dir = tmp_path / "workflows"
    rewritten = _apply_phase_303_allowance(LIVE_WORKFLOWS, workflows_dir)
    assert rewritten == 1, (
        f"the Phase 303 allowance must map exactly one live CI line; mapped {rewritten}")
    warnings = ci_coverage_lint.check_plan(PHASE_89_PLAN, workflows_dir)
    assert warnings == [], (
        f"Phase 89's own plan must cover its own CI surface (or exempt "
        f"explicitly). Unmatched: {warnings}"
    )


_UNCOVERED_WORKFLOW = """\
name: Extra
on: [pull_request]
jobs:
  extra:
    runs-on: ubuntu-latest
    steps:
      - run: python -m example_uncovered_check
"""


@pytest.mark.parametrize("drift", [
    "boundary-scope-value-changed", "boundary-flag-added", "unrelated-command-added"])
def test_phase_303_allowance_does_not_hide_other_ci_drift(tmp_path, drift):
    src = tmp_path / "src"
    src.mkdir()
    phase_303_line = f"run: {_PHASE_303_CI_COMMAND}"
    found = 0
    for wf in LIVE_WORKFLOWS.glob("*.yml"):
        text = wf.read_text(encoding="utf-8")
        found += sum(1 for ln in text.splitlines() if ln.strip() == phase_303_line)
        (src / wf.name).write_text(text, encoding="utf-8")
    assert found == 1, f"the Phase 303 CI line must exist exactly once; found {found}"
    if drift == "unrelated-command-added":
        (src / "extra.yml").write_text(_UNCOVERED_WORKFLOW, encoding="utf-8")
        expected = "python -m example_uncovered_check"
    else:
        expected = (_PHASE_303_CI_COMMAND.replace("structural", "structural+identity")
                    if drift == "boundary-scope-value-changed"
                    else _PHASE_303_CI_COMMAND + " --no-git")
        ci = src / "ci.yml"
        ci.write_text(ci.read_text(encoding="utf-8").replace(
            phase_303_line, f"run: {expected}"), encoding="utf-8")
    dest = tmp_path / "dest"
    rewritten = _apply_phase_303_allowance(src, dest)
    if drift == "unrelated-command-added":
        assert rewritten == 1, rewritten
    warnings = ci_coverage_lint.check_plan(PHASE_89_PLAN, dest)
    assert [w.command for w in warnings] == [expected], warnings
