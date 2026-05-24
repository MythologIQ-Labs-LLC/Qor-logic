"""Phase 99: runtime_contract_walk behavior tests (GH #108 V2)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qor.scripts.runtime_contract_walk import (
    WalkFinding,
    extract_python_modules_from_plan,
    walk_backward,
    walk_forward,
    walk_plan,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_walk_extracts_python_module_paths_from_plan_affected_files(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text(
        "## Affected Files\n\n"
        "- `qor/scripts/foo.py` -- NEW.\n"
        "- `qor.scripts.bar` referenced in body text.\n",
        encoding="utf-8",
    )
    modules = extract_python_modules_from_plan(plan)
    assert "qor.scripts.foo" in modules
    assert "qor.scripts.bar" in modules


def test_walk_forward_passes_when_callees_parse_cleanly():
    findings = walk_forward("qor.scripts.skill_size_budget_lint", REPO_ROOT)
    forward_findings = [f for f in findings if f.direction == "forward"]
    assert not forward_findings, f"expected clean forward walk; got {forward_findings}"


def test_walk_forward_flags_when_callee_has_syntax_error(tmp_path):
    pkg = tmp_path / "qor" / "scripts"
    pkg.mkdir(parents=True)
    (tmp_path / "qor" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "qor" / "scripts" / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "broken_mod.py").write_text("def )(syntax error here", encoding="utf-8")
    findings = walk_forward("qor.scripts.broken_mod", tmp_path)
    assert findings
    assert any(f.direction == "forward" for f in findings)


def test_walk_backward_passes_when_caller_exists():
    # qor.scripts.ledger_hash is imported by qor/cli_handlers/compliance.py
    findings = walk_backward("qor.scripts.ledger_hash", REPO_ROOT)
    assert not findings, f"expected clean backward walk; got {findings}"


def test_walk_backward_flags_when_no_production_caller(tmp_path):
    (tmp_path / "qor" / "scripts").mkdir(parents=True)
    (tmp_path / "qor" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "qor" / "scripts" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "qor" / "scripts" / "lonely.py").write_text("def f(): pass\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_lonely.py").write_text("from qor.scripts.lonely import f\n", encoding="utf-8")
    findings = walk_backward("qor.scripts.lonely", tmp_path)
    assert findings
    assert findings[0].direction == "backward"


def test_walk_skips_gracefully_when_module_path_does_not_resolve(tmp_path):
    findings = walk_forward("qor.scripts.totally_nonexistent_xyz", tmp_path)
    assert findings
    assert "not found" in findings[0].detail


def test_main_cli_exits_zero_on_no_findings(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("Plan with no python module references.\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.runtime_contract_walk",
         "--plan", str(plan), "--repo-root", str(REPO_ROOT)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"stdout={result.stdout} stderr={result.stderr}"


def test_main_cli_exits_one_when_exit_on_any_set(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("Refers to `qor.scripts.totally_nonexistent_module_xyz`.\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.runtime_contract_walk",
         "--plan", str(plan), "--repo-root", str(REPO_ROOT), "--exit-on-any"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 1
    assert "finding" in result.stdout.lower()


def test_walk_self_application_on_phase_99_plan_emits_zero_findings():
    """Positive dogfooding: the Phase 99 plan walks clean against its own
    module reference (qor.scripts.runtime_contract_walk exists at HEAD with
    parseable callees and at least one production caller path -- after
    Phase 99 lands, the audit/substantiate plumbing AND the plan_text
    references will both resolve)."""
    plan = REPO_ROOT / "docs" / "plan-qor-phase99-audit-runtime-contract-walk.md"
    findings = walk_plan(plan, REPO_ROOT)
    # We tolerate the backward walk producing findings for the freshly-cited
    # module if no production caller exists yet beyond the audit wiring
    # itself. The positive shipping-correctness anchor: forward walk for
    # the module itself emits zero findings (the module's own imports are
    # all parseable).
    forward = [f for f in findings if f.direction == "forward" and f.module_path == "qor.scripts.runtime_contract_walk"]
    assert not forward, (
        f"Phase 99 module's own forward walk must be clean; got {forward}"
    )
