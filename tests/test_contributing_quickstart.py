"""Phase 29 Phase 2: CONTRIBUTING.md pointer + quickstart, orphan adoption.

Closes GAP-REPO-07 (no CONTRIBUTING.md) with a minimal pointer-to-chain doc.
Also guards the Phase 28 documentation-integrity rule: every glossary entry
introduced in phase28-documentation-integrity must retain a non-empty
referenced_by: list (no re-orphaning across phases).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRIBUTING = REPO_ROOT / "CONTRIBUTING.md"
GLOSSARY = REPO_ROOT / "qor" / "references" / "glossary.md"


def test_contributing_md_exists():
    assert CONTRIBUTING.exists(), f"CONTRIBUTING.md missing at {CONTRIBUTING}"


def test_contributing_names_canonical_skill_chain():
    body = CONTRIBUTING.read_text(encoding="utf-8")
    chain = ["/qor-research", "/qor-plan", "/qor-audit", "/qor-implement", "/qor-substantiate"]
    positions = [body.find(skill) for skill in chain]
    assert all(p >= 0 for p in positions), f"Missing skills: {[c for c, p in zip(chain, positions) if p < 0]}"
    assert positions == sorted(positions), f"Skill chain out of order: positions={positions}"


def test_contributing_references_governance_enforcement_for_pr_template():
    """Single source of truth: PR contract lives in doctrine-governance-enforcement.md.
    CONTRIBUTING must delegate there, not duplicate the rules."""
    body = CONTRIBUTING.read_text(encoding="utf-8")
    assert "doctrine-governance-enforcement" in body, (
        "CONTRIBUTING must cite doctrine-governance-enforcement.md for PR contract"
    )


def test_contributing_under_line_limit():
    """Option-B scope fence: prevents creeping into full template/example territory."""
    lines = CONTRIBUTING.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 80, f"CONTRIBUTING.md is {len(lines)} lines; cap is 80"


def test_glossary_doctrine_entry_names_contributing():
    entries = {e.term: e for e in doc_integrity.parse_glossary(str(GLOSSARY))}
    assert "Doctrine" in entries
    assert "CONTRIBUTING.md" in entries["Doctrine"].referenced_by, (
        f"Doctrine entry referenced_by should include CONTRIBUTING.md; got {entries['Doctrine'].referenced_by}"
    )


def test_no_phase28_orphan_terms_remain():
    """Ground 1 of audit pass-1 remediation: every glossary entry with
    introduced_in_plan=phase28-documentation-integrity must have a non-empty
    referenced_by: list. Forward-looking regression check for future phases."""
    entries = doc_integrity.parse_glossary(str(GLOSSARY))
    phase28_entries = [e for e in entries if e.introduced_in_plan == "phase28-documentation-integrity"]
    assert phase28_entries, "No phase28-introduced entries found; test precondition not met"
    orphans = [e.term for e in phase28_entries if not e.referenced_by]
    assert not orphans, f"Phase-28-introduced entries lacking referenced_by: {orphans}"
