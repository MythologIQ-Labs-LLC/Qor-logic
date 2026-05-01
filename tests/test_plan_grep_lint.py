"""Phase 55: tests for the infrastructure-mismatch citation detector."""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from qor.scripts.plan_grep_lint import check_plan

REPO_ROOT = Path(__file__).resolve().parent.parent


def _write_plan(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "plan.md"
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "qor" / "scripts").mkdir(parents=True)
    (repo / "qor" / "scripts" / "session.py").write_text("# session", encoding="utf-8")
    (repo / "qor" / "skills" / "test").mkdir(parents=True)
    (repo / "qor" / "skills" / "test" / "SKILL.md").write_text("---\n---", encoding="utf-8")
    return repo


def test_lint_detects_missing_module_citation(tmp_path):
    repo = _make_repo(tmp_path)
    plan = _write_plan(tmp_path, """
        # Plan
        ## Phase 1
        Plan cites `qor.scripts.imaginary_module` for the helper.
    """)
    warnings = check_plan(plan, repo)
    assert len(warnings) == 1
    assert "qor.scripts.imaginary_module" in warnings[0].citation


def test_lint_passes_for_existing_module_citation(tmp_path):
    repo = _make_repo(tmp_path)
    plan = _write_plan(tmp_path, """
        # Plan
        Plan cites `qor.scripts.session` (existing).
    """)
    warnings = check_plan(plan, repo)
    assert warnings == []


def test_lint_excludes_paths_declared_as_new_in_affected_files(tmp_path):
    repo = _make_repo(tmp_path)
    plan = _write_plan(tmp_path, """
        # Plan
        ## Phase 1
        ### Affected Files
        - `qor/scripts/new_helper.py` — NEW
        ### Changes
        Calls `qor.scripts.new_helper` to do work.
    """)
    warnings = check_plan(plan, repo)
    assert warnings == []


def test_lint_detects_missing_skill_path(tmp_path):
    repo = _make_repo(tmp_path)
    plan = _write_plan(tmp_path, """
        Plan cites qor/skills/sdlc/imaginary/SKILL.md for testing.
    """)
    warnings = check_plan(plan, repo)
    assert len(warnings) == 1
    assert "imaginary" in warnings[0].citation


def test_lint_handles_plan_with_no_module_citations(tmp_path):
    repo = _make_repo(tmp_path)
    plan = _write_plan(tmp_path, "# Plan\n\nNo Python references.\n")
    warnings = check_plan(plan, repo)
    assert warnings == []


def test_lint_cli_emits_warnings_to_stderr(tmp_path):
    repo = _make_repo(tmp_path)
    plan = _write_plan(tmp_path, """
        Plan cites `qor.scripts.imaginary_module`.
    """)
    proc = subprocess.run(
        [sys.executable, "-m", "qor.scripts.plan_grep_lint",
         "--plan", str(plan), "--repo-root", str(repo)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0  # WARN-only
    assert "WARN [plan-grep-lint]" in proc.stderr


def test_audit_phase_skills_invoke_both_pre_audit_lints():
    """Co-occurrence behavior invariant: any SKILL.md whose phase: audit
    declares MUST invoke both plan_test_lint AND plan_grep_lint at a
    pre-Step-3 invocation site.
    """
    skills_dir = REPO_ROOT / "qor" / "skills"
    audit_skills: list[Path] = []
    import re
    for skill in skills_dir.rglob("SKILL.md"):
        body = skill.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", body, re.DOTALL)
        if not match:
            continue
        if re.search(r"^phase\s*:\s*audit\s*$", match.group(1), re.MULTILINE):
            audit_skills.append(skill)

    assert audit_skills, "expected >=1 SKILL.md with phase: audit"

    violators: list[str] = []
    for skill in audit_skills:
        body = skill.read_text(encoding="utf-8")
        if "python -m qor.scripts.plan_test_lint" not in body:
            violators.append(f"{skill.relative_to(REPO_ROOT)}: missing plan_test_lint invocation")
        if "python -m qor.scripts.plan_grep_lint" not in body:
            violators.append(f"{skill.relative_to(REPO_ROOT)}: missing plan_grep_lint invocation")
    assert not violators, "audit-phase skills must invoke both pre-audit lints: " + str(violators)
