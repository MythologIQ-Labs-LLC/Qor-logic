"""Phase 48 V2 behavior tests: identity-based grouping + dep_name kind + --strict."""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts.plan_text_consistency_lint import lint, main


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "plan.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_v2_default_groups_pytest_invocations_by_identity():
    body = (
        "# Plan\n\n"
        "## CI Commands\n\n"
        "`python -m pytest tests/a.py`\n\n"
        "`python -m pytest tests/b.py`\n"
    )
    findings = lint(body)
    assert findings == [], "V2 default should treat distinct pytest modules as separate identities"


def test_v2_strict_flag_flags_v1_false_positive_class():
    body = (
        "# Plan\n\n"
        "## CI Commands\n\n"
        "`python -m pytest tests/a.py`\n\n"
        "`python -m pytest tests/b.py`\n"
    )
    findings = lint(body, strict=True)
    assert len(findings) == 1
    assert findings[0].operation_kind == "python_module"


def test_v2_python_module_same_target_different_args_is_drift():
    body = (
        "# Plan\n\n"
        "`python -m pytest tests/a.py -v`\n\n"
        "`python -m pytest tests/a.py`\n"
    )
    findings = lint(body)
    assert len(findings) == 1
    assert findings[0].operation_kind == "python_module"


def test_v2_python_script_apply_vs_check_distinct_identity():
    body = (
        "# Plan\n\n"
        "`python scripts/lint.py --apply X`\n\n"
        "`python scripts/lint.py --check Y`\n"
    )
    findings = lint(body)
    assert findings == []


def test_v2_python_script_same_first_arg_different_rest_is_drift():
    body = (
        "# Plan\n\n"
        "`python scripts/lint.py --check X`\n\n"
        "`python scripts/lint.py --check Y -v`\n"
    )
    findings = lint(body)
    assert len(findings) == 1
    assert findings[0].operation_kind == "python_script"


def test_v2_cargo_test_same_target_different_flags_is_drift():
    body = (
        "# Plan\n\n"
        "`cargo test --features X consumerrepo::skill`\n\n"
        "`cargo test --features Y consumerrepo::skill`\n"
    )
    findings = lint(body)
    assert len(findings) == 1
    assert findings[0].operation_kind == "cargo_test"


def test_v2_cargo_test_different_targets_no_drift():
    body = (
        "# Plan\n\n"
        "`cargo test --release consumerrepo::module_a`\n\n"
        "`cargo test --release consumerrepo::module_b`\n"
    )
    findings = lint(body)
    assert findings == []


def test_dep_name_drift_when_named_but_not_declared_in_cargo(tmp_path):
    (tmp_path / "Cargo.toml").write_text(
        "[package]\nname = \"x\"\n\n[dependencies]\nchrono = \"0.4\"\n",
        encoding="utf-8",
    )
    plan_body = (
        "# Plan\n\n"
        "## Phase 1\n\n"
        "| Module | Imports |\n"
        "|---|---|\n"
        "| foo | schemars chrono |\n"
    )
    findings = lint(plan_body, repo_root=tmp_path)
    dep_findings = [f for f in findings if f.operation_kind == "dep_name"]
    assert any("schemars" in s.raw_text for f in dep_findings for s in f.sites)
    assert not any("chrono" in s.raw_text for f in dep_findings for s in f.sites)


def test_dep_name_no_drift_when_all_declared(tmp_path):
    (tmp_path / "Cargo.toml").write_text(
        "[dependencies]\nschemars = \"0.8\"\nchrono = \"0.4\"\n",
        encoding="utf-8",
    )
    plan_body = (
        "# Plan\n\n"
        "| Module | Imports |\n"
        "|---|---|\n"
        "| foo | schemars chrono |\n"
    )
    findings = lint(plan_body, repo_root=tmp_path)
    dep_findings = [f for f in findings if f.operation_kind == "dep_name"]
    assert dep_findings == []


def test_dep_name_handles_missing_cargo_toml_no_findings(tmp_path):
    plan_body = (
        "# Plan\n\n"
        "| Module | Imports |\n"
        "|---|---|\n"
        "| foo | schemars |\n"
    )
    findings = lint(plan_body, repo_root=tmp_path)
    assert [f for f in findings if f.operation_kind == "dep_name"] == []


def test_dep_name_handles_python_requirements(tmp_path):
    (tmp_path / "requirements.txt").write_text("pydantic==2.0\n", encoding="utf-8")
    plan_body = (
        "# Plan\n\n"
        "| Module | Imports |\n"
        "|---|---|\n"
        "| foo | pydantic numpy |\n"
    )
    findings = lint(plan_body, repo_root=tmp_path)
    dep_findings = [f for f in findings if f.operation_kind == "dep_name"]
    assert any("numpy" in s.raw_text for f in dep_findings for s in f.sites)
    assert not any("pydantic" in s.raw_text for f in dep_findings for s in f.sites)


def test_v2_phase45_plan_pytest_section_not_flagged(tmp_path):
    body = (
        "# Plan\n\n"
        "## CI Commands\n\n"
        "`python -m pytest tests/test_a.py -v`\n\n"
        "`python -m pytest tests/test_b.py -v`\n\n"
        "`python -m pytest tests/test_c.py -v`\n\n"
        "`python -m pytest tests/test_d.py -v`\n\n"
        "`python -m pytest -x`\n\n"
        "`python -m qor.scripts.plan_text_consistency_lint --check x.md`\n\n"
        "`python -m qor.scripts.ledger_hash`\n"
    )
    findings = lint(body)
    assert findings == [], "the Phase 45 false-positive class should be clean under V2 default"


def test_cli_strict_flag_via_main(tmp_path):
    body = (
        "# Plan\n\n"
        "`python -m foo`\n\n"
        "`python -m bar`\n"
    )
    p = _write(tmp_path, body)
    assert main(["--check", str(p)]) == 0
    assert main(["--check", str(p), "--strict"]) == 1
