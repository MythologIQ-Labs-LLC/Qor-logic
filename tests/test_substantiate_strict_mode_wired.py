"""Phase 32 Phase 3: /qor-substantiate Step 4.7 invokes run_all_checks_from_plan
with strict=True. Also verifies composite routing behavior.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
SUBSTANTIATE_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"


def test_step_4_7_passes_strict_true():
    """Structural: Step 4.7 Python block must call run_all_checks_from_plan
    with strict=True kwarg."""
    body = SUBSTANTIATE_SKILL.read_text(encoding="utf-8")
    idx = body.find("### Step 4.7")
    assert idx >= 0, "Step 4.7 missing"
    step_end = body.find("### Step 5", idx)
    section = body[idx:step_end]
    # Find the run_all_checks_from_plan call and assert strict=True is present
    assert "run_all_checks_from_plan" in section, "Step 4.7 must invoke composite check"
    assert re.search(r"run_all_checks_from_plan\s*\([^)]*strict=True", section, re.DOTALL), (
        "Step 4.7 must pass strict=True to run_all_checks_from_plan"
    )


def test_composite_routes_strict_to_strict_module(tmp_path):
    """Behavioral: strict=True routes through doc_integrity_strict and raises
    on the first D finding."""
    (tmp_path / "qor" / "references").mkdir(parents=True)
    (tmp_path / "qor" / "references" / "glossary.md").write_text(
        "```yaml\n"
        "term: Foo\n"
        "definition: A thing.\n"
        "home: qor/gates/home.md\n"
        "referenced_by:\n"
        "  - qor/gates/home.md\n"
        "```\n", encoding="utf-8",
    )
    (tmp_path / "qor" / "gates").mkdir(parents=True)
    (tmp_path / "qor" / "gates" / "home.md").write_text("Foo defined.\n", encoding="utf-8")
    (tmp_path / "qor" / "skills" / "unrelated").mkdir(parents=True)
    (tmp_path / "qor" / "skills" / "unrelated" / "leak.md").write_text("Foo drifting here.\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# r\n", encoding="utf-8")
    plan = {
        "doc_tier": "standard",
        "terms": [{"term": "Foo", "home": "qor/gates/home.md"}],
        "plan_slug": "phase99-test",
    }
    with pytest.raises(ValueError, match="Foo"):
        doc_integrity.run_all_checks_from_plan(plan, repo_root=str(tmp_path), strict=True)


def test_composite_lenient_still_default(tmp_path):
    """Regression guard: without strict=True, drift findings don't raise."""
    (tmp_path / "qor" / "references").mkdir(parents=True)
    (tmp_path / "qor" / "references" / "glossary.md").write_text(
        "```yaml\n"
        "term: Foo\n"
        "definition: A thing.\n"
        "home: qor/gates/home.md\n"
        "referenced_by:\n"
        "  - qor/gates/home.md\n"
        "```\n", encoding="utf-8",
    )
    (tmp_path / "qor" / "gates").mkdir(parents=True)
    (tmp_path / "qor" / "gates" / "home.md").write_text("Foo defined.\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# r\n", encoding="utf-8")
    plan = {
        "doc_tier": "standard",
        "terms": [{"term": "Foo", "home": "qor/gates/home.md"}],
        "plan_slug": "phase99-test",
    }
    # Should complete without raising (lenient default)
    doc_integrity.run_all_checks_from_plan(plan, repo_root=str(tmp_path))
