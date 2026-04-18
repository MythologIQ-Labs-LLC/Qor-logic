"""Phase 31 Phase 1: /qor-audit SKILL.md contains an explicit Python block
that invokes `doc_integrity.render_drift_section`.

Before this phase the SKILL described rendering drift in prose only; LLM
host might or might not execute the helper. Phase 31 requires an explicit
code block naming the invocation so the prompt mechanically drives it.
"""
from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "SKILL.md"
AUDIT_TEMPLATE = (
    REPO_ROOT / "qor" / "skills" / "governance" / "qor-audit" / "references" / "qor-audit-templates.md"
)


def test_audit_skill_has_drift_invocation_block():
    body = AUDIT_SKILL.read_text(encoding="utf-8")
    # Find the Documentation Drift section
    assert "Documentation Drift" in body, "Audit SKILL must declare Documentation Drift section"
    # Scan for a python fence referencing render_drift_section
    py_fences = re.findall(r"```python\s*\n(.*?)\n```", body, re.DOTALL)
    found = any("render_drift_section" in fence for fence in py_fences)
    assert found, (
        "Audit SKILL's Documentation Drift section must contain a ```python fence "
        "invoking doc_integrity.render_drift_section"
    )


def test_audit_template_has_drift_marker():
    body = AUDIT_TEMPLATE.read_text(encoding="utf-8")
    assert "<!-- qor:drift-section -->" in body, (
        "qor-audit-templates.md must carry the <!-- qor:drift-section --> marker "
        "so generated AUDIT_REPORT.md has a canonical insertion point for drift output"
    )
