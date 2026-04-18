"""Phase 30 Phase 1 (Ground 2 remediation): Session Rotation glossary + doctrine.

Asserts the term is formally declared in the canonical glossary with its home
and consumers, AND that doctrine-governance-enforcement.md has §7 body content.
Guards SG-Phase30-B (metadata-only term declaration) from recurring.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = REPO_ROOT / "qor" / "references" / "glossary.md"
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-governance-enforcement.md"


def test_session_rotation_entry_in_glossary():
    entries = {e.term: e for e in doc_integrity.parse_glossary(str(GLOSSARY))}
    assert "Session Rotation" in entries, (
        f"Session Rotation entry missing; got terms: {sorted(entries.keys())}"
    )
    e = entries["Session Rotation"]
    assert e.definition.strip(), "Session Rotation entry has empty definition"
    assert e.home == "qor/references/doctrine-governance-enforcement.md", (
        f"Unexpected home: {e.home}"
    )
    assert "qor/scripts/session.py" in e.referenced_by
    assert "qor/skills/governance/qor-substantiate/SKILL.md" in e.referenced_by


def test_governance_enforcement_doctrine_has_session_rotation_section():
    body = DOCTRINE.read_text(encoding="utf-8")
    assert "## 7." in body or "## Session Rotation" in body, (
        "doctrine-governance-enforcement.md missing §7 Session Rotation header"
    )
    # Section body must be non-trivial -- at least 50 characters after the header.
    idx = max(body.find("## 7."), body.find("## Session Rotation"))
    next_section = body.find("\n## ", idx + 1)
    section_body = body[idx:next_section if next_section > 0 else len(body)]
    assert len(section_body) > 80, (
        f"Session Rotation section too short ({len(section_body)} chars); "
        "suspected metadata-only declaration (SG-Phase30-B)"
    )
