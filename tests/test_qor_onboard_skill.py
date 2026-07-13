"""Phase 189 (GH #241): /qor-onboard tutorial workflow bundle.

Tests the machine-checkable core: admission admits the skill, the
handoff matrix resolves with it present, the structural bundle contract
holds, registration surfaces are consistent, and the narration files
carry no definitional prose for glossary terms (the term-drift ABORT
class stays locked out).
"""
from __future__ import annotations

import re
from pathlib import Path

from qor.reliability.gate_skill_matrix import _skills_root, build_matrix, collect_skills
from qor.reliability.skill_admission import check_admission, discover_skills, parse_frontmatter

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "qor" / "skills" / "meta" / "qor-onboard"
SKILL_MD = SKILL_DIR / "SKILL.md"

CHAIN = ["ideate", "research", "plan", "audit", "implement", "substantiate"]


def test_skill_admission_admits_onboard():
    skills = discover_skills(REPO_ROOT / "qor" / "skills")
    assert "qor-onboard" in skills, "skill directory missing from corpus walk"
    ok, reason = check_admission("qor-onboard", skills)
    assert ok, reason


def test_gate_skill_matrix_resolves_with_onboard():
    skills = collect_skills(_skills_root())
    assert "qor-onboard" in skills
    _, broken = build_matrix(skills)
    assert not broken, f"broken handoffs: {broken}"


def test_bundle_structural_contract():
    text = SKILL_MD.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    assert fm is not None, "missing frontmatter"
    assert fm.get("type") == "workflow-bundle"
    phases_line = fm.get("phases", "")
    positions = [phases_line.find(p) for p in CHAIN]
    assert all(p >= 0 for p in positions), f"phases must list the chain: {phases_line}"
    assert positions == sorted(positions), f"phases must be in chain order: {phases_line}"
    for ref in ("tutorial-narration.md", "improvement-scan.md"):
        assert (SKILL_DIR / "references" / ref).exists(), f"missing references/{ref}"
        assert ref in text, f"SKILL.md must cite references/{ref}"


def test_registry_and_badge_updated():
    registry = (REPO_ROOT / "docs" / "SKILL_REGISTRY.md").read_text(encoding="utf-8")
    assert "| qor-onboard |" in registry, "SKILL_REGISTRY missing the qor-onboard row"
    row_count = len(re.findall(r"^\| qor-", registry, re.MULTILINE))
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    badge = re.search(r"Skills-(\d+)-blue", readme)
    assert badge, "README skills badge missing"
    assert int(badge.group(1)) == row_count, (
        f"README badge says {badge.group(1)} skills; registry has {row_count} rows"
    )


def test_no_definitional_prose_for_glossary_terms():
    """LD-2: the tutorial LINKS terms to glossary homes; it never restates a
    definition ('<Term> is/means/refers to ...' registers as term drift)."""
    glossary = (REPO_ROOT / "qor" / "references" / "glossary.md").read_text(encoding="utf-8")
    terms = re.findall(r"^term: (.+)$", glossary, re.MULTILINE)
    offenders: list[str] = []
    for md in [SKILL_MD, *sorted((SKILL_DIR / "references").glob("*.md"))]:
        text = md.read_text(encoding="utf-8")
        for term in terms:
            pattern = re.compile(
                rf"^{re.escape(term)}\s+(?:is|means|refers to)\b", re.MULTILINE | re.IGNORECASE
            )
            if pattern.search(text):
                offenders.append(f"{md.name}: {term}")
    assert not offenders, f"definitional prose for glossary terms: {offenders}"
