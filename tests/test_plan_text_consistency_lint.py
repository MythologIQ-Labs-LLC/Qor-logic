"""Phase 45 V1 lint behavior tests.

Verifies:
- 5 operation kinds detected (cargo_test, cargo_build, python_module,
  python_script, filesystem_path).
- Broad-rule drift detection (same kind + 2+ distinct normalized).
- Asymmetric drift for filesystem_path (same normalized + 2+ distinct raw_text).
- Placeholder code-spans skipped.
- Section attribution uses nearest preceding heading.
- CLI exit codes match finding presence; stderr describes findings.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from qor.scripts.plan_text_consistency_lint import lint, main


def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "plan.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_no_drift_clean_plan_returns_empty(tmp_path):
    body = "# Plan\n\n## Phase 1\n\nRun `cargo test --features X`.\n"
    assert lint(body) == []


def test_cargo_test_drift_detected_when_two_distinct_invocations(tmp_path):
    body = (
        "# Plan\n\n"
        "## Unit Tests\n\nRun `cargo test --features X`.\n\n"
        "## CI Commands\n\nRun `cargo test --features Y`.\n"
    )
    findings = lint(body)
    assert len(findings) == 1
    assert findings[0].operation_kind == "cargo_test"
    assert len(findings[0].sites) == 2
    sections = {s.section for s in findings[0].sites}
    assert "Unit Tests" in sections
    assert "CI Commands" in sections


def test_cargo_build_drift_detected(tmp_path):
    body = (
        "# Plan\n\n"
        "## A\n\n`cargo build --release`\n\n"
        "## B\n\n`cargo build`\n"
    )
    findings = lint(body)
    assert len(findings) == 1
    assert findings[0].operation_kind == "cargo_build"


def test_python_module_drift_detected(tmp_path):
    body = (
        "# Plan\n\n"
        "## A\n\n`python -m foo`\n\n"
        "## B\n\n`python -m bar`\n"
    )
    findings = lint(body, strict=True)
    assert len(findings) == 1
    assert findings[0].operation_kind == "python_module"


def test_python_script_drift_detected(tmp_path):
    body = (
        "# Plan\n\n"
        "## A\n\n`python scripts/lint.py --apply`\n\n"
        "## B\n\n`python scripts/lint.py --check`\n"
    )
    findings = lint(body, strict=True)
    assert len(findings) == 1
    assert findings[0].operation_kind == "python_script"


def test_filesystem_path_drift_asymmetric_on_raw_text(tmp_path):
    body = (
        "# Plan\n\n"
        "## A\n\n`./docs/plan.md`\n\n"
        "## B\n\n`docs/plan.md`\n"
    )
    findings = lint(body)
    assert any(f.operation_kind == "filesystem_path" for f in findings)
    drift = next(f for f in findings if f.operation_kind == "filesystem_path")
    raws = {s.raw_text for s in drift.sites}
    assert raws == {"./docs/plan.md", "docs/plan.md"}


def test_filesystem_path_no_drift_when_same_raw_text(tmp_path):
    body = (
        "# Plan\n\n"
        "## A\n\n`docs/plan.md`\n\n"
        "## B\n\n`docs/plan.md`\n"
    )
    findings = [f for f in lint(body) if f.operation_kind == "filesystem_path"]
    assert findings == []


def test_placeholder_codespan_is_skipped(tmp_path):
    body = (
        "# Plan\n\n"
        "## A\n\n`cargo test --features <feature>`\n\n"
        "## B\n\n`cargo test --features {placeholder}`\n\n"
        "## C\n\n`cargo test --features ...`\n"
    )
    findings = lint(body)
    assert findings == []


def test_section_attribution_uses_nearest_heading(tmp_path):
    body = (
        "# Plan\n\n"
        "## Outer\n\n"
        "Some prose.\n\n"
        "### Inner\n\n"
        "`cargo test --features X`\n"
    )
    findings = [f for f in lint(_codespan_amplifier(body))]
    assert findings == []
    sites = lint("`cargo test --features X`\n`cargo test --features Y`")
    assert sites
    sites = lint(body + "\n## Other\n\n`cargo test --features Y`\n")
    assert len(sites) == 1
    drift_sections = {s.section for s in sites[0].sites}
    assert "Inner" in drift_sections
    assert "Other" in drift_sections


def _codespan_amplifier(text: str) -> str:
    return text


def test_fenced_code_blocks_skipped(tmp_path):
    body = (
        "# Plan\n\n"
        "## A\n\n```\ncargo test --features X\n```\n\n"
        "## B\n\n`cargo test --features Y`\n"
    )
    findings = lint(body)
    assert findings == []


def test_cli_check_exit_code_zero_on_clean_plan(tmp_path):
    p = _write(tmp_path, "# Plan\n\n`cargo test --features X`\n")
    assert main(["--check", str(p)]) == 0


def test_cli_check_exit_code_one_on_drift(tmp_path):
    body = "# Plan\n\n`cargo test --features X`\n\n`cargo test --features Y`\n"
    p = _write(tmp_path, body)
    assert main(["--check", str(p)]) == 1


def test_cli_check_exit_code_two_on_missing_file(tmp_path):
    assert main(["--check", str(tmp_path / "no.md")]) == 2


def test_cli_stderr_describes_findings(tmp_path, capsys):
    body = "# Plan\n\n`cargo test --features X`\n\n`cargo test --features Y`\n"
    p = _write(tmp_path, body)
    main(["--check", str(p)])
    captured = capsys.readouterr()
    assert "drift detected" in captured.err
    assert "cargo_test" in captured.err
    assert "--features X" in captured.err
    assert "--features Y" in captured.err


def test_normalize_sorts_flags_so_flag_order_is_not_drift(tmp_path):
    body = (
        "# Plan\n\n"
        "`cargo test --release --features X`\n\n"
        "`cargo test --features X --release`\n"
    )
    findings = lint(body)
    assert findings == []


def test_module_via_python_executable(tmp_path):
    body = (
        "# Plan\n\n"
        "`python -m qor.scripts.foo`\n\n"
        "`python -m qor.scripts.bar`\n"
    )
    findings = lint(body, strict=True)
    assert len(findings) == 1
    assert findings[0].operation_kind == "python_module"
