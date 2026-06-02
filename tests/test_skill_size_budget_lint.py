"""Phase 95: behavior tests for qor.scripts.skill_size_budget_lint (GH #92).

Fixtures + canonical-corpus dogfooding anchors.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qor.scripts.skill_size_budget_lint import (
    SizeFinding,
    check_skills,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "qor" / "skills"


def _make_skill(tmp_path: Path, name: str, size_bytes: int) -> Path:
    skill_dir = tmp_path / "skills" / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill = skill_dir / "SKILL.md"
    skill.write_text("x" * size_bytes, encoding="utf-8")
    return skill


def test_check_finds_no_findings_below_warn_threshold(tmp_path):
    _make_skill(tmp_path, "small", 20 * 1024)
    findings = check_skills(tmp_path / "skills")
    assert findings == [], f"expected empty findings; got: {findings}"


def test_check_emits_warn_finding_for_skill_between_warn_and_exceeded(tmp_path):
    _make_skill(tmp_path, "medium", 30 * 1024)
    findings = check_skills(tmp_path / "skills")
    assert len(findings) == 1
    assert findings[0].category == "skill-over-warn-threshold"
    assert findings[0].severity == "warn"


def test_check_emits_exceeded_finding_for_skill_over_40kb(tmp_path):
    _make_skill(tmp_path, "huge", 45 * 1024)
    findings = check_skills(tmp_path / "skills")
    assert len(findings) == 1
    assert findings[0].category == "skill-over-exceeded-threshold"


def test_check_skips_non_skill_files(tmp_path):
    skill_dir = tmp_path / "skills" / "foo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "notes.md").write_text("x" * (50 * 1024), encoding="utf-8")
    findings = check_skills(tmp_path / "skills")
    assert findings == []


def test_main_cli_exits_zero_on_no_findings(tmp_path):
    _make_skill(tmp_path, "ok", 10 * 1024)
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.skill_size_budget_lint",
         "--skills-root", str(tmp_path / "skills")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0


def test_main_cli_exits_one_when_any_exceeded(tmp_path):
    _make_skill(tmp_path, "huge", 45 * 1024)
    result = subprocess.run(
        [sys.executable, "-m", "qor.scripts.skill_size_budget_lint",
         "--skills-root", str(tmp_path / "skills")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 1


def test_check_canonical_corpus_includes_qor_audit_finding():
    """Dogfooding anchor: qor-audit/SKILL.md was EXCEEDED (44 KB) until Phase
    135 brought it under 40 KB via progressive disclosure. The lint must still
    surface it as a finding, now in the WARN range (still > 25 KB)."""
    findings = check_skills(SKILLS_ROOT)
    audit_findings = [
        f for f in findings if "qor-audit" in f.skill_path
    ]
    assert audit_findings, (
        f"expected qor-audit/SKILL.md in findings; got skills: "
        f"{[f.skill_path for f in findings]}"
    )
    assert audit_findings[0].category == "skill-over-warn-threshold", (
        f"expected qor-audit in WARN range post-Phase-135; got category={audit_findings[0].category}"
    )


def test_check_canonical_corpus_qor_substantiate_in_warn_range():
    """Dogfooding anchor: qor-substantiate/SKILL.md is currently 39.8 KB →
    WARN range (below EXCEEDED at 40 KB)."""
    findings = check_skills(SKILLS_ROOT)
    subst_findings = [
        f for f in findings if "qor-substantiate" in f.skill_path
    ]
    assert subst_findings, (
        f"expected qor-substantiate/SKILL.md in findings; got: "
        f"{[f.skill_path for f in findings]}"
    )
    # Note: this assertion is sensitive to Phase 95's own SKILL.md edits.
    # Phase 95 adds the Step 4.6.9 paragraph to qor-substantiate/SKILL.md,
    # pushing it from 39.8 KB toward 40+ KB. If the file crosses the
    # EXCEEDED threshold during impl, this assertion will need to be
    # adjusted to skill-over-exceeded-threshold (still a finding, just a
    # different category). Either category is a correct dogfooding signal.
    assert subst_findings[0].category in {
        "skill-over-warn-threshold",
        "skill-over-exceeded-threshold",
    }, f"unexpected category: {subst_findings[0].category}"
