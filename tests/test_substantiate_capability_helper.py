"""Phase 75 P1: substantiate_capability helper tests."""
from pathlib import Path

import pytest

from qor.scripts import substantiate_capability as sc


def test_parser_extracts_step_prerequisites_table_from_skill_md():
    rows = sc.parse_step_prerequisites(Path("qor/skills/governance/qor-substantiate/SKILL.md"))
    assert len(rows) >= 12, f"Expected 12+ V1 step rows, found {len(rows)}"
    step_ids = {r.step_id for r in rows}
    expected = {"4.6", "4.6.5", "4.6.6", "4.7", "6.5", "6.8", "7.4", "7.5", "7.6", "7.7", "7.8", "8.5"}
    missing = expected - step_ids
    assert not missing, f"Missing expected step ids in table: {missing}"


def test_check_step_file_predicate_returns_present_when_path_exists(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text(
        "# X\n## Step Prerequisites\n\n"
        "| Step | Requires | Notes |\n"
        "|---|---|---|\n"
        "| 9.9 fake step | file:CHANGELOG.md | x |\n",
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text("changelog", encoding="utf-8")
    rows = sc.parse_step_prerequisites(skill)
    report = sc.check_step(rows[0], repo_root=tmp_path)
    assert report.present is True
    assert "CHANGELOG.md" in report.evidence


def test_check_step_module_predicate_returns_absent_when_module_missing(tmp_path):
    row = sc.PrereqRow(step_id="9.9", requires="module:nonexistent_module_xyz_12345", notes="x")
    report = sc.check_step(row, repo_root=tmp_path)
    assert report.present is False
    assert "not found" in report.evidence.lower() or "no module" in report.evidence.lower()


def test_check_step_command_predicate_returns_absent_when_binary_not_on_path(tmp_path):
    row = sc.PrereqRow(step_id="9.9", requires="command:definitely-not-a-real-cli-12345", notes="x")
    report = sc.check_step(row, repo_root=tmp_path)
    assert report.present is False
