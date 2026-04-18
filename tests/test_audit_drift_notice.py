"""Phase 28 Phase 3: /qor-audit Documentation Drift advisory (non-VETO).

Verifies doc_integrity.render_drift_section emits a markdown section when
the plan has doc-integrity issues, omits it when clean, and never raises
(advisory -- audit verdict stands on its own merits).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity  # noqa: E402


def _mk_clean_repo(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text("# x\n")
    (tmp_path / "qor" / "references").mkdir(parents=True)
    (tmp_path / "qor" / "references" / "glossary.md").write_text(
        "# g\n\n"
        "```yaml\n"
        "term: Foo\n"
        "definition: A thing.\n"
        "home: README.md\n"
        "introduced_in_plan: phase99-test\n"
        "```\n"
    )
    return tmp_path


def test_drift_section_absent_when_clean(tmp_path):
    _mk_clean_repo(tmp_path)
    plan = {
        "doc_tier": "standard",
        "terms": [{"term": "Foo", "home": "README.md"}],
        "plan_slug": "phase99-test",
    }
    assert doc_integrity.render_drift_section(plan, str(tmp_path)) == ""


def test_drift_section_present_on_missing_term(tmp_path):
    _mk_clean_repo(tmp_path)
    plan = {
        "doc_tier": "standard",
        "terms": [{"term": "Missing", "home": "README.md"}],
        "plan_slug": "phase99-test",
    }
    section = doc_integrity.render_drift_section(plan, str(tmp_path))
    assert section.startswith("## Documentation Drift")
    assert "Missing" in section


def test_drift_section_does_not_raise_on_violations(tmp_path):
    """Audit must never flip to VETO on drift alone -- the helper returns
    markdown text, never raises."""
    # Empty repo with system tier: catastrophic topology violations
    plan = {
        "doc_tier": "system",
        "terms": [{"term": "X", "home": "README.md"}],
        "plan_slug": "phase99-test",
    }
    section = doc_integrity.render_drift_section(plan, str(tmp_path))
    assert "Topology" in section
    assert "Documentation Drift" in section
    # No exception, even with cascading violations.


def test_drift_section_legacy_bypass(tmp_path):
    """Legacy tier means no drift ever reported (already logged elsewhere)."""
    plan = {"doc_tier": "legacy"}
    assert doc_integrity.render_drift_section(plan, str(tmp_path)) == ""
