"""Phase 28 Phase 3: /qor-substantiate Step 4.7 doc-integrity enforcement.

Tests the helper doc_integrity.run_all_checks_from_plan which substantiate
invokes. Substantiate's SKILL.md wraps this in an ABORT-on-ValueError step.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity  # noqa: E402


def _mk_repo(tmp_path: Path, tier: str = "standard") -> Path:
    (tmp_path / "README.md").write_text("# x\n")
    (tmp_path / "qor" / "references").mkdir(parents=True)
    (tmp_path / "qor" / "references" / "glossary.md").write_text(
        "# Glossary\n\n"
        "```yaml\n"
        "term: Foo\n"
        "definition: A thing.\n"
        "home: README.md\n"
        "introduced_in_plan: phase99-test\n"
        "```\n"
    )
    if tier == "system":
        (tmp_path / "docs").mkdir(exist_ok=True)
        for name in ("architecture.md", "lifecycle.md", "operations.md", "policies.md"):
            (tmp_path / "docs" / name).write_text("# x\n")
    return tmp_path


def test_substantiate_aborts_on_missing_topology(tmp_path):
    """System-tier plan, missing architecture.md -> ValueError."""
    _mk_repo(tmp_path, tier="standard")  # missing system artifacts
    plan = {
        "doc_tier": "system",
        "terms": [{"term": "Foo", "home": "README.md"}],
        "plan_slug": "phase99-test",
    }
    with pytest.raises(ValueError, match="architecture"):
        doc_integrity.run_all_checks_from_plan(plan, repo_root=str(tmp_path))


def test_substantiate_aborts_on_undeclared_term_usage(tmp_path):
    """Plan declares Missing; glossary lacks it -> raise."""
    _mk_repo(tmp_path)
    plan = {
        "doc_tier": "standard",
        "terms": [{"term": "Missing", "home": "README.md"}],
        "plan_slug": "phase99-test",
    }
    with pytest.raises(ValueError, match="Missing"):
        doc_integrity.run_all_checks_from_plan(plan, repo_root=str(tmp_path))


def test_substantiate_passes_legacy_tier(tmp_path):
    """Legacy tier bypasses all checks; even empty repo passes."""
    plan = {
        "doc_tier": "legacy",
        "doc_tier_rationale": "legacy repo",
        "plan_slug": "phase99-test",
    }
    doc_integrity.run_all_checks_from_plan(plan, repo_root=str(tmp_path))


def test_substantiate_passes_clean_standard_plan(tmp_path):
    _mk_repo(tmp_path)
    plan = {
        "doc_tier": "standard",
        "terms": [{"term": "Foo", "home": "README.md"}],
        "plan_slug": "phase99-test",
    }
    doc_integrity.run_all_checks_from_plan(plan, repo_root=str(tmp_path))


def test_substantiate_does_not_retry_silently(tmp_path):
    """One ValueError should abort; no degraded retry path."""
    _mk_repo(tmp_path)
    plan = {
        "doc_tier": "standard",
        "terms": [{"term": "Missing", "home": "README.md"}],
        "plan_slug": "phase99-test",
    }
    # First call raises
    with pytest.raises(ValueError):
        doc_integrity.run_all_checks_from_plan(plan, repo_root=str(tmp_path))
    # Same call on same state must also raise (no caching that hides it)
    with pytest.raises(ValueError):
        doc_integrity.run_all_checks_from_plan(plan, repo_root=str(tmp_path))
